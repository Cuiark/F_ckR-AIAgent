#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI工具模块 - 连接前端界面与后端功能
此模块提供了前端界面调用后端功能的接口
"""

import sys
import os
import json
import threading
import time
import io

# 确保能够导入后端模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入后端功能
from config import logger
from tools.security_tools import (
    get_process_details,
    get_windows_logs,
    get_services,
    load_baseline_processes,
    terminate_process,
    block_ip
)

# 添加通用的线程安全UI调用函数
def safe_ui_call(func, *args, **kwargs):
    """安全地在主线程中调用UI函数"""
    try:
        import tkinter as tk
        
        # 检查是否在主线程中
        if threading.current_thread().name == 'MainThread':
            # 直接调用函数
            return func(*args, **kwargs)
        else:
            # 在主线程中调用函数
            if tk._default_root:
                return tk._default_root.after(0, func, *args, **kwargs)
            else:
                logger.warning("无法在主线程中调用UI函数：Tkinter根窗口不存在")
                return None
    except Exception as e:
        logger.error(f"安全UI调用失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

class BackendThread(threading.Thread):
    """后台线程类，用于执行耗时的后端操作"""
    
    def __init__(self, callback, func, *args, **kwargs):
        super().__init__()
        self.callback = callback
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.daemon = True  # 设置为守护线程，随主线程退出
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            # 在主线程中执行回调
            if self.callback:
                self.callback(result)
        except Exception as e:
            logger.error(f"后台线程执行出错: {str(e)}")
            if self.callback:
                self.callback(f"错误: {str(e)}")

class OutputRedirector:
    """简化的输出重定向类"""
    
    def __init__(self, main_callback, tool_callback):
        """初始化输出重定向器"""
        self.main_callback = main_callback
        self.tool_callback = tool_callback
        
        # 保存原始的标准输出和标准错误
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def start_redirect(self):
        """开始重定向输出"""
        # 创建自定义的输出流
        sys.stdout = self
        sys.stderr = self
    
    def stop_redirect(self):
        """停止重定向输出"""
        # 恢复原始的输出流
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def write(self, text):
        """写入文本"""
        # 写入到原始输出
        self.original_stdout.write(text)
        
        # 发送到UI回调
        if self.main_callback:
            safe_ui_call(self.main_callback, text)
    
    def flush(self):
        """刷新缓冲区"""
        self.original_stdout.flush()

# 增加全局任务锁，防止多轮任务重叠
task_running_lock = threading.Lock()

class GUITools:
    """GUI工具类，提供前端调用后端功能的方法"""
    
    @staticmethod
    def get_processes(callback):
        """获取进程信息"""
        thread = BackendThread(callback, get_process_details)
        thread.start()
    
    @staticmethod
    def get_logs(callback):
        """获取系统日志"""
        thread = BackendThread(callback, get_windows_logs)
        thread.start()
    
    @staticmethod
    def get_services(callback):
        """获取系统服务"""
        thread = BackendThread(callback, get_services)
        thread.start()
    
    @staticmethod
    def terminate_process(pid, callback):
        """终止进程"""
        thread = BackendThread(callback, terminate_process, pid)
        thread.start()
    
    @staticmethod
    def block_ip(ip, callback):
        """阻止IP地址"""
        thread = BackendThread(callback, block_ip, ip)
        thread.start()
    
    @staticmethod
    def run_security_task(group_name, main_callback, tool_callback, log_callback, role_callback, completion_callback, decision_callback=None):
        """运行安全任务"""
        def task_thread():
            # 尝试获取锁，防止多轮任务重叠
            acquired = task_running_lock.acquire(blocking=False)
            if not acquired:
                safe_ui_call(main_callback, "已有任务正在运行，请勿重复启动。\n")
                return
            try:
                # 设置简化的输出重定向
                redirector = OutputRedirector(
                    lambda text: safe_ui_call(main_callback, text),
                    lambda text: safe_ui_call(tool_callback, text)
                )
                redirector.start_redirect()
                
                # 添加日志处理器
                import logging
                class GUILogHandler(logging.Handler):
                    def emit(self, record):
                        log_entry = self.format(record)
                        if log_callback:
                            safe_ui_call(log_callback, log_entry + '\n')
                
                log_handler = GUILogHandler()
                log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                logger.addHandler(log_handler)
                
                # 设置回调函数
                global main_callback_func, tool_callback_func, log_callback_func, decision_callback_func
                main_callback_func = main_callback
                tool_callback_func = tool_callback
                log_callback_func = log_callback
                decision_callback_func = decision_callback
                
                # 运行安全任务
                try:
                    # 设置工具输出回调 - 使用与命令行版本相同的方式
                    from tools.security_tools import set_tool_output_callback
                    set_tool_output_callback(None)  # 不设置特殊回调，使用标准输出
                    
                    # 创建语言模型
                    from models import setup_llm
                    llm = setup_llm(for_crewai=True)
                    
                    # 创建agents
                    from agents.security_agents import create_agents
                    agents = create_agents(llm, group_name)
                    
                    # 更新角色信息
                    if role_callback:
                        roles = []
                        for agent_key, agent in agents.items():
                            roles.append({
                                "key": agent_key,
                                "name": agent.role,
                                "goal": agent.goal,
                                "backstory": agent.backstory
                            })
                        safe_ui_call(role_callback, roles)
                    
                    # 创建任务
                    from agents.tasks import create_tasks
                    tasks = create_tasks(agents)
                    
                    # 创建安全分析团队
                    from agents.crew import create_security_crew
                    crew = create_security_crew(agents, tasks)
                    
                    # 运行团队
                    result = crew.kickoff()
                    
                    # 任务完成回调
                    if completion_callback:
                        safe_ui_call(completion_callback, result)
                    
                except Exception as e:
                    logger.error(f"运行安全任务时出错: {str(e)}")
                    logger.error(traceback.format_exc())
                    safe_ui_call(main_callback, f"运行安全任务时出错: {str(e)}\n")
                    
                finally:
                    # 移除日志处理器
                    logger.removeHandler(log_handler)
                    
                    # 停止重定向
                    redirector.stop_redirect()
                    
                    # 释放锁
                    task_running_lock.release()
                    
            except Exception as e:
                logger.error(f"任务线程出错: {str(e)}")
                logger.error(traceback.format_exc())
                if acquired:
                    task_running_lock.release()
        
        # 创建并启动线程
        thread = threading.Thread(target=task_thread)
        thread.daemon = True
        thread.start()

def enable_decision_controls():
    """启用决策控件"""
    try:
        # 获取当前应用程序实例
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer, QThread
        
        app = QApplication.instance()
        if not app:
            print("WARNING: 没有找到QApplication实例")
            return False
        
        # 检查是否在主线程中
        if app.thread() != QThread.currentThread():
            print("WARNING: enable_decision_controls被从非主线程调用")
            # 在主线程中执行此函数
            QTimer.singleShot(0, enable_decision_controls)
            return False
        
        # 遍历所有顶层窗口，查找TaskExecutionScreen
        for widget in app.topLevelWidgets():
            # 尝试查找execution_screen
            execution_screen = None
            
            # 方法1: 直接查找TaskExecutionScreen类型的窗口
            if widget.__class__.__name__ == 'TaskExecutionScreen':
                execution_screen = widget
                print("DEBUG: 直接找到TaskExecutionScreen")
            
            # 方法2: 从MainWindow查找
            elif hasattr(widget, 'execution_screen'):
                execution_screen = widget.execution_screen
                print("DEBUG: 从MainWindow找到execution_screen")
            
            # 方法3: 从main_screen查找
            elif hasattr(widget, 'main_screen') and hasattr(widget.main_screen, 'execution_screen'):
                execution_screen = widget.main_screen.execution_screen
                print("DEBUG: 从main_screen找到execution_screen")
            
            # 方法4: 从centralWidget查找
            elif hasattr(widget, 'centralWidget'):
                central = widget.centralWidget()
                if hasattr(central, 'currentWidget'):
                    current = central.currentWidget()
                    if hasattr(current, 'execution_screen'):
                        execution_screen = current.execution_screen
                        print("DEBUG: 从centralWidget找到execution_screen")
            
            # 如果找到了execution_screen，启用决策控件
            if execution_screen:
                if hasattr(execution_screen, 'force_enable_decision_controls'):
                    # 直接在主线程中执行
                    execution_screen.force_enable_decision_controls()
                    print("DEBUG: 已启用决策控件")
                    return True
        
        print("WARNING: 没有找到execution_screen")
        return False
    except Exception as e:
        import traceback
        print(f"ERROR: 启用决策控件时出错: {str(e)}")
        print(traceback.format_exc())


# 修改 ask_for_next_round 函数，添加详细调试
def ask_for_next_round():
    """询问用户是否进行下一轮任务"""
    try:
        debug_thread_info("ask_for_next_round 开始")
        
        # 获取当前应用程序实例
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import QTimer, QThread
        import traceback
        
        app = QApplication.instance()
        if not app:
            print("ERROR: 没有找到QApplication实例")
            return False
        
        # 检查是否在主线程中
        is_main_thread = (QThread.currentThread() == app.thread())
        print(f"DEBUG: ask_for_next_round - 是否在主线程: {is_main_thread}")
        
        if not is_main_thread:
            print("WARNING: ask_for_next_round 在非主线程中调用，尝试转到主线程")
            # 使用更安全的方式在主线程中执行
            result_container = [False]
            
            def run_in_main_thread():
                try:
                    debug_thread_info("run_in_main_thread 内部")
                    # 直接在主线程中创建并显示对话框
                    result = QMessageBox.question(
                        None, 
                        "任务完成", 
                        "当前任务已完成，是否安排下一轮任务？\n(将在10分钟后自动开始)",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    print(f"DEBUG: 主线程中对话框结果: {result}")
                    
                    if result == QMessageBox.Yes:
                        # 用户选择继续，设置10分钟后自动开始
                        from main import restart_task_cycle
                        # 设置10分钟后自动开始
                        QTimer.singleShot(10 * 60 * 1000, restart_task_cycle)
                        QMessageBox.information(None, "任务已安排", "系统将在10分钟后自动开始下一轮任务。")
                        result_container[0] = True
                    else:
                        # 用户选择不继续
                        QMessageBox.information(None, "任务结束", "任务已结束，如需再次执行请手动启动。")
                        result_container[0] = False
                except Exception as e:
                    print(f"ERROR: 主线程执行ask_for_next_round时出错: {str(e)}")
                    print(traceback.format_exc())
                
            # 在主线程中执行
            QTimer.singleShot(0, run_in_main_thread)
            
            # 等待一段时间，确保主线程有机会执行
            print("DEBUG: 等待主线程执行完成")
            import time
            time.sleep(1.0)  # 增加等待时间
            print(f"DEBUG: 等待结束，结果={result_container[0]}")
            return result_container[0]
        
        # 以下代码确保在主线程中执行
        print("DEBUG: 直接在主线程中执行ask_for_next_round")
        
        # 使用更简单的消息框实现
        result = QMessageBox.question(
            None, 
            "任务完成", 
            "当前任务已完成，是否安排下一轮任务？\n(将在10分钟后自动开始)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        print(f"DEBUG: 对话框结果: {result}")
        
        if result == QMessageBox.Yes:
            # 用户选择继续，设置10分钟后自动开始
            from main import restart_task_cycle
            # 设置10分钟后自动开始
            QTimer.singleShot(10 * 60 * 1000, restart_task_cycle)
            QMessageBox.information(None, "任务已安排", "系统将在10分钟后自动开始下一轮任务。")
            return True
        else:
            # 用户选择不继续
            QMessageBox.information(None, "任务结束", "任务已结束，如需再次执行请手动启动。")
            return False
            
    except Exception as e:
        import traceback
        print(f"ERROR: 询问下一轮任务时出错: {str(e)}")
        print(traceback.format_exc())
        return False


def restart_task_cycle():
    """重新启动任务循环"""
    print("DEBUG: 准备启动新一轮任务...")
    
    # 获取主窗口实例
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication.instance()
    if not app:
        print("ERROR: 无法获取QApplication实例")
        return
    
    main_window = None
    for widget in app.topLevelWidgets():
        if widget.__class__.__name__ == 'MainWindow':
            main_window = widget
            break
    
    if not main_window:
        print("ERROR: 无法获取主窗口实例")
        return
    
    # 获取主屏幕实例
    if hasattr(main_window, 'main_screen'):
        main_screen = main_window.main_screen
        if main_screen:
            # 在主线程中安全地启动新任务
            safe_ui_call(main_screen.start_new_task)
        else:
            print("ERROR: 无法获取主屏幕实例")
    else:
        print("ERROR: 主窗口没有main_screen属性")

# 在文件顶部添加调试函数
def debug_thread_info(location):
    """打印当前线程信息，用于调试"""
    import threading
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QThread
    
    current_thread = threading.current_thread()
    app = QApplication.instance()
    is_main_thread = False
    if app:
        is_main_thread = (QThread.currentThread() == app.thread())
    
    print(f"DEBUG [{location}]: 线程ID={current_thread.ident}, 名称={current_thread.name}, 是否主线程={is_main_thread}")
    return is_main_thread


# 修改 show_message_box 函数，添加详细调试
def show_message_box(title, message, icon=None, buttons=None, default_button=None):
    """在主线程中显示消息框"""
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import QTimer, QThread, QEventLoop
    import traceback
    
    debug_thread_info(f"show_message_box 开始: {title}")
    
    # 创建一个函数来在主线程中执行
    def _show_dialog():
        debug_thread_info(f"_show_dialog 内部: {title}")
        try:
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            
            # 设置图标
            if icon == "question":
                msg_box.setIcon(QMessageBox.Question)
            elif icon == "information":
                msg_box.setIcon(QMessageBox.Information)
            elif icon == "warning":
                msg_box.setIcon(QMessageBox.Warning)
            elif icon == "critical":
                msg_box.setIcon(QMessageBox.Critical)
                
            # 设置按钮
            if buttons == "yes_no":
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            elif buttons == "ok":
                msg_box.setStandardButtons(QMessageBox.Ok)
            elif buttons == "ok_cancel":
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                
            # 设置默认按钮
            if default_button == "yes":
                msg_box.setDefaultButton(QMessageBox.Yes)
            elif default_button == "no":
                msg_box.setDefaultButton(QMessageBox.No)
            elif default_button == "ok":
                msg_box.setDefaultButton(QMessageBox.Ok)
            elif default_button == "cancel":
                msg_box.setDefaultButton(QMessageBox.Cancel)
                
            print(f"DEBUG: 准备显示对话框: {title}")
            # 显示对话框并返回结果
            result = msg_box.exec_()
            print(f"DEBUG: 对话框已关闭: {title}, 结果={result}")
            return result
        except Exception as e:
            print(f"ERROR: 显示对话框时出错: {str(e)}")
            print(traceback.format_exc())
            return None
    
    # 确保在主线程中执行
    app = QApplication.instance()
    if not app:
        print("ERROR: 没有找到QApplication实例")
        return None
        
    is_main_thread = (QThread.currentThread() == app.thread())
    print(f"DEBUG: 当前是否在主线程: {is_main_thread}")
    
    if not is_main_thread:
        # 在非主线程中，使用QTimer.singleShot
        print(f"DEBUG: 尝试在主线程中显示对话框: {title}")
        try:
            # 使用更简单的方法 - 直接在主线程中执行并等待
            from PyQt5.QtCore import pyqtSignal, QObject
            
            class SignalBridge(QObject):
                result_signal = pyqtSignal(object)
            
            bridge = SignalBridge()
            result = [None]
            
            def on_main_thread():
                try:
                    res = _show_dialog()
                    bridge.result_signal.emit(res)
                except Exception as e:
                    print(f"ERROR: 主线程执行对话框时出错: {str(e)}")
                    print(traceback.format_exc())
                    bridge.result_signal.emit(None)
            
            def on_result(res):
                result[0] = res
                print(f"DEBUG: 收到对话框结果: {res}")
                if hasattr(QThread.currentThread(), '_loop') and QThread.currentThread()._loop:
                    try:
                        QThread.currentThread()._loop.quit()
                    except Exception as e:
                        print(f"ERROR: 退出事件循环时出错: {str(e)}")
            
            bridge.result_signal.connect(on_result)
            QTimer.singleShot(0, on_main_thread)
            
            # 创建事件循环等待结果
            print("DEBUG: 创建事件循环等待结果")
            loop = QThread.currentThread()._loop = QEventLoop()
            loop.exec_()
            print(f"DEBUG: 事件循环结束，结果={result[0]}")
            return result[0]
        except Exception as e:
            print(f"ERROR: 在主线程中显示对话框时出错: {str(e)}")
            print(traceback.format_exc())
            return None
    else:
        # 在主线程中，直接执行
        print(f"DEBUG: 直接在主线程中显示对话框: {title}")
        return _show_dialog()
        
        # 测试API连接
        try:
            test_message = "This is a test message to verify API connection."
            test_response = llm_for_direct.invoke(test_message)
            safe_ui_call(log_callback, f"API连接测试成功: {test_response[:50]}...")
        except Exception as e:
            safe_ui_call(log_callback, f"API连接测试失败: {str(e)}")
            safe_ui_call(main_callback, f"错误: API连接失败，无法继续执行任务。\n详细信息: {str(e)}\n")
            task_running_lock.release()

def gui_get_user_decision(report, stage="执行后", agent_name=None):
    """获取用户对安全报告的决策 - GUI版本"""
    # 更新报告显示
    report_header = f"【{agent_name} - {stage}报告】" if agent_name else "【安全态势报告】"
    formatted_report = f"\n{report_header}\n{'='*80}\n{report}\n{'='*80}\n"
    
    # 通过回调更新报告区域 - 确保报告显示在主界面
    safe_ui_call(main_callback_func, formatted_report)
    safe_ui_call(log_callback_func, f"等待用户对 {agent_name} 的 {stage}报告 进行决策...")
    
    # 创建任务ID
    import time
    task_id = f"task_{int(time.time())}_{agent_name}"
    
    # 记录到日志
    from config import logger
    logger.info(f"任务 {task_id} 等待审批")
    
    # 等待用户决策
    try:
        # 使用决策回调获取决策
        if decision_callback_func:
            # 调用决策回调，传入任务ID
            decision_callback_func(task_id, agent_name, stage)
            
            # 等待决策队列
            from config import DECISION_TIMEOUT
            try:
                from gui.app import get_decision
                decision = get_decision(DECISION_TIMEOUT)
                
                if not decision:
                    logger.warning(f"{agent_name} 的 {stage}决策为None，默认批准")
                    return {"status": "approved", "feedback": "自动批准（决策为None）"}
                
                # 格式化建议内容
                if decision.get("status") == "feedback" and decision.get("feedback"):
                    # 如果建议内容不是以"建议:"开头，则添加前缀
                    feedback = decision.get("feedback", "")
                    if not feedback.startswith("建议:") and not feedback.startswith("建议："):
                        decision["feedback"] = f"建议: {feedback}"
                
                # 记录决策
                status = decision.get("status", "unknown")
                feedback = decision.get("feedback", "")
                logger.info(f"用户{status}了 {agent_name} 的 {stage}报告: {feedback}")
                
                # 显示决策结果
                if status == "approved":
                    safe_ui_call(main_callback_func, f"\n【决策已批准】确认任务完成...\n")
                elif status == "rejected":
                    safe_ui_call(main_callback_func, f"\n【决策已拒绝】原因: {feedback}\n")
                elif status == "feedback":
                    safe_ui_call(main_callback_func, f"\n【决策已反馈】{feedback}\n")
                
                return decision
                
            except Exception as e:
                logger.error(f"获取决策时出错: {str(e)}")
                return {"status": "approved", "feedback": "自动批准（获取决策出错）"}
        else:
            # 使用默认的命令行交互
            from main import get_user_decision
            return get_user_decision(report, stage, agent_name)
            
    except Exception as e:
        logger.error(f"决策处理出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "approved", "feedback": "自动批准（决策处理出错）"}

# 添加缺失的函数
def get_decision_from_queue(timeout=60):
    """从决策队列中获取决策"""
    try:
        from gui.app import decision_queue
        if decision_queue:
            try:
                import queue
                return decision_queue.get(block=True, timeout=timeout)
            except queue.Empty:
                logger.warning(f"决策队列等待超时({timeout}秒)")
                return None
        else:
            logger.error("决策队列未初始化")
            return None
    except Exception as e:
        logger.error(f"从决策队列获取决策时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# 添加缺失的测试API连接函数
def test_api_connection(llm, log_callback=None):
    """测试API连接"""
    try:
        test_message = "This is a test message to verify API connection."
        test_response = llm.invoke(test_message)
        if log_callback:
            safe_ui_call(log_callback, f"API连接测试成功: {test_response[:50]}...")
        return True
    except Exception as e:
        if log_callback:
            safe_ui_call(log_callback, f"API连接测试失败: {str(e)}")
        return False
