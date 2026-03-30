"""
view_config.py — 配置编辑视图
左侧属性面板 + 右侧画布（组件卡片列表）
"""

import customtkinter as ctk
import tkinter as tk
from theme import *
from widgets import ComponentCard, ContextMenu, CoordPicker, Toast
from models import Component, Automation


class ConfigView(ctk.CTkFrame):
    """
    配置 / 编辑视图
    on_save(automation): 保存回调
    on_cancel(): 取消回调
    """

    def __init__(self, master, store, on_save=None, on_cancel=None, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.store = store
        self.on_save = on_save
        self.on_cancel = on_cancel
        self._editing_id = None
        self._components = []   # list of dict
        self._ctx_menu = ContextMenu(self)
        self._build()

    # ── 公开接口 ──────────────────────────────────────────────────────────

    def load_new(self):
        """新建模式"""
        self._editing_id = None
        self._components = []
        self._name_var.set("")
        self._refresh_canvas()

    def load_automation(self, aid: str):
        """加载已有任务"""
        a = self.store.get(aid)
        if not a:
            return
        self._editing_id = aid
        self._name_var.set(a.name)
        self._components = [
            {"type": c.type, "name": c.name, "x": c.x, "y": c.y,
             "value": c.value, "extra_wait": c.extra_wait}
            for c in a.components
        ]
        self._refresh_canvas()

    # ── 构建 UI ──────────────────────────────────────────────────────────

    def _build(self):
        # 主体水平分栏
        pane = ctk.CTkFrame(self, fg_color="transparent")
        pane.pack(fill="both", expand=True)

        # 左侧面板（固定宽度）
        self._build_left(pane)

        # 垂直分割线
        ctk.CTkFrame(pane, fg_color=BORDER, width=1, corner_radius=0).pack(
            side="left", fill="y")

        # 右侧画布
        self._build_right(pane)

    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=0, width=270)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # 面板标题
        title_bar = ctk.CTkFrame(left, fg_color=SURFACE2, corner_radius=0, height=40)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        ctk.CTkLabel(title_bar, text="🛠  属性配置",
                     font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                     text_color=TEXT_DIM).pack(side="left", padx=14, pady=10)

        # 任务名称
        name_sect = ctk.CTkFrame(left, fg_color="transparent")
        name_sect.pack(fill="x", padx=14, pady=(14, 0))
        ctk.CTkLabel(name_sect, text="任务名称",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DIM).pack(anchor="w")
        self._name_var = tk.StringVar()
        self._name_var.trace_add("write", self._on_name_change)
        ctk.CTkEntry(name_sect, textvariable=self._name_var,
                     placeholder_text="输入名称，如：表单提交助手",
                     fg_color=SURFACE2, border_color=BORDER_HI,
                     text_color=TEXT,
                     font=ctk.CTkFont(size=13)).pack(fill="x", pady=(4, 0))

        sep = ctk.CTkFrame(left, fg_color=BORDER, height=1, corner_radius=0)
        sep.pack(fill="x", pady=14)

        # 添加组件区域
        comp_sect = ctk.CTkFrame(left, fg_color="transparent")
        comp_sect.pack(fill="x", padx=14)
        ctk.CTkLabel(comp_sect, text="添加组件",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=TEXT_DIM).pack(anchor="w", pady=(0, 8))

        type_btns = [
            ("object", "🖥   对象组件", COLOR_OBJECT, "启动软件"),
            ("input",  "📝  输入组件", COLOR_INPUT,  "文本输入"),
            ("upload", "📎  上传组件", COLOR_UPLOAD, "文件上传"),
            ("button", "🖱   按钮组件", COLOR_BUTTON, "点击操作"),
            ("enter",  "↵    回车组件", COLOR_ENTER,  "按回车键"),
        ]
        for t, label, color, hint in type_btns:
            btn_frame = ctk.CTkFrame(comp_sect, fg_color=SURFACE2,
                                      border_color=BORDER_HI, border_width=1,
                                      corner_radius=RADIUS)
            btn_frame.pack(fill="x", pady=3)

            inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(inner, text="●", text_color=color,
                         font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(inner, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT).pack(side="left", padx=8)
            ctk.CTkLabel(inner, text=hint,
                         font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="right")

            # 整行可点击
            for w in [btn_frame, inner] + inner.winfo_children():
                w.bind("<Button-1>", lambda e, _t=t: self._add_comp(_t))
                w.configure(cursor="hand2")
            btn_frame.bind("<Enter>", lambda e, f=btn_frame, c=color:
                           f.configure(border_color=c))
            btn_frame.bind("<Leave>", lambda e, f=btn_frame:
                           f.configure(border_color=BORDER_HI))

        sep2 = ctk.CTkFrame(left, fg_color=BORDER, height=1, corner_radius=0)
        sep2.pack(fill="x", pady=14)

        # 说明
        hint_frame = ctk.CTkFrame(left, fg_color="transparent")
        hint_frame.pack(fill="x", padx=14)
        ctk.CTkLabel(hint_frame, text="使用说明",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_DIM).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(hint_frame,
                     text="• 对象组件放第一位，点击图标打开软件\n• 回车组件：移动到坐标后按回车\n• 右键组件可上移 / 下移 / 删除\n• X/Y 为屏幕像素坐标\n• 每个组件可设置执行后等待时长",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
                     justify="left", wraplength=230).pack(anchor="w")

    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        right.pack(side="left", fill="both", expand=True)

        # 工具栏
        toolbar = ctk.CTkFrame(right, fg_color=SURFACE, corner_radius=0, height=44)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text="画布 —", text_color=TEXT_DIM,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=14, pady=12)
        self._canvas_name_lbl = ctk.CTkLabel(toolbar, text="未命名",
                                              text_color=TEXT,
                                              font=ctk.CTkFont(size=13, weight="bold"))
        self._canvas_name_lbl.pack(side="left")

        self._comp_count_lbl = ctk.CTkLabel(toolbar, text="组件数: 0",
                                             text_color=TEXT_DIM,
                                             font=ctk.CTkFont(family="Consolas", size=11))
        self._comp_count_lbl.pack(side="right", padx=16)

        sep = ctk.CTkFrame(right, fg_color=BORDER, height=1, corner_radius=0)
        sep.pack(fill="x")

        # 画布滚动区
        self._canvas_scroll = ctk.CTkScrollableFrame(
            right, fg_color=BG, corner_radius=0,
            scrollbar_button_color=BORDER_HI,
            scrollbar_button_hover_color=TEXT_MUTED,
        )
        self._canvas_scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # 空状态
        self._empty_frame = ctk.CTkFrame(self._canvas_scroll, fg_color="transparent")
        ctk.CTkLabel(self._empty_frame, text="⬡",
                     font=ctk.CTkFont(size=48), text_color=TEXT_MUTED).pack(pady=(40, 8))
        ctk.CTkLabel(self._empty_frame, text="画布为空",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DIM).pack()
        ctk.CTkLabel(self._empty_frame,
                     text="从左侧面板添加\n输入、上传或按钮组件",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
                     justify="center").pack(pady=(4, 0))

        # 保存栏
        self._build_savebar(right)

    def _build_savebar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=0, height=52)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="💡  修改后请保存，保存后可在管理中心查看",
                     text_color=TEXT_DIM, font=ctk.CTkFont(size=12)).pack(
            side="left", padx=16, pady=14)

        ctk.CTkButton(bar, text="💾  保存", width=100,
                      fg_color=ACCENT, hover_color=ACCENT_DIM,
                      text_color="#000", font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._save).pack(side="right", padx=10, pady=10)

        ctk.CTkButton(bar, text="取消", width=80,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM, font=ctk.CTkFont(size=12),
                      command=self._cancel).pack(side="right", padx=4, pady=10)

    # ── 画布刷新 ──────────────────────────────────────────────────────────

    def _refresh_canvas(self):
        # 清空
        for w in self._canvas_scroll.winfo_children():
            w.destroy()

        name = self._name_var.get() or "未命名"
        self._canvas_name_lbl.configure(text=name)
        self._comp_count_lbl.configure(text=f"组件数: {len(self._components)}")

        if not self._components:
            self._empty_frame = ctk.CTkFrame(self._canvas_scroll, fg_color="transparent")
            self._empty_frame.pack(fill="both", expand=True)
            ctk.CTkLabel(self._empty_frame, text="⬡",
                         font=ctk.CTkFont(size=48), text_color=TEXT_MUTED).pack(pady=(40, 8))
            ctk.CTkLabel(self._empty_frame, text="画布为空",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=TEXT_DIM).pack()
            ctk.CTkLabel(self._empty_frame,
                         text="从左侧面板添加\n输入、上传或按钮组件",
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
                         justify="center").pack(pady=(4, 0))
            return

        for i, comp in enumerate(self._components):
            card = ComponentCard(
                self._canvas_scroll,
                comp_data=comp,
                idx=i,
                on_change=self._on_comp_change,
                on_context=self._on_ctx,
            )
            card.pack(fill="x", pady=(0, 8))

    def _on_name_change(self, *_):
        self._canvas_name_lbl.configure(text=self._name_var.get() or "未命名")

    def _on_comp_change(self, idx):
        pass  # 数据已通过变量直接写入 comp_data dict

    def _on_ctx(self, event, idx):
        self._ctx_menu.show(
            event.x_root, event.y_root,
            on_up=lambda: self._move(idx, -1),
            on_down=lambda: self._move(idx, 1),
            on_delete=lambda: self._delete_comp(idx),
        )

    # ── 组件操作 ─────────────────────────────────────────────────────────

    def _add_comp(self, comp_type: str):
        AddCompDialog(self, comp_type, on_add=self._confirm_add)

    def _confirm_add(self, comp_dict: dict):
        self._components.append(comp_dict)
        self._refresh_canvas()
        Toast.show(self, f"已添加「{comp_dict['name']}」", "success")

    def _move(self, idx: int, delta: int):
        new_idx = idx + delta
        if 0 <= new_idx < len(self._components):
            self._components[idx], self._components[new_idx] = \
                self._components[new_idx], self._components[idx]
            self._refresh_canvas()
            Toast.show(self, "已移动", "info")

    def _delete_comp(self, idx: int):
        name = self._components[idx]["name"]
        self._components.pop(idx)
        self._refresh_canvas()
        Toast.show(self, f"已删除「{name}」", "success")

    # ── 保存 / 取消 ──────────────────────────────────────────────────────

    def _save(self):
        name = self._name_var.get().strip()
        if not name:
            Toast.show(self, "请填写任务名称", "error")
            return
        if not self._components:
            Toast.show(self, "至少添加一个组件", "error")
            return

        def _make_comp(c):
            return Component(
                type=c["type"],
                name=c["name"],
                x=int(c.get("x", 0)),
                y=int(c.get("y", 0)),
                value=c.get("value", ""),
                extra_wait=str(c.get("extra_wait", "0")),
            )

        if self._editing_id:
            a = self.store.get(self._editing_id)
            a.name = name
            a.components = [_make_comp(c) for c in self._components]
            self.store.update(a)
        else:
            a = Automation(
                name=name,
                components=[_make_comp(c) for c in self._components],
            )
            self.store.add(a)

        if self.on_save:
            self.on_save(a)

    def _cancel(self):
        if self.on_cancel:
            self.on_cancel()


