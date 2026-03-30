"""
app.py — 主应用程序外壳
Tab 导航 + 视图切换 + 标题栏 + API 服务器控制
"""

import customtkinter as ctk
import tkinter as tk
from theme import *
from models import AutomationStore
from view_manage import ManageView
from view_config import ConfigView
from widgets import Toast
from api_server import ApiServer, API_HOST, API_PORT


# 全局 customtkinter 设置
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class AutoFlowApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.store = AutomationStore()

        self.title("AutoFlow — 可视化自动化管理平台")
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.configure(fg_color=BG)

        # 初始化 API 服务器
        self._api_server = ApiServer(
            store=self.store,
            on_status=self._on_api_status,
            on_log=self._on_api_log,
        )

        self._build_header()
        self._build_tabs()
        self._build_views()
        self._show_manage()

        # 窗口关闭时停止服务器
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 标题栏 ────────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(header, fg_color=ACCENT, corner_radius=6,
                                   width=28, height=28)
        logo_frame.pack(side="left", padx=(18, 8), pady=12)
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=14),
                     text_color="#000").pack(expand=True)

        ctk.CTkLabel(header, text="AUTOFLOW",
                     font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
                     text_color=ACCENT).pack(side="left")

        # ── 右侧：API 服务器控制区 ──
        api_area = ctk.CTkFrame(header, fg_color="transparent")
        api_area.pack(side="right", padx=16)

        # 状态指示灯 + 地址
        self._api_dot = ctk.CTkLabel(api_area, text="●",
                                      font=ctk.CTkFont(size=13),
                                      text_color=TEXT_MUTED)
        self._api_dot.pack(side="left", padx=(0, 4))

        self._api_status_lbl = ctk.CTkLabel(
            api_area,
            text=f"API 未启动",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=TEXT_MUTED)
        self._api_status_lbl.pack(side="left", padx=(0, 10))

        # 启动/停止按钮
        self._api_btn = ctk.CTkButton(
            api_area, text="启动 API",
            width=90, height=28,
            fg_color=ACCENT_BG, hover_color=ACCENT_BG2,
            border_color=ACCENT, border_width=1,
            text_color=ACCENT,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._toggle_api)
        self._api_btn.pack(side="left")

        # 查看文档按钮
        self._api_doc_btn = ctk.CTkButton(
            api_area, text="接口文档",
            width=72, height=28,
            fg_color=SURFACE2, hover_color=SURFACE3,
            border_color=BORDER_HI, border_width=1,
            text_color=TEXT_DIM,
            font=ctk.CTkFont(size=11),
            command=self._show_api_doc,
            state="disabled")
        self._api_doc_btn.pack(side="left", padx=(6, 0))

        # 分割线
        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

    # ── Tab 栏 ────────────────────────────────────────────────────────────

    def _build_tabs(self):
        tab_bar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=42)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        self._tab_btns = {}
        tabs = [
            ("manage", "📋  管理中心"),
            ("config", "⚙  配置编辑"),
        ]
        for key, label in tabs:
            btn = _TabButton(tab_bar, text=label,
                             command=lambda k=key: self._on_tab(k))
            btn.pack(side="left")
            self._tab_btns[key] = btn

        self._badge = ctk.CTkLabel(tab_bar,
                                    text=self._badge_text(),
                                    fg_color=ACCENT, corner_radius=10,
                                    text_color="#000",
                                    font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
                                    padx=7, pady=1)
        self._badge.pack(side="left", padx=2)

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

    def _badge_text(self):
        return str(len(self.store.all()))

    def _on_tab(self, key: str):
        if key == "manage":
            self._show_manage()
        elif key == "config":
            self._config_view.load_new()
            self._show_config()

    def _set_active_tab(self, key: str):
        for k, btn in self._tab_btns.items():
            btn.set_active(k == key)

    # ── 视图区 ────────────────────────────────────────────────────────────

    def _build_views(self):
        self._view_container = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._view_container.pack(fill="both", expand=True)

        self._manage_view = ManageView(
            self._view_container,
            store=self.store,
            on_edit=self._edit_automation,
            on_new=self._new_automation,
        )
        self._config_view = ConfigView(
            self._view_container,
            store=self.store,
            on_save=self._on_config_saved,
            on_cancel=self._show_manage,
        )

    def _show_manage(self):
        self._config_view.place_forget()
        self._manage_view.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._manage_view.refresh()
        self._set_active_tab("manage")
        self._badge.configure(text=self._badge_text())

    def _show_config(self):
        self._manage_view.place_forget()
        self._config_view.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._set_active_tab("config")

    # ── API 服务器控制 ────────────────────────────────────────────────────

    def _toggle_api(self):
        self._api_server.toggle()

    def _on_api_status(self, running: bool, msg: str):
        """服务器状态变化 → 更新 UI（需在主线程执行）"""
        def _update():
            if running:
                self._api_dot.configure(text_color=ACCENT)
                self._api_status_lbl.configure(
                    text=f"http://{API_HOST}:{API_PORT}",
                    text_color=ACCENT)
                self._api_btn.configure(
                    text="停止 API",
                    fg_color=ACCENT3_BG, hover_color=ACCENT3_BG2,
                    border_color=ACCENT3, text_color=ACCENT3)
                self._api_doc_btn.configure(state="normal")
                Toast.show(self, f"API 服务已启动 :{API_PORT}", "success")
            else:
                self._api_dot.configure(text_color=TEXT_MUTED)
                self._api_status_lbl.configure(text="API 未启动", text_color=TEXT_MUTED)
                self._api_btn.configure(
                    text="启动 API",
                    fg_color=ACCENT_BG, hover_color=ACCENT_BG2,
                    border_color=ACCENT, text_color=ACCENT)
                self._api_doc_btn.configure(state="disabled")
                Toast.show(self, "API 服务已停止", "info")
        self.after(0, _update)

    def _on_api_log(self, msg: str):
        """API 日志（目前仅打印，可扩展到日志面板）"""
        print(msg)

    def _show_api_doc(self):
        """显示接口文档弹窗"""
        ApiDocPopup(self)

    # ── 回调 ─────────────────────────────────────────────────────────────

    def _new_automation(self):
        self._config_view.load_new()
        self._show_config()

    def _edit_automation(self, aid: str):
        self._config_view.load_automation(aid)
        self._show_config()

    def _on_config_saved(self, automation):
        Toast.show(self, f"「{automation.name}」已保存 ✓", "success")
        self._show_manage()

    def _on_close(self):
        if self._api_server.running:
            self._api_server.stop()
        self.destroy()


