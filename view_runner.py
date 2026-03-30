"""
view_runner.py — 任务执行视图（弹窗）
可视化填参 + 实时执行日志 + 停止
"""

import customtkinter as ctk
import tkinter as tk
from theme import *
from widgets import Toast
from engine import TaskRunner, HAS_PYAUTOGUI
from models import Automation


class RunDialog(ctk.CTkToplevel):
    """
    执行一个自动化任务的对话框
    - 列出所有 input/upload 组件，让用户填写参数
    - 点击执行后倒计时 3 秒（让用户切换窗口）
    - 实时显示执行日志
    - 支持强制停止
    """

    def __init__(self, master, auto: Automation):
        super().__init__(master)
        self.auto = auto
        self._runner = None
        self._param_vars = {}

        self.title(f"执行 — {auto.name}")
        self.geometry("600x560")
        self.resizable(True, True)
        self.configure(fg_color=SURFACE)
        self.grab_set()
        self.transient(master)
        self._build()

    def _build(self):
        # 顶部标题
        hdr = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"▶  {self.auto.name}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=16, pady=12)

        comp_count = len(self.auto.components)
        ctk.CTkLabel(hdr, text=f"{comp_count} 个组件",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(family="Consolas", size=10)).pack(side="right", padx=16)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── 左侧：参数填写 ──
        left = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=RADIUS)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkLabel(left, text="参数配置",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(10, 6))

        params_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                                corner_radius=0)
        params_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        has_params = False
        for comp in self.auto.components:
            if comp.type == "object":
                has_params = True
                item = ctk.CTkFrame(params_scroll, fg_color=SURFACE2,
                                     border_color=COLOR_OBJECT, border_width=1,
                                     corner_radius=RADIUS)
                item.pack(fill="x", pady=4)
                row = ctk.CTkFrame(item, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"🖥  {comp.name}",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=TEXT).pack(side="left")
                wait = comp.extra_wait if comp.extra_wait else "2"
                ctk.CTkLabel(row, text=f"点击({comp.x},{comp.y}) → 等待{wait}s",
                             font=ctk.CTkFont(family="Consolas", size=10),
                             text_color=ACCENT4).pack(side="right")

            elif comp.type == "enter":
                has_params = True
                item = ctk.CTkFrame(params_scroll, fg_color=SURFACE2,
                                     border_color=COLOR_ENTER, border_width=1,
                                     corner_radius=RADIUS)
                item.pack(fill="x", pady=4)
                row = ctk.CTkFrame(item, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"↵  {comp.name}",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=TEXT).pack(side="left")
                extra = comp.extra_wait or "0"
                ctk.CTkLabel(row, text=f"移动到({comp.x},{comp.y}) → 按回车  等待{extra}s",
                             font=ctk.CTkFont(family="Consolas", size=10),
                             text_color=COLOR_ENTER).pack(side="right")

            elif comp.type in ("input", "upload"):
                has_params = True
                color = COLOR_INPUT if comp.type == "input" else COLOR_UPLOAD
                meta = COMP_TYPES[comp.type]

                item = ctk.CTkFrame(params_scroll, fg_color=SURFACE2,
                                     border_color=color, border_width=1,
                                     corner_radius=RADIUS)
                item.pack(fill="x", pady=4)

                top = ctk.CTkFrame(item, fg_color="transparent")
                top.pack(fill="x", padx=10, pady=(8, 0))
                ctk.CTkLabel(top, text=f"{meta['icon']} {comp.name}",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=TEXT).pack(side="left")
                ctk.CTkLabel(top, text=f"({comp.x}, {comp.y})",
                             font=ctk.CTkFont(family="Consolas", size=10),
                             text_color=TEXT_MUTED).pack(side="right")

                var = tk.StringVar(value=comp.value)
                self._param_vars[comp.name] = var

                if comp.type == "input":
                    entry = ctk.CTkEntry(item, textvariable=var,
                                         placeholder_text="输入内容...",
                                         fg_color=BG, border_color=BORDER,
                                         text_color=TEXT,
                                         font=ctk.CTkFont(size=12))
                    entry.pack(fill="x", padx=10, pady=(4, 10))
                elif comp.type == "upload":
                    row = ctk.CTkFrame(item, fg_color="transparent")
                    row.pack(fill="x", padx=10, pady=(4, 10))
                    ctk.CTkEntry(row, textvariable=var,
                                 placeholder_text="/path/to/file",
                                 fg_color=BG, border_color=BORDER,
                                 text_color=TEXT,
                                 font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(0, 6))
                    ctk.CTkButton(row, text="浏览", width=56,
                                  fg_color=SURFACE3, hover_color=BORDER_HI,
                                  text_color=TEXT_DIM,
                                  command=lambda v=var: self._browse(v)).pack(side="right")

            elif comp.type == "button":
                has_params = True
                item = ctk.CTkFrame(params_scroll, fg_color=SURFACE2,
                                     border_color=COLOR_BUTTON, border_width=1,
                                     corner_radius=RADIUS)
                item.pack(fill="x", pady=4)
                row = ctk.CTkFrame(item, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"🖱  {comp.name}",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=TEXT).pack(side="left")
                extra = comp.extra_wait or "0"
                ctk.CTkLabel(row, text=f"自动点击({comp.x},{comp.y})  等待{extra}s",
                             font=ctk.CTkFont(family="Consolas", size=10),
                             text_color=ACCENT3).pack(side="right")

        if not has_params:
            ctk.CTkLabel(params_scroll,
                         text="此任务无需填写参数\n点击执行即可自动运行",
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
                         justify="center").pack(pady=30)

        # ── 右侧：执行日志 ──
        right = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=RADIUS, width=240)
        right.pack(side="right", fill="both", expand=True)
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="执行日志",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(10, 6))

        self._log_box = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=BG,
            text_color=ACCENT,
            border_width=0,
            corner_radius=0,
            state="disabled",
        )
        self._log_box.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        # 底部控制栏
        footer = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0, height=56)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        if not HAS_PYAUTOGUI:
            ctk.CTkLabel(footer, text="⚠ pyautogui 未安装，将模拟执行",
                         text_color=ACCENT4, font=ctk.CTkFont(size=11)).pack(
                side="left", padx=16, pady=16)

        self._status_lbl = ctk.CTkLabel(footer, text="就绪",
                                         text_color=TEXT_MUTED,
                                         font=ctk.CTkFont(family="Consolas", size=11))
        self._status_lbl.pack(side="left", padx=16, pady=16)

        ctk.CTkButton(footer, text="关闭", width=80,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM, command=self._close).pack(
            side="right", padx=10, pady=10)

        self._stop_btn = ctk.CTkButton(footer, text="⏹ 停止", width=90,
                                        fg_color=ACCENT3_BG,
                                        hover_color=ACCENT3_BG2,
                                        text_color=ACCENT3, state="disabled",
                                        command=self._stop)
        self._stop_btn.pack(side="right", padx=4, pady=10)

        self._run_btn = ctk.CTkButton(footer, text="▶ 执行（3s后开始）", width=160,
                                       fg_color=ACCENT, hover_color=ACCENT_DIM,
                                       text_color="#000",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       command=self._start_countdown)
        self._run_btn.pack(side="right", padx=4, pady=10)

    # ── 文件浏览 ─────────────────────────────────────────────────────────

    def _browse(self, var: tk.StringVar):
        from tkinter import filedialog
        path = filedialog.askopenfilename(parent=self)
        if path:
            var.set(path)

    # ── 倒计时 ────────────────────────────────────────────────────────────

    def _start_countdown(self):
        self._run_btn.configure(state="disabled")
        self._log("⏳ 3 秒后开始执行，请切换到目标窗口...\n")
        self._countdown(3)

    def _countdown(self, n):
        if n <= 0:
            self._execute()
            return
        self._status_lbl.configure(text=f"倒计时 {n}s...")
        self._log(f"  {n}...")
        self.after(1000, lambda: self._countdown(n - 1))

    # ── 执行 ─────────────────────────────────────────────────────────────

    def _execute(self):
        self._status_lbl.configure(text="执行中...")
        self._stop_btn.configure(state="normal")
        self._log("\n")

        params = {k: v.get() for k, v in self._param_vars.items()}

        self._runner = TaskRunner(
            automation=self.auto,
            params=params,
            on_log=lambda msg: self.after(0, self._log, msg),
            on_done=lambda ok, msg: self.after(0, self._on_done, ok, msg),
        )
        self._runner.run_async()

    def _stop(self):
        if self._runner:
            self._runner.stop()
        self._log("\n⏹ 正在停止...")
        self._stop_btn.configure(state="disabled")

    def _on_done(self, ok: bool, msg: str):
        self._stop_btn.configure(state="disabled")
        self._run_btn.configure(state="normal", text="▶ 再次执行")
        self._status_lbl.configure(
            text=f"{'✓ 完成' if ok else '✕ 失败'}",
        )
        self._log(f"\n{'─'*30}\n{msg}")
        Toast.show(self.master, msg, "success" if ok else "error")

    # ── 日志 ─────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _close(self):
        if self._runner:
            self._runner.stop()
        self.destroy()
