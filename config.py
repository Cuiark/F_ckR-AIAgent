#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sys

# 添加config目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config'))

# 现在可以直接导入constants
from constants import *

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 设置环境变量
try:
    setup_environment()
except NameError:
    # 如果constants中没有定义setup_environment函数
    pass

# 导出所有常量，使其可以通过 config 模块访问
__all__ = [
    'MONITORING_INTERVAL', 'ERROR_RETRY_INTERVAL', 'DECISION_TIMEOUT',
    'DEFAULT_MODEL_TYPE', 'MODEL_CONFIGS', 'BASE_DIR', 'JSON_CONFIG_DIR',
    'LOG_CONFIG_DIR', 'WHITELIST_FILE', 'BASELINE_PROCESSES_FILE',
    'OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'DEEPSEEK_API_BASE',
    'UI_MIN_WIDTH', 'UI_MIN_HEIGHT', 'UI_WINDOW_TITLE'
]