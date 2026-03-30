"""
widgets.py — 可复用自定义组件
Toast 通知、确认弹窗、组件卡片、坐标拾取器等
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
from theme import *


# ── Toast 通知 ─────────────────────────────────────────────────────────────

class Toast:
    """右下角短暂弹出通知"""

    _queue = []

    @staticmethod
    def show(master, message: str, kind: str = "success"):
        """
        kind: success | error | info | warn
        """
        colors = {
            "success": (ACCENT,   "✓"),
            "error":   (ACCENT3,  "✕"),
            "info":    (ACCENT2,  "ℹ"),
            "warn":    (ACCENT4,  "⚠"),
        }
        color, icon = colors.get(kind, (ACCENT, "·"))

        win = tk.Toplevel(master)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=SURFACE)

        frame = tk.Frame(win, bg=SURFACE, highlightbackground=color,
                         highlightthickness=1, padx=14, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=f"{icon}  {message}", bg=SURFACE, fg=TEXT,
                 font=FONT_BODY).pack()

        # 定位到右下角
        def _place():
            win.update_idletasks()
            sw = master.winfo_screenwidth()
            sh = master.winfo_screenheight()
            w = win.winfo_width()
            h = win.winfo_height()
            win.geometry(f"+{sw - w - 24}+{sh - h - 64}")

        master.after(10, _place)

        def _close():
            try:
                win.destroy()
            except Exception:
                pass

        master.after(2500, _close)


# ── 确认弹窗 ───────────────────────────────────────────────────────────────

class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, message: str):
        super().__init__(master)
        self.result = False
        self.title(title)
        self.geometry("340x160")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.grab_set()
        self.transient(master)

        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=13),
                     text_color=TEXT, wraplength=280).pack(pady=(28, 16))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(btn_frame, text="取消", width=100,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM,
                      command=self.destroy).pack(side="left", padx=6)

        ctk.CTkButton(btn_frame, text="确认删除", width=100,
                      fg_color=ACCENT3, hover_color="#cc5555",
                      text_color="#fff",
                      command=self._confirm).pack(side="left", padx=6)

        self.wait_window()

    def _confirm(self):
        self.result = True
        self.destroy()


# ── 组件卡片 ──────────────────────────────────────────────────────────────

class ComponentCard(ctk.CTkFrame):
    """
    画布中的单个组件卡片
    包含：类型标签、名称输入、X/Y输入、右键菜单
    回调：on_change(idx) / on_context(event, idx)
    """

    def __init__(self, master, comp_data: dict, idx: int,
                 on_change=None, on_context=None, **kwargs):
        color = COMP_TYPES[comp_data["type"]]["color"]
        super().__init__(master, fg_color=SURFACE, border_color=color,
                         border_width=2, corner_radius=RADIUS, **kwargs)

        self.comp_data = comp_data
        self.idx = idx
        self.on_change = on_change
        self.on_context = on_context

        self._build(color)
        self.bind("<Button-3>", self._right_click)
        self._bind_children(self, "<Button-3>", self._right_click)

    def _bind_children(self, widget, event, callback):
        widget.bind(event, callback)
        for child in widget.winfo_children():
            self._bind_children(child, event, callback)

    def _build(self, color):
        meta = COMP_TYPES[self.comp_data["type"]]

        # ── 顶部标题栏 ──
        header = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0)
        header.pack(fill="x")
        header.bind("<Button-3>", self._right_click)

        idx_lbl = ctk.CTkLabel(header, text=f"{self.idx+1:02d}",
                                font=ctk.CTkFont(family="Consolas", size=10),
                                text_color=TEXT_DIM, width=28)
        idx_lbl.pack(side="left", padx=(10, 0), pady=8)

        TYPE_BG = {
            "input":  ACCENT_BG,
            "upload": ACCENT2_BG,
            "button": ACCENT3_BG,
        }
        tag = ctk.CTkLabel(header,
                            text=f"{meta['icon']} {meta['tag']}",
                            font=ctk.CTkFont(size=10, weight="bold"),
                            text_color=color,
                            fg_color=TYPE_BG.get(self.comp_data["type"], SURFACE3),
                            corner_radius=10, padx=8, pady=2)
        tag.pack(side="left", padx=8)

        # 名称预览
        self._name_preview = ctk.CTkLabel(header, text=self.comp_data["name"] or "未命名",
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           text_color=TEXT)
        self._name_preview.pack(side="left", padx=4)

        hint = ctk.CTkLabel(header, text="右键操作", font=ctk.CTkFont(size=10),
                             text_color=TEXT_DIM)
        hint.pack(side="right", padx=12)

        # ── 内容区 ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=10)
        is_object = self.comp_data["type"] == "object"

        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_columnconfigure(2, weight=0)
        body.grid_columnconfigure(3, weight=0)

        # 名称
        name_lbl = "对象名称" if is_object else "组件名称"
        name_frame = ctk.CTkFrame(body, fg_color="transparent")
        name_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(name_frame, text=name_lbl, font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=TEXT_DIM).pack(anchor="w")
        self._name_var = tk.StringVar(value=self.comp_data["name"])
        name_entry = ctk.CTkEntry(name_frame, textvariable=self._name_var,
                                   fg_color=SURFACE2, border_color=BORDER_HI,
                                   text_color=TEXT, font=ctk.CTkFont(size=12))
        name_entry.pack(fill="x")
        self._name_var.trace_add("write", self._on_name_change)

        # X 坐标
        x_lbl = "图标 X" if is_object else "X 坐标"
        x_frame = ctk.CTkFrame(body, fg_color="transparent")
        x_frame.grid(row=0, column=1, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(x_frame, text=x_lbl, font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=TEXT_DIM).pack(anchor="w")
        self._x_var = tk.StringVar(value=str(self.comp_data["x"]))
        ctk.CTkEntry(x_frame, textvariable=self._x_var, width=72,
                     fg_color=SURFACE2, border_color=BORDER_HI,
                     text_color=TEXT, font=ctk.CTkFont(size=12)).pack()
        self._x_var.trace_add("write", self._on_coord_change)

        # Y 坐标
        y_lbl = "图标 Y" if is_object else "Y 坐标"
        y_frame = ctk.CTkFrame(body, fg_color="transparent")
        y_frame.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(y_frame, text=y_lbl, font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=TEXT_DIM).pack(anchor="w")
        self._y_var = tk.StringVar(value=str(self.comp_data["y"]))
        ctk.CTkEntry(y_frame, textvariable=self._y_var, width=72,
                     fg_color=SURFACE2, border_color=BORDER_HI,
                     text_color=TEXT, font=ctk.CTkFont(size=12)).pack()
        self._y_var.trace_add("write", self._on_coord_change)

        # 等待时长（所有组件通用）
        wait_lbl = "等待(秒)" if not is_object else "启动等待"
        wait_color = ACCENT4 if is_object else TEXT_MUTED
        wait_border = ACCENT4_BG2 if is_object else BORDER_HI
        w_frame = ctk.CTkFrame(body, fg_color="transparent")
        w_frame.grid(row=0, column=3, sticky="ew")
        ctk.CTkLabel(w_frame, text=wait_lbl,
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=wait_color).pack(anchor="w")
        default_wait = "2" if is_object else "0"
        self._wait_var = tk.StringVar(
            value=str(self.comp_data.get("extra_wait", default_wait)))
        ctk.CTkEntry(w_frame, textvariable=self._wait_var, width=56,
                     fg_color=SURFACE2, border_color=wait_border,
                     text_color=wait_color, font=ctk.CTkFont(size=12)).pack()
        self._wait_var.trace_add("write", self._on_wait_change)

    def _on_name_change(self, *_):
        self.comp_data["name"] = self._name_var.get()
        self._name_preview.configure(text=self.comp_data["name"] or "未命名")
        if self.on_change:
            self.on_change(self.idx)

    def _on_coord_change(self, *_):
        try:
            self.comp_data["x"] = int(self._x_var.get())
        except ValueError:
            pass
        try:
            self.comp_data["y"] = int(self._y_var.get())
        except ValueError:
            pass
        if self.on_change:
            self.on_change(self.idx)

    def _on_wait_change(self, *_):
        if self._wait_var:
            self.comp_data["extra_wait"] = self._wait_var.get()
        if self.on_change:
            self.on_change(self.idx)

    def _right_click(self, event):
        if self.on_context:
            self.on_context(event, self.idx)

    def get_data(self) -> dict:
        return self.comp_data.copy()


# ── 右键菜单 ──────────────────────────────────────────────────────────────

class ContextMenu:
    """浮动右键菜单"""

    def __init__(self, master):
        self.master = master
        self._win = None

    def show(self, x, y, on_up, on_down, on_delete):
        self.close()
        win = tk.Toplevel(self.master)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=SURFACE, highlightbackground=BORDER_HI, highlightthickness=1)
        self._win = win

        items = [
            ("⬆  上移", ACCENT2, on_up),
            ("⬇  下移", ACCENT2, on_down),
            None,  # separator
            ("🗑  删除", ACCENT3, on_delete),
        ]

        for item in items:
            if item is None:
                sep = tk.Frame(win, bg=BORDER, height=1)
                sep.pack(fill="x", padx=4, pady=2)
            else:
                label, color, cmd = item
                def _make_btn(c, w):
                    btn = tk.Label(w, text=c[0], bg=SURFACE, fg=c[1],
                                   font=("微软雅黑", 12), padx=16, pady=7,
                                   anchor="w", cursor="hand2")
                    btn.pack(fill="x")

                    def _enter(e): btn.configure(bg=SURFACE3)
                    def _leave(e): btn.configure(bg=SURFACE)
                    def _click(e):
                        self.close()
                        c[2]()

                    btn.bind("<Enter>", _enter)
                    btn.bind("<Leave>", _leave)
                    btn.bind("<Button-1>", _click)

                _make_btn(item, win)

        win.geometry(f"+{x}+{y}")

        # 点击其他地方关闭
        self.master.bind("<Button-1>", lambda e: self.close(), add="+")

    def close(self):
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None


# ── 坐标拾取器 ────────────────────────────────────────────────────────────

class CoordPicker(ctk.CTkToplevel):
    """
    悬浮窗口实时显示鼠标坐标
    用户点击「选定」后返回坐标给回调
    """

    def __init__(self, master, on_pick=None):
        super().__init__(master)
        self.on_pick = on_pick
        self.title("坐标拾取器")
        self.geometry("300x200")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.attributes("-topmost", True)
        # 不使用 grab_set，避免抢占焦点导致按钮无响应

        self._running = True
        self._x = 0
        self._y = 0

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 窗口居中
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"300x200+{(sw-300)//2}+{(sh-200)//2}")

        self._poll()

    def _build(self):
        # 标题提示
        ctk.CTkLabel(self, text="将鼠标移动到目标位置",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_DIM).pack(pady=(18, 4))

        ctk.CTkLabel(self, text="当前鼠标坐标",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=TEXT_MUTED).pack()

        self._coord_lbl = ctk.CTkLabel(
            self, text="X: ——   Y: ——",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            text_color=ACCENT)
        self._coord_lbl.pack(pady=(6, 18))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row, text="✓  选定此位置", width=130, height=36,
            fg_color=ACCENT, hover_color=ACCENT_DIM,
            text_color="#000", font=ctk.CTkFont(size=13, weight="bold"),
            command=self._pick
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="取消", width=72, height=36,
            fg_color=SURFACE3, hover_color=BORDER_HI,
            text_color=TEXT_DIM, font=ctk.CTkFont(size=12),
            command=self._on_close
        ).pack(side="left")

    def _poll(self):
        if not self._running:
            return
        try:
            # 直接用 winfo_pointerxy 读取系统鼠标绝对坐标，不依赖 pyautogui
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            self._x, self._y = x, y
            self._coord_lbl.configure(text=f"X: {x}   Y: {y}")
        except Exception:
            pass
        self.after(80, self._poll)

    def _pick(self):
        x, y = self._x, self._y
        self._on_close()  # 先关闭窗口
        if self.on_pick:
            # after 延迟确保窗口已销毁再执行回调
            try:
                self.master.after(50, lambda: self.on_pick(x, y))
            except Exception:
                pass

    def _on_close(self):
        self._running = False
        try:
            self.destroy()
        except Exception:
            pass