# ── API 文档弹窗 ──────────────────────────────────────────────────────────

class ApiDocPopup(ctk.CTkToplevel):
    """接口文档总览"""

    def __init__(self, master):
        super().__init__(master)
        self.title("AutoFlow API 接口文档")
        self.geometry("620x540")
        self.configure(fg_color=SURFACE)
        self.transient(master)
        self.grab_set()
        self._build(master)

    def _build(self, master):
        # 标题
        hdr = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"🔌  AutoFlow API  —  http://{API_HOST}:{API_PORT}",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=16, pady=12)

        body = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        doc = f"""# AutoFlow HTTP API

基础地址：http://{API_HOST}:{API_PORT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET  /api/ping
  测试服务是否在运行

GET  /api/tasks
  获取所有已发布任务列表

GET  /api/tasks/{{task_id}}
  获取单个任务详情及调用示例

POST /api/run
  执行指定任务（同步，执行完成后返回）

  请求体（JSON）：
  {{
    "task_id": "任务ID",
    "params": {{
      "组件名称": "填写的值",
      ...
    }}
  }}

  响应示例（成功）：
  {{
    "success": true,
    "message": "执行完成 ✓",
    "task_id": "demo01",
    "task_name": "登录表单自动填写",
    "log": ["▶ 开始执行...", ...]
  }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

params 填写规则：
  输入组件  →  "组件名": "文本内容"
  上传组件  →  "组件名": "C:/path/file.jpg"
  按钮组件  →  自动点击，无需传参
  对象组件  →  自动点击图标，无需传参

注意：任务必须先在管理中心「发布」才能调用
"""
        tb = ctk.CTkTextbox(body,
                             font=ctk.CTkFont(family="Consolas", size=11),
                             fg_color=BG, text_color=TEXT_DIM,
                             border_width=0, corner_radius=0)
        tb.pack(fill="both", expand=True, padx=16, pady=12)
        tb.insert("1.0", doc)
        tb.configure(state="disabled")

        footer = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0)
        footer.pack(fill="x")

        def copy_base():
            self.clipboard_clear()
            self.clipboard_append(f"http://{API_HOST}:{API_PORT}")
            Toast.show(self, "已复制基础地址", "success")

        ctk.CTkButton(footer, text="📋 复制地址", width=100, height=32,
                      fg_color=ACCENT_BG, hover_color=ACCENT_BG2,
                      border_color=ACCENT, border_width=1,
                      text_color=ACCENT, font=ctk.CTkFont(size=11),
                      command=copy_base).pack(side="right", padx=(4, 12), pady=8)
        ctk.CTkButton(footer, text="关闭", width=72, height=32,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM, font=ctk.CTkFont(size=11),
                      command=self.destroy).pack(side="right", padx=4, pady=8)


# ── Tab 按钮组件 ──────────────────────────────────────────────────────────

class _TabButton(ctk.CTkFrame):
    def __init__(self, master, text: str, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", cursor="hand2", **kwargs)
        self._cmd = command
        self._active = False

        self._lbl = ctk.CTkLabel(self, text=text,
                                  font=ctk.CTkFont(size=13),
                                  text_color=TEXT_MUTED,
                                  padx=18, pady=10)
        self._lbl.pack()

        self._bar = ctk.CTkFrame(self, fg_color="transparent", height=2, corner_radius=0)
        self._bar.pack(fill="x")

        self.bind("<Button-1>", self._click)
        self._lbl.bind("<Button-1>", self._click)
        self._lbl.bind("<Enter>", lambda e: self._hover(True))
        self._lbl.bind("<Leave>", lambda e: self._hover(False))

    def _click(self, e=None):
        if self._cmd:
            self._cmd()

    def _hover(self, on: bool):
        if not self._active:
            self._lbl.configure(text_color=TEXT_DIM if on else TEXT_MUTED)

    def set_active(self, active: bool):
        self._active = active
        self._lbl.configure(text_color=ACCENT if active else TEXT_MUTED)
        self._bar.configure(fg_color=ACCENT if active else "transparent")
