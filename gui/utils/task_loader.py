import os
import re
from datetime import datetime
from PyQt5.QtWidgets import QTextEdit

# 修改加载任务详情的方法，从日志文件中读取数据
def load_task_details(self, timestamp):
    """从日志文件中加载指定时间的任务详情"""
    import os
    import re
    from datetime import datetime
    from gui.gui_tools import safe_ui_call
    
    # 获取日期部分，用于查找对应的日志文件
    date_part = timestamp.split()[0]
    
    # 构建日志文件路径
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
    log_file = os.path.join(log_dir, f"security_log_{date_part}.log")
    
    if not os.path.exists(log_file):
        safe_ui_call(self.text_widget.append, f"未找到对应的日志文件: {log_file}")
        return
    
    # 读取日志文件
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
    
    # 查找对应时间戳的任务记录
    timestamp_pattern = re.escape(timestamp)
    task_pattern = f"({timestamp_pattern}.*?)(\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}}|$)"
    task_match = re.search(task_pattern, log_content, re.DOTALL)
    
    if task_match:
        task_content = task_match.group(1)
        safe_ui_call(self.text_widget.clear)
        safe_ui_call(self.text_widget.append, task_content)
    else:
        safe_ui_call(self.text_widget.append, f"未找到时间戳为 {timestamp} 的任务记录")
    
    # 日志文件路径
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "log")
    pre_log_file = os.path.join(log_dir, f"pre_execution_{date_part}.log")
    post_log_file = os.path.join(log_dir, f"post_execution_{date_part}.log")
    
    # 读取执行前日志
    pre_reports = {}
    if os.path.exists(pre_log_file):
        try:
            with open(pre_log_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 使用正则表达式提取各个阶段的报告
                sections = re.split(r'=+\n【(.*?) - 执行前报告】- (.*?)\n=+', content)
                for i in range(1, len(sections), 3):
                    if i+1 < len(sections):
                        agent_name = sections[i]
                        report_time = sections[i+1]
                        report_content = sections[i+2]
                        
                        # 将时间字符串转换为datetime对象进行比较
                        try:
                            report_datetime = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S")
                            timestamp_datetime = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                            
                            # 如果报告时间接近任务时间（前后5分钟内），则认为是同一任务
                            time_diff = abs((report_datetime - timestamp_datetime).total_seconds())
                            if time_diff <= 300:  # 5分钟 = 300秒
                                if "数据收集" in agent_name:
                                    pre_reports["数据收集"] = report_content
                                elif "进程" in agent_name:
                                    pre_reports["进程分析"] = report_content
                                elif "日志" in agent_name:
                                    pre_reports["日志分析"] = report_content
                                elif "应急响应" in agent_name or "响应" in agent_name:
                                    pre_reports["应急响应"] = report_content
                        except ValueError:
                            continue
        except Exception as e:
            print(f"读取执行前日志出错: {str(e)}")
    
    # 读取执行后日志
    post_reports = {}
    if os.path.exists(post_log_file):
        try:
            with open(post_log_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 使用正则表达式提取各个阶段的报告
                sections = re.split(r'=+\n【(.*?) - 执行后报告】- (.*?)\n=+', content)
                for i in range(1, len(sections), 3):
                    if i+1 < len(sections):
                        agent_name = sections[i]
                        report_time = sections[i+1]
                        report_content = sections[i+2]
                        
                        # 将时间字符串转换为datetime对象进行比较
                        try:
                            report_datetime = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S")
                            timestamp_datetime = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                            
                            # 如果报告时间接近任务时间（前后5分钟内），则认为是同一任务
                            time_diff = abs((report_datetime - timestamp_datetime).total_seconds())
                            if time_diff <= 300:  # 5分钟 = 300秒
                                if "数据收集" in agent_name:
                                    post_reports["数据收集"] = report_content
                                elif "进程" in agent_name:
                                    post_reports["进程分析"] = report_content
                                elif "日志" in agent_name:
                                    post_reports["日志分析"] = report_content
                                elif "应急响应" in agent_name or "响应" in agent_name:
                                    post_reports["应急响应"] = report_content
                        except ValueError:
                            continue
        except Exception as e:
            print(f"读取执行后日志出错: {str(e)}")
    
    # 更新各阶段页面的内容
    phases = ["数据收集", "进程分析", "日志分析", "应急响应"]
    for i, phase in enumerate(phases):
        page = self.content_stack.widget(i)
        
        # 更新执行前报告
        pre_report_text = page.findChild(QTextEdit, f"{phase.lower()}_pre_report")
        if pre_report_text and phase in pre_reports:
            pre_report_text.setText(pre_reports[phase])
        elif pre_report_text:
            pre_report_text.setText(f"未找到{phase}阶段的执行前报告")
        
        # 更新执行后报告
        post_report_text = page.findChild(QTextEdit, f"{phase.lower()}_post_report")
        if post_report_text and phase in post_reports:
            post_report_text.setText(post_reports[phase])
        elif post_report_text:
            post_report_text.setText(f"未找到{phase}阶段的执行后报告")
    
    # 默认显示数据收集阶段
    self.content_stack.setCurrentIndex(0)
    
    # 模拟数据 - 实际应用中应该从日志文件中读取
    pre_report = """
=================================================================
【数据收集专家 - 执行前报告】
=================================================================
【任务描述】
收集系统中的进程、服务和日志信息，为后续安全分析提供数据支持。

【工具与方法】
1. PowerShell Get-Process - 获取进程信息
2. wevtutil qe Security - 导出安全日志
3. sc query state= all - 枚举服务状态
4. Sysinternals Sigcheck - 验证进程签名
"""
    
    post_report = """
=================================================================
【数据收集专家 - 执行后报告】
=================================================================
【结果分析与评估】
系统中发现以下可疑进程：
1. com.vortex.helper.exe - 位于非标准路径，缺乏数字签名
2. Trae.exe - 多实例运行，资源占用较高
3. Zou.exe - 未知厂商，可能为第三方工具

建议进一步分析这些进程的行为和网络连接。

"""
    
    # 更新文本框内容
    self.pre_report_text = self.data_collection_page.findChild(QTextEdit, "")
    if self.pre_report_text:
        self.pre_report_text.setText(pre_report)
    
    self.post_report_text = self.data_collection_page.findChild(QTextEdit, "")
    if self.post_report_text:
        self.post_report_text.setText(post_report)

    def create_placeholder_page(self, message):
        """创建未实现功能的占位页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        
        # 添加占位信息
        icon_label = QLabel()
        # 使用Unicode字符作为图标
        icon_label.setText("🚧")
        icon_label.setStyleSheet("font-size: 48px; color: #7f8c8d;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        message_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label)
        
        return page
    
    def create_monitoring_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 系统状态显示区域
        status_text = QTextEdit()
        status_text.setReadOnly(True)
        status_text.setPlaceholderText("系统状态信息将显示在这里...")
        status_text.setStyleSheet("background-color: white; border: 1px solid #dcdde1; border-radius: 5px; padding: 5px;")
        layout.addWidget(status_text)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        start_button = QPushButton("开始监控")
        start_button.setStyleSheet("background-color: #3498db; color: white; padding: 8px 16px; border-radius: 4px;")
        start_button.clicked.connect(lambda: self.start_monitoring(status_text))
        
        stop_button = QPushButton("停止监控")
        stop_button.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px;")
        
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addStretch(1)  # 添加弹性空间，使按钮靠左对齐
        layout.addLayout(button_layout)
        
        return page
    
    def create_process_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 进程列表显示区域
        process_text = QTextEdit()
        process_text.setReadOnly(True)
        process_text.setPlaceholderText("进程信息将显示在这里...")
        process_text.setStyleSheet("background-color: white; border: 1px solid #dcdde1; border-radius: 5px; padding: 5px;")
        layout.addWidget(process_text)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新进程")
        refresh_button.setStyleSheet("background-color: #3498db; color: white; padding: 8px 16px; border-radius: 4px;")
        refresh_button.clicked.connect(lambda: self.refresh_processes(process_text))
        
        analyze_button = QPushButton("分析异常进程")
        analyze_button.setStyleSheet("background-color: #2ecc71; color: white; padding: 8px 16px; border-radius: 4px;")
        
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(analyze_button)
        button_layout.addStretch(1)  # 添加弹性空间，使按钮靠左对齐
        layout.addLayout(button_layout)
        
        return page
    
    def create_log_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 日志显示区域
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setPlaceholderText("系统日志将显示在这里...")
        layout.addWidget(log_text)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        get_logs_button = QPushButton("获取日志")
        get_logs_button.clicked.connect(lambda: self.get_logs(log_text))
        analyze_logs_button = QPushButton("分析日志")
        button_layout.addWidget(get_logs_button)
        button_layout.addWidget(analyze_logs_button)
        layout.addLayout(button_layout)
        
        return page
    
    def create_threat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 威胁信息显示区域
        threat_text = QTextEdit()
        threat_text.setReadOnly(True)
        threat_text.setPlaceholderText("威胁检测结果将显示在这里...")
        layout.addWidget(threat_text)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        detect_button = QPushButton("开始检测")
        detect_button.clicked.connect(lambda: self.start_detection(threat_text))
        report_button = QPushButton("生成报告")
        button_layout.addWidget(detect_button)
        button_layout.addWidget(report_button)
        layout.addLayout(button_layout)
        
        return page
    
    def create_response_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 响应操作显示区域
        response_text = QTextEdit()
        response_text.setReadOnly(True)
        response_text.setPlaceholderText("应急响应操作将显示在这里...")
        layout.addWidget(response_text)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        isolate_button = QPushButton("隔离系统")
        isolate_button.clicked.connect(lambda: self.isolate_system(response_text))
        recover_button = QPushButton("恢复系统")
        button_layout.addWidget(isolate_button)
        button_layout.addWidget(recover_button)
        layout.addLayout(button_layout)
        
        return page
    
    # 功能实现方法
    def start_monitoring(self, text_widget):
        """开始安全监控"""
        from gui.gui_tools import safe_ui_call
        
        safe_ui_call(text_widget.append, "开始安全监控...")
        # 调用后端安全监控功能
        from gui.gui_tools import GUITools
        
        def update_response_text(result):
            safe_ui_call(text_widget.append, f"监控结果: {result}")
        
        # 启动安全监控
        GUITools.run_security_task(
            "default_group",
            lambda text: safe_ui_call(text_widget.append, text),
            lambda text: safe_ui_call(text_widget.append, f"[工具输出] {text}"),
            lambda text: safe_ui_call(text_widget.append, f"[日志] {text}"),
            lambda text: safe_ui_call(text_widget.append, f"[当前角色] {text}"),
            lambda text: safe_ui_call(text_widget.append, f"[完成] {text}")
        )
        # 启动监控，持续60秒
        GUITools.run_monitoring(update_monitoring_text, 60)
    
    def refresh_processes(self, text_widget):
        text_widget.append("正在获取进程信息...")
        # 调用后端获取进程信息的功能
        from gui.gui_tools import GUITools
        
        def update_process_text(result):
            formatted_result = GUITools.format_process_list(result)
            text_widget.setText("正在获取进程信息...\n\n" + formatted_result)
        
        GUITools.get_processes(update_process_text)
    
    def get_logs(self, text_widget):
        text_widget.append("正在获取系统日志...")
        # 调用后端获取日志的功能
        from gui.gui_tools import GUITools
        
        def update_logs_text(result):
            formatted_result = GUITools.format_logs(result)
            text_widget.setText("正在获取系统日志...\n\n" + formatted_result)
        
        GUITools.get_logs(update_logs_text)
    
    def start_detection(self, text_widget):
        text_widget.append("开始威胁检测...")
        # 调用后端威胁检测功能
        from gui.gui_tools import GUITools
        
        def update_detection_text(result):
            text_widget.append(result)
        
        GUITools.analyze_threats(update_detection_text)
    
    def isolate_system(self, text_widget):
        text_widget.append("正在执行系统隔离...")
        # 调用后端系统隔离功能
        from gui.gui_tools import GUITools
        
        def update_response_text(result):
            text_widget.append(result)
        
        GUITools.emergency_response("isolate", update_response_text)