# ── 添加组件弹窗 ────────────────────────────────────────────────────────

class AddCompDialog(ctk.CTkToplevel):
    def __init__(self, master, comp_type: str, on_add=None):
        super().__init__(master)
        self.comp_type = comp_type
        self.on_add = on_add
        meta = COMP_TYPES[comp_type]

        self.title(f"添加{meta['label']}")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.grab_set()
        self.transient(master)
        self._build(meta)

        # 自适应高度，窗口居中
        self.update_idletasks()
        w, h = 380, self.winfo_reqheight() + 20
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self.after(150, lambda: self._name_entry.focus())

    def _build(self, meta):
        color = meta["color"]
        is_object = self.comp_type == "object"

        # ── 标题栏 ──
        hdr = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkFrame(hdr, fg_color=color, width=4, corner_radius=0).pack(side="left", fill="y")
        ctk.CTkLabel(hdr,
                     text=f"  {meta['icon']}  添加{meta['label']}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=8, pady=14)

        # ── 主体 ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=16)

        # 对象组件：显示用途说明
        if is_object:
            info = ctk.CTkFrame(body, fg_color=ACCENT4_BG, corner_radius=RADIUS)
            info.pack(fill="x", pady=(0, 14))
            ctk.CTkLabel(info,
                         text="🖥  点击任务栏/桌面图标激活目标软件\n执行后续组件前会等待软件完全加载",
                         font=ctk.CTkFont(size=11), text_color=ACCENT4,
                         justify="left").pack(anchor="w", padx=12, pady=8)

        # 组件名称
        ctk.CTkLabel(body, text="对象名称" if is_object else "组件名称",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DIM).pack(anchor="w", pady=(0, 5))

        self._name_var = tk.StringVar()
        self._name_entry = ctk.CTkEntry(
            body, textvariable=self._name_var,
            placeholder_text="如：微信" if is_object else "如：姓名 / 照片 / 提交",
            height=38,
            fg_color=SURFACE2, border_color=BORDER_HI,
            text_color=TEXT, font=ctk.CTkFont(size=13))
        self._name_entry.pack(fill="x", pady=(0, 14))
        self._name_entry.bind("<Return>", lambda e: self._confirm())

        # X / Y 坐标
        coord_lbl_row = ctk.CTkFrame(body, fg_color="transparent")
        coord_lbl_row.pack(fill="x")
        ctk.CTkLabel(coord_lbl_row,
                     text="图标 X 坐标（像素）" if is_object else "X 坐标（像素）",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DIM).pack(side="left", expand=True, anchor="w")
        ctk.CTkLabel(coord_lbl_row,
                     text="图标 Y 坐标（像素）" if is_object else "Y 坐标（像素）",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DIM).pack(side="left", expand=True, anchor="w", padx=(8, 0))

        coord_row = ctk.CTkFrame(body, fg_color="transparent")
        coord_row.pack(fill="x", pady=(5, 0))

        self._x_var = tk.StringVar(value="0")
        ctk.CTkEntry(coord_row, textvariable=self._x_var,
                     height=38, fg_color=SURFACE2, border_color=BORDER_HI,
                     text_color=TEXT, font=ctk.CTkFont(size=13)).pack(
            side="left", fill="x", expand=True, padx=(0, 8))

        self._y_var = tk.StringVar(value="0")
        ctk.CTkEntry(coord_row, textvariable=self._y_var,
                     height=38, fg_color=SURFACE2, border_color=BORDER_HI,
                     text_color=TEXT, font=ctk.CTkFont(size=13)).pack(
            side="left", fill="x", expand=True)

        # ── 等待时长（所有组件通用）──
        wait_default = "2" if is_object else "0"
        wait_hint = "秒  （建议 2~5 秒，等软件加载完再操作）" if is_object else "秒  （0 = 不等待，执行完立即继续）"
        ctk.CTkLabel(body,
                     text="启动后等待秒数" if is_object else "执行后等待时长",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DIM).pack(anchor="w", pady=(14, 5))
        wait_row = ctk.CTkFrame(body, fg_color="transparent")
        wait_row.pack(fill="x")
        self._wait_var = tk.StringVar(value=wait_default)
        ctk.CTkEntry(wait_row, textvariable=self._wait_var,
                     height=38, width=80,
                     fg_color=SURFACE2, border_color=BORDER_HI,
                     text_color=TEXT, font=ctk.CTkFont(size=13)).pack(side="left")
        ctk.CTkLabel(wait_row, text=wait_hint,
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(
            side="left", padx=10)

        # ── 底部按钮 ──
        footer = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0)
        footer.pack(fill="x")

        hover_colors = {
            "object": "#c4821c", "input": ACCENT_DIM,
            "upload": "#3a80d4", "button": "#cc5555", "enter": "#a066d4",
        }
        ctk.CTkButton(footer, text="✓  添加", width=110, height=36,
                      fg_color=color, hover_color=hover_colors.get(self.comp_type, ACCENT_DIM),
                      text_color="#000", font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._confirm).pack(side="right", padx=12, pady=10)

        ctk.CTkButton(footer, text="取消", width=80, height=36,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM, font=ctk.CTkFont(size=12),
                      command=self.destroy).pack(side="right", padx=(0, 4), pady=10)

    def _confirm(self):
        name = self._name_var.get().strip()
        if not name:
            Toast.show(self, "请填写名称", "error")
            return
        try:
            x = int(self._x_var.get())
            y = int(self._y_var.get())
        except ValueError:
            x, y = 0, 0

        extra_wait = self._wait_var.get().strip() or "0"

        if self.on_add:
            self.on_add({
                "type": self.comp_type,
                "name": name,
                "x": x, "y": y,
                "value": "",
                "extra_wait": extra_wait,
            })
        self.destroy()


# ── 坐标结果展示 ─────────────────────────────────────────────────────────

class CoordPickResult(ctk.CTkToplevel):
    """拾取到坐标后展示，方便复制粘贴到组件"""

    def __init__(self, master, x: int, y: int):
        super().__init__(master)
        self.title("坐标已拾取")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.attributes("-topmost", True)
        self.grab_set()
        self.transient(master)

        ctk.CTkLabel(self, text="✓  坐标拾取成功",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=ACCENT).pack(pady=(20, 6))

        ctk.CTkLabel(self,
                     text=f"X = {x}      Y = {y}",
                     font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
                     text_color=TEXT).pack(pady=6)

        ctk.CTkLabel(self,
                     text="请将上方数值填入对应组件的坐标输入框",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(pady=(4, 16))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(0, 20))

        def copy_x():
            self.clipboard_clear(); self.clipboard_append(str(x))
            Toast.show(self, f"已复制 X={x}", "success")

        def copy_y():
            self.clipboard_clear(); self.clipboard_append(str(y))
            Toast.show(self, f"已复制 Y={y}", "success")

        ctk.CTkButton(btn_row, text=f"复制 X={x}", width=110, height=34,
                      fg_color=ACCENT_BG, hover_color=ACCENT_BG2,
                      text_color=ACCENT, font=ctk.CTkFont(size=12),
                      command=copy_x).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text=f"复制 Y={y}", width=110, height=34,
                      fg_color=ACCENT_BG, hover_color=ACCENT_BG2,
                      text_color=ACCENT, font=ctk.CTkFont(size=12),
                      command=copy_y).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text="关闭", width=70, height=34,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM, font=ctk.CTkFont(size=12),
                      command=self.destroy).pack(side="left", padx=4)

        self.update_idletasks()
        w = self.winfo_reqwidth() + 40
        h = self.winfo_reqheight() + 20
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
