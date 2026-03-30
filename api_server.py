"""
api_server.py — AutoFlow HTTP API 服务器
使用 Python 内置 http.server，无需额外依赖
启动后监听 localhost:8765，接受 POST /api/run 请求
"""

import json
import threading
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional
from models import AutomationStore, Automation
from engine import TaskRunner


API_HOST = "127.0.0.1"
API_PORT = 8765


class AutoFlowHandler(BaseHTTPRequestHandler):
    """处理所有 HTTP 请求"""

    # 注入的依赖（由 ApiServer 设置）
    store: AutomationStore = None
    on_log: Callable = None

    def log_message(self, fmt, *args):
        # 屏蔽默认的 stderr 日志，改用我们自己的
        msg = fmt % args
        if self.on_log:
            self.on_log(f"[HTTP] {msg}")

    def do_OPTIONS(self):
        """处理跨域预检"""
        self._send_cors_headers(200)
        self.end_headers()

    def do_GET(self):
        """GET /api/tasks — 列出所有任务"""
        if self.path == "/api/tasks":
            tasks = [
                {
                    "id": a.id,
                    "name": a.name,
                    "published": a.published,
                    "component_count": len(a.components),
                    "updated_at": a.updated_at,
                }
                for a in self.store.all()
            ]
            self._json(200, {"success": True, "tasks": tasks})
        elif self.path.startswith("/api/tasks/"):
            aid = self.path.split("/api/tasks/")[-1]
            a = self.store.get(aid)
            if a:
                self._json(200, {"success": True, "task": self._auto_detail(a)})
            else:
                self._json(404, {"success": False, "error": f"任务 {aid} 不存在"})
        elif self.path == "/api/ping":
            self._json(200, {"success": True, "message": "AutoFlow API 运行中", "port": API_PORT})
        else:
            self._json(404, {"success": False, "error": "接口不存在"})

    def do_POST(self):
        """POST /api/run — 执行任务"""
        if self.path != "/api/run":
            self._json(404, {"success": False, "error": "接口不存在"})
            return

        # 读取请求体
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
        except Exception as e:
            self._json(400, {"success": False, "error": f"请求体解析失败：{e}"})
            return

        task_id = payload.get("task_id", "")
        params = payload.get("params", {})

        if not task_id:
            self._json(400, {"success": False, "error": "缺少 task_id"})
            return

        a = self.store.get(task_id)
        if not a:
            self._json(404, {"success": False, "error": f"任务 {task_id} 不存在"})
            return

        if not a.published:
            self._json(403, {"success": False, "error": f"任务「{a.name}」未发布，请先在管理中心发布"})
            return

        # 同步执行（最多等 60 秒）
        result = {"ok": False, "msg": "超时"}
        done_event = threading.Event()
        logs = []

        def on_log(msg):
            logs.append(msg)
            if self.on_log:
                self.on_log(msg)

        def on_done(ok, msg):
            result["ok"] = ok
            result["msg"] = msg
            done_event.set()

        runner = TaskRunner(automation=a, params=params,
                            on_log=on_log, on_done=on_done)
        runner.run_async()
        done_event.wait(timeout=120)

        status = 200 if result["ok"] else 500
        self._json(status, {
            "success": result["ok"],
            "message": result["msg"],
            "task_id": task_id,
            "task_name": a.name,
            "log": logs,
        })

    # ── 辅助方法 ──────────────────────────────────────────────────────────

    def _send_cors_headers(self, code: int):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self._send_cors_headers(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auto_detail(self, a: Automation) -> dict:
        return {
            "id": a.id,
            "name": a.name,
            "published": a.published,
            "updated_at": a.updated_at,
            "components": [
                {"type": c.type, "name": c.name, "x": c.x, "y": c.y}
                for c in a.components
            ],
            "api_example": {
                "method": "POST",
                "url": f"http://{API_HOST}:{API_PORT}/api/run",
                "body": a.generate_api_doc(),
            }
        }


class ApiServer:
    """
    在后台线程中运行 HTTP 服务器
    on_status(running: bool, msg: str) — 状态变化回调（供 UI 显示）
    on_log(msg: str) — 日志回调
    """

    def __init__(self, store: AutomationStore,
                 on_status: Callable = None,
                 on_log: Callable = None):
        self.store = store
        self.on_status = on_status or (lambda r, m: None)
        self.on_log = on_log or (lambda m: None)
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self.running = False

    def start(self):
        if self.running:
            return
        try:
            # 动态注入依赖到 handler
            store = self.store
            log_fn = self.on_log

            class _Handler(AutoFlowHandler):
                pass
            _Handler.store = store
            _Handler.on_log = log_fn

            self._server = HTTPServer((API_HOST, API_PORT), _Handler)
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
            self.running = True
            self.on_status(True, f"API 服务已启动  http://{API_HOST}:{API_PORT}")
            self.on_log(f"✓ AutoFlow API 服务器启动成功，监听 {API_HOST}:{API_PORT}")
        except OSError as e:
            msg = f"启动失败：端口 {API_PORT} 已被占用，请关闭占用程序后重试"
            self.on_status(False, msg)
            self.on_log(f"✕ {msg}\n  原始错误：{e}")
        except Exception as e:
            msg = f"启动失败：{e}"
            self.on_status(False, msg)
            self.on_log(f"✕ {msg}\n{traceback.format_exc()}")

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None
        self.running = False
        self.on_status(False, "API 服务已停止")
        self.on_log("⏹ API 服务器已停止")

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()
