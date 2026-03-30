"""
view_manage.py — 管理中心视图
列表展示所有自动化任务，支持搜索、双击编辑、发布、删除
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from theme import *
from widgets import Toast, ConfirmDialog


class ManageView(ctk.CTkFrame):
    """
    管理中心视图
    signals: on_edit(automation_id), on_new()
    """

    def __init__(self, master, store, on_edit=None, on_new=None, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.store = store
        self.on_edit = on_edit
        self.on_new = on_new
        self._filter = ""
        self._build()
        self.refresh()

    def _build(self):
        # ── 工具栏 ──
        toolbar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=52)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkButton(toolbar, text="＋ 新建自动化", width=130,
                      fg_color=ACCENT, hover_color=ACCENT_DIM,
                      text_color="#000", font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._new).pack(side="left", padx=16, pady=10)

        # 搜索框
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        search = ctk.CTkEntry(toolbar, textvariable=self._search_var,
                               placeholder_text="搜索任务名称...",
                               width=240, fg_color=SURFACE2,
                               border_color=BORDER, text_color=TEXT,
                               font=ctk.CTkFont(size=12))
        search.pack(side="left", padx=0, pady=10)

        hint = ctk.CTkLabel(toolbar, text="双击行可进入编辑",
                             text_color=TEXT_DIM,
                             font=ctk.CTkFont(size=11))
        hint.pack(side="right", padx=20)

        self._count_lbl = ctk.CTkLabel(toolbar, text="共 0 条",
                                        text_color=TEXT_DIM,
                                        font=ctk.CTkFont(family="Consolas", size=11))
        self._count_lbl.pack(side="right", padx=4)

        # 分割线
        sep = ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0)
        sep.pack(fill="x")

        # ── 表格区 ──
        table_wrap = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        table_wrap.pack(fill="both", expand=True, padx=20, pady=16)

        # 表头
        header_frame = ctk.CTkFrame(table_wrap, fg_color=SURFACE2,
                                     corner_radius=RADIUS, height=36)
        header_frame.pack(fill="x", pady=(0, 1))
        header_frame.pack_propagate(False)
        header_frame.grid_propagate(False)

        cols = [
            ("#",       40,  "center"),
            ("任务名称",  240, "w"),
            ("组件数",   70,  "center"),
            ("状态",     90,  "center"),
            ("更新时间", 140, "center"),
            ("操作",    180,  "center"),
        ]
        self._col_widths = [c[1] for c in cols]

        for i, (text, w, _) in enumerate(cols):
            lbl = ctk.CTkLabel(header_frame, text=text,
                                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                                text_color=TEXT_DIM,
                                width=w)
            lbl.grid(row=0, column=i, sticky="nsew", padx=0, pady=8)
            header_frame.grid_columnconfigure(i, minsize=w)

        # 滚动列表
        scroll_container = ctk.CTkScrollableFrame(
            table_wrap, fg_color=SURFACE, corner_radius=RADIUS,
            scrollbar_button_color=BORDER_HI,
            scrollbar_button_hover_color=TEXT_MUTED,
        )
        scroll_container.pack(fill="both", expand=True)
        self._list_frame = scroll_container

        # 空状态
        self._empty_lbl = ctk.CTkLabel(
            scroll_container,
            text="🤖\n\n暂无自动化任务\n点击「新建自动化」开始创建",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            justify="center",
        )

    def refresh(self):
        """刷新列表"""
        for w in self._list_frame.winfo_children():
            w.destroy()

        all_items = self.store.all()
        filtered = [a for a in all_items
                    if self._filter.lower() in a.name.lower()] if self._filter else all_items

        count = len(all_items)
        self._count_lbl.configure(text=f"共 {count} 条")

        if not filtered:
            self._empty_lbl.pack(pady=60)
            return

        self._empty_lbl.pack_forget()

        for i, auto in enumerate(filtered):
            row = _TableRow(
                self._list_frame,
                auto=auto,
                idx=i,
                on_edit=lambda aid=auto.id: self._edit(aid),
                on_publish=lambda aid=auto.id: self._publish(aid),
                on_delete=lambda aid=auto.id: self._delete(aid),
            )
            row.pack(fill="x", pady=(0, 1))

    def _on_search(self, *_):
        self._filter = self._search_var.get()
        self.refresh()

    def _new(self):
        if self.on_new:
            self.on_new()

    def _edit(self, aid: str):
        if self.on_edit:
            self.on_edit(aid)

    def _publish(self, aid: str):
        a = self.store.get(aid)
        if not a:
            return
        a.published = True
        self.store.update(a)
        self.refresh()
        # 显示 API 文档弹窗
        ApiDocDialog(self, a)

    def _delete(self, aid: str):
        a = self.store.get(aid)
        if not a:
            return
        dlg = ConfirmDialog(self, "确认删除", f"确定要删除「{a.name}」吗？\n此操作不可撤销。")
        if dlg.result:
            self.store.delete(aid)
            self.refresh()
            Toast.show(self, f"已删除「{a.name}」", "success")


class _TableRow(ctk.CTkFrame):
    """列表中的一行"""

    def __init__(self, master, auto, idx, on_edit, on_publish, on_delete, **kwargs):
        bg = SURFACE if idx % 2 == 0 else SURFACE2
        super().__init__(master, fg_color=bg, corner_radius=0, **kwargs)
        self.auto = auto
        self._bg = bg
        self._build(on_edit, on_publish, on_delete)
        self.bind("<Double-Button-1>", lambda e: on_edit())
        self._bind_all("<Double-Button-1>", on_edit)

    def _bind_all(self, event, callback):
        for child in self.winfo_children():
            child.bind(event, lambda e: callback())

    def _build(self, on_edit, on_publish, on_delete):
        self.grid_columnconfigure(1, weight=1)

        # # 序号
        ctk.CTkLabel(self, text=f"{self.winfo_name()[:2]}",
                     width=40, text_color=TEXT_MUTED,
                     font=ctk.CTkFont(family="Consolas", size=10)).grid(
            row=0, column=0, padx=4, pady=12)

        # 名称
        ctk.CTkLabel(self, text=self.auto.name or "未命名",
                     text_color=TEXT,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     width=240, anchor="w").grid(
            row=0, column=1, padx=8, pady=12, sticky="w")

        # 组件数
        ctk.CTkLabel(self, text=str(len(self.auto.components)),
                     text_color=TEXT_DIM,
                     font=ctk.CTkFont(family="Consolas", size=12),
                     width=70).grid(row=0, column=2, padx=4)

        # 状态徽章
        if self.auto.published:
            status_text = "● 已发布"
            status_color = ACCENT
            status_bg = BADGE_PUB
        else:
            status_text = "○ 草稿"
            status_color = TEXT_MUTED
            status_bg = BADGE_DRAFT

        ctk.CTkLabel(self, text=status_text,
                     text_color=status_color,
                     fg_color=status_bg,
                     corner_radius=10,
                     font=ctk.CTkFont(size=10, weight="bold"),
                     width=80, padx=8, pady=3).grid(row=0, column=3, padx=8)

        # 时间
        ctk.CTkLabel(self, text=self.auto.updated_at,
                     text_color=TEXT_DIM,
                     font=ctk.CTkFont(family="Consolas", size=11),
                     width=140).grid(row=0, column=4, padx=4)

        # 操作按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", width=180)
        btn_frame.grid(row=0, column=5, padx=8, pady=8)

        ctk.CTkButton(btn_frame, text="✏ 编辑", width=58, height=28,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM, font=ctk.CTkFont(size=11),
                      command=on_edit).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="🔗 发布", width=68, height=28,
                      fg_color=ACCENT2_BG, hover_color=ACCENT2_BG2,
                      text_color=ACCENT2, font=ctk.CTkFont(size=11),
                      command=on_publish).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="🗑", width=36, height=28,
                      fg_color=ACCENT3_BG, hover_color=ACCENT3_BG2,
                      text_color=ACCENT3, font=ctk.CTkFont(size=12),
                      command=on_delete).pack(side="left", padx=2)

        # hover 效果
        self.bind("<Enter>", lambda e: self.configure(fg_color=SURFACE3))
        self.bind("<Leave>", lambda e: self.configure(fg_color=self._bg))


class ApiDocDialog(ctk.CTkToplevel):
    """API 文档展示弹窗"""

    def __init__(self, master, auto):
        super().__init__(master)
        self.title("API 接口文档")
        self.geometry("560x480")
        self.resizable(True, True)
        self.configure(fg_color=SURFACE)
        self.grab_set()
        self.transient(master)
        self._build(auto)

    def _build(self, auto):
        # 标题
        title_frame = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0)
        title_frame.pack(fill="x")
        ctk.CTkLabel(title_frame,
                     text=f"🔗  API 接口已生成 — {auto.name}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=20, pady=14)

        badge = ctk.CTkLabel(title_frame, text="● 已发布",
                              text_color=ACCENT, fg_color=BADGE_PUB,
                              corner_radius=10, padx=10, pady=3,
                              font=ctk.CTkFont(size=10, weight="bold"))
        badge.pack(side="right", padx=20)

        # 内容
        body = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        doc_text = auto.generate_api_doc()
        text_box = ctk.CTkTextbox(
            body,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=SURFACE2,
            text_color=ACCENT,
            border_color=BORDER,
            border_width=1,
            corner_radius=RADIUS,
            height=300,
        )
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", doc_text)
        text_box.configure(state="disabled")

        # 底部按钮
        footer = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        footer.pack(fill="x")
        ctk.CTkButton(footer, text="📋 复制", width=90,
                      fg_color=ACCENT2_BG, hover_color=ACCENT2_BG2,
                      text_color=ACCENT2,
                      command=lambda: self._copy(doc_text)).pack(side="right", padx=(6, 16), pady=10)
        ctk.CTkButton(footer, text="关闭", width=80,
                      fg_color=SURFACE3, hover_color=BORDER_HI,
                      text_color=TEXT_DIM,
                      command=self.destroy).pack(side="right", padx=4, pady=10)

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        Toast.show(self, "已复制到剪贴板", "success")
