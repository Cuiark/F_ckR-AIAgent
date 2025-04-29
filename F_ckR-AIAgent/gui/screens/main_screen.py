import sys
import os
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget, 
                             QListWidget, QListWidgetItem, QTextEdit, QSplitter, QSizePolicy)
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont, QIcon, QPixmap, QLinearGradient
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize
import random
import math
from gui.utils.task_loader import load_task_details
#from gui.utils.task_manager import TaskManager
#from gui.utils.task_phase_manager import TaskPhaseManager
#from gui.utils.task_phase import TaskPhase  

# 导入后端功能
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import logger

# 主界面
class MainScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_task_records()

    def init_ui(self):
        # 创建主布局
        main_layout = QHBoxLayout(self)
        
        # 左侧任务记录列表区
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 20, 10, 20)
        
        # 添加标题
        title_label = QLabel("任务记录列表")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2980b9;")
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)
        left_layout.addSpacing(10)
        
        # 任务记录列表
        self.task_list = QListWidget()
        self.task_list.setStyleSheet(
            "QListWidget {background-color: #f5f5f5; border-radius: 5px;}"
            "QListWidget::item {padding: 8px; margin: 2px;}"
            "QListWidget::item:selected {background-color: #3498db; color: white;}"
        )
        
        self.task_list.currentRowChanged.connect(self.change_task)
        left_layout.addWidget(self.task_list, 1)  # 1表示拉伸因子
        
        # 右侧内容区
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        # 内容区标题和状态栏
        header_layout = QHBoxLayout()
        self.content_title = QLabel("任务详情")
        self.content_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(self.content_title)
        
        # 添加状态指示器和时间戳
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.task_time_label = QLabel("执行时间: 2025-04-18 12:46:50")
        self.task_time_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self.task_time_label.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.task_time_label)
        
        self.task_status_label = QLabel("状态: 已完成")
        self.task_status_label.setStyleSheet("color: green; font-weight: bold;")
        self.task_status_label.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.task_status_label)
        
        header_layout.addWidget(status_container)
        
        # 添加设置按钮
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(40, 40)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8c8d;
                font-size: 20px;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                color: #2c3e50;
            }
        """)
        settings_btn.clicked.connect(self.show_settings)
        header_layout.addWidget(settings_btn)
        
        right_layout.addLayout(header_layout)
        right_layout.addSpacing(10)
        
        # 添加分隔线
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        separator.setStyleSheet("background-color: #bdc3c7;")
        right_layout.addWidget(separator)
        
        # 内容区主体 - 使用堆叠窗口部件显示任务的不同阶段
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #f9f9f9; border-radius: 5px;")
        
        # 添加任务阶段页面
        self.data_collection_page = self.create_task_phase_page("数据收集")
        self.process_analysis_page = self.create_task_phase_page("进程分析")
        self.log_analysis_page = self.create_task_phase_page("日志分析")
        self.incident_response_page = self.create_task_phase_page("应急响应")
        
        self.content_stack.addWidget(self.data_collection_page)
        self.content_stack.addWidget(self.process_analysis_page)
        self.content_stack.addWidget(self.log_analysis_page)
        self.content_stack.addWidget(self.incident_response_page)
        
        right_layout.addWidget(self.content_stack)
        
        # 添加左右面板到主布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 750])  # 设置初始大小比例
        splitter.setStyleSheet("QSplitter::handle {background-color: #bdc3c7; width: 2px;}")
        
        main_layout.addWidget(splitter)

        # 在任务列表上方添加"新建任务"按钮
        new_task_btn = QPushButton("新建任务")
        new_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        new_task_btn.clicked.connect(self.show_new_task_dialog)
        left_layout.insertWidget(1, new_task_btn)  # 插入到标题之后
        left_layout.addSpacing(20)  # 添加一些间距
        
        # 修改右侧默认显示
        self.welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_layout.setAlignment(Qt.AlignCenter)
        
        # 添加启动图标
        start_icon = QPushButton()
        start_icon.setFixedSize(120, 120)
        start_icon.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                border-radius: 60px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        start_icon.clicked.connect(self.start_new_task)
        
        # 添加图标文字
        icon_text = QLabel("▶")  # 使用Unicode字符作为播放图标
        icon_text.setStyleSheet("color: white; font-size: 48px;")
        icon_text.setParent(start_icon)
        icon_text.move(45, 30)
        
        welcome_text = QLabel("点击开始新任务")
        welcome_text.setStyleSheet("color: #34495e; font-size: 18px; margin-top: 20px;")
        
        welcome_layout.addWidget(start_icon)
        welcome_layout.addWidget(welcome_text)
        
        # 将欢迎界面添加到堆叠窗口的最前面
        self.content_stack.insertWidget(0, self.welcome_widget)
        self.content_stack.setCurrentWidget(self.welcome_widget)

    def show_settings(self):
        """显示设置对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 添加开发中提示
        label = QLabel("设置功能开发中...")
        label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label)
        dialog.exec_()

    # 在文件顶部导入新的界面类
    from gui.screens.task_execution_screen import TaskExecutionScreen
    
    def show_new_task_dialog(self):
        """显示新建任务对话框"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                                   QPushButton, QListWidget, QFrame)
        import json
        import os
        
        # 读取配置文件
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, "config", "json", "agents_config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                all_agents_config = json.load(f)
        except Exception as e:
            print(f"读取配置文件失败: {str(e)}")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("新建任务")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 添加任务模式选择
        mode_label = QLabel("选择任务模式：")
        mode_combo = QComboBox()
        
        # 从配置文件中获取可用的角色组
        available_groups = list(all_agents_config.keys())
        group_display_names = {
            "default_group": "默认安全监控模式",
            "custom_group": "自定义安全分析模式"
        }
        
        for group in available_groups:
            display_name = group_display_names.get(group, group)
            mode_combo.addItem(display_name, group)  # 显示名称和实际值
        
        # 添加角色列表区域
        roles_label = QLabel("当前模式包含的角色：")
        roles_list = QListWidget()
        roles_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        # 更新角色列表的函数
        def update_roles(index):
            roles_list.clear()
            group_name = mode_combo.itemData(index)  # 获取实际的组名
            if group_name in all_agents_config:
                for agent_id, agent_info in all_agents_config[group_name].items():
                    role_text = f"{agent_info['role']} - {agent_info['goal']}"
                    roles_list.addItem(role_text)
        
        mode_combo.currentIndexChanged.connect(update_roles)
        update_roles(0)  # 初始显示默认模式的角色
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #bdc3c7;")
        
        # 添加确认按钮
        confirm_btn = QPushButton("开始任务")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 修改确认按钮的点击事件
        def on_confirm():
            # 获取选中的任务模式
            selected_index = mode_combo.currentIndex()
            selected_group = mode_combo.itemData(selected_index)
            
            # 关闭对话框
            dialog.accept()
            
            # 启动任务执行界面
            self.start_task_execution(selected_group)
        
        confirm_btn.clicked.connect(on_confirm)
        
        # 布局添加组件
        layout.addWidget(mode_label)
        layout.addWidget(mode_combo)
        layout.addSpacing(10)
        layout.addWidget(roles_label)
        layout.addWidget(roles_list)
        layout.addWidget(separator)
        layout.addSpacing(20)
        layout.addWidget(confirm_btn)
        
        dialog.exec_()

    def create_new_task(self, display_name, group_name, dialog):
        """创建新任务"""
        from datetime import datetime
        
        # 创建新任务记录
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_task_record(timestamp, display_name, "进行中", group_name)
        
        # 关闭对话框
        dialog.accept()
        
        # 切换到新任务
        self.task_list.setCurrentRow(0)  # 新任务会被添加到列表顶部

    def start_new_task(self):
        """启动新任务"""
        print("DEBUG: 开始启动新任务...")
        
        # 获取当前选中的任务组
        current_group = self.get_current_task_group()
        if not current_group:
            print("ERROR: 无法获取当前任务组")
            return
        
        # 创建并显示任务执行屏幕
        self.show_task_execution_screen(current_group)

    def show_new_task_dialog(self):
        """显示新建任务对话框"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                                   QPushButton, QListWidget, QFrame)
        import json
        import os
        
        # 读取配置文件
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, "config", "json", "agents_config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                all_agents_config = json.load(f)
        except Exception as e:
            print(f"读取配置文件失败: {str(e)}")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("新建任务")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 添加任务模式选择
        mode_label = QLabel("选择任务模式：")
        mode_combo = QComboBox()
        
        # 从配置文件中获取可用的角色组
        available_groups = list(all_agents_config.keys())
        group_display_names = {
            "default_group": "默认安全监控模式",
            "custom_group": "自定义安全分析模式"
        }
        
        for group in available_groups:
            display_name = group_display_names.get(group, group)
            mode_combo.addItem(display_name, group)  # 显示名称和实际值
        
        # 添加角色列表区域
        roles_label = QLabel("当前模式包含的角色：")
        roles_list = QListWidget()
        roles_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        # 更新角色列表的函数
        def update_roles(index):
            roles_list.clear()
            group_name = mode_combo.itemData(index)  # 获取实际的组名
            if group_name in all_agents_config:
                for agent_id, agent_info in all_agents_config[group_name].items():
                    role_text = f"{agent_info['role']} - {agent_info['goal']}"
                    roles_list.addItem(role_text)
        
        mode_combo.currentIndexChanged.connect(update_roles)
        update_roles(0)  # 初始显示默认模式的角色
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #bdc3c7;")
        
        # 添加确认按钮
        confirm_btn = QPushButton("开始任务")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 修改确认按钮的点击事件
        def on_confirm():
            # 获取选中的任务模式
            selected_index = mode_combo.currentIndex()
            selected_group = mode_combo.itemData(selected_index)
            
            # 关闭对话框
            dialog.accept()
            
            # 启动任务执行界面
            self.start_task_execution(selected_group)
        
        confirm_btn.clicked.connect(on_confirm)
        
        # 布局添加组件
        layout.addWidget(mode_label)
        layout.addWidget(mode_combo)
        layout.addSpacing(10)
        layout.addWidget(roles_label)
        layout.addWidget(roles_list)
        layout.addWidget(separator)
        layout.addSpacing(20)
        layout.addWidget(confirm_btn)
        
        dialog.exec_()

    def create_new_task(self, display_name, group_name, dialog):
        """创建新任务"""
        from datetime import datetime
        
        # 创建新任务记录
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_task_record(timestamp, display_name, "进行中", group_name)
        
        # 关闭对话框
        dialog.accept()
        
        # 切换到新任务
        self.task_list.setCurrentRow(0)  # 新任务会被添加到列表顶部

    def start_new_task(self):
        """点击启动图标时的响应"""
        self.show_new_task_dialog()
    #添加新方法：从日志文件中加载任务记录列表
    def load_task_records(self):
        """从日志文件中加载任务记录列表"""
        import os
        import re
        from datetime import datetime
        
        # 清空现有任务列表
        self.task_list.clear()

        # 修正日志文件路径，基于项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, "config", "log")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        post_log_files = [f for f in os.listdir(log_dir) if f.startswith("post_execution_")]
        
        # 存储任务记录的列表
        task_records = []
        
        # 从执行后日志文件中提取任务记录
        for log_file in post_log_files:
            try:
                with open(os.path.join(log_dir, log_file), "r", encoding="utf-8") as f:
                    content = f.read()
                    # 使用正则表达式提取各个阶段的报告时间
                    matches = re.findall(r'=+\n【(.*?) - 执行后报告】- (.*?)\n=+', content)
                    for agent_name, report_time in matches:
                        # 将每个报告时间作为一个任务记录
                        task_records.append((report_time, "安全监控任务", "已完成"))
            except Exception as e:
                print(f"读取日志文件 {log_file} 出错: {str(e)}")
        
        # 按时间倒序排序任务记录
        task_records.sort(key=lambda x: x[0], reverse=True)
        
        # 添加到任务列表
        for timestamp, task_type, status in task_records:
            self.add_task_record(timestamp, task_type, status)  # 移除多余的self参数
        

    # 修改添加任务记录的方法
    def add_task_record(self, timestamp, task_type, status):
        """添加任务记录到列表"""
        # 创建任务记录项
        item = QListWidgetItem()
    
        # 创建任务记录容器
        task_widget = QWidget()
        task_layout = QVBoxLayout(task_widget)
        task_layout.setContentsMargins(5, 5, 5, 5)
    
        # 添加时间戳
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        task_layout.addWidget(time_label)
    
        # 添加任务类型
        task_label = QLabel(task_type)
        task_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        task_layout.addWidget(task_label)
    
        # 添加任务状态
        status_label = QLabel(status)
        if status == "已完成":
            status_label.setStyleSheet("color: #27ae60; font-size: 12px;")
        elif status == "进行中":
            status_label.setStyleSheet("color: #f39c12; font-size: 12px;")
        else:
            status_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        task_layout.addWidget(status_label)
    
        # 设置项目大小
        item.setSizeHint(task_widget.sizeHint())
    
        # 添加到列表
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, task_widget)

