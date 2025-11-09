#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模块初始化文件
"""

import os
import logging
import sys

# 设置日志
logger = logging.getLogger("ai_agent")
logger.setLevel(logging.INFO)

# 添加控制台处理器
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# 确保当前目录在路径中
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 尝试导入常量
try:
    from .constants import *
except ImportError as e:
    logger.warning(f"无法从config.constants导入常量，使用默认值: {str(e)}")
    
    # 设置默认值
    # 基础路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    JSON_CONFIG_DIR = os.path.join(BASE_DIR, "config", "json")
    LOG_CONFIG_DIR = os.path.join(BASE_DIR, "config", "log")
    
    # 确保配置目录存在
    os.makedirs(JSON_CONFIG_DIR, exist_ok=True)
    os.makedirs(LOG_CONFIG_DIR, exist_ok=True)
    
    # 配置文件路径
    WHITELIST_FILE = os.path.join(JSON_CONFIG_DIR, "whitelist.json")
    BASELINE_PROCESSES_FILE = os.path.join(JSON_CONFIG_DIR, "baseline_processes.json")
    SUGGESTION_NOTES_FILE = os.path.join(JSON_CONFIG_DIR, "suggestion_notes.json")
    
    # 时间间隔配置（秒）
    MONITORING_INTERVAL = 600  # 10分钟
    ERROR_RETRY_INTERVAL = 60  # 1分钟
    DECISION_TIMEOUT = 300  # 5分钟
    
    # 默认模型类型
    DEFAULT_MODEL_TYPE = "deepseek-chat"