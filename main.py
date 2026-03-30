"""
AutoFlow — 可视化自动化管理平台
主入口文件
"""

import sys
import os

# 确保当前目录在 path 中
sys.path.insert(0, os.path.dirname(__file__))

from app import AutoFlowApp

if __name__ == "__main__":
    app = AutoFlowApp()
    app.mainloop()
