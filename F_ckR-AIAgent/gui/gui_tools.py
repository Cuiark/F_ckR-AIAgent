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
    """
    确保函数在主线程中执行的工具函数
    
    参数:
        func: 要执行的函数
        *args, **kwargs: 传递给函数的参数
    """
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QThread, QTimer
    
    app = QApplication.instance()
    if app and QThread.currentThread() == app.thread():
        # 在主线程中，直接调用函数
        return func(*args, **kwargs)
    else:
        # 在非主线程中，使用QTimer.singleShot确保在主线程中执行
        QTimer.singleShot(0, lambda: func(*args, **kwargs))
        return None  # 注意：这种情况下无法获取返回值

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
    """输出重定向类，用于捕获标准输出和标准错误"""
    
    def __init__(self, main_callback, tool_callback):
        """
        初始化输出重定向器
        
        参数:
            main_callback: 主输出回调函数
            tool_callback: 工具输出回调函数
        """
        self.main_callback = main_callback
        self.tool_callback = tool_callback
        self.main_buffer = ""
        self.tool_buffer = ""
        
        # 保存原始的标准输出和标准错误
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def start_redirect(self):
        """开始重定向"""
        sys.stdout = self
        sys.stderr = self
    
    def stop_redirect(self):
        """停止重定向并恢复原始输出"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def write(self, text):
        """写入文本到缓冲区"""
        # 检查是否为空字符串
        if not text or not text.strip():
            return
            
        # 检测是否为工具输出
        if text.startswith("[TOOL]"):
            # 移除前缀并添加到工具输出缓冲区
            self.tool_buffer += text[6:]
        else:
            # 添加到主输出缓冲区
            self.main_buffer += text
        
        # 如果文本以换行符结束，则刷新缓冲区
        if text.endswith('\n'):
            self.flush()
    
    def flush(self):
        """刷新缓冲区"""
        # 刷新主输出缓冲区
        if self.main_buffer and self.main_callback:
            # 使用QApplication.instance()检查是否在主线程中
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer, QThread
            
            app = QApplication.instance()
            if app and app.thread() == QThread.currentThread():
                # 在主线程中，直接调用回调
                self.main_callback(self.main_buffer)
            else:
                # 在非主线程中，使用QTimer.singleShot
                buffer_copy = self.main_buffer
                QTimer.singleShot(0, lambda: self.main_callback(buffer_copy))
            self.main_buffer = ""
        
        # 刷新工具输出缓冲区
        if self.tool_buffer and self.tool_callback:
            # 使用QApplication.instance()检查是否在主线程中
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer, QThread
            
            app = QApplication.instance()
            if app and app.thread() == QThread.currentThread():
                # 在主线程中，直接调用回调
                self.tool_callback(self.tool_buffer)
            else:
                # 在非主线程中，使用QTimer.singleShot
                buffer_copy = self.tool_buffer
                QTimer.singleShot(0, lambda: self.tool_callback(buffer_copy))
            self.tool_buffer = ""

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
        """
        运行安全任务
        """
        def task_thread():
            # 尝试获取锁，防止多轮任务重叠
            acquired = task_running_lock.acquire(blocking=False)
            if not acquired:
                safe_ui_call(main_callback, "已有任务正在运行，请勿重复启动。\n")
                return
            try:
                # 设置输出重定向
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
                
                # 设置工具输出回调
                from tools.security_tools import set_tool_output_callback
                
                # 确保工具输出回调在主线程中执行
                def tool_output_wrapper(text):
                    # 添加[TOOL]前缀，以便OutputRedirector能够识别
                    print(f"[TOOL]{text}")
                
                # 设置工具输出回调
                set_tool_output_callback(tool_output_wrapper)
                
                # 导入必要的模块
                from models import setup_llm
                from config import DEFAULT_MODEL_TYPE
                from agents import create_agents, create_tasks
                
                # 设置语言模型 - 确保正确创建两个不同用途的LLM
                llm_for_agents = setup_llm(model_type=DEFAULT_MODEL_TYPE, for_crewai=True)
                llm_for_direct = setup_llm(model_type=DEFAULT_MODEL_TYPE, for_crewai=False)
                
                # 创建agents - 使用专门为CrewAI配置的LLM
                agents = create_agents(llm_for_agents, group_name=group_name)
                
                # 获取秘书Agent
                secretary_agent = agents.get("secretary")
                if not secretary_agent:
                    safe_ui_call(main_callback, "错误: 未找到秘书Agent，请确保已添加秘书角色\n")
                    safe_ui_call(log_callback, "错误: 未找到秘书Agent，请检查agents_config.json中是否定义了secretary角色")
                    return
                
                # 记录秘书角色信息，帮助调试
                safe_ui_call(log_callback, f"秘书角色已初始化: {secretary_agent.role}")
                
                # 创建tasks
                tasks = create_tasks(agents)
                
                # 导入执行函数
                from main import execute_agent_with_approval
                
                # 重写get_user_decision函数，使用GUI交互
                # 在gui_tools.py中找到处理决策的部分，确保正确处理建议类型的决策
                # 例如在run_security_task方法中的gui_get_user_decision函数内
                
                def gui_get_user_decision(report, stage="执行后", agent_name=None):
                    """获取用户对安全报告的决策 - GUI版本"""
                    # 更新报告显示
                    report_header = f"【{agent_name} - {stage}报告】" if agent_name else "【安全态势报告】"
                    formatted_report = f"\n{report_header}\n{'='*80}\n{report}\n{'='*80}\n"
                    
                    # 通过回调更新报告区域 - 确保报告显示在主界面
                    safe_ui_call(main_callback, formatted_report)
                    safe_ui_call(log_callback, f"等待用户对 {agent_name} 的 {stage}报告 进行决策...")
                    
                    # 启用决策控件
                    try:
                        from gui.gui_tools import enable_decision_controls
                        safe_ui_call(enable_decision_controls)
                    except Exception as e:
                        print(f"WARNING: 启用决策控件时出错: {str(e)}")
                    
                    # 等待用户决策 - 使用全局队列
                    try:
                        from gui.app import get_decision
                        # 等待决策，设置超时时间 - 延长超时时间
                        timeout = 600  # 10分钟超时
                        decision = get_decision(timeout)
                        
                        if decision.get("status") == "timeout":
                            safe_ui_call(log_callback, f"决策请求超时({timeout}秒)，默认批准")
                            return {"status": "approved", "feedback": f"自动批准（{timeout}秒超时）"}
                        
                        # 格式化建议内容
                        if decision.get("status") == "feedback" and decision.get("feedback"):
                            # 如果建议内容不是以"建议:"开头，则添加前缀
                            feedback = decision.get("feedback", "")
                            if not feedback.startswith("建议:") and not feedback.startswith("建议："):
                                decision["feedback"] = f"建议: {feedback}"
                            print(f"DEBUG: 格式化后的建议: {decision['feedback']}")
                            
                            # 添加：处理建议类型的决策前的UI反馈
                            try:
                                # 更新UI，显示建议已被接收
                                safe_ui_call(main_callback, f"\n已接收您的建议: {decision['feedback']}\n正在处理中，请稍候...\n")
                            except Exception as e:
                                print(f"ERROR: 更新UI时出错: {str(e)}")
                        
                        # 记录决策结果
                        safe_ui_call(log_callback, f"用户决策: {decision['status']} - {decision.get('feedback', '')}")
                        return decision
                    except Exception as e:
                        error_msg = f"获取决策时出错: {str(e)}"
                        safe_ui_call(log_callback, error_msg)
                        print(f"ERROR: {error_msg}")
                        import traceback
                        print(traceback.format_exc())
                        return {"status": "approved", "feedback": f"自动批准（出错）"}
                
                # 开始执行任务
                safe_ui_call(main_callback, "开始执行安全分析任务...\n")
                
                # 根据不同的角色组选择不同的工作流程
                if group_name == "default_group":
                    # 1. 数据收集任务
                    safe_ui_call(role_callback, "数据收集专家 - 收集系统安全相关数据")
                    data_collection_result = execute_agent_with_approval(
                        agents["data_collector"], 
                        tasks[0].description, 
                        llm_for_direct, 
                        secretary_agent,
                        get_user_decision=gui_get_user_decision  # 使用修改后的决策函数
                    )
                    if data_collection_result["status"] != "completed":
                        safe_ui_call(main_callback, "数据收集任务未获批准，任务终止\n")
                        return
                    
                    # 提取数据收集结果，用于后续分析
                    collected_data = data_collection_result["result"]
                    
                    # 2. 并行执行进程分析和日志分析任务
                    # 2.1 进程分析任务 - 传入原始数据
                    safe_ui_call(role_callback, "进程安全分析师 - 分析系统进程安全状况")
                    process_analysis_result = execute_agent_with_approval(
                        agents["process_analyzer"], 
                        tasks[1].description, 
                        llm_for_direct,
                        secretary_agent,
                        raw_data=collected_data,
                        get_user_decision=gui_get_user_decision
                    )
                    if process_analysis_result["status"] != "completed":
                        safe_ui_call(main_callback, "进程分析任务未获批准，任务终止\n")
                        return
                    
                    # 2.2 日志分析任务 - 传入原始数据
                    safe_ui_call(role_callback, "日志分析专家 - 分析系统日志")
                    log_analysis_result = execute_agent_with_approval(
                        agents["log_analyzer"], 
                        tasks[2].description, 
                        llm_for_direct,
                        secretary_agent,
                        raw_data=collected_data,
                        get_user_decision=gui_get_user_decision
                    )
                    if log_analysis_result["status"] != "completed":
                        safe_ui_call(main_callback, "日志分析任务未获批准，任务终止\n")
                        return
                    
                    # 3. 应急响应任务 - 传入进程分析和日志分析结果
                    safe_ui_call(role_callback, "安全应急响应专家 - 制定并执行响应措施")
                    incident_response_result = execute_agent_with_approval(
                        agents["incident_responder"], 
                        tasks[3].description, 
                        llm_for_direct,
                        secretary_agent,
                        previous_report=process_analysis_result["result"] + "\n\n" + log_analysis_result["result"],
                        get_user_decision=gui_get_user_decision
                    )
                    
                    # 任务完成
                    safe_ui_call(role_callback, "任务完成")
                    safe_ui_call(main_callback, "\n所有任务执行完成！\n")
                    
                elif group_name == "custom_group":
                    # 自定义工作流程
                    # ... 类似实现
                    pass
                
                # 任务完成后，确保在主线程中执行清理操作
                from PyQt5.QtCore import QTimer
                
                # 恢复标准输出
                redirector.stop_redirect()
                
                # 移除日志处理器
                logger.removeHandler(log_handler)
                
                # 调用完成回调 - 确保在主线程中执行
                if completion_callback:
                    safe_ui_call(completion_callback, "任务执行完成")
                
                # 添加一个延迟，确保所有UI更新完成
                QTimer.singleShot(500, lambda: print("DEBUG: 任务线程完成，UI更新应该已完成"))
                
            
                debug_thread_info("准备调用 task_completion_handler")
                from main import task_completion_handler

                def delayed_task_completion():
                    debug_thread_info("delayed_task_completion 内部")
                    try:
                        print("DEBUG: 直接调用 task_completion_handler")
                        task_completion_handler("任务执行完成")
                    except Exception as e:
                        import traceback
                        print(f"ERROR: 调用 task_completion_handler 时出错: {str(e)}")
                        print(traceback.format_exc())

                # 使用更长的延迟，确保UI更新完成
                print("DEBUG: 设置延迟调用 task_completion_handler")
                QTimer.singleShot(2000, lambda: safe_ui_call(delayed_task_completion))
                
                # 移除自动循环部分，改为由task_completion_handler中的ask_for_next_round处理
            except Exception as e:
                import traceback
                error_msg = f"任务执行出错: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                safe_ui_call(main_callback, f"\n{error_msg}\n")
                if completion_callback:
                    safe_ui_call(completion_callback, f"错误: {str(e)}")
            finally:
                # 释放锁，允许下一轮任务启动
                if task_running_lock.locked():
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