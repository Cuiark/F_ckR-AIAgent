#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from crewai import Task
import logging

# 设置日志
logger = logging.getLogger("tasks")

def create_tasks(agents):
    """
    创建安全分析团队的任务
    
    参数:
        agents: 包含所有agents的字典
    
    返回:
        包含所有任务的列表
    """
    tasks = []
    
    # 检查必要的角色是否存在
    if "data_collector" in agents:
        tasks.append(Task(
            description="收集系统安全相关数据，包括进程、服务和事件日志",
            agent=agents["data_collector"],
            expected_output="系统安全数据集合"
        ))
    
    if "process_analyzer" in agents:
        tasks.append(Task(
            description="分析系统进程，识别可疑或恶意进程",
            agent=agents["process_analyzer"],
            expected_output="进程安全分析报告"
        ))
    
    if "log_analyzer" in agents:
        tasks.append(Task(
            description="分析Windows事件日志，识别潜在安全威胁",
            agent=agents["log_analyzer"],
            expected_output="日志安全分析报告"
        ))
    
    if "incident_responder" in agents:
        tasks.append(Task(
            description="根据分析结果执行应急响应措施",
            agent=agents["incident_responder"],
            expected_output="应急响应执行报告"
        ))
    
    if "security_analyst" in agents:
        tasks.append(Task(
            description="综合分析系统安全状况，识别潜在威胁",
            agent=agents["security_analyst"],
            expected_output="综合安全分析报告"
        ))
    
    # 如果没有找到任何任务，记录警告
    if not tasks:
        logger.warning("未创建任何任务，请检查角色配置")
    
    return tasks