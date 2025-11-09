#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from crewai import Agent
from typing import Dict, List

# 设置日志
logger = logging.getLogger("security_agents")

# 导入工具函数
from tools.security_tools import (
    get_process_details, get_services, get_windows_logs,
    compare_with_baseline, terminate_process, block_ip,
    add_to_whitelist, check_whitelist, add_suggestion_note,
    get_suggestion_notes, log_agent_report, load_process_history,
    load_log_history, load_service_history, load_network_history,
    load_all_department_history, save_process_analysis, save_log_analysis,
    save_service_analysis, save_network_analysis, filter_processes_by_time,
    filter_logs_by_time, filter_services_by_time, filter_connections_by_time,
    get_network_connections, analyze_network_traffic, detect_suspicious_connections,
    analyze_service_security, check_service_integrity
)

def create_tools():
    """创建安全分析工具集"""
    tools = {
        # 原有工具
        "GetProcessDetails": get_process_details,
        "GetServices": get_services,
        "GetWindowsLogs": get_windows_logs,
        "CompareWithBaseline": compare_with_baseline,
        "TerminateProcess": terminate_process,
        "BlockIP": block_ip,
        "AddToWhitelist": add_to_whitelist,
        "CheckWhitelist": check_whitelist,
        "AddSuggestionNote": add_suggestion_note,
        "GetSuggestionNotes": get_suggestion_notes,
        "LogAgentReport": log_agent_report,
        
        # 部门历史管理工具
        "LoadProcessHistory": load_process_history,
        "LoadLogHistory": load_log_history,
        "LoadServiceHistory": load_service_history,
        "LoadNetworkHistory": load_network_history,
        "LoadAllDepartmentHistory": load_all_department_history,
        "SaveProcessAnalysis": save_process_analysis,
        "SaveLogAnalysis": save_log_analysis,
        "SaveServiceAnalysis": save_service_analysis,
        "SaveNetworkAnalysis": save_network_analysis,
        
        # 时间过滤工具
        "FilterProcessesByTime": filter_processes_by_time,
        "FilterLogsByTime": filter_logs_by_time,
        "FilterServicesByTime": filter_services_by_time,
        "FilterConnectionsByTime": filter_connections_by_time,
        
        # 网络分析工具
        "GetNetworkConnections": get_network_connections,
        "AnalyzeNetworkTraffic": analyze_network_traffic,
        "DetectSuspiciousConnections": detect_suspicious_connections,
        
        # 服务分析工具
        "AnalyzeServiceSecurity": analyze_service_security,
        "CheckServiceIntegrity": check_service_integrity
    }
    return tools

def create_agents(llm, group_name="default_group"):
    """
    创建安全分析团队的agents
    
    参数:
        llm: 语言模型实例
        group_name: 角色组名称
    
    返回:
        包含所有agents的字典
    """
    # 加载角色配置
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "config", "json", "agents_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            agents_config = json.load(f)
    except Exception as e:
        logger.error(f"加载角色配置时出错: {str(e)}")
        agents_config = {}
    
    # 检查角色组是否存在
    if group_name not in agents_config:
        logger.error(f"未找到角色组: {group_name}")
        return {}
    
    # 获取角色组配置
    group_config = agents_config[group_name]
    
    # 创建工具
    tools = create_tools()  # 这里调用了上面新增的函数
    
    # 创建agents
    agents = {}
    for agent_key, agent_config in group_config.items():
        # 获取角色配置
        role = agent_config.get("role", f"未命名角色_{agent_key}")
        goal = agent_config.get("goal", "执行安全分析任务")
        backstory = agent_config.get("backstory", "你是一名安全分析专家")
        
        # 获取工具配置
        tool_names = agent_config.get("tools", [])
        agent_tools = [tools[tool_name] for tool_name in tool_names if tool_name in tools]
        
        # 创建agent
        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            llm=llm,
            tools=agent_tools
        )
        
        # 添加到字典
        agents[agent_key] = agent
    
    return agents