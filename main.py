#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-Agent应急响应系统 - 主模块
此模块是应用程序的后端入口点
"""

import os
import sys
import json
import time
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable

# 确保当前目录在路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入配置
try:
    from config.constants import (
        DEFAULT_MODEL_TYPE, DECISION_TIMEOUT, ERROR_RETRY_INTERVAL,
        MONITORING_INTERVAL
    )
except ImportError as e:
    # 设置默认值
    DEFAULT_MODEL_TYPE = "deepseek-chat"
    DECISION_TIMEOUT = 300
    ERROR_RETRY_INTERVAL = 60
    MONITORING_INTERVAL = 600
    logging.warning(f"无法导入配置常量，使用默认值: {str(e)}")

# 导入其他模块
from models import setup_llm
from agents.security_agents import create_agents
from agents.tasks import create_tasks

# 设置日志
logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

import os
import sys
import time
import traceback
import logging

# 尝试不同的导入路径
try:
    # 新版本 LangChain
    from langchain_core.messages import HumanMessage
except ImportError:
    try:
        # 旧版本 LangChain
        from langchain.schema import HumanMessage
    except ImportError:
        # 如果都失败，可以创建一个简单的替代类
        class HumanMessage:
            def __init__(self, content):
                self.content = content

# 设置日志
logger = logging.getLogger("ai_agent")
logger.setLevel(logging.INFO)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# 导入常量 - 添加错误处理
try:
    from config.constants import (
        MONITORING_INTERVAL, 
        ERROR_RETRY_INTERVAL, 
        DEFAULT_MODEL_TYPE,
        DECISION_TIMEOUT
    )
except ImportError as e:
    # 如果导入失败，定义默认值
    logger.warning(f"无法从config.constants导入常量，使用默认值: {str(e)}")
    MONITORING_INTERVAL = 600  # 10分钟
    ERROR_RETRY_INTERVAL = 60  # 1分钟
    DEFAULT_MODEL_TYPE = "deepseek-chat"
    DECISION_TIMEOUT = 300  # 5分钟

# 其他导入
from models import setup_llm
from agents import create_agents, create_tasks
from tools.security_tools import extract_section
from gui.gui_tools import enable_decision_controls

def get_user_decision(report, stage="执行后", agent_name=None):
    """获取用户对安全报告的决策"""
    print("\n" + "="*80)
    if agent_name:
        print(f"【{agent_name} - {stage}报告】")
    else:
        print("【安全态势报告】")
    print("="*80)
    print(report)
    print("\n" + "="*80)
    
    while True:
        decision = input("\n请输入您的决策 (批准/拒绝/建议: <您的建议>): ")
        
        if decision.lower() == "批准":
            return {"status": "approved", "feedback": ""}
        elif decision.lower() == "拒绝":
            return {"status": "rejected", "feedback": ""}
        elif decision.lower().startswith("建议:"):
            feedback = decision[3:].strip()
            return {"status": "feedback", "feedback": feedback}
        else:
            print("无效的输入，请输入 '批准'、'拒绝' 或 '建议: <您的建议>'")

def process_decision(decision, llm, secretary_agent, last_report, stage="执行后", agent_name=None):
    """处理用户决策，生成新的报告或执行批准的措施"""
    # 获取当前时间作为响应时间
    response_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 添加对None的检查
    if decision is None:
        print(f"\n【决策为空】默认批准...")
        logger.warning(f"{agent_name} 的 {stage}报告 收到了空决策，默认批准")
        return {"approved": True, "report": last_report, "auto_approved": True}
    
    # 检查决策类型 - 确保使用get方法避免KeyError
    if decision.get("status") == "approved":
        action = "继续执行任务" if stage == "执行前" else "确认任务完成"
        print(f"\n【决策已批准】{action}...")
        
        # 记录已批准的报告
        from tools import log_agent_report
        report_type = "pre" if stage == "执行前" else "post"
        # 修改这里：使用run而不是invoke
        log_agent_report.run(
            content=last_report,
            report_type=report_type,
            agent_name=agent_name if agent_name else "系统"
        )
        
        return {"approved": True, "report": last_report}
    
    elif decision.get("status") == "feedback":
        print("\n【收到反馈】正在根据您的建议调整方案...")
        try:
            feedback = decision.get("feedback", "").strip()
            if feedback.startswith("建议:"):
                feedback = feedback[3:].strip()
            elif feedback.startswith("建议："):
                feedback = feedback[3:].strip()
            print(f"用户反馈: {feedback}")

            # 直接用llm处理建议反馈
            prompt = f"""
            用户对报告提供了以下反馈:
            {feedback}

            原始报告:
            {last_report}

            请根据用户反馈，调整报告内容，并提供更新后的完整报告。
            """
            try:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=prompt)]
                updated_report = llm.invoke(messages).content
            except Exception:
                # 兼容旧版本
                updated_report = llm(prompt)

            print("\n【反馈处理完成】已根据您的建议更新报告")
            from tools import log_agent_report
            report_type = "pre_updated" if stage == "执行前" else "post_updated"
            log_agent_report.run(
                content=updated_report,
                report_type=report_type,
                agent_name=agent_name if agent_name else "系统"
            )
            # 关键：返回pending_approval状态
            result = {
                "approved": False,
                "pending_approval": True,
                "report": updated_report,
                "feedback_processed": True
            }
            
            # 触发UI刷新以显示更新后的报告
            try:
                import gui.workflow_integration as wi
                if hasattr(wi, 'current_integration') and wi.current_integration:
                    # 更新任务的approval_data
                    if hasattr(wi.current_integration, 'current_task') and wi.current_integration.current_task:
                        task = wi.current_integration.current_task
                        if hasattr(task, 'approval_data') and task.approval_data:
                            task.approval_data["report"] = updated_report
                            # 触发UI刷新
                            wi.current_integration.refresh_ui_for_approval(task)
            except Exception as refresh_error:
                print(f"UI刷新失败: {refresh_error}")
            
            return result
        except Exception as e:
            import traceback
            error_msg = f"处理用户反馈时出错: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            try:
                from config import logger
                logger.error(error_msg)
            except:
                pass
            return {"approved": True, "report": last_report, "feedback_processed": False, "error": str(e)}
    
    elif decision.get("status") == "rejected":
        print("\n【决策已拒绝】终止任务执行...")
        
        # 获取拒绝原因
        reason = decision.get("feedback", "未提供拒绝原因")
        if reason:
            print(f"拒绝原因: {reason}")
        
        # 记录被拒绝的报告
        from tools import log_agent_report
        report_type = f"pre_rejected" if stage == "执行前" else "post_rejected"
        log_agent_report.run(
            content=last_report,
            report_type=report_type,
            agent_name=agent_name if agent_name else "系统"
        )
        
        return {"approved": False, "report": last_report, "reason": reason}
    
    else:
        # 未知决策类型，默认批准
        print(f"\n【未知决策类型】{decision.get('status', 'unknown')}，默认批准...")
        
        # 记录报告
        from tools import log_agent_report
        report_type = "pre" if stage == "执行前" else "post"
        log_agent_report.run(
            content=last_report,
            report_type=report_type,
            agent_name=agent_name if agent_name else "系统"
        )
        
        return {"approved": True, "report": last_report, "auto_approved": True}

def execute_agent_with_approval(agent, task_description, llm, secretary_agent, previous_report=None, raw_data=None, get_decision_func=None):
    """执行单个Agent的任务，包含执行前和执行后的审批流程"""
    # 这个函数基本保持不变，因为它是核心执行逻辑
    # 如果没有提供自定义的get_user_decision函数，则使用默认的
    if get_decision_func is None:
        get_decision_func = get_user_decision
        
    agent_name = agent.role
    
    # 1. 秘书准备执行前报告
    logger.info(f"秘书正在准备 {agent_name} 的执行前报告...")
    
    # 如果有上一位角色的报告，提取关键信息
    previous_info = ""
    previous_suggestions = ""
    if previous_report:
        # 提取上一位角色的关键发现
        previous_results = extract_section(previous_report, "结果分析", "建议措施")
        if not previous_results:
            previous_results = extract_section(previous_report, "详细分析", "已执行操作")
        if not previous_results:
            previous_results = extract_section(previous_report, "执行结果")
            
        # 提取上一位角色的建议或用户的建议
        suggestions = extract_section(previous_report, "后续建议", "")
        if not suggestions:
            suggestions = extract_section(previous_report, "建议措施", "")
        
        # 检查是否有用户建议（通常在报告末尾的"决策者反馈"部分）
        user_feedback = extract_section(previous_report, "决策者反馈", "")
        
        if previous_results:
            previous_info = f"""
            上一位角色的关键发现：
            {previous_results}
            
            请在准备报告时考虑上述信息。
            """
        
        if suggestions or user_feedback:
            previous_suggestions = f"""
            需要关注的建议：
            {suggestions if suggestions else ""}
            
            用户反馈：
            {user_feedback if user_feedback else ""}
            
            请特别关注以上建议和反馈，将其纳入你的分析和处理中。
            """
    
    # 添加原始数据信息（如果有）
    raw_data_info = ""
    if raw_data:
        raw_data_info = f"""
        原始数据：
        {raw_data}
        
        请基于上述原始数据进行分析。
        """
    
    pre_execution_prompt = f"""
    你是一名安全情报秘书。请严格按照下列要求工作：

    【要求】
    - 只基于实际数据分析，禁止编造、补全、推测未出现的事件。
    - 如未发现异常或威胁，请明确说明"未发现异常事件"。
    - 禁止虚构时间、文件、进程、IP等信息。
    - 输出格式必须严格遵循模板，不得重复段落或章节。

    请为 {agent_name} 准备一份执行前报告，说明：
    1. 该角色将要执行的任务内容
    2. 任务的目的和重要性
    3. 可能使用的工具和方法
    4. 预期的执行结果
    
    任务描述：{task_description}
    {previous_info}
    {previous_suggestions}
    {raw_data_info}
    """
    
    # 修改这里：直接使用llm而不是secretary_agent.llm
    try:
        # 尝试使用 HumanMessage
        messages = [HumanMessage(content=pre_execution_prompt)]
        pre_report = llm.invoke(messages).content
    except (NameError, AttributeError):
        # 如果 HumanMessage 不可用，尝试直接使用字典
        try:
            messages = [{"role": "user", "content": pre_execution_prompt}]
            pre_report = llm.invoke(messages).content
        except:
            # 最后的备选方案
            pre_report = llm(pre_execution_prompt)
    
    # 2. 获取执行前的审批
    pre_decision = get_decision_func(pre_report, "执行前", agent_name)
    
    # 添加对None的检查
    if pre_decision is None:
        logger.warning(f"{agent_name} 的执行前决策为None，默认批准")
        pre_decision = {"status": "approved", "feedback": "自动批准（决策为None）"}
    
    pre_result = process_decision(pre_decision, llm, secretary_agent, pre_report, "执行前", agent_name)
    
    # 新增：处理建议后再次审批
    while pre_result.get("pending_approval"):
        pre_decision = get_decision_func(pre_result["report"], "执行前", agent_name)
        pre_result = process_decision(pre_decision, llm, secretary_agent, pre_result["report"], "执行前", agent_name)

    if not pre_result["approved"]:
        return {"status": "rejected_before_execution", "result": None}
    
    # 3. 执行Agent任务
    logger.info(f"正在执行 {agent_name} 的任务...")
    
    # 修改这里：使用正确的方式执行Agent任务
    # 创建一个临时任务来执行
    from crewai import Task
    
    # 构建任务描述，包含上下文信息
    task_context = task_description
    
    # 添加原始数据到任务描述（如果有）
    if raw_data:
        task_context = f"""
        {task_description}
        
        请基于以下原始数据进行分析：
        {raw_data}
        """
    
    # 添加上一位角色的报告和建议到任务描述（如果有）
    if previous_report:
        if previous_results:
            task_context = f"""
            {task_context}
            
            上一位角色的关键发现：
            {previous_results}
            """
        
        # 添加建议和用户反馈
        if suggestions or user_feedback:
            task_context = f"""
            {task_context}
            
            需要关注的建议：
            {suggestions if suggestions else ""}
            
            用户反馈：
            {user_feedback if user_feedback else ""}
            
            请特别关注以上建议和反馈，将其纳入你的分析和处理中。
            """
    
    task = Task(
        description=task_context,
        agent=agent,
        expected_output="详细的执行结果"
    )
    
    # 使用agent.execute方法执行任务
    execution_result = agent.execute_task(task)
    
    # 4. 秘书准备执行后报告
    logger.info(f"秘书正在准备 {agent_name} 的执行后报告...")
    post_execution_prompt = f"""
    你是一名安全情报秘书。请严格按照下列要求工作：

    【要求】
    - 只基于实际数据分析，禁止编造、补全、推测未出现的事件。
    - 如未发现异常或威胁，请明确说明"未发现异常事件"。
    - 禁止虚构时间、文件、进程、IP等信息。
    - 输出格式必须严格遵循模板，不得重复段落或章节。
    - 每项建议只列出一次，避免重复列出相同的建议。

    请为 {agent_name} 准备一份执行后报告，说明：
    1. 任务的执行情况
    2. 执行结果和发现
    3. 结果分析和评估
    4. 后续建议（如有，每项建议只列出一次）
    
    执行结果：
    {execution_result}
    """
    
    # 修改这里：直接使用llm
    messages = [HumanMessage(content=post_execution_prompt)]
    post_report = llm.invoke(messages).content
    
    # 5. 获取执行后的审批
    post_decision = get_decision_func(post_report, "执行后", agent_name)
    
    # 添加对None的检查
    if post_decision is None:
        logger.warning(f"{agent_name} 的执行后决策为None，默认批准")
        post_decision = {"status": "approved", "feedback": "自动批准（决策为None）"}
    
    post_result = process_decision(post_decision, llm, secretary_agent, post_report, "执行后", agent_name)
    
    # 新增：处理建议后再次审批
    while post_result.get("pending_approval"):
        post_decision = get_decision_func(post_result["report"], "执行后", agent_name)
        post_result = process_decision(post_decision, llm, secretary_agent, post_result["report"], "执行后", agent_name)

    if not post_result["approved"]:
        return {"status": "rejected_after_execution", "result": execution_result}
    
    # 返回执行结果和报告
    return {
        "status": "completed",
        "result": execution_result,
        "pre_report": pre_report,
        "post_report": post_report
    }

def main(group_name="default_group"):
    """主函数，创建并运行安全分析团队"""
    logger.info(f"正在初始化安全分析团队 (使用角色组: {group_name})...")
    # 设置语言模型 - 为CrewAI使用的模型
    llm_for_agents = setup_llm(model_type=DEFAULT_MODEL_TYPE, for_crewai=True)
    # 设置语言模型 - 为直接调用使用的模型
    llm_for_direct = setup_llm(model_type=DEFAULT_MODEL_TYPE, for_crewai=False)
    # 创建agents - 使用CrewAI专用模型
    agents = create_agents(llm_for_agents, group_name=group_name)
    # 获取秘书Agent
    secretary_agent = agents.get("secretary")
    if not secretary_agent:
        logger.error("未找到秘书Agent，请确保已添加秘书角色")
        return
    
    # 创建tasks (仅用于获取任务描述)
    tasks = create_tasks(agents)
    
    # 根据不同的角色组选择不同的工作流程
    if group_name == "default_group":
        run_default_workflow(agents, tasks, llm_for_direct, secretary_agent)
    elif group_name == "custom_group":
        run_custom_workflow(agents, tasks, llm_for_direct, secretary_agent)
    else:
        logger.error(f"未知的角色组: {group_name}")
        return

def run_default_workflow(agents, tasks, llm_for_direct, secretary_agent):
    """运行默认工作流程 - 部门化架构"""
    logger.info("开始安全监控 (部门化工作流程)...")
    while True:
        try:
            # 1. 进程部门：数据收集 + 分析
            logger.info("=== 进程部门工作开始 ===")
            
            # 1.1 进程数据收集
            process_data_result = execute_agent_with_approval(
                agents["process_data_collector"], 
                "收集系统进程信息，并根据历史记录过滤已分析的进程", 
                llm_for_direct, 
                secretary_agent
            )
            if process_data_result["status"] != "completed":
                logger.warning("进程数据收集任务未获批准，跳过进程部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 1.2 进程安全分析
            process_analysis_result = execute_agent_with_approval(
                agents["process_security_analyst"], 
                "分析进程安全状况，识别可疑进程和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=process_data_result["result"]
            )
            
            # 2. 日志部门：数据收集 + 分析
            logger.info("=== 日志部门工作开始 ===")
            
            # 2.1 日志数据收集
            log_data_result = execute_agent_with_approval(
                agents["log_data_collector"], 
                "收集系统日志信息，并根据历史记录过滤已分析的日志", 
                llm_for_direct, 
                secretary_agent
            )
            if log_data_result["status"] != "completed":
                logger.warning("日志数据收集任务未获批准，跳过日志部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 2.2 日志安全分析
            log_analysis_result = execute_agent_with_approval(
                agents["log_security_analyst"], 
                "分析日志安全状况，识别异常事件和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=log_data_result["result"]
            )
            
            # 3. 服务部门：数据收集 + 分析
            logger.info("=== 服务部门工作开始 ===")
            
            # 3.1 服务数据收集
            service_data_result = execute_agent_with_approval(
                agents["service_data_collector"], 
                "收集系统服务信息，并根据历史记录过滤已分析的服务", 
                llm_for_direct, 
                secretary_agent
            )
            if service_data_result["status"] != "completed":
                logger.warning("服务数据收集任务未获批准，跳过服务部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 3.2 服务安全分析
            service_analysis_result = execute_agent_with_approval(
                agents["service_security_analyst"], 
                "分析服务安全状况，识别异常服务和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=service_data_result["result"]
            )
            
            # 4. 网络部门：数据收集 + 分析
            logger.info("=== 网络部门工作开始 ===")
            
            # 4.1 网络数据收集
            network_data_result = execute_agent_with_approval(
                agents["network_data_collector"], 
                "收集网络连接信息，并根据历史记录过滤已分析的连接", 
                llm_for_direct, 
                secretary_agent
            )
            if network_data_result["status"] != "completed":
                logger.warning("网络数据收集任务未获批准，跳过网络部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 4.2 网络安全分析
            network_analysis_result = execute_agent_with_approval(
                agents["network_security_analyst"], 
                "分析网络安全状况，识别可疑连接和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=network_data_result["result"]
            )
            
            # 5. 威胁整合（秘书）
            logger.info("=== 威胁整合阶段 ===")
            
            # 收集所有部门的分析结果
            all_analysis_results = ""
            if process_analysis_result["status"] == "completed":
                all_analysis_results += f"进程部门分析结果：\n{process_analysis_result['result']}\n\n"
            if log_analysis_result["status"] == "completed":
                all_analysis_results += f"日志部门分析结果：\n{log_analysis_result['result']}\n\n"
            if service_analysis_result["status"] == "completed":
                all_analysis_results += f"服务部门分析结果：\n{service_analysis_result['result']}\n\n"
            if network_analysis_result["status"] == "completed":
                all_analysis_results += f"网络部门分析结果：\n{network_analysis_result['result']}\n\n"
            
            threat_integration_result = execute_agent_with_approval(
                agents["secretary"], 
                "整合各部门的安全分析结果，生成综合威胁评估报告", 
                llm_for_direct,
                secretary_agent,
                raw_data=all_analysis_results
            )
            
            # 6. 应急响应
            logger.info("=== 应急响应阶段 ===")
            
            incident_response_result = execute_agent_with_approval(
                agents["incident_responder"], 
                "基于威胁评估结果，制定和执行应急响应措施", 
                llm_for_direct,
                secretary_agent,
                previous_report=threat_integration_result["result"] if threat_integration_result["status"] == "completed" else all_analysis_results
            )
            
            # 等待下一次监控周期
            logger.info(f"安全监控周期完成，等待 {MONITORING_INTERVAL} 秒后开始下一轮...")
            time.sleep(MONITORING_INTERVAL)
            
        except Exception as e:
            logger.error(f"安全监控过程中发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            logger.info(f"等待 {ERROR_RETRY_INTERVAL} 秒后重试...")
            time.sleep(ERROR_RETRY_INTERVAL)

def run_custom_workflow(agents, tasks, llm_for_direct, secretary_agent):
    """运行自定义工作流程 - 部门化架构"""
    logger.info("开始安全监控 (自定义部门化工作流程)...")
    while True:
        try:
            # 1. 进程部门：数据收集 + 分析
            logger.info("=== 进程部门工作开始 ===")
            
            # 1.1 进程数据收集
            process_data_result = execute_agent_with_approval(
                agents["process_data_collector"], 
                "收集系统进程信息，并根据历史记录过滤已分析的进程", 
                llm_for_direct, 
                secretary_agent
            )
            if process_data_result["status"] != "completed":
                logger.warning("进程数据收集任务未获批准，跳过进程部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 1.2 进程安全分析
            process_analysis_result = execute_agent_with_approval(
                agents["process_security_analyst"], 
                "分析进程安全状况，识别可疑进程和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=process_data_result["result"]
            )
            
            # 2. 日志部门：数据收集 + 分析
            logger.info("=== 日志部门工作开始 ===")
            
            # 2.1 日志数据收集
            log_data_result = execute_agent_with_approval(
                agents["log_data_collector"], 
                "收集系统日志信息，并根据历史记录过滤已分析的日志", 
                llm_for_direct, 
                secretary_agent
            )
            if log_data_result["status"] != "completed":
                logger.warning("日志数据收集任务未获批准，跳过日志部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 2.2 日志安全分析
            log_analysis_result = execute_agent_with_approval(
                agents["log_security_analyst"], 
                "分析日志安全状况，识别异常事件和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=log_data_result["result"]
            )
            
            # 3. 服务部门：数据收集 + 分析
            logger.info("=== 服务部门工作开始 ===")
            
            # 3.1 服务数据收集
            service_data_result = execute_agent_with_approval(
                agents["service_data_collector"], 
                "收集系统服务信息，并根据历史记录过滤已分析的服务", 
                llm_for_direct, 
                secretary_agent
            )
            if service_data_result["status"] != "completed":
                logger.warning("服务数据收集任务未获批准，跳过服务部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 3.2 服务安全分析
            service_analysis_result = execute_agent_with_approval(
                agents["service_security_analyst"], 
                "分析服务安全状况，识别异常服务和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=service_data_result["result"]
            )
            
            # 4. 网络部门：数据收集 + 分析
            logger.info("=== 网络部门工作开始 ===")
            
            # 4.1 网络数据收集
            network_data_result = execute_agent_with_approval(
                agents["network_data_collector"], 
                "收集网络连接信息，并根据历史记录过滤已分析的连接", 
                llm_for_direct, 
                secretary_agent
            )
            if network_data_result["status"] != "completed":
                logger.warning("网络数据收集任务未获批准，跳过网络部门任务")
                time.sleep(MONITORING_INTERVAL)
                continue
            
            # 4.2 网络安全分析
            network_analysis_result = execute_agent_with_approval(
                agents["network_security_analyst"], 
                "分析网络安全状况，识别可疑连接和威胁", 
                llm_for_direct,
                secretary_agent,
                raw_data=network_data_result["result"]
            )
            
            # 5. 安全分析（综合分析师）
            logger.info("=== 综合安全分析阶段 ===")
            
            # 收集所有部门的分析结果
            all_analysis_results = ""
            if process_analysis_result["status"] == "completed":
                all_analysis_results += f"进程部门分析结果：\n{process_analysis_result['result']}\n\n"
            if log_analysis_result["status"] == "completed":
                all_analysis_results += f"日志部门分析结果：\n{log_analysis_result['result']}\n\n"
            if service_analysis_result["status"] == "completed":
                all_analysis_results += f"服务部门分析结果：\n{service_analysis_result['result']}\n\n"
            if network_analysis_result["status"] == "completed":
                all_analysis_results += f"网络部门分析结果：\n{network_analysis_result['result']}\n\n"
            
            security_analysis_result = execute_agent_with_approval(
                agents["security_analyst"], 
                "综合分析各部门的安全状况，识别潜在威胁和风险", 
                llm_for_direct,
                secretary_agent,
                raw_data=all_analysis_results
            )
            
            # 6. 报告生成（秘书）
            logger.info("=== 报告生成阶段 ===")
            
            report_generation_result = execute_agent_with_approval(
                agents["secretary"], 
                "生成综合安全分析报告，总结各部门发现和建议", 
                llm_for_direct,
                secretary_agent,
                previous_report=security_analysis_result["result"] if security_analysis_result["status"] == "completed" else all_analysis_results
            )
            
            # 等待下一次监控周期
            logger.info(f"安全监控周期完成，等待 {MONITORING_INTERVAL} 秒后开始下一轮...")
            time.sleep(MONITORING_INTERVAL)
            
        except Exception as e:
            logger.error(f"安全监控过程中发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            logger.info(f"等待 {ERROR_RETRY_INTERVAL} 秒后重试...")
            time.sleep(ERROR_RETRY_INTERVAL)

# 替换现有的execute_custom_workflow函数
def execute_custom_workflow(group_name, report_callback=None, tool_callback=None, log_callback=None, role_callback=None, decision_callback=None, completion_callback=None):
    """
    执行自定义工作流程 - 基于配置文件
    
    参数:
        group_name: 角色组名称
        report_callback: 报告输出回调函数
        tool_callback: 工具输出回调函数
        log_callback: 日志回调函数
        role_callback: 角色更新回调函数
        decision_callback: 决策回调函数
        completion_callback: 完成回调函数
    """
    from tools.security_tools import set_tool_output_callback
    set_tool_output_callback(tool_callback)

    # 初始化模型和agents
    llm_for_direct = setup_llm(model_type=DEFAULT_MODEL_TYPE, for_crewai=False)
    llm_for_agents = setup_llm(model_type=DEFAULT_MODEL_TYPE, for_crewai=True)
    
    try:
        # 加载工作流程配置
        workflow_config = load_workflow_config(group_name)
        if not workflow_config:
            if log_callback:
                log_callback(f"错误: 未找到角色组 {group_name} 的工作流程配置")
            return []
        
        # 创建agents
        agents = create_agents(llm_for_agents, group_name=group_name)
        secretary_agent = agents.get("secretary")
        
        if log_callback:
            log_callback(f"正在初始化工作流程，角色组: {group_name}")
            log_callback("初始化角色，包括秘书角色...")
        
        # 执行工作流程中的每个模块
        results = []
        previous_report = None
        raw_data = None
        
        # 创建决策适配器
        def decision_adapter(report, stage, agent_name):
            """适配器函数，确保参数匹配"""
            if log_callback:
                log_callback(f"请求决策: {agent_name} - {stage}")
            
            # 显示报告
            if report_callback:
                report_header = f"【{agent_name} - {stage}报告】"
                formatted_report = f"\n{report_header}\n{'='*80}\n{report}\n{'='*80}\n"
                report_callback(formatted_report, True)
            
            # 获取决策
            if decision_callback:
                try:
                    from gui.app import get_decision
                    decision = get_decision(DECISION_TIMEOUT)
                    
                    if decision is None:
                        logger.warning(f"{agent_name} 的 {stage}决策为None，默认批准")
                        return {"status": "approved", "feedback": "自动批准（决策为None）"}
                    
                    return decision
                except Exception as e:
                    logger.error(f"获取决策时出错: {str(e)}")
                    return {"status": "approved", "feedback": "自动批准（获取决策出错）"}
            else:
                # 使用默认的命令行交互
                return get_user_decision(report, stage, agent_name)
        
        # 遍历工作流程中的每个模块
        for module in workflow_config:
            module_name = module.get("name", "未命名模块")
            agent_key = module.get("agent")
            description = module.get("description", "")
            
            if not agent_key or agent_key not in agents:
                if log_callback:
                    log_callback(f"警告: 未找到Agent {agent_key}，跳过模块 {module_name}")
                continue
            
            # 更新当前角色
            if role_callback:
                role_callback(module_name)
            
            if log_callback:
                log_callback(f"正在执行 {module_name} 阶段...")
            
            # 执行Agent任务
            agent = agents[agent_key]
            result = execute_agent_with_approval(
                agent, 
                description, 
                llm_for_direct,
                secretary_agent,
                previous_report=previous_report,
                raw_data=raw_data,
                get_decision_func=decision_adapter
            )
            
            # 阶段报告输出
            if report_callback and result:
                if "pre_report" in result:
                    report_callback(f"【{module_name}】执行前报告：\n{result['pre_report']}", False)
                if "post_report" in result:
                    report_callback(f"【{module_name}】执行后报告：\n{result['post_report']}", False)
            
            # 失败处理
            if result["status"] != "completed":
                if log_callback:
                    log_callback(f"{module_name} 阶段未获批准，流程中断。")
                break
            
            # 更新前一个报告，用于下一个模块
            if "post_report" in result:
                previous_report = result["post_report"]
            
            # 如果是数据收集模块，保存原始数据
            if agent_key == "data_collector" and "result" in result:
                raw_data = result["result"]
            
            results.append(result)
        
            # 任务完成后，调用完成回调
            if completion_callback:
                # 使用QTimer确保在主线程中调用
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(0, lambda: completion_callback("任务执行完成"))
            
            # 调用任务完成处理程序
            task_completion_handler("任务执行完成")
            
            return results
            
    except Exception as e:
            error_msg = f"执行工作流程时出错: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            if log_callback:
                log_callback(f"异常详情:\n{traceback.format_exc()}")
                log_callback(f"异常类型: {type(e).__name__}")
                log_callback(f"Python版本: {sys.version}")
            
            return []

def load_workflow_config(group_name):
    """加载工作流程配置"""
    try:
        # 配置文件路径
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  "config", "json", "workflows.json")
        
        # 检查文件是否存在
        if not os.path.exists(config_path):
            logger.error(f"工作流程配置文件不存在: {config_path}")
            return None
        
        # 加载配置
        with open(config_path, "r", encoding="utf-8") as f:
            workflows = json.load(f)
        
        # 检查角色组是否存在
        if group_name not in workflows:
            logger.error(f"未找到角色组 {group_name} 的工作流程配置")
            return None
        
        return workflows[group_name]
    except Exception as e:
        logger.error(f"加载工作流程配置时出错: {str(e)}")
        return None

def task_completion_handler(result):
    """处理任务完成事件"""
    print(f"DEBUG: 任务完成处理程序被调用: {result}")
    
    try:
        # 导入调试函数
        from gui.gui_tools import debug_thread_info
        debug_thread_info("task_completion_handler 内部")
        
        # 清理UI
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        from gui.gui_tools import safe_ui_call
        
        # 使用safe_ui_call确保在主线程中执行
        from gui.gui_tools import ask_for_next_round, safe_ui_call
        
        print("DEBUG: 准备调用 ask_for_next_round")
        # 确保在主线程中执行
        def call_ask_for_next_round():
            debug_thread_info("call_ask_for_next_round 内部")
            try:
                print("DEBUG: 直接调用 ask_for_next_round")
                ask_for_next_round()
            except Exception as e:
                import traceback
                print(f"ERROR: 调用 ask_for_next_round 时出错: {str(e)}")
                print(traceback.format_exc())
        
        # 使用更长的延迟
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(3000, lambda: safe_ui_call(call_ask_for_next_round))
        
    except Exception as e:
        import traceback
        print(f"ERROR: 任务完成处理出错: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()