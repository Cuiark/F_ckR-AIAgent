#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from crewai import Task
from config import logger

def create_tasks(agents):
    """
    创建安全分析所需的各种Task
    
    参数:
        agents: 包含所有Agent的字典
        
    返回:
        包含所有Task的列表
    """
    # 创建数据收集任务
    collect_data_task = Task(
        description="""
        你是一名Windows系统安全数据收集专家。请严格按照下列要求工作：

        【要求】
        - 只输出你实际采集到的原始数据（进程、服务、事件日志、基准进程等）。
        - 禁止推测、补全、虚构任何未采集到的数据。
        - 输出需为结构化JSON格式，字段必须与实际采集结果一致。
        - 如某项数据为空或未采集到，请明确写明“未采集到相关数据”。

        【采集任务】
        1. 当前运行的所有进程详情
        2. Windows安全事件日志
        3. 系统服务状态
        4. 基准进程列表

        将收集到的数据整理成结构化格式，以便后续分析。
        """,
        agent=agents["data_collector"],
        expected_output="包含所有系统安全数据的JSON格式报告"
    )
    
    # 创建进程分析任务
    analyze_processes_task = Task(
        description="""
        你是一名进程安全分析师。请根据下方实际采集到的进程数据，完成如下任务：

        【要求】
        - 只分析实际采集到的进程数据，禁止推测、虚构不存在的进程或风险。
        - 对比基准进程列表，找出未知或可疑进程，并详细说明可疑原因和潜在风险。
        - 如未发现可疑进程，请明确说明“未发现可疑进程”。
        - 输出需包含：可疑进程列表、分析理由、风险等级。

        1. 获取当前进程列表和基准进程列表
        2. 比对找出未知进程
        3. 分析未知进程的特征，判断是否存在可疑行为
        4. 如发现可疑进程，详细说明原因和潜在风险

        输出分析结果，包括可疑进程列表及详细分析。
        """,
        agent=agents["process_analyzer"],
        expected_output="进程安全分析报告，包含可疑进程列表及详细分析",
        context=[collect_data_task]
    )
    
    # 创建日志分析任务
    analyze_logs_task = Task(
        description="""
        你是一名Windows事件日志分析专家。请根据下方实际采集到的事件日志，完成如下任务：

        【要求】
        - 只分析实际采集到的事件日志，禁止推测、虚构不存在的事件。
        - 检查登录失败(4625)、权限提升(4672)、进程创建(4688)等事件，识别潜在安全威胁。
        - 如未发现异常，请明确说明“未发现异常事件”。
        - 输出需包含：发现的安全威胁、事件ID、详细分析。

        1. 分析登录失败事件(4625)，检测是否存在暴力破解尝试
        2. 分析权限提升事件(4672)，检测是否存在异常的权限提升
        3. 分析进程创建事件(4688)，检测是否存在可疑进程创建

        输出分析结果，包括发现的安全威胁及详细分析。
        """,
        agent=agents["log_analyzer"],
        expected_output="日志安全分析报告，包含发现的安全威胁及详细分析",
        context=[collect_data_task]
    )
    
    # 创建应急响应任务
    incident_response_task = Task(
        description="""
        你是一名安全应急响应专家。请根据下方分析结果，制定并执行应急响应措施：

        【要求】
        - 只针对已确认的安全威胁制定响应措施，禁止对未确认或虚构的威胁做出响应。
        - 每项响应措施需说明目标、操作步骤、预期结果。
        - 如未发现需要响应的威胁，请明确说明“未发现需要响应的威胁”。
        - 输出需包含：响应措施列表、执行结果、时间戳。

        1. 综合评估进程分析和日志分析的结果
        2. 确定是否存在需要响应的安全威胁
        3. 如存在威胁，制定响应措施（如终止可疑进程、阻止可疑IP等）
        4. 执行响应措施并记录结果

        输出应急响应报告，包括采取的措施及结果。
        """,
        agent=agents["incident_responder"],
        expected_output="应急响应报告，包括采取的措施及结果",
        context=[analyze_processes_task, analyze_logs_task]
    )
    
    return [
        collect_data_task,
        analyze_processes_task,
        analyze_logs_task,
        incident_response_task
    ]