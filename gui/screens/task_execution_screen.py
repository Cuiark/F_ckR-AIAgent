#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import threading
import traceback
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, List, Any, Optional, Callable

from gui.task_manager import TaskStatus
from gui.workflow_integration import WorkflowIntegration

logger = logging.getLogger("task_execution_screen")

class TaskExecutionScreen(ttk.Frame):
    """任务执行界面 - 流程驱动版本"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # 获取根窗口
        self.root = self.winfo_toplevel()
        self.workflow_integration = None
        self.current_task_id = None
        self.decision_thread = None
        self.running = False
        self.current_stage = None  # 当前流程阶段
        self.current_agent = None  # 当前执行的Agent
        # 添加日志记录器
        self.logger = logging.getLogger("task_execution_screen")
        
        # 创建界面
        self._create_workflow_ui()
        
        # 初始化工作流集成
        self._initialize_workflow()
        
    def _create_workflow_ui(self):
        """创建现代化流程驱动界面"""
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 页面标题
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="⚡ 任务执行中心", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, text="智能工作流程管理与执行", style="Subtitle.TLabel")
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # 控制卡片
        control_card = ttk.Frame(main_container, style="Card.TFrame")
        control_card.pack(fill=tk.X, pady=(0, 20))
        
        # 卡片内容
        self.control_frame = ttk.Frame(control_card)
        self.control_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 工作流选择区域
        workflow_frame = ttk.Frame(self.control_frame)
        workflow_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.workflow_label = ttk.Label(workflow_frame, text="🔄 选择工作流程:", 
                                       font=("Segoe UI", 10, "bold"))
        self.workflow_label.pack(anchor=tk.W)
        
        self.workflow_combo = ttk.Combobox(workflow_frame, width=35, state="readonly",
                                          font=("Segoe UI", 10))
        self.workflow_combo.pack(anchor=tk.W, pady=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        # 执行按钮 - 主要操作
        self.execute_button = ttk.Button(
            button_frame, 
            text="🚀 开始执行", 
            command=self._on_execute_workflow,
            style="Accent.TButton"
        )
        self.execute_button.pack(pady=(0, 8))
        
        # 停止按钮 - 次要操作
        self.stop_button = ttk.Button(
            button_frame, 
            text="⏹️ 停止执行", 
            command=self._on_stop_workflow,
            state=tk.DISABLED
        )
        self.stop_button.pack()
        
        # 主内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧流程面板卡片
        flow_card = ttk.Frame(content_frame, style="Card.TFrame")
        flow_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 流程面板标题
        flow_header = ttk.Frame(flow_card)
        flow_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        flow_title = ttk.Label(flow_header, text="📋 工作流程", 
                              font=("Segoe UI", 12, "bold"))
        flow_title.pack(side=tk.LEFT)
        
        # 流程状态指示器
        self.flow_status = ttk.Label(flow_header, text="⏸️ 未开始", 
                                    font=("Segoe UI", 10),
                                    foreground="#6b7280")
        self.flow_status.pack(side=tk.RIGHT)
        
        # 流程步骤列表
        steps_frame = ttk.Frame(flow_card)
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.flow_steps = ttk.Treeview(steps_frame, 
                                      columns=("部门", "角色", "状态"), 
                                      show="tree headings",
                                      height=12)
        
        # 设置列标题和样式
        self.flow_steps.heading("#0", text="📝 执行步骤")
        self.flow_steps.heading("部门", text="🏢 部门")
        self.flow_steps.heading("角色", text="👤 角色")
        self.flow_steps.heading("状态", text="📊 状态")
        
        self.flow_steps.column("#0", width=200, minwidth=150)
        self.flow_steps.column("部门", width=120, minwidth=100)
        self.flow_steps.column("角色", width=120, minwidth=100)
        self.flow_steps.column("状态", width=100, minwidth=80)
        
        # 添加滚动条
        steps_scrollbar = ttk.Scrollbar(steps_frame, orient=tk.VERTICAL, command=self.flow_steps.yview)
        self.flow_steps.configure(yscrollcommand=steps_scrollbar.set)
        
        self.flow_steps.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        steps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右侧报告面板卡片
        report_card = ttk.Frame(content_frame, style="Card.TFrame")
        report_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 报告面板标题
        report_header = ttk.Frame(report_card)
        report_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        report_title_label = ttk.Label(report_header, text="📄 执行报告", 
                                      font=("Segoe UI", 12, "bold"))
        report_title_label.pack(side=tk.LEFT)
        
        # 报告状态
        self.report_status = ttk.Label(report_header, text="💤 等待中", 
                                      font=("Segoe UI", 10),
                                      foreground="#6b7280")
        self.report_status.pack(side=tk.RIGHT)
        
        # 报告内容框架
        self.report_frame = ttk.Frame(report_card)
        self.report_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # 报告标题
        self.report_title = ttk.Label(self.report_frame, text="等待任务执行...", 
                                     font=("Segoe UI", 11, "bold"),
                                     foreground="#374151")
        self.report_title.pack(fill=tk.X, padx=5, pady=5)
        
        # 报告内容
        self.report_content = scrolledtext.ScrolledText(self.report_frame, height=20, wrap=tk.WORD)
        self.report_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.report_content.config(state=tk.DISABLED)
        
        # 决策面板
        self.decision_frame = ttk.LabelFrame(self, text="决策区域")
        self.decision_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 建议输入框
        self.suggestion_frame = ttk.Frame(self.decision_frame)
        self.suggestion_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.suggestion_label = ttk.Label(self.suggestion_frame, text="决策者建议:")
        self.suggestion_label.pack(side=tk.LEFT, padx=5)
        
        # 将Entry改为Text控件，以支持get("1.0", tk.END)方法
        self.suggestion_entry = scrolledtext.ScrolledText(self.suggestion_frame, width=50, height=3)
        self.suggestion_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 决策标题标签
        self.decision_title = ttk.Label(self.decision_frame, text="请做出决策", font=("Microsoft YaHei", 10, "bold"))
        self.decision_title.pack(anchor=tk.W, padx=5, pady=2)
        
        # 决策按钮
        self.button_frame = ttk.Frame(self.decision_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.approve_button = ttk.Button(
            self.button_frame, 
            text="批准", 
            command=self._approve_task
        )
        self.approve_button.pack(side=tk.LEFT, padx=5)
        
        self.reject_button = ttk.Button(
            self.button_frame, 
            text="拒绝", 
            command=self._reject_task
        )
        self.reject_button.pack(side=tk.LEFT, padx=5)
        
        self.feedback_button = ttk.Button(
            self.button_frame, 
            text="提供建议", 
            command=self._provide_feedback
        )
        self.feedback_button.pack(side=tk.LEFT, padx=5)
        
        # 自动批准按钮
        self.auto_approve_button = ttk.Button(
            self.button_frame, 
            text="🤖 自动批准", 
            command=self._toggle_auto_approve,
            style="Accent.TButton"
        )
        self.auto_approve_button.pack(side=tk.LEFT, padx=5)
        
        # 决策按钮列表
        self.decision_buttons = [self.approve_button, self.reject_button, self.feedback_button, self.auto_approve_button]
        
        # 自动批准状态
        self.auto_approve_enabled = False
        
        # 默认禁用决策控件
        self._set_decision_controls_state(tk.DISABLED)
        
        # 不再使用模板管理器
        
        # 历史记录面板
        self.history_frame = ttk.LabelFrame(self, text="历史记录")
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.history_content = scrolledtext.ScrolledText(self.history_frame, height=8, wrap=tk.WORD)
        self.history_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_content.config(state=tk.DISABLED)
    
    def _initialize_workflow(self):
        """初始化工作流集成"""
        try:
            # 创建工作流集成
            self.workflow_integration = WorkflowIntegration(root=self.root)
            
            # 设置回调函数
            self.workflow_integration.set_report_callback(self._update_report_display)
            self.workflow_integration.set_decision_callback(self._on_decision_needed)
            
            # 添加：注册工作流完成回调
            self.workflow_integration.set_completion_callback(self._on_workflow_completed)
            
            # 初始化工作流引擎
            self.workflow_integration.initialize()
            
            # 加载工作流列表
            self._load_workflow_list()
            
        except Exception as e:
            self.logger.error(f"初始化工作流集成失败: {str(e)}")
            messagebox.showerror("错误", f"初始化工作流集成失败: {str(e)}")
    
    # 添加工作流完成处理方法
    def _on_workflow_completed(self, workflow_name):
        """工作流完成回调"""
        self.logger.info(f"工作流 {workflow_name} 已完成")
        
        # 更新UI状态
        self.running = False
        self.execute_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.workflow_combo.config(state="readonly")
        
        # 禁用决策控件
        self._set_decision_controls_state(tk.DISABLED)
        
        # 更新流程状态
        self.flow_status.config(text="工作流已完成")
        
        # 更新流程步骤
        self._update_flow_steps()
        
        # 添加到历史记录
        self._add_to_history(f"工作流 {workflow_name} 已完成")
        
        # 显示完成消息
        messagebox.showinfo("完成", f"工作流 {workflow_name} 已成功完成！")
    
    def _on_task_created(self, task):
        """任务创建回调"""
        self._update_flow_steps()
    
    def _on_task_started(self, task):
        """任务开始回调"""
        self._update_flow_steps()
    
    def _on_task_completed(self, task):
        """任务完成回调"""
        self._update_flow_steps()
    
    def _on_task_failed(self, task):
        """任务失败回调"""
        self._update_flow_steps()
    
    def _on_task_waiting_approval(self, task):
        """任务等待审批回调"""
        try:
            self._update_flow_steps()
            
            # 如果有报告，显示报告
            if hasattr(task, 'approval_data') and task.approval_data and "report" in task.approval_data:
                report = task.approval_data["report"]
                stage = task.approval_data.get("stage", "未知阶段")
                agent_name = task.approval_data.get("agent_name", "未知代理")
                is_pre_execution = (stage == "执行前")
                
                # 更新当前状态
                self.current_stage = stage
                self.current_agent = agent_name
                self.current_task_id = task.task_id
                
                # 更新reported报告
                self._update_report_display(report, is_pre_execution)
                
                # 更新流程状态
                self.flow_status.config(text=f"当前流程: {agent_name} - {stage}报告审批")
                
                # 启用决策控件
                self._set_decision_controls_state(tk.NORMAL)
                
                # 添加到历史记录
                self._add_to_history(f"等待用户对 {agent_name} 的 {stage}报告 进行决策")
                
                # 确保界面更新
                self.update()
                
                logger.info(f"已启用决策控件，等待用户决策: {agent_name} - {stage}")
            else:
                logger.warning("任务等待审批，但没有报告数据")
        except Exception as e:
            logger.error(f"处理任务等待审批回调时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _on_task_approved(self, task):
        """任务批准回调"""
        self._update_flow_steps()
    
    def _on_task_rejected(self, task):
        """任务拒绝回调"""
        self._update_flow_steps()
    
    def _on_execute_workflow(self):
        """执行按钮点击事件"""
        selected_workflow = self.workflow_combo.get()
        
        if not selected_workflow:
            messagebox.showwarning("警告", "请先选择一个工作流")
            return
            
        # 更新UI状态
        self.execute_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.workflow_combo.config(state=tk.DISABLED)
        
        # 清空历史记录和流程步骤
        self.history_content.config(state=tk.NORMAL)
        self.history_content.delete(1.0, tk.END)
        self.history_content.config(state=tk.DISABLED)
        
        for item in self.flow_steps.get_children():
            self.flow_steps.delete(item)
        
        # 启动工作流
        self._add_to_history(f"开始执行工作流: {selected_workflow}")
        self.workflow_integration.start_workflow(selected_workflow)
        
        # 更新流程状态
        self.flow_status.config(text=f"当前流程: {selected_workflow} - 正在执行")
        
        # 更新流程步骤
        self._update_flow_steps()
        
        # 确保决策控件可用（不锁定）
        self._set_decision_controls_state(tk.NORMAL)
    
    def _on_stop_workflow(self):
        """停止按钮点击事件"""
        if messagebox.askyesno("确认", "确定要停止当前工作流吗？"):
            # 停止工作流
            if self.workflow_integration:
                self.workflow_integration.stop_workflow()
            
            # 更新UI状态
            self.execute_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.workflow_combo.config(state="readonly")
            
            # 更新流程状态
            self.flow_status.config(text="当前流程: 已停止")
            
            # 添加到历史记录
            self._add_to_history("工作流已手动停止")
    
    def _create_default_decision_buttons(self):
        """创建默认决策按钮"""
        # 清除现有按钮
        for button in self.decision_buttons:
            if isinstance(button, tk.Widget) and button.winfo_exists():
                button.destroy()
        self.decision_buttons = []
        
        # 创建默认按钮
        self.approve_button = ttk.Button(
            self.button_frame, 
            text="批准", 
            command=self._approve_task
        )
        self.approve_button.pack(side=tk.LEFT, padx=5)
        self.decision_buttons.append(self.approve_button)
        
        self.reject_button = ttk.Button(
            self.button_frame, 
            text="拒绝", 
            command=self._reject_task
        )
        self.reject_button.pack(side=tk.LEFT, padx=5)
        self.decision_buttons.append(self.reject_button)
        
        self.feedback_button = ttk.Button(
            self.button_frame, 
            text="提供建议", 
            command=self._provide_feedback
        )
        self.feedback_button.pack(side=tk.LEFT, padx=5)
        self.decision_buttons.append(self.feedback_button)
        
        # 自动批准按钮
        auto_text = "🔴 关闭自动批准" if self.auto_approve_enabled else "🤖 自动批准"
        self.auto_approve_button = ttk.Button(
            self.button_frame, 
            text=auto_text, 
            command=self._toggle_auto_approve,
            style="Accent.TButton" if not self.auto_approve_enabled else "TButton"
        )
        self.auto_approve_button.pack(side=tk.LEFT, padx=5)
        self.decision_buttons.append(self.auto_approve_button)
    
    # 移除_create_template_buttons方法，使用默认的批准/拒绝/提供建议按钮
    
    # 移除模板相关方法，使用默认的批准/拒绝/提供建议按钮
    
    def _set_decision_controls_state(self, state):
        """设置决策控件状态"""
        self.suggestion_entry.config(state=state)
        for button in self.decision_buttons:
            if isinstance(button, tk.Widget) and button.winfo_exists():
                button.config(state=state)
    
    def _on_report_received(self, report, is_pre_execution):
        """报告接收回调"""
        # 更新reported报告
        self.report_content.config(state=tk.NORMAL)
        self.report_content.delete(1.0, tk.END)
        self.report_content.insert(tk.END, report)
        self.report_content.config(state=tk.DISABLED)
        
        # 更新历史记录
        self._add_to_history(f"收到{'执行前' if is_pre_execution else '执行后'}报告")
    
    def _on_decision_needed(self, report, agent_name, stage, task_id):
        """当需要决策时的回调函数
        
        参数:
            report: 报告内容
            agent_name: 代理名称
            stage: 阶段名称
            task_id: 任务ID
        
        返回:
            决策结果
        """
        logger.info(f"需要对 {agent_name} 的 {stage} 报告做出决策")
        
        # 保存当前任务ID
        self.current_task_id = task_id
        self.current_agent = agent_name
        self.current_stage = stage
        
        # 更新报告显示
        self.report_content.config(state=tk.NORMAL)
        self.report_content.delete("1.0", tk.END)
        self.report_content.insert(tk.END, report)
        self.report_content.config(state=tk.DISABLED)
        
        # 更新决策标题
        self.decision_title.config(text=f"请对{agent_name}的{stage}报告做出决策")
        
        # 始终使用默认按钮（批准/拒绝/提供建议/自动批准）
        self._create_default_decision_buttons()
        
        # 启用决策控件
        self._set_decision_controls_state(tk.NORMAL)
        
        # 添加到历史记录
        self._add_to_history(f"等待用户对 {agent_name} 的 {stage}报告 进行决策")
        
        # 如果启用了自动批准，自动批准任务
        if self.auto_approve_enabled:
            self._add_to_history(f"自动批准模式已启用，自动批准 {agent_name} 的 {stage}报告")
            # 延迟1秒后自动批准，让用户看到报告
            self.after(1000, self._auto_approve_task)
        
        # 返回一个占位决策，实际决策将通过按钮点击提交
        return {"status": "pending", "feedback": ""}
    
    def _approve_task(self):
        """批准任务"""
        try:
            # 获取当前任务ID
            task_id = self.current_task_id
            if not task_id:
                messagebox.showwarning("警告", "没有正在等待决策的任务")
                return
                
            # 创建决策对象
            decision = {
                "task_id": task_id,
                "status": "approved",
                "feedback": ""
            }
            
            # 提交决策
            if self.workflow_integration:
                try:
                    result = self.workflow_integration.submit_decision(decision)
                    
                    # 无论结果如何，都执行以下操作
                    # 禁用决策控件
                    self._set_decision_controls_state(tk.DISABLED)
                    
                    # 清空建议输入框
                    self.suggestion_entry.delete("1.0", tk.END)
                    
                    # 添加到历史记录
                    history_entry = f"用户批准了 {self.current_agent} 的 {self.current_stage}报告"
                    self._add_to_history(history_entry)
                    
                    # 记录日志
                    logger.info(f"用户批准了任务 {task_id}")
                    
                    # 如果提交失败，记录日志但不显示警告
                    if not result:
                        logger.warning(f"提交决策可能失败，但程序将继续执行: {task_id}")
                except Exception as e:
                    # 只有在发生异常时才显示警告
                    logger.error(f"提交决策时发生异常: {str(e)}")
                    messagebox.showwarning("警告", "提交决策时发生错误，请检查日志获取详细信息")
            else:
                messagebox.showerror("错误", "工作流集成未初始化")
                
        except Exception as e:
            logger.error(f"批准任务时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            messagebox.showerror("错误", f"批准任务时出错: {str(e)}")
    
    def _reject_task(self):
        """拒绝任务"""
        try:
            # 获取当前任务ID
            task_id = self.current_task_id
            if not task_id:
                messagebox.showwarning("警告", "没有正在等待决策的任务")
                return
                
            # 获取拒绝原因
            reason = self.suggestion_entry.get("1.0", tk.END).strip()
            if not reason:
                messagebox.showwarning("警告", "拒绝任务时必须提供原因")
                return
                
            # 创建决策对象
            decision = {
                "task_id": task_id,
                "status": "rejected",
                "feedback": reason
            }
            
            # 提交决策
            if self.workflow_integration:
                try:
                    result = self.workflow_integration.submit_decision(decision)
                    
                    # 无论结果如何，都执行以下操作
                    # 禁用决策控件
                    self._set_decision_controls_state(tk.DISABLED)
                    
                    # 清空建议输入框
                    self.suggestion_entry.delete("1.0", tk.END)
                    
                    # 添加到历史记录
                    history_entry = f"用户拒绝了 {self.current_agent} 的 {self.current_stage}报告，原因: {reason}"
                    self._add_to_history(history_entry)
                    
                    # 记录日志
                    logger.info(f"用户拒绝了任务 {task_id}，原因: {reason}")
                    
                    # 如果提交失败，记录日志但不显示警告
                    if not result:
                        logger.warning(f"提交决策可能失败，但程序将继续执行: {task_id}")
                except Exception as e:
                    # 只有在发生异常时才显示警告
                    logger.error(f"提交决策时发生异常: {str(e)}")
                    messagebox.showwarning("警告", "提交决策时发生错误，请检查日志获取详细信息")
            else:
                messagebox.showerror("错误", "工作流集成未初始化")
                
        except Exception as e:
            logger.error(f"拒绝任务时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            messagebox.showerror("错误", f"拒绝任务时出错: {str(e)}")
            
    def _provide_feedback(self):
        """提供建议反馈"""
        try:
            # 获取建议文本
            feedback = self.suggestion_entry.get("1.0", tk.END).strip()
            if not feedback:
                messagebox.showwarning("警告", "请输入建议内容")
                return
                
            # 获取当前任务ID
            task_id = self.current_task_id
            if not task_id:
                messagebox.showwarning("警告", "没有正在等待决策的任务")
                return
                
            # 创建决策对象
            decision = {
                "task_id": task_id,
                "status": "feedback",
                "feedback": feedback
            }
            
            # 提交决策
            if self.workflow_integration:
                try:
                    # 暂时禁用决策控件，防止重复提交
                    self._set_decision_controls_state(tk.DISABLED)
                    
                    # 添加到历史记录
                    history_entry = f"用户对 {self.current_agent} 的 {self.current_stage}报告提供了建议: {feedback}"
                    self._add_to_history(history_entry)
                    self._add_to_history("正在处理建议，请等待更新后的报告...")
                    
                    # 清空建议输入框
                    self.suggestion_entry.delete("1.0", tk.END)
                    
                    # 提交决策
                    result = self.workflow_integration.submit_decision(decision)
                    
                    if result:
                        # 记录日志
                        logger.info(f"用户对任务 {task_id} 提供了建议: {feedback}")
                        
                        # 延迟重新启用决策控件，给处理时间
                        self.after(3000, lambda: self._set_decision_controls_state(tk.NORMAL))
                        
                        # 显示处理成功消息
                        self._add_to_history("建议已提交，正在生成更新后的报告...")
                    else:
                        logger.warning(f"建议提交失败: {task_id}")
                        self._add_to_history("建议提交失败，请重试")
                        # 立即重新启用决策控件
                        self._set_decision_controls_state(tk.NORMAL)
                        
                except Exception as e:
                    # 只有在发生异常时才显示警告
                    logger.error(f"提交建议时发生异常: {str(e)}")
                    self._add_to_history(f"建议提交失败: {str(e)}")
                    messagebox.showwarning("警告", "提交建议时发生错误，请检查日志获取详细信息")
                    # 重新启用决策控件
                    self._set_decision_controls_state(tk.NORMAL)
            else:
                messagebox.showerror("错误", "工作流集成未初始化")
                
        except Exception as e:
            logger.error(f"提供建议时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            messagebox.showerror("错误", f"提供建议时出错: {str(e)}")
            # 重新启用决策控件
            self._set_decision_controls_state(tk.NORMAL)
    
    def _toggle_auto_approve(self):
        """切换自动批准模式"""
        self.auto_approve_enabled = not self.auto_approve_enabled
        
        # 更新按钮文本和样式
        if self.auto_approve_enabled:
            self.auto_approve_button.config(
                text="🔴 关闭自动批准",
                style="TButton"
            )
            self._add_to_history("已启用自动批准模式")
            messagebox.showinfo("自动批准", "自动批准模式已启用\n\n系统将自动批准所有决策请求，无需手动干预。")
        else:
            self.auto_approve_button.config(
                text="🤖 自动批准",
                style="Accent.TButton"
            )
            self._add_to_history("已关闭自动批准模式")
            messagebox.showinfo("自动批准", "自动批准模式已关闭\n\n系统将恢复手动决策模式。")
    
    def _auto_approve_task(self):
        """自动批准当前任务"""
        if not self.auto_approve_enabled or not self.current_task_id:
            return
            
        try:
            # 创建自动批准决策
            decision = {
                "task_id": self.current_task_id,
                "status": "approved",
                "feedback": "[自动批准] 系统自动批准此任务"
            }
            
            # 提交决策
            if self.workflow_integration:
                try:
                    result = self.workflow_integration.submit_decision(decision)
                    
                    # 禁用决策控件
                    self._set_decision_controls_state(tk.DISABLED)
                    
                    # 清空建议输入框
                    self.suggestion_entry.delete("1.0", tk.END)
                    
                    # 添加到历史记录
                    history_entry = f"系统自动批准了 {self.current_agent} 的 {self.current_stage}报告"
                    self._add_to_history(history_entry)
                    
                    # 记录日志
                    logger.info(f"系统自动批准了任务 {self.current_task_id}")
                    
                    if not result:
                        logger.warning(f"自动批准决策可能失败，但程序将继续执行: {self.current_task_id}")
                        
                except Exception as e:
                    logger.error(f"自动批准决策时发生异常: {str(e)}")
                    self._add_to_history(f"自动批准失败: {str(e)}")
            else:
                logger.error("工作流集成未初始化，无法自动批准")
                self._add_to_history("自动批准失败: 工作流集成未初始化")
                
        except Exception as e:
            logger.error(f"自动批准任务时出错: {str(e)}")
            self._add_to_history(f"自动批准失败: {str(e)}")
    
    def _add_to_history(self, entry):
        """添加条目到历史记录"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_entry = f"[{timestamp}] {entry}"
        
        self.history_content.config(state=tk.NORMAL)
        self.history_content.insert(tk.END, formatted_entry + "\n")
        self.history_content.see(tk.END)
        self.history_content.config(state=tk.DISABLED)
        
    def _show_button_tooltip(self, event, button):
        """显示按钮提示
        
        参数:
            event: 事件对象
            button: 按钮对象
        """
        try:
            # 取消之前的延迟任务（如果有）
            if hasattr(button, 'tooltip_after_id') and button.tooltip_after_id:
                self.after_cancel(button.tooltip_after_id)
                button.tooltip_after_id = None
            
            # 创建新的延迟任务
            if hasattr(button, 'tooltip_text') and button.tooltip_text:
                # 使用after方法延迟显示提示
                button.tooltip_after_id = self.after(500, lambda: self._display_tooltip(button))
        except Exception as e:
            logger.error(f"显示按钮提示时出错: {str(e)}")
    
    def _hide_button_tooltip(self, event, button):
        """隐藏按钮提示
        
        参数:
            event: 事件对象
            button: 按钮对象
        """
        try:
            # 取消延迟任务
            if hasattr(button, 'tooltip_after_id') and button.tooltip_after_id:
                self.after_cancel(button.tooltip_after_id)
                button.tooltip_after_id = None
        except Exception as e:
            logger.error(f"隐藏按钮提示时出错: {str(e)}")
    
    def _display_tooltip(self, button):
        """显示提示对话框
        
        参数:
            button: 按钮对象
        """
        try:
            # 检查按钮是否仍然存在
            if button.winfo_exists() and hasattr(button, 'tooltip_text'):
                from tkinter import messagebox
                messagebox.showinfo("选项说明", button.tooltip_text)
        except Exception as e:
            logger.error(f"显示提示对话框时出错: {str(e)}")
    
    def _monitor_decisions(self):
        """监听决策请求"""
        while self.running:
            try:
                # 检查是否有新的决策请求
                if (self.workflow_integration and 
                    hasattr(self.workflow_integration, 'current_workflow') and 
                    self.workflow_integration.current_workflow):
                    
                    # 检查组件是否仍然存在
                    try:
                        if self.winfo_exists():
                            # 检查流程步骤树视图是否仍然存在
                            if hasattr(self, 'flow_steps') and self.flow_steps.winfo_exists():
                                # 更新流程步骤
                                self._update_flow_steps()
                    except tk.TclError:
                        # 应用程序已被销毁，停止监听
                        self.running = False
                        break
                        
            except Exception as e:
                print(f"监听决策失败: {str(e)}")
            
            time.sleep(0.5)
    
    def _update_flow_steps(self):
        """更新流程步骤显示"""
        # 获取当前工作流的所有模块
        if not self.workflow_integration or not hasattr(self.workflow_integration, 'current_workflow') or not self.workflow_integration.current_workflow:
            return
        
        try:
            # 使用safe_ui_call确保在主线程中更新UI
            from gui.gui_tools import safe_ui_call
            
            def _do_update():
                # 清空现有项目
                for item in self.flow_steps.get_children():
                    self.flow_steps.delete(item)
                    
                # 获取当前工作流
                workflow_name = self.workflow_integration.current_workflow
                
                # 获取工作流配置
                workflow = self.workflow_integration.workflow_engine.workflows.get(workflow_name)
                if not workflow:
                    return
                    
                # 处理不同的工作流格式
                if isinstance(workflow, list):
                    modules = workflow
                elif isinstance(workflow, dict) and "modules" in workflow:
                    modules = workflow.get("modules", [])
                else:
                    return
                    
                # 添加模块到树形视图
                for i, module in enumerate(modules):
                    module_name = module.get("name", f"模块 {i+1}")
                    agent_name = module.get("agent", "未知代理")
                    department = module.get("department", "未知部门")
                    
                    # 获取任务状态
                    status = "等待中"
                    if self.workflow_integration.task_manager.current_task:
                        if self.workflow_integration.task_manager.current_task.name == module_name:
                            status = "执行中"
                    
                    # 添加到树形视图，包含部门、角色和状态信息
                    self.flow_steps.insert("", "end", text=module_name, values=(department, agent_name, status))
            
            # 使用safe_ui_call确保在主线程中执行
            safe_ui_call(_do_update)
        except Exception as e:
            import traceback
            logger.error(f"更新流程步骤时出错: {str(e)}")
            logger.error(traceback.format_exc())

    def _update_report_display(self, content, is_pre_execution=False):
        """更新报告显示"""
        report_type = "执行前" if is_pre_execution else "执行后"
        
        try:
            # 清空报告区域
            self.report_content.config(state=tk.NORMAL)
            self.report_content.delete("1.0", tk.END)
            
            # 设置报告标题
            self.report_title.config(text=f"【{report_type}报告】")
            
            # 插入报告内容
            self.report_content.insert(tk.END, content)
            
            # 滚动到顶部
            self.report_content.see("1.0")
            self.report_content.config(state=tk.DISABLED)
            
            # 保存当前报告内容
            self.current_report = content
            
            # 更新UI
            self._update_flow_steps()
            
            # 确保界面更新
            self.update()
            
            # 添加到历史记录
            self._add_to_history(f"收到{report_type}报告")
            
            # 检查是否包含建议处理后的内容
            if "决策者反馈" in content or "用户建议" in content:
                self._add_to_history("报告已根据建议更新")
                
        except Exception as e:
            logger.error(f"更新报告显示时出错: {str(e)}")
            logger.error(traceback.format_exc())

    def _populate_workflow_combo(self):
        """填充工作流下拉框"""
        try:
            if not self.workflow_integration or not self.workflow_integration.workflow_engine:
                logger.warning("工作流引擎未初始化，无法加载工作流列表")
                return
                
            # 获取工作流列表
            workflows = self.workflow_integration.workflow_engine.workflows
            
            if not workflows:
                logger.warning("没有可用的工作流")
                return
                
            # 清空下拉框
            self.workflow_combo['values'] = []
            
            # 添加工作流到下拉框
            workflow_names = list(workflows.keys())
            self.workflow_combo['values'] = workflow_names
            
            # 默认选择第一个
            if workflow_names:
                self.workflow_combo.current(0)
                
        except Exception as e:
            logger.error(f"填充工作流下拉框时出错: {str(e)}")
            logger.error(traceback.format_exc())

    def _load_workflow_list(self):
        """加载工作流列表"""
        self._populate_workflow_combo()

    def on_show(self):
        """显示此界面时的回调"""
        # 启动决策监听线程
        self.running = True
        self.decision_thread = threading.Thread(target=self._monitor_decisions)
        self.decision_thread.daemon = True
        self.decision_thread.start()
        
        # 填充工作流下拉框
        try:
            self._populate_workflow_combo()
        except Exception as e:
            logger.error(f"填充工作流下拉框时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def on_hide(self):
        """隐藏此界面时的回调"""
        # 停止决策监听线程
        self.running = False
        if self.decision_thread:
            self.decision_thread.join(timeout=1)
            self.decision_thread = None

    def _on_feedback_submit(self):
        """提交反馈"""
        if not self.current_task_id:
            messagebox.showwarning("警告", "当前没有等待反馈的任务")
            return
            
        feedback = self.feedback_text.get("1.0", tk.END).strip()
        if not feedback:
            messagebox.showwarning("警告", "请输入反馈内容")
            return
            
        self.logger.info(f"提交反馈: {feedback}")
        
        # 创建决策数据
        decision = {
            "task_id": self.current_task_id,
            "status": "feedback",  # 使用feedback状态表示这是一个建议
            "feedback": feedback
        }
        
        # 提交决策
        try:
            result = self.workflow_integration.submit_decision(decision)
            if result:
                self.logger.info("反馈提交成功")
                self._add_to_history(f"提交了反馈: {feedback[:50]}...")
                
                # 清空反馈文本框
                self.feedback_text.delete("1.0", tk.END)
                
                # 更新报告显示（如果有新报告）
                if hasattr(self, "current_report") and self.current_report:
                    self._update_report_display(self.current_report, 
                                               self.current_stage == "执行前")
            else:
                self.logger.error("反馈提交失败")
                messagebox.showerror("错误", "反馈提交失败")
        except Exception as e:
            self.logger.error(f"提交反馈时出错: {str(e)}")
            messagebox.showerror("错误", f"提交反馈时出错: {str(e)}")