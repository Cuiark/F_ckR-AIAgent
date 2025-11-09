#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import tkinter as tk
from tkinter import font
from gui.main_window import MainWindow

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gui.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("gui")

def run_app():
    """运行GUI应用"""
    try:
        # 创建主窗口
        app = MainWindow()
        
        # 设置全局字体
        default_font = font.nametofont("TkDefaultFont")
        text_font = font.nametofont("TkTextFont")
        fixed_font = font.nametofont("TkFixedFont")
        
        # 设置支持中文的字体
        default_font.configure(family="Microsoft YaHei", size=10)
        text_font.configure(family="Microsoft YaHei", size=10)
        fixed_font.configure(family="Microsoft YaHei", size=10)
        
        # 设置关闭事件
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # 运行应用
        app.mainloop()
        
    except Exception as e:
        logger.error(f"应用运行失败: {str(e)}", exc_info=True)
        
if __name__ == "__main__":
    run_app()


# 确保get_decision函数正确实现
# 全局决策队列
import queue
decision_queue = queue.Queue()

def get_decision(timeout=60):
    """从决策队列中获取决策"""
    try:
        return decision_queue.get(block=True, timeout=timeout)
    except queue.Empty:
        logger.warning(f"决策队列等待超时({timeout}秒)")
        return None
    except Exception as e:
        logger.error(f"从决策队列获取决策时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def submit_decision(task_id, status, feedback=""):
    """提交决策到队列"""
    try:
        decision = {
            "task_id": task_id,
            "status": status,
            "feedback": feedback
        }
        decision_queue.put(decision)
        return True
    except Exception as e:
        logger.error(f"提交决策到队列时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

