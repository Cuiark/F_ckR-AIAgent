"""
系统常量配置文件 - 集中管理所有配置参数
"""
import os

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

# API密钥配置
OPENAI_API_KEY = "NULL"
DEEPSEEK_API_KEY = ""
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"

# 时间间隔配置（秒）
MONITORING_INTERVAL = 600  # 10分钟
ERROR_RETRY_INTERVAL = 60  # 1分钟
DECISION_TIMEOUT = 300  # 5分钟

# 默认模型类型
DEFAULT_MODEL_TYPE = "deepseek-chat"  # 可选: "openai", "deepseek-chat", "deepseek-reasoner", "openai-4o"

# 模型配置
MODEL_CONFIGS = {
    "openai": {
        "temperature": 0.1,
        "model": "gpt-3.5-turbo"
    },
    "deepseek-chat": {
        "temperature": 0.1,
        "model": "deepseek-chat",  # 直接调用API时使用的模型名称
        "crewai_model": "deepseek/deepseek-chat",  # CrewAI使用的模型名称
        "model_kwargs": {
        }
    },
    "deepseek-reasoner": {
        "temperature": 0.1,
        "model": "deepseek-reasoner",  # 直接调用API时使用的模型名称
        "crewai_model": "deepseek/deepseek-reasoner",  # CrewAI使用的模型名称
        "model_kwargs": {
        }
    },
    "openai-4o": {
        "temperature": 0.1,
        "model": "gpt-4o"
    }
}

# UI配置
UI_MIN_WIDTH = 1200
UI_MIN_HEIGHT = 800
UI_WINDOW_TITLE = "AI-Agent 应急响应系统"

# 设置环境变量
def setup_environment():
    """设置环境变量"""
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
    os.environ["DEEPSEEK_API_BASE"] = DEEPSEEK_API_BASE