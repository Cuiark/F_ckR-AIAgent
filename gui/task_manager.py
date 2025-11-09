#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading
import queue
import logging
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from datetime import datetime  # 添加缺失的datetime导入

# 设置日志记录器
logger = logging.getLogger("task_manager")

# 任务状态枚举
class TaskStatus(Enum):
    PENDING = "等待中"
    RUNNING = "执行中"
    WAITING_APPROVAL = "等待审批"
    APPROVED = "已批准"
    REJECTED = "已拒绝"
    COMPLETED = "已完成"
    FAILED = "执行失败"
    CANCELLED = "已取消"

class Task:
    """任务类，表示一个需要执行的任务"""
    
    def __init__(self, task_id: str, name: str, description: str, 
                 agent_name: str, expected_output: str, group_id: str = 'default_group'):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.agent_name = agent_name
        self.expected_output = expected_output
        self.group_id = group_id  # 添加角色组ID
        self.current_step = 'initialization'  # 添加当前工作流步骤
        self.status = TaskStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None
        self.approval_data = None
        self.logs = []
        self.approval_event = threading.Event()  # 添加审批事件
        self.approval_result = None  # 添加审批结果
        self.approval_data = {}  # 添加审批数据
        self.add_log(f"任务等待审批")
        self.approval_event.clear()   # 新增：清除事件
        self.approval_result = None   # 新增：清空结果
        
    def start(self):
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.start_time = time.time()
        self.add_log(f"任务开始执行")
        
    def complete(self, result: Any):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.end_time = time.time()
        self.result = result
        self.add_log(f"任务执行完成")
        
    def fail(self, error: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.end_time = time.time()
        self.error = error
        self.add_log(f"任务执行失败: {error}")
        
    def cancel(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.end_time = time.time()
        self.add_log(f"任务被取消")
        
    def wait_approval(self, approval_data: Any):
        self.status = TaskStatus.WAITING_APPROVAL
        self.approval_data = approval_data
        self.add_log(f"任务等待审批")
        self.approval_event.clear()   # 新增：清除事件
        self.approval_result = None   # 新增：清空结果
        
    def approve(self):
        """批准任务"""
        self.status = TaskStatus.APPROVED
        self.add_log("任务已批准")
        self.approval_result = "approved"
        self.approval_event.set()  # 新增：唤醒等待
    
    def reject(self):
        """拒绝任务"""
        self.status = TaskStatus.REJECTED
        self.add_log("任务已拒绝")
        self.approval_result = "rejected"
        self.approval_event.set()  # 新增：唤醒等待
        
    def add_log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        
    def get_duration(self) -> float:
        """获取任务持续时间（秒）"""
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "agent_name": self.agent_name,
            "expected_output": self.expected_output,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.get_duration(),
            "result": self.result,
            "error": self.error,
            "logs": self.logs
        }

class TaskManager:
    """任务管理器，负责管理和执行任务"""
    
    def __init__(self):
        """初始化任务管理器"""
        self.tasks = {}
        self.task_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.current_task = None
        self.task_lock = threading.RLock()  # 使用可重入锁
        self.queue_lock = threading.Lock()
        self.decision_queue = queue.Queue()
        
        # 回调函数
        self.on_task_created = None
        self.on_task_started = None
        self.on_task_completed = None
        self.on_task_failed = None
        self.on_task_cancelled = None
        self.on_task_waiting_approval = None
        self.on_task_approved = None
        self.on_task_rejected = None
        self.on_all_tasks_completed = None
        
        # 启动任务处理线程
        self.start_processing()
    
    def set_callbacks(self, **callbacks):
        """设置回调函数"""
        for name, callback in callbacks.items():
            if hasattr(self, name) and callable(callback):
                setattr(self, name, callback)
                
    def create_task(self, name: str, description: str, agent_name: str, 
                   expected_output: str, group_id: str = 'default_group') -> str:
        """创建任务"""
        task_id = f"task_{int(time.time())}_{len(self.tasks)}"
        
        with self.task_lock:
            task = Task(
                task_id=task_id,
                name=name,
                description=description,
                agent_name=agent_name,
                expected_output=expected_output,
                group_id=group_id
            )
            self.tasks[task_id] = task
            
            # 触发回调
            if self.on_task_created:
                self.on_task_created(task)
                
        return task_id
        
    def add_task_to_queue(self, task_id: str):
        """将任务添加到队列"""
        if task_id in self.tasks:
            self.task_queue.put(task_id)
            
    def start_processing(self):
        """开始处理任务队列"""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_tasks)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
    def stop_processing(self):
        """停止处理任务队列"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1)
            
    def _process_tasks(self):
        """处理任务队列的工作线程"""
        while self.running:
            try:
                if not self.task_queue.empty():
                    with self.queue_lock:
                        task_id = self.task_queue.get(block=False)
                    
                    with self.task_lock:
                        task = self.tasks.get(task_id)
                        
                        if task:
                            # 只负责开始任务
                            if task.status == TaskStatus.PENDING:
                                task.start()
                                self.current_task = task
                                if self.on_task_started:
                                    self.on_task_started(task)
                                
                                # 记录日志
                                logger.info(f"开始执行任务: {task.name}")
                        else:
                            # 队列为空时短暂休眠
                            time.sleep(0.1)
                            
            except queue.Empty:
                        # 队列为空时短暂休眠
                        time.sleep(0.1)
            except Exception as e:
                    logger.error(f"处理任务时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    time.sleep(0.5)  # 出错时稍长休眠
    
    # 添加以下方法到TaskManager类
    
    # 修改任务审批逻辑，确保正确处理审批事件
    
    def wait_for_approval(self, task_id, approval_data):
        """等待任务审批"""
        with self.task_lock:
            if task_id not in self.tasks:
                logger.error(f"找不到任务: {task_id}")
                return None
            
            task = self.tasks[task_id]
            task.status = TaskStatus.WAITING_APPROVAL
            task.approval_data = approval_data
            task.add_log(f"任务等待审批: {approval_data.get('agent_name')} - {approval_data.get('stage')}")
            
            # 重置审批事件
            task.approval_event.clear()
            task.approval_result = None
            
            # 触发任务等待审批回调
            if self.on_task_waiting_approval:
                self.on_task_waiting_approval(task)
            
            # 设置当前任务
            self.current_task = task
            
            # 记录日志
            logger.info(f"任务 {task_id} 等待审批")
            
            return task

    def approve_task(self, task_id, feedback=""):
        """批准任务"""
        with self.task_lock:
            if task_id not in self.tasks:
                logger.error(f"找不到任务: {task_id}")
                return False
            
            task = self.tasks[task_id]
            if task.status != TaskStatus.WAITING_APPROVAL:
                logger.warning(f"任务 {task_id} 不在等待审批状态，当前状态: {task.status}")
                return False
            
            # 更新任务状态
            task.status = TaskStatus.APPROVED
            task.feedback = feedback
            task.approved_at = datetime.now()
            
            # 更新审批数据
            if not hasattr(task, 'approval_data'):
                task.approval_data = {}
            task.approval_data["feedback"] = feedback
            task.approval_result = "approved"
            
            # 设置审批事件
            task.approval_event.set()
            
            # 调用回调
            if self.on_task_approved:
                self.on_task_approved(task)
            
            logger.info(f"任务 {task_id} 已批准")
            
    def reject_task(self, task_id, feedback=""):
        """拒绝任务"""
        with self.task_lock:
            if task_id not in self.tasks:
                logger.error(f"找不到任务: {task_id}")
                return False
            
            task = self.tasks[task_id]
            if task.status != TaskStatus.WAITING_APPROVAL:
                logger.warning(f"任务 {task_id} 不在等待审批状态，当前状态: {task.status}")
                return False
            
            # 更新任务状态
            task.status = TaskStatus.REJECTED
            task.feedback = feedback
            task.rejected_at = datetime.now()
            
            # 更新审批数据
            if not hasattr(task, 'approval_data'):
                task.approval_data = {}
            task.approval_data["feedback"] = feedback
            task.approval_result = "rejected"
            
            # 设置审批事件
            task.approval_event.set()
            
            # 调用回调
            if self.on_task_rejected:
                self.on_task_rejected(task)
            
            logger.info(f"任务 {task_id} 已拒绝")
            return True
            # 将决策放入队列
            self.decision_queue.put(("reject", task_id))
            
    def cancel_task(self, task_id: str):
        """取消任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.cancel()
            if self.on_task_cancelled:
                self.on_task_cancelled(task)
                
    def get_task(self, task_id: str):
        """根据任务ID获取任务对象"""
        return self.tasks.get(task_id)
        
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())
        
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """获取指定状态的任务"""
        return [task for task in self.tasks.values() if task.status == status]
        
    def get_decision(self, timeout: float = None) -> tuple:
        """获取决策"""
        try:
            return self.decision_queue.get(timeout=timeout)
        except queue.Empty:
            return None
            
    def clear_all_tasks(self):
        """清除所有任务"""
        self.tasks.clear()
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except queue.Empty:
                break

    def peek_next_task_id(self):
        """安全获取队首任务ID，不移除"""
        if not self.task_queue.empty():
            return self.task_queue.queue[0]
        return None
        
    def start_task(self, task_id):
        """开始执行指定任务
        
        参数:
            task_id: 任务ID
        """
        task = self.tasks.get(task_id)
        if not task:
            logging.warning(f"任务不存在: {task_id}")
            return False
            
        # 设置当前任务
        self.current_task = task
        
        # 更新任务状态
        task.start()
        
        # 触发回调
        if self.on_task_started:
            self.on_task_started(task)
            
        return True

    def complete_task(self, task_id, result=None):
        """完成指定任务
        
        参数:
            task_id: 任务ID
            result: 任务结果
        """
        task = self.tasks.get(task_id)
        if not task:
            logging.warning(f"任务不存在: {task_id}")
            return False
            
        # 更新任务状态
        task.complete(result or {})
        
        # 触发回调
        if self.on_task_completed:
            self.on_task_completed(task)
            
        return True

    def update_task_status(self, task_id, status):
        """更新任务状态并触发UI刷新
        
        参数:
            task_id: 任务ID
            status: 新状态
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
            
        task.status = status
        
        # 根据状态触发相应回调
        if status == TaskStatus.RUNNING and self.on_task_started:
            self.on_task_started(task)
        elif status == TaskStatus.COMPLETED and self.on_task_completed:
            self.on_task_completed(task)
        elif status == TaskStatus.FAILED and self.on_task_failed:
            self.on_task_failed(task)
        elif status == TaskStatus.CANCELLED and self.on_task_cancelled:
            self.on_task_cancelled(task)
        elif status == TaskStatus.WAITING_APPROVAL and self.on_task_waiting_approval:
            self.on_task_waiting_approval(task)
            
        return True

    def _update_ui(self):
        """强制更新UI"""
        # 这里可以添加直接更新UI的代码
        # 例如，如果使用tkinter，可以调用update()方法
        try:
            import tkinter as tk
            for widget in tk._default_root.winfo_children():
                if hasattr(widget, 'update_task_display'):
                    widget.update_task_display()
        except:
            pass  # 如果更新失败，静默处理
    
    def complete_all_tasks(self):
        """将所有未完成的任务标记为已完成"""
        logger.info("标记所有未完成任务为已完成")
        
        with self.task_lock:
            for task_id, task in self.tasks.items():
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    logger.info(f"自动完成任务: {task.name}")
                    task.complete({"status": "auto_completed", "message": "工作流结束时自动完成"})
                    if self.on_task_completed:
                        self.on_task_completed(task)
        
        # 触发所有任务完成回调
        if self.on_all_tasks_completed:
            self.on_all_tasks_completed()
    
    def fail_task(self, task_id, error_message):
        """将任务标记为失败"""
        logger.info(f"标记任务失败: {task_id}, 错误: {error_message}")
        
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.fail(error_message)
            if self.on_task_failed:
                self.on_task_failed(task)
            return True
        return False