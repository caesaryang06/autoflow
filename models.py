"""
models.py — 数据模型 & JSON 持久化存储
"""

import json
import os
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional


DATA_FILE = os.path.join(os.environ.get(
    "APPDATA", os.path.expanduser("~")), ".autoflow", "automations.json")


@dataclass
class Component:
    """单个组件配置"""
    type: str          # object / input / upload / button / enter
    name: str          # 组件名称
    x: int = 0         # 屏幕 X 坐标
    y: int = 0         # 屏幕 Y 坐标
    value: str = ""    # 默认值（运行时填充，input/upload 使用）
    extra_wait: str = "0"  # 执行后额外等待秒数（所有组件通用；object 默认 2）

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Component":
        return Component(
            type=d["type"],
            name=d["name"],
            x=int(d.get("x", 0)),
            y=int(d.get("y", 0)),
            value=d.get("value", ""),
            extra_wait=str(d.get("extra_wait", d.get("value", "0") if d["type"] == "object" else "0")),
        )


@dataclass
class Automation:
    """一条自动化任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "未命名任务"
    components: List[Component] = field(default_factory=list)
    published: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def touch(self):
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "components": [c.to_dict() for c in self.components],
            "published": self.published,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Automation":
        a = Automation(
            id=d["id"],
            name=d["name"],
            components=[Component.from_dict(c) for c in d.get("components", [])],
            published=d.get("published", False),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )
        return a

    def generate_api_doc(self) -> str:
        """生成 API 调用示例文档"""
        lines = [
            f"# AutoFlow API — {self.name}",
            f"# 任务 ID: {self.id}",
            "",
            "POST http://localhost:8765/api/run",
            "Content-Type: application/json",
            "",
            "{",
            f'  "task_id": "{self.id}",',
            '  "params": {',
        ]
        for i, c in enumerate(self.components):
            comma = "," if i < len(self.components) - 1 else ""
            if c.type == "object":
                lines.append(f'    "{c.name}_wait": {c.extra_wait or 2}{comma}  // 等待秒数')
            elif c.type == "input":
                lines.append(f'    "{c.name}": "填入文本内容"{comma}')
            elif c.type == "upload":
                lines.append(f'    "{c.name}": "/path/to/file.jpg"{comma}')
            elif c.type == "button":
                lines.append(f'    "{c.name}": true{comma}  // 自动点击')
            elif c.type == "enter":
                lines.append(f'    "{c.name}": true{comma}  // 自动按回车')
        lines += ["  }", "}"]
        return "\n".join(lines)


# ── 存储层 ────────────────────────────────────────────

class AutomationStore:
    """负责加载/保存所有任务到 JSON"""

    def __init__(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        self._data: List[Automation] = []
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._data = [Automation.from_dict(d) for d in raw]
            except Exception:
                self._data = []
        else:
            self._data = self._demo_data()
            self.save()

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in self._data], f, ensure_ascii=False, indent=2)

    def all(self) -> List[Automation]:
        return list(self._data)

    def get(self, aid: str) -> Optional[Automation]:
        return next((a for a in self._data if a.id == aid), None)

    def add(self, a: Automation):
        self._data.append(a)
        self.save()

    def update(self, a: Automation):
        a.touch()
        for i, x in enumerate(self._data):
            if x.id == a.id:
                self._data[i] = a
                break
        self.save()

    def delete(self, aid: str):
        self._data = [a for a in self._data if a.id != aid]
        self.save()

    def _demo_data(self) -> List[Automation]:
        return [
            Automation(
                id="demo01",
                name="登录表单自动填写",
                components=[
                    Component("input",  "用户名", 320, 420),
                    Component("input",  "密码",   320, 500),
                    Component("button", "登录",   320, 580),
                ],
                published=False,
                created_at="2025-03-29 09:00",
                updated_at="2025-03-29 09:21",
            ),
            Automation(
                id="demo02",
                name="注册信息上传",
                components=[
                    Component("input",  "姓名",     450, 300),
                    Component("upload", "头像照片", 450, 380),
                    Component("input",  "手机号",   450, 460),
                    Component("button", "提交注册", 450, 550),
                ],
                published=True,
                created_at="2025-03-28 14:00",
                updated_at="2025-03-29 16:44",
            ),
        ]
