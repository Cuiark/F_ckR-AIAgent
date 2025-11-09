# AI-Agent 应急响应系统

## 项目概述
本项目是一个基于CrewAI框架的Windows安全应急响应系统，通过多个AI代理协作完成系统安全监控、分析和响应任务。系统能够自动收集Windows系统数据，分析潜在安全威胁，并执行相应的应急响应措施。

## 项目结构

## 核心组件说明

### 1. Agent角色 (agents/security_agents.py)
系统包含四个主要Agent角色：
- **数据收集专家**: 负责收集系统进程、服务和事件日志等数据
- **进程安全分析师**: 分析系统进程，识别可疑或恶意进程
- **日志分析专家**: 分析Windows事件日志，识别潜在安全威胁
- **安全应急响应专家**: 根据分析结果执行应急响应措施

### 2. 任务流程 (agents/tasks.py)
系统任务按以下顺序执行：
- **数据收集任务**: 收集系统安全相关数据
- **进程分析任务**: 分析系统进程，识别可疑进程
- **日志分析任务**: 分析事件日志，识别安全威胁
- **应急响应任务**: 执行应急响应措施

### 3. 安全工具 (tools/security_tools.py)
系统提供多种安全工具函数：
- **GetProcessDetails**: 获取系统进程详情
- **GetWindowsLogs**: 获取Windows安全事件日志
- **GetServices**: 获取系统服务列表
- **LoadBaselineProcesses**: 加载基准进程列表
- **TerminateProcess**: 终止指定进程
- **BlockIP**: 在防火墙中阻止IP地址

### 4. 模型配置 (models/llm_setup.py)
支持多种语言模型：
- OpenAI (GPT-3.5-turbo)
- DeepSeek Chat
- DeepSeek Reasoner
- OpenAI GPT-4o

### 5. 配置文件 (config.py)
包含API密钥、模型参数、监控间隔等配置项

## 如何扩展功能

### 1. 添加新的Agent角色
在`agents/security_agents.py`中添加新的Agent定义：
```python
# 创建新的Agent
new_agent = Agent(
    role="新角色名称",
    goal="新角色目标",
    backstory="新角色背景故事",
    verbose=True,
    llm=llm,
    tools=[tool1, tool2]  # 为新角色分配工具
)

# 在返回的字典中添加新Agent
return {
    # 现有Agent...
    "new_agent_key": new_agent
}

###2、添加新的工具函数
@tool("NewToolName")
def new_tool_function(param1: str) -> str:
    """工具函数说明文档"""
    try:
        # 工具函数实现
        return "结果"
    except Exception as e:
        logger.error(f"工具函数执行失败: {str(e)}")
        return f"错误: {str(e)}"

然后在 tools/__init__.py 中导出新工具：
from .security_tools import (
    # 现有工具...
    new_tool_function
)

__all__ = [
    # 现有工具...
    'new_tool_function'
]

###3. 添加新的任务
在 agents/tasks.py 中添加新的任务：
# 创建新任务
new_task = Task(
    description="""
    新任务描述
    """,
    agent=agents["对应的agent_key"],
    expected_output="预期输出描述",
    context=[依赖的其他任务]
)

# 在返回的任务列表中添加新任务
return [
    # 现有任务...
    new_task
]

###### 4. 添加新的模型
在 config.py 中添加新模型配置：
MODEL_CONFIGS = {
    # 现有模型...
    "new-model": {
        "temperature": 0.1,
        "model": "new-model-name",
        "model_kwargs": {
            # 模型特定参数
        }
    }
}
然后在 models/llm_setup.py 中添加新模型的处理逻辑。

## 注意事项
1. 使用前请确保已安装所有依赖包
2. 请替换config.py中的API密钥为有效密钥
3. 默认使用DeepSeek Chat模型，可在config.py中修改DEFAULT_MODEL_TYPE
4. 系统默认每5分钟进行一次安全分析，可在config.py中调整MONITORING_INTERVAL