#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from crewai import Agent
from tools import (
    get_process_details,
    get_windows_logs,
    get_services,
    load_baseline_processes,
    terminate_process,
    block_ip,
    read_whitelist,
    add_to_whitelist,
    check_whitelist,
    TimeViewer,
    log_agent_report
)
from config import logger

# 共享工具集 - 所有Agent都可以使用的工具
common_tools = [
    read_whitelist,
    check_whitelist,
    # 删除JSON记录工具
    # add_suggestion_note,
    # get_suggestion_notes,
    TimeViewer,
    # 添加新的日志记录工具
    log_agent_report
]

# 工具映射字典，用于将字符串工具名映射到实际工具函数
tool_mapping = {
    "get_process_details": get_process_details,
    "get_windows_logs": get_windows_logs,
    "get_services": get_services,
    "load_baseline_processes": load_baseline_processes,
    "terminate_process": terminate_process,
    "block_ip": block_ip,
    "read_whitelist": read_whitelist,
    "add_to_whitelist": add_to_whitelist,
    "check_whitelist": check_whitelist,
    "TimeViewer": TimeViewer,
    "log_agent_report": log_agent_report,
    "common_tools": common_tools
}

def create_agents(llm, group_name="default_group"):
    """
    从JSON配置文件创建安全分析所需的各种Agent
    
    参数:
        llm: 配置好的语言模型实例
        group_name: 要使用的角色组名称
        
    返回:
        包含所有Agent的字典
    """
    # 添加调试信息，检查传入的llm参数
    logger.info(f"创建Agent时接收到的LLM: {llm}")
    
    # 检查llm的属性和结构
    if hasattr(llm, 'model'):
        logger.info(f"LLM模型名称: {llm.model}")
    elif hasattr(llm, 'model_name'):
        logger.info(f"LLM模型名称: {llm.model_name}")
    
    # 直接修改llm对象，添加正确格式的模型名称
    # 这是关键修复 - 确保CrewAI能够识别正确的模型格式
    if hasattr(llm, 'model_name') and 'deepseek' in str(llm.model_name).lower():
        # 检查是否已经有正确的前缀
        if not str(llm.model_name).startswith('deepseek/'):
            logger.info(f"修正模型名称格式: {llm.model_name} -> deepseek/{llm.model_name}")
            llm.model_name = f"deepseek/{llm.model_name}"
    
    # 配置文件路径
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "config", "json", "agents_config.json")
    
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        logger.error(f"Agent配置文件不存在: {config_path}")
        raise FileNotFoundError(f"Agent配置文件不存在: {config_path}")
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            all_agents_config = json.load(f)
    except Exception as e:
        logger.error(f"读取Agent配置文件失败: {str(e)}")
        raise
    
    # 获取指定组的配置
    if group_name not in all_agents_config:
        logger.warning(f"未找到角色组 '{group_name}'，使用默认组")
        group_name = "default_group"
        
    agents_config = all_agents_config.get(group_name, {})
    if not agents_config:
        logger.error(f"角色组 '{group_name}' 为空")
        raise ValueError(f"角色组 '{group_name}' 为空")
    
    # 创建Agent字典
    agents = {}
    
    # 根据配置创建每个Agent
    for agent_id, config in agents_config.items():
        # 解析工具列表
        tools_list = []
        for tool_name in config.get("tools", []):
            if tool_name == "common_tools":
                tools_list.extend(common_tools)
            elif tool_name in tool_mapping:
                tools_list.append(tool_mapping[tool_name])
            else:
                logger.warning(f"未知工具: {tool_name}，已忽略")
        
        # 创建Agent前再次确认llm参数
        if hasattr(llm, 'model'):
            logger.info(f"为Agent '{agent_id}' 创建时使用的LLM模型: {llm.model}")
        elif hasattr(llm, 'model_name'):
            logger.info(f"为Agent '{agent_id}' 创建时使用的LLM模型: {llm.model_name}")
        else:
            logger.info(f"为Agent '{agent_id}' 创建时使用的LLM模型: Unknown")
        
        # 创建Agent
        agent = Agent(
            role=config.get("role", "未命名角色"),
            goal=config.get("goal", "未定义目标"),
            backstory=config.get("backstory", "未定义背景故事"),
            verbose=config.get("verbose", True),
            llm=llm,  # 确保llm参数被正确传递
            tools=tools_list
        )
        
        # 添加到Agent字典
        agents[agent_id] = agent
        logger.info(f"已创建Agent: {config.get('role')}")
    
    return agents