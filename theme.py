"""
theme.py — 统一主题配置
所有颜色、字体、尺寸常量
"""

# ── 颜色 ──────────────────────────────────────────────
BG          = "#0d0f14"
SURFACE     = "#14171f"
SURFACE2    = "#1d2130"
SURFACE3    = "#252a38"
BORDER      = "#313749"
BORDER_HI   = "#454e66"

ACCENT      = "#00e5a0"   # 绿色 主强调
ACCENT_DIM  = "#00b87c"
ACCENT2     = "#4d9fff"   # 蓝色
ACCENT3     = "#ff6b6b"   # 红色
ACCENT4     = "#f5a623"   # 橙色

TEXT        = "#f0f4ff"   # 主文字：更亮白
TEXT_DIM    = "#bcc5db"   # 次要文字：提亮
TEXT_MUTED  = "#8a96b0"   # 辅助文字：提亮，原来太暗

# 组件类型颜色
COLOR_INPUT  = ACCENT    # 绿
COLOR_UPLOAD = ACCENT2   # 蓝
COLOR_BUTTON = ACCENT3   # 红
COLOR_OBJECT = ACCENT4   # 橙 — 对象/软件启动组件
COLOR_ENTER  = "#c97fff"  # 紫 — 回车组件

# ── 预混合色（替代 8 位 hex 透明色，CustomTkinter 不支持） ──
# ACCENT (#00e5a0) 混合到深色背景
ACCENT_BG     = "#0d2e24"   # ACCENT 低饱和背景
ACCENT_BG2    = "#0a2018"   # ACCENT 更深背景（hover）
# ACCENT2 (#4d9fff) 蓝色系
ACCENT2_BG    = "#0e1e33"   # 蓝色低饱和背景
ACCENT2_BG2   = "#162840"   # 蓝色背景 hover
# ACCENT3 (#ff6b6b) 红色系
ACCENT3_BG    = "#2e1212"   # 红色低饱和背景
ACCENT3_BG2   = "#3d1a1a"   # 红色背景 hover
# ACCENT4 (#f5a623) 橙色系
ACCENT4_BG    = "#2e2008"   # 橙色低饱和背景
ACCENT4_BG2   = "#3d2a0a"   # 橙色背景 hover
# 紫色系 — 回车组件
ENTER_BG      = "#1e1030"   # 紫色低饱和背景
ENTER_BG2     = "#2a1a40"   # 紫色 hover
# 状态徽章
BADGE_DRAFT   = SURFACE3    # 草稿状态背景
BADGE_PUB     = "#0d2e24"   # 已发布状态背景

# ── 字体 ──────────────────────────────────────────────
FONT_BODY   = ("微软雅黑", 12)
FONT_SMALL  = ("微软雅黑", 11)
FONT_TITLE  = ("微软雅黑", 14, "bold")
FONT_MONO   = ("Consolas", 11)
FONT_MONO_S = ("Consolas", 10)

# ── 尺寸 ──────────────────────────────────────────────
RADIUS      = 8
PAD         = 16
PAD_S       = 8
PAD_L       = 24

# ── 组件类型元数据 ─────────────────────────────────────
COMP_TYPES = {
    "object": {"label": "对象组件", "icon": "🖥",  "color": COLOR_OBJECT, "tag": "对象"},
    "input":  {"label": "输入组件", "icon": "📝", "color": COLOR_INPUT,  "tag": "输入"},
    "upload": {"label": "上传组件", "icon": "📎", "color": COLOR_UPLOAD, "tag": "上传"},
    "button": {"label": "按钮组件", "icon": "🖱",  "color": COLOR_BUTTON, "tag": "按钮"},
    "enter":  {"label": "回车组件", "icon": "↵",  "color": COLOR_ENTER,  "tag": "回车"},
}
