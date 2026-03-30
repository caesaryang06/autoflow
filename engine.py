"""
engine.py — PyAutoGUI 自动化执行引擎
负责将组件配置转化为真实的鼠标/键盘操作
"""

import time
import threading
import os
from typing import Dict, Any, Callable, Optional
from models import Automation, Component
import pyperclip


# 安全导入 pyautogui（允许无显示器环境不崩溃）
try:
    import pyautogui
    pyautogui.FAILSAFE = True       # 鼠标移到左上角紧急停止
    pyautogui.PAUSE = 0.3           # 每步操作间隔
    HAS_PYAUTOGUI = True
except Exception:
    HAS_PYAUTOGUI = False


class ExecutionError(Exception):
    pass


class TaskRunner:
    """
    执行单个 Automation 任务
    
    参数 params: { 组件名称 -> 值 }
      - input  组件: str 文本
      - upload 组件: str 文件路径
      - button 组件: bool (True=点击)
    """

    def __init__(
        self,
        automation: Automation,
        params: Dict[str, Any],
        on_log: Optional[Callable[[str], None]] = None,
        on_done: Optional[Callable[[bool, str], None]] = None,
    ):
        self.automation = automation
        self.params = params
        self.on_log = on_log or (lambda msg: None)
        self.on_done = on_done or (lambda ok, msg: None)
        self._stop = False

    def stop(self):
        self._stop = True

    def run_async(self):
        """在后台线程中执行，不阻塞 UI"""
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        try:
            self._execute()
            self.on_done(True, "执行完成 ✓")
        except ExecutionError as e:
            self.on_done(False, f"执行失败：{e}")
        except Exception as e:
            self.on_done(False, f"未知错误：{e}")

    def _execute(self):
        if not HAS_PYAUTOGUI:
            raise ExecutionError("pyautogui 未安装或当前环境不支持")

        self._log(f"▶ 开始执行：{self.automation.name}")
        self._log(f"  共 {len(self.automation.components)} 个组件")
        time.sleep(0.8)  # 给用户切换窗口的时间

        for i, comp in enumerate(self.automation.components):
            if self._stop:
                self._log("⏹ 已手动停止")
                return

            self._log(f"\n[{i+1}/{len(self.automation.components)}] {comp.name} ({comp.type})")
            self._log(f"  坐标 → ({comp.x}, {comp.y})")

            try:
                self._handle_component(comp)
            except pyautogui.FailSafeException:
                raise ExecutionError("触发紧急停止（鼠标移至屏幕左上角）")
            except Exception as e:
                raise ExecutionError(f"组件「{comp.name}」执行出错：{e}")

        self._log("\n✓ 所有组件执行完毕")

    def _handle_component(self, comp: Component):
        value = self.params.get(comp.name, comp.value)

        if comp.type == "object":
            # ── 对象组件：点击任务栏/桌面图标，激活/打开软件 ──
            self._log(f"  🖥  激活软件：{comp.name}")
            pyautogui.moveTo(comp.x, comp.y, duration=0.5)
            time.sleep(0.15)
            pyautogui.click()
            obj_wait = self._parse_wait(comp.extra_wait, default=2)
            self._log(f"  ⏳ 等待软件就绪 {obj_wait}s ...")
            time.sleep(obj_wait)

        else:
            # ── 所有其他组件：先移动到坐标 ──
            pyautogui.moveTo(comp.x, comp.y, duration=0.4)
            time.sleep(0.1)

            if comp.type == "input":
                pyautogui.click()
                time.sleep(0.2)
                pyautogui.hotkey("ctrl", "a")
                time.sleep(0.1)
                if value:
                    pyperclip.copy(str(value))
                    pyautogui.hotkey("ctrl", "v")
                    self._log(f"  ✍ 已输入：{value}")
                else:
                    self._log(f"  ⚠ 无值，跳过输入")

            elif comp.type == "upload":
                pyautogui.click()
                time.sleep(1.0)
                if value and os.path.exists(str(value)):
                    pyperclip.copy(str(value))
                    pyautogui.hotkey("ctrl", "v")
                    time.sleep(0.2)
                    pyautogui.press("enter")
                    self._log(f"  📎 已上传：{value}")
                else:
                    pyautogui.press("escape")
                    self._log(f"  ⚠ 文件不存在或未指定：{value}")

            elif comp.type == "button":
                pyautogui.click()
                self._log(f"  🖱 已点击")

            elif comp.type == "enter":
                # ── 回车组件：移动到坐标后按回车键 ──
                pyautogui.click()
                time.sleep(0.1)
                pyautogui.press("enter")
                self._log(f"  ↵ 已按回车")

            # ── 通用等待时长（每个组件执行后） ──
            extra = self._parse_wait(comp.extra_wait, default=0)
            if extra > 0:
                self._log(f"  ⏳ 等待 {extra}s ...")
                time.sleep(extra)
            else:
                time.sleep(0.3)  # 最短间隔

    @staticmethod
    def _parse_wait(val: str, default: float = 0) -> float:
        """安全解析等待秒数字符串"""
        try:
            v = float(str(val).strip())
            return max(0.0, v)
        except (ValueError, TypeError):
            return default

    def _log(self, msg: str):
        self.on_log(msg)


class ScreenHelper:
    """屏幕辅助工具：坐标拾取、截图"""

    @staticmethod
    def get_mouse_pos():
        """实时获取鼠标坐标"""
        if not HAS_PYAUTOGUI:
            return (0, 0)
        return pyautogui.position()

    @staticmethod
    def screenshot_region(x, y, w=100, h=100):
        """截取指定区域截图"""
        if not HAS_PYAUTOGUI:
            return None
        try:
            return pyautogui.screenshot(region=(x - w//2, y - h//2, w, h))
        except Exception:
            return None

    @staticmethod
    def screen_size():
        if not HAS_PYAUTOGUI:
            return (1920, 1080)
        return pyautogui.size()
