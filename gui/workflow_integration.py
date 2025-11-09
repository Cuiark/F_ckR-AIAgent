#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading
import logging
import traceback
import queue  # 添加队列模块导入
import json  # 添加json模块导入
from typing import Dict, List, Any, Optional, Callable

from gui.task_manager import TaskManager, Task, TaskStatus
from workflow.engine import WorkflowEngine
from models import setup_llm

# 导入execute_agent_with_approval函数
from main import execute_agent_with_approval
from agents import create_agents

# 全局变量用于跟踪当前工作流集成实例
current_integration = None

class WorkflowIntegration:
    """工作流集成类，连接任务管理器和工作流引擎"""
    
    def __init__(self, model_type: str = "deepseek-chat", root=None):
        global current_integration
        self.model_type = model_type
        self.task_manager = TaskManager()
        self.workflow_engine = None
        self.initialized = False
        self.running = False
        self.worker_thread = None
        self.current_workflow = None  # 添加当前工作流属性
        self.current_task = None  # 添加当前任务属性
        self.decision_queue = queue.Queue()  # 添加决策队列
        self.report_callback = None  # 添加报告回调
        self.decision_callback = None  # 添加决策回调
        self.root = root  # 添加root引用用于UI更新
        # 移除冗余的事件字典，统一使用任务对象的审批事件
        # self.decision_events = {}  # 移除
        self.decision_results = {}  # 保留决策结果字典
        self.logger = logging.getLogger("workflow_integration")
        # 设置全局当前实例
        import gui.workflow_integration as wi
        wi.current_integration = self
    
    def _process_feedback(self, task, feedback):
        """处理用户建议反馈"""
        try:
            if not hasattr(task, 'approval_data') or not task.approval_data:
                self.logger.error("任务缺少审批数据")
                return False
            
            original_report = task.approval_data.get("report", "")
            agent_name = task.approval_data.get("agent_name", "未知代理")
            stage = task.approval_data.get("stage", "未知阶段")
            
            self.logger.info(f"开始处理用户建议: {agent_name} - {stage}")
            
            # 构造决策对象
            decision = {
                "status": "feedback",
                "feedback": feedback
            }
            
            # 使用main.py中的process_decision函数处理建议
            from main import process_decision
            
            # 获取LLM实例
            from models import setup_llm
            llm = setup_llm(self.model_type)
            
            # 处理决策
            result = process_decision(
                decision=decision,
                llm=llm,
                secretary_agent=None,  # 可以传入secretary_agent如果需要
                last_report=original_report,
                stage=stage,
                agent_name=agent_name
            )
            
            if result and result.get("feedback_processed"):
                updated_report = result.get("report", original_report)
                
                # 更新任务的审批数据
                task.approval_data["report"] = updated_report
                task.approval_data["feedback"] = feedback
                task.approval_data["updated"] = True
                
                # 记录更新后的报告
                from tools import log_agent_report
                report_type = "pre_updated" if stage == "执行前" else "post_updated"
                log_agent_report.run(
                    content=updated_report,
                    report_type=report_type,
                    agent_name=agent_name
                )
                
                self.logger.info(f"已处理用户建议并更新报告: {agent_name} - {stage}")
                
                # 刷新UI显示更新后的报告
                self.refresh_ui_for_approval(task)
                
                # 添加到决策队列，状态为pending_approval
                feedback_decision = {
                    "task_id": task.task_id,
                    "status": "pending_approval",
                    "feedback": feedback,
                    "updated_report": updated_report
                }
                self.decision_queue.put(feedback_decision)
                
                return True
            else:
                self.logger.error(f"建议处理失败: {result}")
                return False
            
        except Exception as e:
            self.logger.error(f"处理建议反馈时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False    
    
    def initialize(self):
        """初始化工作流引擎"""
        if self.initialized:
            return
            
        try:
            # 创建工作流引擎
            self.workflow_engine = WorkflowEngine(self.model_type)
            
            # 设置回调函数
            self.workflow_engine.set_callbacks(
                report_callback=self._on_report,
                tool_callback=self._on_tool_output,
                log_callback=self._on_log,
                role_callback=self._on_role_change,
                decision_callback=self._on_decision_needed,
                completion_callback=self._on_workflow_completed
            )
            
            # 设置任务管理器回调
            self.task_manager.set_callbacks(
                on_task_created=self._on_task_created,
                on_task_started=self._on_task_started,
                on_task_completed=self._on_task_completed,
                on_task_failed=self._on_task_failed,
                on_task_cancelled=self._on_task_cancelled,
                on_task_waiting_approval=self._on_task_waiting_approval,
                on_task_approved=self._on_task_approved,
                on_task_rejected=self._on_task_rejected,
                on_all_tasks_completed=self._on_all_tasks_completed
            )
            
            self.initialized = True
            self.logger.info("工作流集成初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化工作流引擎失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            # 添加：重置状态
            self.workflow_engine = None
            self.initialized = False
            raise
            
    def start_workflow(self, workflow_name: str, module_name: str = None):
        """启动工作流"""
        if not self.initialized:
            self.initialize()
            
        if self.running:
            self.logger.warning("工作流已在运行中")
            return
        
        # 设置当前工作流名称
        self.current_workflow = workflow_name
        self.logger.info(f"设置当前工作流: {workflow_name}")
            
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._run_workflow,
            args=(workflow_name, module_name)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    
    def stop_workflow(self):
        """停止当前正在运行的工作流"""
        if not self.running:
            self.logger.warning("没有正在运行的工作流")
            return
        
        self.logger.info("正在停止工作流...")
        self.running = False
        
        # 停止任务管理器
        self.task_manager.stop_processing()
        
        # 等待工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)
            if self.worker_thread.is_alive():
                self.logger.warning("工作线程未能在超时时间内结束")
    
        self.logger.info("工作流已停止")
    
    def _run_workflow(self, workflow_name: str, module_name: str = None):
        """执行工作流的线程函数"""
        try:
            self.logger.info(f"开始执行工作流: {workflow_name}")
            self.current_workflow = workflow_name  # 设置当前工作流
        
            # 检查工作流是否存在
            if workflow_name not in self.workflow_engine.workflows:
                self.logger.error(f"工作流 '{workflow_name}' 不存在")
                self.running = False
                return
            
            # 获取工作流配置
            workflow = self.workflow_engine.workflows[workflow_name]
            
            # 处理不同的工作流格式
            # 如果工作流是列表（直接的模块列表）
            if isinstance(workflow, list):
                modules = workflow
            # 如果工作流是字典（包含modules键）
            elif isinstance(workflow, dict) and "modules" in workflow:
                modules = workflow.get("modules", [])
            else:
                self.logger.error(f"工作流 '{workflow_name}' 格式不正确")
                self.running = False
                return
        
            # 如果指定了模块名称，只运行该模块
            if module_name:
                modules = [m for m in modules if m.get("name") == module_name]
                if not modules:
                    self.logger.error(f"模块 '{module_name}' 在工作流 '{workflow_name}' 中不存在")
                    self.running = False
                    return
            
            # 创建agents
            group_name = workflow_name if workflow_name != "default_group" else "default_group"
            agents = create_agents(self.workflow_engine.llm_for_agents, group_name=group_name)
            secretary_agent = agents.get("secretary")
            
            if not secretary_agent:
                self.logger.error("未找到秘书Agent，无法生成报告")
                self.running = False
                return
            
            # 执行工作流中的每个模块
            previous_results = {}  # 存储前一个模块的结果
            
            for module in modules:
                if not self.running:
                    self.logger.info("工作流执行被中断")
                    break
                
                module_name = module.get("name", "未命名模块")
                agent_name = module.get("agent", "未知代理")
                
                self.logger.info(f"执行模块: {module_name}, 代理: {agent_name}")
                
                # 创建执行前报告任务
                pre_report_task_id = self.task_manager.create_task(
                    name=f"{agent_name}执行前报告",
                    description=f"生成{agent_name}的执行前报告",
                    agent_name="secretary",
                    expected_output="执行前报告"
                )
                
                # 开始执行前报告任务
                self.task_manager.start_task(pre_report_task_id)
                
                # 创建任务
                task_id = self.task_manager.create_task(
                    name=module_name,
                    description=f"执行 {agent_name} 的任务",
                    agent_name=agent_name,
                    expected_output=f"{agent_name}的执行结果"
                )
                
                # 获取Task对象
                task = self.task_manager.get_task(task_id)
                
                if task is None:
                    self.logger.error(f"无法获取任务对象，任务ID: {task_id}")
                    continue
                    
                # 更新任务状态
                self.task_manager.start_task(task.task_id)
                
                # 准备输入数据
                input_data = previous_results.get(agent_name, {})
                
                # 创建决策函数适配器
                def decision_adapter(report, stage, agent_name):
                    """决策适配器 - 简化版本"""
                    try:
                        # 创建任务并等待审批
                        task_id = self.task_manager.create_task(
                            name=f"{agent_name} {stage}报告审批",
                            description=f"审批 {agent_name} 的 {stage}报告",
                            agent_name=agent_name,
                            expected_output="审批结果"
                        )
                        
                        # 开始任务
                        self.task_manager.start_task(task_id)
                        
                        # 准备审批数据
                        approval_data = {
                            "report": report,
                            "stage": stage,
                            "agent_name": agent_name,
                            "feedback": ""
                        }
                        
                        # 等待审批
                        task = self.task_manager.wait_for_approval(task_id, approval_data)
                        
                        # 显示报告
                        if self.report_callback:
                            report_header = f"【{agent_name} - {stage}报告】"
                            formatted_report = f"\n{report_header}\n{'='*80}\n{report}\n{'='*80}\n"
                            self.report_callback(formatted_report, True)
                        
                        # 等待审批完成
                        timeout = 600  # 10分钟
                        self.logger.info(f"等待任务 {task_id} 的审批事件")
                        approved = task.approval_event.wait(timeout)
                        
                        if not approved:
                            self.logger.warning(f"审批超时，自动批准: {agent_name} - {stage}")
                            return {"status": "approved", "feedback": "自动批准（审批超时）"}
                        
                        # 获取审批结果
                        status = task.approval_result
                        feedback = task.approval_data.get("feedback", "")
                        
                        self.logger.info(f"获取到审批结果: {status}, 反馈: {feedback}")
                        
                        return {
                            "status": status if status else "approved", 
                            "feedback": feedback
                        }
                    except Exception as e:
                        self.logger.error(f"决策适配器出错: {str(e)}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                        return {"status": "approved", "feedback": f"自动批准（决策适配器出错: {str(e)}）"}
                
                try:
                    # 创建一个正确的决策适配器函数
                    def decision_adapter(report, stage, agent_name):
                        return self._on_decision_needed(report, stage, agent_name)
                    
                    # 直接调用execute_agent_with_approval，让秘书Agent负责报告生成
                    result = execute_agent_with_approval(
                        agents[agent_name],
                        module.get("description", ""),
                        self.workflow_engine.llm_for_direct,
                        secretary_agent,
                        previous_report=previous_results.get("previous_report"),
                        raw_data=input_data,
                        get_decision_func=decision_adapter
                    )
                    
                    # 存储结果供下一个模块使用，不再管理长度
                    previous_results[agent_name] = result.get("result", {})
                    previous_results["previous_report"] = result.get("post_report", "")
                    
                    # 更新任务状态
                    if getattr(task, 'approval_result', "approved") == "approved":
                        self.task_manager.complete_task(task.task_id)
                        task.add_log(f"任务执行结果: {str(result.get('result', {}))[:1000]}")  # 限制日志长度
                    else:
                        self.task_manager.fail_task(task.task_id, "用户拒绝了执行")
                        break
                    
                except Exception as e:
                    self.logger.error(f"执行模块 {module_name} 时出错: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    self.task_manager.fail_task(task.task_id, f"执行失败: {str(e)}")
                    continue
                
                if not self.running:
                    break
            
            # 工作流完成
            if self.running:
                self.logger.info(f"工作流 '{workflow_name}' 执行完成")
                if self.workflow_engine.completion_callback:
                    self.workflow_engine.completion_callback(workflow_name)
        
        except Exception as e:
            self.logger.error(f"执行工作流时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
        finally:
            self.running = False
        # 在WorkflowIntegration类中添加以下方法
        
    def _on_report(self, content: str, is_pre_execution: bool = False):
        """报告回调"""
        report_type = "执行前" if is_pre_execution else "执行后"
        self.logger.info(f"收到{report_type}报告")
        
        # 更新当前任务
        if self.task_manager.current_task:
            # 使用更明确的日志标记
            log_entry = f"## {report_type}报告 ##\n{content}"
            self.task_manager.current_task.add_log(log_entry)
            
            # 触发报告回调
            if self.report_callback:
                self.report_callback(content, is_pre_execution)
                
            # 保存报告到文件系统
            try:
                from tools.security_tools import log_agent_report
                from tools import log_agent_report_enhanced
                
                agent_name = self.task_manager.current_task.agent_name or "未知代理"
                group_id = getattr(self.task_manager.current_task, 'group_id', 'default_group')
                
                # 使用原有的日志系统
                log_agent_report(
                    content=content,
                    report_type="pre" if is_pre_execution else "post",
                    agent_name=agent_name
                )
                
                # 使用增强的日志系统
                enhanced_report_type = "pre_execution" if is_pre_execution else "post_execution"
                metadata = {
                    "task_id": self.task_manager.current_task.task_id,
                    "stage": report_type,
                    "workflow_step": getattr(self.task_manager.current_task, 'current_step', 'unknown')
                }
                
                log_result = log_agent_report_enhanced(
                    role_name=agent_name,
                    group_id=group_id,
                    content=content,
                    report_type=enhanced_report_type,
                    metadata=metadata
                )
                
                if log_result.get('status') == 'success':
                    self.logger.info(f"增强日志记录成功: {agent_name} - {enhanced_report_type}")
                else:
                    self.logger.warning(f"增强日志记录失败: {log_result.get('message')}")
                
                # 同时保存为HTML报告
                self.save_report_to_file(
                    content=content,
                    report_type=report_type,
                    agent_name=agent_name
                )
            except Exception as e:
                self.logger.error(f"保存报告失败: {str(e)}")
    def _on_tool_output(self, message: str):
        """工具输出回调"""
        self.logger.info(f"工具输出: {message}")
        # 更新当前任务
        if self.task_manager.current_task:
            self.task_manager.current_task.add_log(f"工具输出: {message}")
                
    def _on_log(self, message: str):
        """日志回调"""
        self.logger.info(f"日志: {message}")
        # 更新当前任务
        if self.task_manager.current_task:
            self.task_manager.current_task.add_log(f"日志: {message}")
                
    def _on_role_change(self, role_name: str):
        """角色变更回调"""
        self.logger.info(f"角色变更: {role_name}")
        # 更新当前任务
        if self.task_manager.current_task:
            self.task_manager.current_task.add_log(f"角色变更: {role_name}")
                
    # 添加以下方法到WorkflowIntegration类
    
    def set_report_callback(self, callback):
        """设置报告回调函数"""
        self.report_callback = callback
    
    def set_decision_callback(self, callback):
        """设置决策回调函数"""
        self.decision_callback = callback

    def set_completion_callback(self, callback):
        """设置工作流完成回调函数"""
        self.completion_callback = callback
    
    def submit_decision(self, decision):
        """提交决策到工作流引擎
        
        参数:
            decision: 决策对象，包含task_id, status, feedback
            
        返回:
            bool: 是否成功
        """
        try:
            # 获取任务ID和状态
            task_id = decision.get("task_id")
            status = decision.get("status")
            feedback = decision.get("feedback", "")
            
            self.logger.info(f"提交决策: {task_id} - {status} - {feedback}")
            
            # 获取任务对象
            task = self.task_manager.get_task(task_id)
            if not task:
                self.logger.error(f"找不到任务: {task_id}")
                return False
            
            # 处理建议反馈
            if status == "feedback":
                return self._process_feedback(task, feedback)
            
            # 存储决策
            self.decision_results[task_id] = decision
            
            # 更新任务审批数据
            if hasattr(task, "approval_data") and task.approval_data:
                task.approval_data["feedback"] = feedback
            
            # 处理其他决策
            result = False
            if status == "approved":
                result = self.task_manager.approve_task(task_id)
            elif status == "rejected":
                result = self.task_manager.reject_task(task_id)
            else:
                # 未知状态，默认为批准
                self.logger.warning(f"未知的决策状态: {status}，默认为批准")
                result = self.task_manager.approve_task(task_id)
                
            # 将决策放入队列
            self.decision_queue.put(decision)
                
            return result
                
        except Exception as e:
            self.logger.error(f"提交决策时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _on_decision_needed(self, report, stage, agent_name):
        """决策回调"""
        self.logger.info(f"请求决策: {agent_name} - {stage}")
        
        # 获取当前任务
        current_task = self.task_manager.current_task
        if not current_task:
            self.logger.error("请求决策时没有当前任务")
            return {"status": "approved", "feedback": "自动批准（无当前任务）"}
        
        # 设置当前任务引用
        self.current_task = current_task
    
        # 更新任务状态为等待审批
        approval_data = {
            "report": report,
            "stage": stage,
            "agent_name": agent_name,
            "feedback": ""  # 确保有feedback字段
        }
        
        # 等待审批
        self.task_manager.wait_for_approval(current_task.task_id, approval_data)
        
        # 显示报告
        report_header = f"【{agent_name} - {stage}报告】"
        formatted_report = f"\n{report_header}\n{'='*80}\n{report}\n{'='*80}\n"
    
        # 使用回调函数更新UI
        try:
            if hasattr(self, "report_callback") and self.report_callback:
                # 使用safe_ui_call确保在主线程中更新UI
                from gui.gui_tools import safe_ui_call
                safe_ui_call(self.report_callback, formatted_report, True)
                
            # 添加：如果有决策回调，调用它
            if hasattr(self, "decision_callback") and self.decision_callback:
                # 在决策回调中传递任务ID
                from gui.app import submit_decision
                # 保存原始的submit_decision函数
                original_submit_decision = submit_decision
                
                # 定义一个新的submit_decision函数，自动添加task_id
                def wrapped_submit_decision(status, feedback=""):
                    return original_submit_decision(current_task.task_id, status, feedback)
                
                # 临时替换全局函数
                import gui.app
                gui.app.submit_decision = wrapped_submit_decision
                
                # 调用决策回调
                safe_ui_call(self.decision_callback, report, agent_name, stage, current_task.task_id)
                
                # 恢复原始函数
                gui.app.submit_decision = original_submit_decision
        except Exception as e:
            self.logger.error(f"更新报告显示时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
    
        # 等待任务的审批事件
        try:
            # 设置超时，防止无限等待
            timeout = 600  # 10分钟
            self.logger.info(f"等待任务 {current_task.task_id} 的审批事件")
            approved = current_task.approval_event.wait(timeout)
        
            if not approved:
                # 超时，自动批准
                self.logger.warning(f"审批超时，自动批准: {agent_name} - {stage}")
                return {"status": "approved", "feedback": "自动批准（审批超时）"}
            
            # 获取审批结果
            status = current_task.approval_result
            feedback = current_task.approval_data.get("feedback", "")
            original_option = current_task.approval_data.get("original_option", "")
            
            # 记录原始选项（如果有）
            if original_option:
                self.logger.info(f"用户选择了模板选项: {original_option}，映射为: {status}")
            
            self.logger.info(f"获取到审批结果: {status}, 反馈: {feedback}")
            
            # 简化的决策处理逻辑，只处理标准状态
            if status in ["approved", "rejected", "feedback"]:
                # 标准状态直接返回
                return {
                    "status": status, 
                    "feedback": feedback
                }
            else:
                # 未知状态，默认为批准
                self.logger.warning(f"未知的决策状态: {status}，默认为批准")
                return {
                    "status": "approved", 
                    "feedback": feedback
                }
            
        except Exception as e:
            self.logger.error(f"等待审批时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"status": "approved", "feedback": f"自动批准（等待审批出错: {str(e)}）"}
                
    def _on_workflow_completed(self, message=None):
        """工作流完成回调
        
        参数:
            message: 完成消息，可选
        """
        self.logger.info(f"工作流完成: {message if message else ''}")
        
        # 添加：通知UI工作流已完成
        try:
            # 使用safe_ui_call确保在主线程中更新UI
            from gui.gui_tools import safe_ui_call
            if hasattr(self, "completion_callback") and self.completion_callback:
                safe_ui_call(self.completion_callback, self.current_workflow)
        except Exception as e:
            self.logger.error(f"通知UI工作流完成时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
    
    # 任务管理器回调函数
    def _on_task_created(self, task: Task):
        """任务创建回调"""
        self.logger.info(f"任务创建: {task.name}")
        
    def _on_task_started(self, task: Task):
        """任务开始回调"""
        self.logger.info(f"任务开始: {task.name}")
        
    def _on_task_completed(self, task: Task):
        """任务完成回调"""
        self.logger.info(f"任务完成: {task.name}")
        
    def _on_task_failed(self, task: Task):
        """任务失败回调"""
        self.logger.info(f"任务失败: {task.name} - {task.error}")
        
    def _on_task_cancelled(self, task: Task):
        """任务取消回调"""
        self.logger.info(f"任务取消: {task.name}")
        
    def _on_task_waiting_approval(self, task: Task):
        """任务等待审批回调"""
        self.logger.info(f"任务等待审批: {task.name}")
        # 新增：强制刷新UI
        try:
            from gui.gui_tools import safe_ui_call
            safe_ui_call(self.refresh_ui_for_approval, task)
        except Exception as e:
            self.logger.error(f"刷新审批UI失败: {str(e)}")
    
    def refresh_ui_for_approval(self, task):
        """刷新UI以显示等待审批的任务"""
        try:
            # 检查任务是否有approval_data和report
            if hasattr(task, 'approval_data') and task.approval_data and "report" in task.approval_data:
                report = task.approval_data["report"]
                stage = task.approval_data.get("stage", "未知阶段")
                agent_name = task.approval_data.get("agent_name", "未知代理")
                feedback = task.approval_data.get("feedback", "")
                is_pre_execution = (stage == "执行前")
                
                # 使用safe_ui_call确保在主线程中更新UI
                from gui.gui_tools import safe_ui_call
                
                # 使用report_callback更新报告显示
                if self.report_callback:
                    safe_ui_call(self.report_callback, report, is_pre_execution)
                
                # 延迟一小段时间后触发决策需求，确保报告已更新
                def delayed_decision_callback():
                    if self.decision_callback:
                        safe_ui_call(self.decision_callback, report, agent_name, stage, task.task_id)
                
                # 使用after方法延迟执行
                if hasattr(self, 'root') and self.root:
                    self.root.after(100, delayed_decision_callback)
                else:
                    delayed_decision_callback()
                
                self.logger.info(f"已刷新UI，显示任务 {task.task_id} 的审批请求")
            else:
                self.logger.warning(f"任务 {task.task_id} 没有报告数据，无法刷新UI")
        except Exception as e:
            self.logger.error(f"刷新审批UI失败: {str(e)}")
            self.logger.error(traceback.format_exc())
        
    def _on_task_approved(self, task: Task):
        """任务批准回调"""
        self.logger.info(f"任务批准: {task.name}")
        
    def _on_task_rejected(self, task: Task):
        """任务拒绝回调"""
        self.logger.info(f"任务拒绝: {task.name}")
        
    def _on_all_tasks_completed(self):
        """所有任务完成回调"""
        self.logger.info("所有任务完成")
    
    def get_workflow_data(self, workflow_name):
        """获取工作流配置数据
        
        参数:
            workflow_name: 工作流名称（对应group_name）
            
        返回:
            工作流配置数据字典
        """
        try:
            # 如果工作流引擎未初始化，先初始化
            if not self.initialized:
                self.logger.info(f"工作流引擎未初始化，正在初始化...")
                self.initialize()
                
            # 检查工作流引擎是否正确初始化
            if not self.workflow_engine:
                self.logger.error("工作流引擎初始化失败")
                return {}
                
            # 检查workflows属性是否存在
            if not hasattr(self.workflow_engine, 'workflows'):
                self.logger.error("工作流引擎没有workflows属性")
                return {}
                
            # 从工作流引擎获取工作流配置
            if workflow_name in self.workflow_engine.workflows:
                group_modules = self.workflow_engine.workflows.get(workflow_name, [])
                
                # 构建工作流数据字典
                workflow_data = {
                    "name": workflow_name,
                    "description": f"{workflow_name}工作组",
                    "modules": {}
                }
                
                # 将组中的每个模块添加到modules字典中
                for i, module_info in enumerate(group_modules):
                    # 使用模块名称作为键，如果没有则使用索引
                    module_name = module_info.get("name", f"module_{i}")
                    module_id = f"module_{i}"  # 生成唯一ID
                    
                    # 保留agent字段
                    agent_name = module_info.get("agent", "")
                    
                    workflow_data["modules"][module_id] = {
                        "name": module_name,
                        "description": module_info.get("description", ""),
                        "agent": agent_name,
                        "tools": []  # 工具列表可能需要从其他地方获取
                        }
                    
                self.logger.info(f"处理后的工作流数据: {workflow_data}")
                return workflow_data
            else:
                self.logger.warning(f"未找到工作流: {workflow_name}")
                return {}
                
        except Exception as e:
            self.logger.error(f"获取工作流数据失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}  # 返回空字典而不是None，保持一致的返回类型
    
    def run_workflow(self, workflow_name):
        """运行指定的工作流
        
        参数:
            workflow_name: 工作流名称
            
        返回:
            工作流执行结果
        """
        try:
            self.logger.info(f"准备运行工作流: {workflow_name}")
            
            # 获取工作流配置
            workflow_data = self.get_workflow_data(workflow_name)
            
            # 确保workflow_data是字典类型
            if not isinstance(workflow_data, dict):
                self.logger.error(f"工作流数据类型错误: {type(workflow_data)}")
                return {"status": "error", "message": "工作流数据类型错误"}
                
            # 获取模块信息
            modules = workflow_data.get("modules", {})
            if not modules:
                self.logger.warning(f"工作流 {workflow_name} 没有模块")
                return {"status": "completed", "message": "工作流没有模块", "results": {}}
                
            # 启动工作流
            self.logger.info(f"开始启动工作流: {workflow_name}")
            self.start_workflow(workflow_name)
            return {"status": "started", "message": f"工作流 {workflow_name} 已启动"}
            
        except Exception as e:
            self.logger.error(f"运行工作流失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"status": "error", "message": f"运行工作流失败: {str(e)}"}

    def save_report_to_file(self, content: str, report_type: str, agent_name: str):
        """保存报告到文件"""
        try:
            # 创建reports目录（如果不存在）
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            # 生成文件名 - 优先保存为JSON格式以支持报告查看模块
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            json_filename = f"{timestamp}_{agent_name}_{report_type}.json"
            json_filepath = os.path.join(reports_dir, json_filename)
            
            # 解析报告内容，提取结构化信息
            summary = self._extract_summary(content)
            details = self._extract_details(content)
            recommendations = self._extract_recommendations(content)
            
            # 创建JSON报告数据
            report_data = {
                "title": f"{report_type}报告 - {agent_name}",
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": report_type,
                "generator": agent_name,
                "summary": summary,
                "details": details,
                "recommendations": recommendations,
                "raw_content": content
            }
            
            # 保存JSON格式报告（优先级高）
            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            # 同时保存HTML格式报告（兼容性）
            html_filename = f"{timestamp}_{agent_name}_{report_type}.html"
            html_filepath = os.path.join(reports_dir, html_filename)
            
            content_html = content.replace("\n", "<br>")
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report_type}报告 - {agent_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .report-content {{ 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            border-left: 4px solid #3498db; 
        }}
        .metadata {{ 
            background-color: #eaf2f8; 
            padding: 10px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }}
    </style>
</head>
<body>
    <h1>{report_type}报告 - {agent_name}</h1>
    
    <div class="metadata">
        <p><strong>生成时间:</strong> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>代理:</strong> {agent_name}</p>
        <p><strong>报告类型:</strong> {report_type}</p>
    </div>
    
    <div class="report-content">
        {content_html}
    </div>
</body>
</html>"""
            
            with open(html_filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            self.logger.info(f"报告已保存到: {json_filepath} (JSON) 和 {html_filepath} (HTML)")
            return json_filepath
        except Exception as e:
            self.logger.error(f"保存报告到文件失败: {str(e)}")
            return None
    
    def _extract_summary(self, content: str) -> str:
        """从报告内容中提取摘要"""
        try:
            # 查找摘要部分
            summary_markers = ["摘要", "概述", "总结", "执行摘要"]
            for marker in summary_markers:
                if marker in content:
                    lines = content.split("\n")
                    summary_lines = []
                    found_marker = False
                    for line in lines:
                        if marker in line:
                            found_marker = True
                            continue
                        if found_marker:
                            if line.strip() and not any(m in line for m in ["详细", "建议", "结论"]):
                                summary_lines.append(line.strip())
                            elif line.strip() and any(m in line for m in ["详细", "建议", "结论"]):
                                break
                    if summary_lines:
                        return "\n".join(summary_lines[:5])  # 限制摘要长度
            
            # 如果没有找到明确的摘要，取前几行作为摘要
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            return "\n".join(lines[:3]) if lines else "无摘要信息"
        except:
            return "无摘要信息"
    
    def _extract_details(self, content: str) -> list:
        """从报告内容中提取详细信息"""
        try:
            details = []
            lines = content.split("\n")
            current_section = ""
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否是新的章节标题
                if any(marker in line for marker in ["详细", "分析", "结果", "发现", "执行"]):
                    if current_section and current_content:
                        details.append({
                            "title": current_section,
                            "content": "\n".join(current_content)
                        })
                    current_section = line
                    current_content = []
                else:
                    current_content.append(line)
            
            # 添加最后一个章节
            if current_section and current_content:
                details.append({
                    "title": current_section,
                    "content": "\n".join(current_content)
                })
            
            return details if details else [{"title": "详细内容", "content": content}]
        except:
            return [{"title": "详细内容", "content": content}]
    
    def _extract_recommendations(self, content: str) -> list:
        """从报告内容中提取建议"""
        try:
            recommendations = []
            lines = content.split("\n")
            found_recommendations = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if any(marker in line for marker in ["建议", "推荐", "措施", "行动"]):
                    found_recommendations = True
                    continue
                    
                if found_recommendations:
                    if line.startswith(("1.", "2.", "3.", "-", "•")) or "建议" in line:
                        recommendations.append(line)
                    elif line and not any(marker in line for marker in ["总结", "结论"]):
                        recommendations.append(line)
                    else:
                        break
            
            return recommendations if recommendations else ["暂无具体建议"]
        except:
            return ["暂无具体建议"]


    def execute_workflow(self, workflow_name, callbacks=None):
        """执行指定的工作流"""
        if not workflow_name in self.workflow_engine.workflows:
            self.logger.error(f"工作流 '{workflow_name}' 不存在")
            return False
        
        # 设置回调
        if callbacks:
            self.workflow_engine.set_callbacks(**callbacks)
        
        # 获取工作流配置
        workflow = self.workflow_engine.workflows[workflow_name]
        
        # 创建任务组
        task_ids = []
        for step in workflow.get("steps", []):
            agent_name = step.get("agent")
            task_name = f"{agent_name} 任务"
            task_description = step.get("description", f"执行 {agent_name} 的任务")
            expected_output = step.get("output", "任务输出")
            
            task_id = self.task_manager.create_task(
                name=task_name,
                description=task_description,
                agent_name=agent_name,
                expected_output=expected_output
            )
            task_ids.append(task_id)
        
        # 记录任务组
        self.task_manager.task_groups[workflow_name] = task_ids
        self.task_manager.current_group = workflow_name
        
        # 启动工作流执行线程
        thread = threading.Thread(
            target=self._execute_workflow_thread,
            args=(workflow_name, workflow, task_ids)
        )
        thread.daemon = True
        thread.start()
        
        return True

