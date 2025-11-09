#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-Agent应急响应系统 - GUI入口点
此模块是应用程序的图形界面入口点
"""

import os
import sys

# 确保当前目录在路径中，以便正确导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入日志模块
try:
    from config import logger
    logger.info("启动GUI界面...")
except ImportError:
    import logging
    logger = logging.getLogger("ai_agent")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    logger.info("启动GUI界面...")

def main():
    """
    GUI应用程序主入口函数
    """
    try:
        # 导入新的GUI应用
        from gui.app import run_app
        
        # 启动GUI应用
        logger.info("正在初始化GUI应用...")
        run_app()
    except ImportError as e:
        logger.error(f"导入GUI模块失败: {str(e)}")
        print(f"错误: 无法导入GUI模块。请确保所有依赖已安装。\n详细信息: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动GUI应用时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"错误: 启动GUI应用时出现异常。\n详细信息: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()