# 修改任务切换方法
    def change_task(self, index):
        """切换右侧内容区显示选中任务的详情"""
        # 获取选中的任务记录项
        item = self.task_list.item(index)
        if item:
           # 获取任务记录容器
            task_widget = self.task_list.itemWidget(item)
            if task_widget:
                # 获取任务类型（第二个标签）
                task_type = task_widget.layout().itemAt(1).widget().text()
                # 获取时间戳（第一个标签）
                timestamp = task_widget.layout().itemAt(0).widget().text()
                # 获取状态（第三个标签）
                status = task_widget.layout().itemAt(2).widget().text()
            
                # 更新右侧内容区标题和状态
                self.content_title.setText(f"{task_type}详情")
                self.task_time_label.setText(f"执行时间: {timestamp}")
                self.task_status_label.setText(f"状态: {status}")
            
                # 根据状态设置状态标签颜色
                if status == "已完成":
                    self.task_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                elif status == "进行中":
                    self.task_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                else:
                    self.task_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
                # 加载任务详情（这里应该从日志文件中读取实际数据）
                load_task_details(self.content_stack, timestamp)

    # 添加新方法：创建任务阶段页面
    # 修复文本框引用问题，并添加从日志文件读取任务记录的功能
    # 修复create_task_phase_page方法中的文本框引用问题
    def create_task_phase_page(self, phase_name):
        """创建显示任务阶段的页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
    
        # 阶段标题
        phase_title = QLabel(f"{phase_name}阶段")
        phase_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(phase_title)
    
        # 添加执行前报告区域
        pre_report_label = QLabel("执行前报告")
        pre_report_label.setStyleSheet("font-weight: bold; color: #3498db;")
        layout.addWidget(pre_report_label)
    
        pre_report_text = QTextEdit()
        pre_report_text.setReadOnly(True)
        pre_report_text.setObjectName(f"{phase_name.lower()}_pre_report")
        pre_report_text.setStyleSheet("background-color: white; border: 1px solid #dcdde1; border-radius: 5px; padding: 5px;")
        layout.addWidget(pre_report_text)
    
        # 添加执行后报告区域
        post_report_label = QLabel("执行后报告")
        post_report_label.setStyleSheet("font-weight: bold; color: #3498db;")
        layout.addWidget(post_report_label)
    
        post_report_text = QTextEdit()
        post_report_text.setReadOnly(True)
        post_report_text.setObjectName(f"{phase_name.lower()}_post_report")
        post_report_text.setStyleSheet("background-color: white; border: 1px solid #dcdde1; border-radius: 5px; padding: 5px;")
        layout.addWidget(post_report_text)
    
        return page

    def start_task_execution(self, group_name):
        """启动任务执行界面"""
        from gui.screens.task_execution_screen import TaskExecutionScreen
        import time
        import traceback
    
        # 清空内容区域
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if widget:  # 添加这个检查
                self.content_stack.removeWidget(widget)
                widget.deleteLater()
    
        # 创建任务执行界面
        execution_screen = TaskExecutionScreen(self)
        # 连接决策信号
        if hasattr(execution_screen, 'decision_made'):
            execution_screen.decision_made.connect(self.on_decision_made)
        self.content_stack.addWidget(execution_screen)
        self.content_stack.setCurrentWidget(execution_screen)
        
        # 更新界面标题
        self.content_title.setText("任务执行中")
        self.task_status_label.setText("状态: 进行中")
        self.task_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
    
        # 获取当前时间
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.task_time_label.setText(f"执行时间: {current_time}")
        
        # 保存执行屏幕的引用，以便后续使用
        self.task_execution_screen = execution_screen
        
        # 存储当前决策回调
        self.current_decision_callback = None
    
        # 创建一个后台线程来运行任务
        def run_task():
            # 设置输出重定向
            from gui.gui_tools import OutputRedirector
            redirector = OutputRedirector(
                main_callback=execution_screen.update_report,
                tool_callback=execution_screen.update_tool_output
            )
            redirector.start_redirect()
            import threading 
            # 在函数开始处定义这些变量，确保它们在所有异常处理块中可用
            execution_completed = threading.Event()  # 使用 threading 模块
            timeout_timer = None
            
            try:
                # 开始执行任务
                execution_screen.update_report("开始执行安全分析任务...\n", False)
                
                # 导入必要的模块
                from main import execute_custom_workflow
                import sys
                
                # 添加调试信息
                execution_screen.update_log_output("正在初始化工作流程...")
                
                # 定义决策处理函数
                def decision_handler(decision_or_callback, report=None, stage=None, agent_name=None):
                    """处理决策请求
                    
                    参数:
                        decision_or_callback: 决策对象或回调函数
                        report: 报告内容（可选）
                        stage: 阶段（执行前/执行后）（可选）
                        agent_name: 角色名称（可选）
                    """
                    from PyQt5.QtCore import QTimer, QEventLoop
                    import threading
                    
                    # 添加调试信息
                    print(f"DEBUG: decision_handler被调用，参数类型: {type(decision_or_callback)}")
                    print(f"DEBUG: report参数: {'有值' if report else '无值'}")
                    print(f"DEBUG: stage参数: {stage}")
                    print(f"DEBUG: agent_name参数: {agent_name}")
                    
                    # 检查是否是回调函数而不是决策对象
                    if callable(decision_or_callback) and report is None:
                        # 这是一个回调函数，保存它
                        callback = decision_or_callback
                        print(f"DEBUG: 保存回调函数: {callback}")
                        
                        # 设置决策回调函数
                        execution_screen.current_decision_callback = callback
                        print(f"DEBUG: 已设置current_decision_callback")
                        
                        # 返回一个包装函数，确保参数正确传递
                        def wrapped_callback(decision, *args, **kwargs):
                            print(f"DEBUG: 包装回调被调用，决策: {decision}, 额外参数: {args}, {kwargs}")
                            try:
                                # 检查决策类型
                                if decision.get("status") == "feedback" and len(args) >= 3:
                                    # 对于建议类型的决策，需要传递额外的参数
                                    print(f"DEBUG: 调用原始回调，传递额外参数")
                                    return callback(decision, *args)
                                else:
                                    # 对于其他类型的决策，只传递决策对象
                                    print(f"DEBUG: 调用原始回调，只传递决策对象")
                                    return callback(decision)
                            except TypeError as e:
                                # 如果参数不匹配，尝试不同的调用方式
                                print(f"ERROR: 调用回调时参数错误: {str(e)}")
                                try:
                                    # 尝试只传递决策对象
                                    return callback(decision)
                                except Exception as e2:
                                    print(f"ERROR: 尝试只传递决策对象也失败: {str(e2)}")
                                    # 最后的尝试：返回默认决策
                                    return {"status": "approved", "feedback": "自动批准（回调错误）"}
                        
                        return wrapped_callback
                    
                    # 如果是决策对象，则处理决策
                    decision = decision_or_callback
                    callback = execution_screen.current_decision_callback
                    
                    # 确保reported显示在UI上
                    if report and stage and agent_name:
                        report_header = f"【{agent_name} - {stage}报告】"
                        formatted_report = f"\n{report_header}\n{'='*80}\n{report}\n{'='*80}\n"
                        
                        # 添加调试信息
                        print(f"DEBUG: 格式化后的报告长度: {len(formatted_report)}")
                        
                        # 直接调用update_report方法，确保reported显示
                        execution_screen.update_report(formatted_report, True)  # 修改为True，启用决策控件
                        print(f"DEBUG: 已调用update_report方法")
                    
                    # 强制启用决策控件
                    execution_screen.force_enable_decision_controls()
                    print(f"DEBUG: 已强制启用决策控件")
                    
                    # 强制处理事件，确保UI更新
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    # 记录日志
                    if stage and agent_name:
                        execution_screen.update_log_output(f"等待用户对 {agent_name} 的 {stage}报告 进行决策...")
                    
                    # 创建决策事件和结果容器
                    decision_event = threading.Event()
                    decision_result = [None]
                    
                    def on_decision(result):
                        print(f"DEBUG: on_decision被调用，结果: {result}")
                        decision_result[0] = result
                        decision_event.set()
                        # 调用原始回调
                        if callback:
                            try:
                                # 如果是建议类型的决策，需要传递额外的参数
                                if result.get("status") == "feedback" and report and stage and agent_name:
                                    print(f"DEBUG: 调用原始回调，传递额外参数")
                                    callback(result, report, stage, agent_name)
                                else:
                                    print(f"DEBUG: 调用原始回调，只传递决策对象")
                                    callback(result)
                            except TypeError as e:
                                # 如果参数不匹配，尝试不同的调用方式
                                print(f"ERROR: 调用回调时参数错误: {str(e)}")
                                try:
                                    # 尝试只传递决策对象
                                    callback(result)
                                except Exception as e2:
                                    print(f"ERROR: 尝试只传递决策对象也失败: {str(e2)}")
                            except Exception as e:
                                print(f"ERROR: 调用决策回调时出错: {str(e)}")
                                import traceback
                                print(traceback.format_exc())
                    
                    # 设置决策处理函数
                    execution_screen.on_decision = on_decision
                    
                    # 如果已经有决策，直接处理
                    if isinstance(decision, dict):
                        on_decision(decision)
                        return decision_result[0]
                    
                    # 等待决策事件
                    decision_event.wait()
                    return decision_result[0]
                
                # 添加超时处理
                execution_timeout = 300  # 5分钟超时
                
                def timeout_handler():
                    if not execution_completed.is_set():
                        execution_screen.update_report("\n警告: 任务执行超时，可能存在阻塞。请检查日志获取更多信息。\n", False)
                        execution_screen.update_log_output("任务执行超时，可能的原因：\n1. 网络请求超时\n2. LLM响应缓慢\n3. 程序逻辑死锁")
            
                timeout_timer = threading.Timer(execution_timeout, timeout_handler)
                timeout_timer.daemon = True
                timeout_timer.start()
                
                try:
                    # 执行自定义工作流程
                    execution_screen.update_log_output(f"开始执行工作流程，角色组: {group_name}")
                    execution_screen.update_current_role("准备中...")
                    
                    # 确保秘书角色正确初始化
                    execution_screen.update_log_output("初始化角色，包括秘书角色...")
                    
                    results = execute_custom_workflow(
                        group_name=group_name,
                        report_callback=execution_screen.update_report,
                        tool_callback=execution_screen.update_tool_output,
                        log_callback=execution_screen.update_log_output,
                        role_callback=execution_screen.update_current_role,
                        decision_callback=decision_handler  # 使用修改后的决策处理函数
                    )
                    
                    # 标记执行完成
                    execution_completed.set()
                    
                    # 输出结果
                    execution_screen.update_report("\n任务执行完成！\n", False)
                    for result in results:
                        execution_screen.update_report(f"\n{result}\n", False)
                    
                    # 更新任务状态
                    self.task_status_label.setText("状态: 已完成")
                    self.task_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                    
                    # 刷新任务列表
                    self.load_task_records()
                except Exception as inner_e:
                    execution_completed.set()
                    error_msg = f"执行工作流程时出错: {str(inner_e)}"
                    execution_screen.update_report(f"\n错误: {error_msg}\n", False)
                    execution_screen.update_log_output(f"异常详情:\n{traceback.format_exc()}")
                    # 添加更详细的错误信息
                    import sys
                    execution_screen.update_log_output(f"异常类型: {type(inner_e).__name__}")
                    execution_screen.update_log_output(f"Python版本: {sys.version}")
                finally:
                    # 取消超时计时器
                    if timeout_timer and timeout_timer.is_alive():
                        timeout_timer.cancel()
            
            except Exception as e:
                execution_screen.update_report(f"\n错误: {str(e)}\n", False)
                execution_screen.update_log_output(f"异常详情:\n{traceback.format_exc()}")
            finally:
                # 恢复标准输出
                redirector.stop_redirect()
        
        # 创建并启动线程
        import threading
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

    def on_decision_made(self, decision):
        """处理用户决策"""
        # 存储决策并通知等待决策的线程
        if hasattr(self, 'current_decision_callback') and self.current_decision_callback:
            self.current_decision_callback(decision)
            self.current_decision_callback = None

    def show_decision_dialog(self, report, stage, agent_name):
        """显示决策对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
        from PyQt5.QtCore import Qt
        
        print(f"DEBUG: show_decision_dialog被调用")
        
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
            print(f"DEBUG: 拒绝按钮被点击")
            if self.current_decision_callback:
                self.current_decision_callback({
                    "status": "rejected", 
                    "feedback": feedback_text.toPlainText()
                })
            dialog.accept()
        
        def on_approve():
            print(f"DEBUG: 批准按钮被点击")
            if self.current_decision_callback:
                self.current_decision_callback({
                    "status": "approved", 
                    "feedback": feedback_text.toPlainText()
                })
            dialog.accept()
        
        reject_btn.clicked.connect(on_reject)
        approve_btn.clicked.connect(on_approve)
        
        # 显示对话框
        print(f"DEBUG: 准备显示对话框")
        dialog.exec_()
        print(f"DEBUG: 对话框已关闭")



