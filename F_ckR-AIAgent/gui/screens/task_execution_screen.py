#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QSplitter, QFrame, QPushButton,
                            QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

class TaskExecutionScreen(QWidget):
    """任务执行界面，显示任务执行过程中的各种输出"""
    
    # 添加决策信号
    decision_made = pyqtSignal(dict)
    
    # 添加更新UI的信号
    # 添加启用决策控件的信号
    report_update_signal = pyqtSignal(str, bool)
    tool_update_signal = pyqtSignal(str)
    log_update_signal = pyqtSignal(str)
    role_update_signal = pyqtSignal(str)
    enable_decision_signal = pyqtSignal(bool)  # 新增信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # 初始化决策回调
        self.current_decision_callback = None
        
        # 连接信号到槽函数
        self.report_update_signal.connect(self._update_report_impl)
        self.tool_update_signal.connect(self._update_tool_impl)
        self.log_update_signal.connect(self._update_log_impl)
        self.role_update_signal.connect(self._update_role_impl)
        # 确保决策信号连接到决策处理槽
        self.decision_made.connect(self.on_decision_made)
        # 连接启用决策控件信号
        self.enable_decision_signal.connect(self.enable_decision_controls)
    
    def init_ui(self):
        """初始化界面"""
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        
        # 左侧区域 - Agent报告
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧标题
        left_title = QLabel("Agent 报告")
        left_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        left_layout.addWidget(left_title)
        
        # 左侧文本区域
        self.report_output = QTextEdit()
        self.report_output.setReadOnly(True)
        self.report_output.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dfe6e9;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }
        """)
        left_layout.addWidget(self.report_output)
        
        # 添加决策输入区域
        decision_group = QGroupBox("决策输入")
        decision_layout = QVBoxLayout(decision_group)
        
        # 决策按钮
        decision_buttons = QHBoxLayout()
        self.approve_button = QPushButton("批准")
        self.approve_button.clicked.connect(self.on_approve)
        self.reject_button = QPushButton("拒绝")
        self.reject_button.clicked.connect(self.on_reject)
        decision_buttons.addWidget(self.approve_button)
        decision_buttons.addWidget(self.reject_button)
        decision_layout.addLayout(decision_buttons)
        
        # 建议输入
        suggestion_layout = QHBoxLayout()
        suggestion_layout.addWidget(QLabel("建议:"))
        self.suggestion_input = QLineEdit()
        self.send_suggestion_button = QPushButton("发送建议")
        self.send_suggestion_button.clicked.connect(self.on_send_suggestion)
        suggestion_layout.addWidget(self.suggestion_input)
        suggestion_layout.addWidget(self.send_suggestion_button)
        decision_layout.addLayout(suggestion_layout)
        
        left_layout.addWidget(decision_group)
        
        # 右侧区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 右侧上部 - 日志输出
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout(log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dfe6e9;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                color: #636e72;
            }
        """)
        log_layout.addWidget(self.log_output)
        right_layout.addWidget(log_group)
        
        # 右侧中部 - 当前角色
        role_group = QGroupBox("当前工作角色")
        role_layout = QVBoxLayout(role_group)
        self.current_role = QLabel("等待任务开始...")
        self.current_role.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        role_layout.addWidget(self.current_role)
        right_layout.addWidget(role_group)
        
        # 右侧下部 - 工具输出
        tool_group = QGroupBox("工具输出")
        tool_layout = QVBoxLayout(tool_group)
        self.tool_output = QTextEdit()
        self.tool_output.setReadOnly(True)
        self.tool_output.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dfe6e9;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        tool_layout.addWidget(self.tool_output)
        right_layout.addWidget(tool_group)
        
        # 设置右侧区域的比例
        right_layout.setStretch(0, 3)  # 日志输出
        right_layout.setStretch(1, 1)  # 当前角色
        right_layout.setStretch(2, 3)  # 工具输出
        
        # 添加左右两侧到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        
        # 初始禁用决策按钮，等待报告生成后启用
        self.enable_decision_controls(False)
    
    def enable_decision_controls(self, enabled=True):
        """启用或禁用决策控件"""
        self.approve_button.setEnabled(enabled)
        self.reject_button.setEnabled(enabled)
        self.suggestion_input.setEnabled(enabled)
        self.send_suggestion_button.setEnabled(enabled)
    
    def force_enable_decision_controls(self):
        """强制启用决策控件"""
        print("DEBUG: 强制启用决策控件")
        try:
            # 使用信号在主线程中启用决策控件
            self.enable_decision_signal.emit(True)
            
            # 强制处理事件，确保UI更新
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            print("DEBUG: 决策控件已强制启用")
        except Exception as e:
            print(f"ERROR: 强制启用决策控件时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # 备用方法：直接调用
            try:
                print("DEBUG: 尝试直接调用enable_decision_controls")
                self.enable_decision_controls(True)
            except Exception as e2:
                print(f"ERROR: 直接调用也失败: {str(e2)}")
    
    def on_approve(self):
        """批准按钮点击事件"""
        print("DEBUG: 批准按钮被点击")
        try:
            # 简化处理：直接将决策放入全局队列
            from gui.app import put_decision
            decision = {"status": "approved", "feedback": ""}
            put_decision(decision)
            print(f"DEBUG: 批准决策已放入队列")
            
            # 发送信号（可选，用于UI更新）
            self.decision_made.emit(decision)
            
            # 更新日志
            self.update_log_output("用户批准了当前报告")
        except Exception as e:
            print(f"ERROR: 执行批准决策时出错: {str(e)}")
    
    def on_reject(self):
        """拒绝按钮点击事件"""
        print("DEBUG: 拒绝按钮被点击")
        try:
            # 简化处理：直接将决策放入全局队列
            from gui.app import put_decision
            decision = {"status": "rejected", "feedback": ""}
            put_decision(decision)
            print(f"DEBUG: 拒绝决策已放入队列")
            
            # 发送信号（可选，用于UI更新）
            self.decision_made.emit(decision)
            
            # 更新日志
            self.update_log_output("用户拒绝了当前报告")
        except Exception as e:
            print(f"ERROR: 执行拒绝决策时出错: {str(e)}")
    
    def on_send_suggestion(self):
        """发送建议按钮点击事件"""
        suggestion = self.suggestion_input.text().strip()
        print(f"DEBUG: 发送建议按钮被点击，建议内容: {suggestion}")
        
        if suggestion:
            try:
                # 统一处理建议格式 - 改进空格处理
                if suggestion.startswith("建议:"):
                    suggestion = suggestion[3:].strip()
                    suggestion = f"建议: {suggestion}"
                elif suggestion.startswith("建议："):
                    suggestion = suggestion[3:].strip()
                    suggestion = f"建议: {suggestion}"
                else:
                    suggestion = f"建议: {suggestion}"
                    
                print(f"DEBUG: 格式化后的建议: {suggestion}")
                
                # 简化处理：直接将决策放入全局队列
                from gui.app import put_decision
                decision = {"status": "feedback", "feedback": suggestion}
                put_decision(decision)
                print(f"DEBUG: 建议决策已放入队列: {suggestion}")
                
                # 发送信号（可选，用于UI更新）
                self.decision_made.emit(decision)
                
                # 清空输入框
                self.suggestion_input.clear()
                
                # 更新日志
                self.update_log_output(f"用户提供了建议: {suggestion}")
                
                # 添加：禁用决策控件，表示已经处理了决策
                self.enable_decision_controls(False)
                
                # 添加：显示处理中提示
                self.update_report(f"正在处理您的建议: {suggestion}\n请稍候...", False)
                
                # 添加：设置超时处理
                from PyQt5.QtCore import QTimer
                
                def check_suggestion_status():
                    # 检查是否有新的报告更新，如果没有，提示用户建议处理可能出错
                    print("DEBUG: 检查建议处理状态")
                    self.update_report(f"您的建议 \"{suggestion}\" 正在处理中...\n如长时间无响应，可能是处理过程中出现了错误。\n您可以尝试重新提交建议或继续等待。", False)
                    self.enable_decision_controls(True)  # 重新启用决策控件
                
                # 30秒后检查状态
                QTimer.singleShot(30000, check_suggestion_status)
                
            except Exception as e:
                print(f"ERROR: 执行建议决策时出错: {str(e)}")
        else:
            print(f"WARNING: 建议内容为空")
    
    def on_decision_made(self, decision):
        """处理用户决策"""
        print(f"DEBUG: on_decision_made被调用，决策: {decision}")
        if hasattr(self, 'current_decision_callback') and self.current_decision_callback:
            try:
                # 调用回调函数
                self.current_decision_callback(decision)
                print(f"DEBUG: 决策回调已执行")
                # 不要在这里将current_decision_callback设为None
                # self.current_decision_callback = None
            except Exception as e:
                print(f"ERROR: 执行决策回调时出错: {str(e)}")
        else:
            print(f"WARNING: 没有找到current_decision_callback")
    
    def update_report(self, text, enable_decision=True):
        """更新报告区域"""
        # 确保text是字符串
        if not isinstance(text, str):
            text = str(text)
        
        # 检查是否为空字符串或只包含空白字符，如果是则直接返回
        if not text.strip():
            return
        
        # 使用原始标准输出进行调试，避免递归
        import sys
        original_stdout = sys.stdout
        
        # 避免处理调试信息，防止递归
        if not text.startswith("DEBUG:"):
            # 使用原始输出打印调试信息
            temp_stdout = sys.stdout
            sys.stdout = original_stdout
            print(f"DEBUG: update_report被调用，文本长度: {len(text)}, enable_decision: {enable_decision}")
            if len(text) > 0:
                print(f"DEBUG: 文本内容前50个字符: {text[:50]}")
            sys.stdout = temp_stdout
            
            try:
                # 使用信号在主线程中更新UI
                self.report_update_signal.emit(text, enable_decision)
                print(f"DEBUG: report_update_signal已发送")
                
                # 直接启用决策控件，确保按钮可用
                self.enable_decision_controls(enable_decision)
                
                # 强制处理事件，确保UI更新
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
            except Exception as e:
                sys.stdout = original_stdout
                print(f"ERROR: 发送信号时出错: {str(e)}")
                sys.stdout = temp_stdout
    
    def update_main_output(self, text):
        """更新主输出区域 - 为了兼容性保留，实际转发到报告区域"""
        self.update_report(text, False)
    
    # 删除第二个update_report方法，保留上面的方法
    
    def _update_report_impl(self, text, enable_decision=True):
        """在主线程中执行报告更新"""
        # 检查是否为空字符串或只包含空白字符，如果是则直接返回
        if not text.strip():
            return
        
        # 使用原始标准输出进行调试，避免递归
        import sys
        original_stdout = sys.stdout
        
        # 避免处理调试信息，防止递归
        if not text.startswith("DEBUG:"):
            # 使用原始输出打印调试信息
            temp_stdout = sys.stdout
            sys.stdout = original_stdout
            print(f"DEBUG: _update_report_impl被调用，文本长度: {len(text)}, enable_decision: {enable_decision}")
            if len(text) > 0:
                print(f"DEBUG: 文本内容前50个字符: {text[:50]}")
            sys.stdout = temp_stdout
            
            # 直接设置内容，而不是追加
            self.report_output.setText(text)
            
            # 滚动到顶部，确保用户看到报告开头
            self.report_output.verticalScrollBar().setValue(0)
            
            # 强制启用决策控件 - 这是关键修改
            print(f"DEBUG: 强制启用决策控件")
            self.enable_decision_controls(True)  # 修改为True，强制启用
            
            # 刷新界面
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            # 再次使用原始输出打印调试信息
            sys.stdout = original_stdout
            print(f"DEBUG: _update_report_impl完成")
            sys.stdout = temp_stdout
    
    def update_tool_output(self, text):
        """更新工具输出区域"""
        # 确保text是字符串
        if not isinstance(text, str):
            text = str(text)
            
        # 使用信号在主线程中更新UI
        self.tool_update_signal.emit(text)
    
    def _update_tool_impl(self, text):
        """在主线程中执行工具输出更新"""
        self.tool_output.append(text)
        # 滚动到底部
        self.tool_output.verticalScrollBar().setValue(self.tool_output.verticalScrollBar().maximum())
        # 刷新界面
        QApplication.processEvents()

    def update_log_output(self, text):
        """更新日志输出区域"""
        # 确保text是字符串
        if not isinstance(text, str):
            text = str(text)
            
        # 检查文本是否已经包含时间戳
        import re
        has_timestamp = re.match(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]', text)
        
        # 如果没有时间戳，则添加
        if not has_timestamp:
            # 使用信号在主线程中更新UI
            self.log_update_signal.emit(text)
        else:
            # 已有时间戳，直接发送
            self.log_update_signal.emit(text)
    
    def _update_log_impl(self, text):
        """在主线程中更新日志输出区域"""
        # 确保text是字符串
        if not isinstance(text, str):
            text = str(text)
        
        # 添加时间戳
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_text = f"[{timestamp}] {text}"
        
        # 将文本添加到日志区域
        self.log_output.append(formatted_text)
        
        # 滚动到底部
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # 刷新界面
        QApplication.processEvents()

    def update_current_role(self, role_name):
        """更新当前角色显示"""
        # 确保role_name是字符串
        if not isinstance(role_name, str):
            role_name = str(role_name)
            
        # 使用信号在主线程中更新UI
        self.role_update_signal.emit(role_name)
    
    def _update_role_impl(self, role_name):
        """在主线程中执行角色更新"""
        self.current_role.setText(role_name)
        # 刷新界面
        QApplication.processEvents()
    
    def request_decision(self, report, stage, agent_name, callback):
        """请求用户决策
        
        参数:
            report: 报告内容
            stage: 阶段（执行前/执行后）
            agent_name: 角色名称
            callback: 决策结果回调函数
        """
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
        from PyQt5.QtCore import Qt, pyqtSignal
        
        # 创建决策对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{agent_name} - {stage}报告决策")
        dialog.setMinimumSize(700, 500)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加报告标题
        title_label = QLabel(f"【{agent_name} - {stage}报告】")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # 添加报告内容
        report_text = QTextEdit()
        report_text.setReadOnly(True)
        report_text.setPlainText(report)
        report_text.setStyleSheet("background-color: white; border: 1px solid #dcdde1; border-radius: 5px; padding: 10px;")
        layout.addWidget(report_text)
        
        # 添加反馈输入框
        feedback_label = QLabel("反馈意见 (可选):")
        layout.addWidget(feedback_label)
        
        feedback_text = QTextEdit()
        feedback_text.setPlaceholderText("在此输入您对报告的反馈意见...")
        feedback_text.setMaximumHeight(100)
        layout.addWidget(feedback_text)
        
        # 添加按钮区域
        button_layout = QHBoxLayout()
        
        # 拒绝按钮
        reject_btn = QPushButton("拒绝")
        reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # 批准按钮
        approve_btn = QPushButton("批准")
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        button_layout.addWidget(reject_btn)
        button_layout.addWidget(approve_btn)
        layout.addLayout(button_layout)
        
        # 设置按钮点击事件
        def on_reject():
            callback({
                "status": "rejected", 
                "feedback": feedback_text.toPlainText()
            })
            dialog.accept()
        
        def on_approve():
            callback({
                "status": "approved", 
                "feedback": feedback_text.toPlainText()
            })
            dialog.accept()
        
        reject_btn.clicked.connect(on_reject)
        approve_btn.clicked.connect(on_approve)
        
        # 显示对话框
        dialog.exec_()