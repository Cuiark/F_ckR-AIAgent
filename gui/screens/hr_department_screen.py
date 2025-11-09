# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
from typing import Dict, List
from datetime import datetime

class HRDepartmentScreen(ttk.Frame):
    """人事部门界面 - 负责Agent和角色组的智能创建"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conversation_history = []
        self.pending_agents = []  # 待创建的Agent列表
        self.pending_groups = []  # 待创建的角色组列表
        self.required_tools = []  # 需要的工具列表
        self.tool_warehouse = None  # 工具仓库引用
        
        # 创建界面
        self._create_widgets()
        
        # 初始化对话
        self._init_conversation()
        
    def set_tool_warehouse(self, tool_warehouse):
        """设置工具仓库引用"""
        self.tool_warehouse = tool_warehouse
        
    def _create_widgets(self):
        """创建现代化界面组件"""
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 页面标题区域
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🏢 人事部门", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, text="AI智能角色管理与团队构建", style="Subtitle.TLabel")
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # 主内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：对话区域卡片
        chat_card = ttk.Frame(content_frame, style="Card.TFrame")
        chat_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 对话卡片标题
        chat_header = ttk.Frame(chat_card)
        chat_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        chat_title = ttk.Label(chat_header, text="💬 智能对话助手", 
                              font=("Segoe UI", 12, "bold"))
        chat_title.pack(side=tk.LEFT)
        
        chat_status = ttk.Label(chat_header, text="🤖 在线", 
                               font=("Segoe UI", 10),
                               foreground="#10b981")
        chat_status.pack(side=tk.RIGHT)
        
        # 对话内容区域
        left_frame = ttk.Frame(chat_card)
        left_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # 对话历史显示
        self.chat_display = scrolledtext.ScrolledText(
            left_frame, 
            wrap=tk.WORD, 
            height=18, 
            state=tk.DISABLED,
            font=("Segoe UI", 10),
            bg="#ffffff",
            relief="flat",
            borderwidth=1
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 输入区域
        input_frame = ttk.Frame(left_frame)
        input_frame.pack(fill=tk.X)
        
        # 输入标签
        input_label = ttk.Label(input_frame, text="💭 输入您的需求:", 
                               font=("Segoe UI", 10, "bold"))
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 输入框和按钮容器
        input_container = ttk.Frame(input_frame)
        input_container.pack(fill=tk.X)
        
        self.user_input = tk.Text(input_container, height=3, wrap=tk.WORD,
                                 font=("Segoe UI", 10),
                                 relief="flat", borderwidth=1,
                                 bg="#ffffff")
        self.user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 按钮区域
        button_container = ttk.Frame(input_container)
        button_container.pack(side=tk.RIGHT, fill=tk.Y)
        
        send_button = ttk.Button(button_container, text="📤 发送", 
                                command=self._send_message,
                                style="Accent.TButton")
        send_button.pack(fill=tk.X, pady=(0, 5))
        
        clear_button = ttk.Button(button_container, text="🗑️ 清空", 
                                 command=lambda: self.user_input.delete(1.0, tk.END))
        clear_button.pack(fill=tk.X)
        
        # 绑定回车键
        self.user_input.bind("<Control-Return>", lambda e: self._send_message())
        
        # 右侧：任务面板
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=0)
        
        # Agent管理卡片
        agent_card = ttk.Frame(right_frame, style="Card.TFrame")
        agent_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Agent卡片标题
        agent_header = ttk.Frame(agent_card)
        agent_header.pack(fill=tk.X, padx=15, pady=(12, 8))
        
        agent_title = ttk.Label(agent_header, text="📋 待创建Agent", 
                               font=("Segoe UI", 11, "bold"))
        agent_title.pack(side=tk.LEFT)
        
        agent_count = ttk.Label(agent_header, text="0", 
                               font=("Segoe UI", 10),
                               foreground="#6b7280")
        agent_count.pack(side=tk.RIGHT)
        self.agent_count_label = agent_count
        
        # Agent列表
        agent_list_frame = ttk.Frame(agent_card)
        agent_list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.agent_listbox = tk.Listbox(agent_list_frame, height=8,
                                       font=("Segoe UI", 9),
                                       relief="flat", borderwidth=1,
                                       bg="#f8fafc",
                                       selectbackground="#3b82f6",
                                       selectforeground="white")
        self.agent_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Agent按钮区域
        agent_btn_frame = ttk.Frame(agent_card)
        agent_btn_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
        
        ttk.Button(agent_btn_frame, text="✅ 创建Agent", 
                  command=self._create_agents,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(agent_btn_frame, text="🗑️ 清空", 
                  command=self._clear_agents).pack(side=tk.RIGHT)
        
        # 角色组管理卡片
        group_card = ttk.Frame(right_frame, style="Card.TFrame")
        group_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 角色组卡片标题
        group_header = ttk.Frame(group_card)
        group_header.pack(fill=tk.X, padx=15, pady=(12, 8))
        
        group_title = ttk.Label(group_header, text="👥 待创建角色组", 
                               font=("Segoe UI", 11, "bold"))
        group_title.pack(side=tk.LEFT)
        
        group_count = ttk.Label(group_header, text="0", 
                               font=("Segoe UI", 10),
                               foreground="#6b7280")
        group_count.pack(side=tk.RIGHT)
        self.group_count_label = group_count
        
        # 角色组列表
        group_list_frame = ttk.Frame(group_card)
        group_list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.group_listbox = tk.Listbox(group_list_frame, height=6,
                                       font=("Segoe UI", 9),
                                       relief="flat", borderwidth=1,
                                       bg="#f8fafc",
                                       selectbackground="#3b82f6",
                                       selectforeground="white")
        self.group_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 角色组按钮区域
        group_btn_frame = ttk.Frame(group_card)
        group_btn_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
        
        ttk.Button(group_btn_frame, text="✅ 创建角色组", 
                  command=self._create_groups,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(group_btn_frame, text="🗑️ 清空", 
                  command=self._clear_groups).pack(side=tk.RIGHT)
        
        # 工具需求卡片
        tool_card = ttk.Frame(right_frame, style="Card.TFrame")
        tool_card.pack(fill=tk.BOTH, expand=True)
        
        # 工具卡片标题
        tool_header = ttk.Frame(tool_card)
        tool_header.pack(fill=tk.X, padx=15, pady=(12, 8))
        
        tool_title = ttk.Label(tool_header, text="🔧 工具需求", 
                              font=("Segoe UI", 11, "bold"))
        tool_title.pack(side=tk.LEFT)
        
        tool_count = ttk.Label(tool_header, text="0", 
                              font=("Segoe UI", 10),
                              foreground="#6b7280")
        tool_count.pack(side=tk.RIGHT)
        self.tool_count_label = tool_count
        
        # 工具列表
        tool_list_frame = ttk.Frame(tool_card)
        tool_list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.tools_listbox = tk.Listbox(tool_list_frame, height=6,
                                       font=("Segoe UI", 9),
                                       relief="flat", borderwidth=1,
                                       bg="#f8fafc",
                                       selectbackground="#3b82f6",
                                       selectforeground="white")
        self.tools_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 工具按钮区域
        tools_btn_frame = ttk.Frame(tool_card)
        tools_btn_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
        
        ttk.Button(tools_btn_frame, text="🚀 请求工具", 
                  command=self._request_tools,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(tools_btn_frame, text="🗑️ 清空", 
                  command=self._clear_tools).pack(side=tk.RIGHT)
        
    def _init_conversation(self):
        """初始化对话"""
        welcome_msg = """🤖 您好！我是人事部门的AI助手。

我可以帮助您：
• 根据安全任务需求创建专业的Agent角色
• 组合多个Agent形成高效的角色组
• 分析所需工具并生成工具清单
• 提供最佳的团队配置建议

请描述您的安全任务需求，我将为您量身定制最适合的AI团队！

💡 示例："我需要一个专门处理网络入侵检测的团队"""
        
        self._add_message("AI助手", welcome_msg, "system")
        
    def _add_message(self, sender, message, msg_type="user"):
        """添加消息到对话历史"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.config(state=tk.NORMAL)
        
        # 根据消息类型设置颜色
        if msg_type == "system":
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}:\n", "system_sender")
            self.chat_display.insert(tk.END, f"{message}\n\n", "system_msg")
        elif msg_type == "user":
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}:\n", "user_sender")
            self.chat_display.insert(tk.END, f"{message}\n\n", "user_msg")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}:\n", "ai_sender")
            self.chat_display.insert(tk.END, f"{message}\n\n", "ai_msg")
        
        # 配置文本样式
        self.chat_display.tag_config("system_sender", foreground="#2c3e50", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("system_msg", foreground="#34495e")
        self.chat_display.tag_config("user_sender", foreground="#27ae60", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("user_msg", foreground="#2c3e50")
        self.chat_display.tag_config("ai_sender", foreground="#3498db", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("ai_msg", foreground="#2c3e50")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
        # 保存到历史记录
        self.conversation_history.append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message,
            "type": msg_type
        })
        
    def _send_message(self):
        """发送用户消息"""
        user_message = self.user_input.get("1.0", tk.END).strip()
        if not user_message:
            return
            
        # 显示用户消息
        self._add_message("您", user_message, "user")
        
        # 清空输入框
        self.user_input.delete("1.0", tk.END)
        
        # 在新线程中处理AI响应
        threading.Thread(target=self._process_ai_response, args=(user_message,), daemon=True).start()
        
    def _process_ai_response(self, user_message):
        """处理AI响应（模拟）"""
        # 显示思考状态
        self.after(100, lambda: self._add_message("AI助手", "🤔 正在分析您的需求...", "ai"))
        
        # 模拟处理时间
        import time
        time.sleep(2)
        
        # 分析用户需求并生成响应
        response = self._analyze_user_request(user_message)
        
        # 显示AI响应
        self.after(0, lambda: self._add_message("AI助手", response, "ai"))
        
    def _analyze_user_request(self, message):
        """智能分析用户请求并生成响应"""
        # 使用更智能的需求分析
        security_needs = self._extract_security_needs(message)
        threat_level = self._assess_threat_level(message)
        scope = self._determine_scope(message)
        
        # 基于分析结果生成智能响应
        return self._generate_intelligent_response(message, security_needs, threat_level, scope)
    
    def _extract_security_needs(self, message):
        """提取安全需求"""
        message_lower = message.lower()
        needs = []
        
        # 网络安全需求
        network_keywords = ["网络", "入侵", "防火墙", "连接", "流量", "ip", "端口", "攻击"]
        if any(keyword in message_lower for keyword in network_keywords):
            needs.append("network")
            
        # 进程安全需求
        process_keywords = ["进程", "恶意软件", "病毒", "木马", "程序", "应用", "exe", "运行"]
        if any(keyword in message_lower for keyword in process_keywords):
            needs.append("process")
            
        # 日志分析需求
        log_keywords = ["日志", "审计", "监控", "记录", "事件", "告警", "异常"]
        if any(keyword in message_lower for keyword in log_keywords):
            needs.append("log")
            
        # 服务安全需求
        service_keywords = ["服务", "系统", "启动", "停止", "配置", "管理"]
        if any(keyword in message_lower for keyword in service_keywords):
            needs.append("service")
            
        # 文件安全需求
        file_keywords = ["文件", "目录", "文档", "数据", "备份", "加密", "权限", "完整性", "保护"]
        if any(keyword in message_lower for keyword in file_keywords):
            needs.append("file")
            
        # 团队协作需求
        team_keywords = ["团队", "协作", "配合", "统筹", "管理", "指挥"]
        if any(keyword in message_lower for keyword in team_keywords):
            needs.append("team")
            
        return needs if needs else ["general"]
    
    def _assess_threat_level(self, message):
        """评估威胁级别"""
        message_lower = message.lower()
        
        high_threat_keywords = ["攻击", "入侵", "恶意", "病毒", "木马", "泄露", "破坏", "紧急"]
        medium_threat_keywords = ["异常", "可疑", "风险", "威胁", "安全"]
        
        if any(keyword in message_lower for keyword in high_threat_keywords):
            return "high"
        elif any(keyword in message_lower for keyword in medium_threat_keywords):
            return "medium"
        else:
            return "low"
    
    def _determine_scope(self, message):
        """确定安全范围"""
        message_lower = message.lower()
        
        if "全面" in message_lower or "整体" in message_lower or "系统" in message_lower:
            return "comprehensive"
        elif "实时" in message_lower or "监控" in message_lower:
            return "realtime"
        elif "定期" in message_lower or "检查" in message_lower:
            return "periodic"
        else:
            return "targeted"
    
    def _generate_intelligent_response(self, message, security_needs, threat_level, scope):
        """生成智能响应"""
        # 如果是多重需求，生成综合方案
        if len(security_needs) > 1:
            return self._generate_comprehensive_security_response(message, security_needs, threat_level, scope)
        
        # 单一需求处理
        need = security_needs[0]
        if need == "network":
            return self._generate_adaptive_network_response(threat_level, scope)
        elif need == "process":
            return self._generate_adaptive_process_response(threat_level, scope)
        elif need == "log":
            return self._generate_adaptive_log_response(threat_level, scope)
        elif need == "service":
            return self._generate_adaptive_service_response(threat_level, scope)
        elif need == "file":
            return self._generate_adaptive_file_response(threat_level, scope)
        elif need == "team":
            return self._generate_adaptive_team_response(threat_level, scope)
        else:
            return self._generate_intelligent_general_response(message)
            
    def _generate_network_security_response(self):
        """生成网络安全相关响应"""
        # 添加待创建的Agent
        agents = [
            {"id": "network_monitor", "name": "网络监控专家", "role": "网络流量监控与分析"},
            {"id": "intrusion_detector", "name": "入侵检测专家", "role": "入侵行为识别与响应"},
            {"id": "firewall_manager", "name": "防火墙管理员", "role": "防火墙规则配置与管理"}
        ]
        
        # 添加角色组
        group = {"id": "network_security_team", "name": "网络安全团队", "agents": [a["id"] for a in agents]}
        
        # 添加所需工具
        tools = [
            "GetNetworkConnections - 获取网络连接信息",
            "AnalyzeNetworkTraffic - 分析网络流量",
            "DetectSuspiciousConnections - 检测可疑连接",
            "BlockSuspiciousIP - 阻止可疑IP地址",
            "GenerateNetworkReport - 生成网络安全报告"
        ]
        
        self._update_pending_lists(agents, [group], tools)
        
        return """🔍 基于您的网络安全需求，我为您设计了以下方案：

👥 **推荐团队配置：**
• 网络监控专家 - 实时监控网络流量
• 入侵检测专家 - 识别异常行为模式
• 防火墙管理员 - 动态调整安全策略

🔧 **所需工具清单：**
• 网络连接获取工具
• 流量分析工具
• 可疑连接检测工具
• IP阻断工具
• 报告生成工具

✅ 已将相关Agent和工具添加到待创建列表，您可以点击右侧按钮进行创建。

💡 **建议：** 这个团队配置可以实现7x24小时的网络安全监控，自动识别和响应网络威胁。"""
        
    def _generate_process_security_response(self):
        """生成进程安全相关响应"""
        agents = [
            {"id": "process_monitor", "name": "进程监控专家", "role": "系统进程监控与分析"},
            {"id": "malware_detector", "name": "恶意软件检测专家", "role": "恶意进程识别与处理"}
        ]
        
        group = {"id": "process_security_team", "name": "进程安全团队", "agents": [a["id"] for a in agents]}
        
        tools = [
            "GetProcessDetails - 获取进程详细信息",
            "AnalyzeProcessBehavior - 分析进程行为",
            "DetectMaliciousProcess - 检测恶意进程",
            "TerminateProcess - 终止危险进程",
            "GenerateProcessReport - 生成进程安全报告"
        ]
        
        self._update_pending_lists(agents, [group], tools)
        
        return """🛡️ 针对进程安全需求，我为您配置了专业团队：

👥 **团队成员：**
• 进程监控专家 - 持续监控系统进程
• 恶意软件检测专家 - 识别和处理恶意程序

🔧 **工具配置：**
• 进程信息获取
• 行为分析引擎
• 恶意进程检测
• 进程终止控制
• 安全报告生成

✅ 团队和工具已添加到创建列表。

💡 **优势：** 可以实时发现异常进程，快速响应恶意软件威胁。"""
        
    def _generate_log_analysis_response(self):
        """生成日志分析相关响应"""
        agents = [
            {"id": "log_collector", "name": "日志收集专家", "role": "系统日志收集与整理"},
            {"id": "log_analyzer", "name": "日志分析专家", "role": "日志模式分析与威胁识别"}
        ]
        
        group = {"id": "log_analysis_team", "name": "日志分析团队", "agents": [a["id"] for a in agents]}
        
        tools = [
            "GetWindowsLogs - 获取Windows事件日志",
            "AnalyzeSecurityLogs - 分析安全日志",
            "CorrelateEvents - 关联事件分析",
            "DetectAnomalies - 检测异常模式",
            "GenerateLogReport - 生成日志分析报告"
        ]
        
        self._update_pending_lists(agents, [group], tools)
        
        return """📊 日志分析团队配置方案：

👥 **专业团队：**
• 日志收集专家 - 全面收集系统日志
• 日志分析专家 - 深度分析安全事件

🔧 **分析工具：**
• Windows事件日志获取
• 安全日志分析引擎
• 事件关联分析
• 异常模式检测
• 专业报告生成

✅ 已准备创建相关组件。

💡 **特色：** 通过智能日志分析，可以发现隐蔽的安全威胁和攻击模式。"""
        
    def _generate_service_security_response(self):
        """生成服务安全相关响应"""
        agents = [
            {"id": "service_monitor", "name": "服务监控专家", "role": "系统服务监控与管理"},
            {"id": "service_analyzer", "name": "服务安全分析师", "role": "服务安全性评估"}
        ]
        
        group = {"id": "service_security_team", "name": "服务安全团队", "agents": [a["id"] for a in agents]}
        
        tools = [
            "GetServices - 获取系统服务列表",
            "AnalyzeServiceSecurity - 分析服务安全性",
            "CheckServiceIntegrity - 检查服务完整性",
            "ManageServiceStatus - 管理服务状态",
            "GenerateServiceReport - 生成服务安全报告"
        ]
        
        self._update_pending_lists(agents, [group], tools)
        
        return """⚙️ 服务安全管理方案：

👥 **管理团队：**
• 服务监控专家 - 监控服务运行状态
• 服务安全分析师 - 评估服务安全风险

🔧 **管理工具：**
• 服务列表获取
• 安全性分析
• 完整性检查
• 状态管理
• 报告生成

✅ 服务安全团队配置完成。

💡 **价值：** 确保关键系统服务的安全运行，防止服务被恶意利用。"""
        
    def _generate_file_security_response(self):
        """生成文件安全相关响应"""
        agents = [
            {"id": "file_monitor", "name": "文件监控专家", "role": "文件系统实时监控与异常检测"},
            {"id": "file_integrity_checker", "name": "文件完整性检查员", "role": "文件完整性验证与篡改检测"},
            {"id": "file_permission_manager", "name": "文件权限管理员", "role": "文件访问权限管理与控制"},
            {"id": "file_backup_specialist", "name": "文件备份专家", "role": "重要文件备份与恢复管理"},
            {"id": "file_encryption_expert", "name": "文件加密专家", "role": "敏感文件加密与解密管理"}
        ]
        
        group = {"id": "file_security_team", "name": "文件安全团队", "agents": [a["id"] for a in agents]}
        
        tools = [
            "MonitorFileChanges - 监控文件变化",
            "CheckFileIntegrity - 检查文件完整性",
            "VerifyFileHash - 验证文件哈希值",
            "ManageFilePermissions - 管理文件权限",
            "BackupCriticalFiles - 备份关键文件",
            "EncryptSensitiveFiles - 加密敏感文件",
            "DecryptFiles - 解密文件",
            "RestoreFromBackup - 从备份恢复文件",
            "ScanForMaliciousFiles - 扫描恶意文件",
            "QuarantineFiles - 隔离可疑文件",
            "GenerateFileSecurityReport - 生成文件安全报告"
        ]
        
        self._update_pending_lists(agents, [group], tools)
        
        return """🗂️ 文件安全保护方案：
 
 👥 **专业团队：**
 • 文件监控专家 - 实时监控文件系统变化
 • 文件完整性检查员 - 验证文件完整性，检测篡改
 • 文件权限管理员 - 管理文件访问权限
 • 文件备份专家 - 重要文件备份与恢复
 • 文件加密专家 - 敏感文件加密保护
 
 🔧 **安全工具：**
 • 文件变化监控
 • 完整性验证
 • 哈希值校验
 • 权限管理
 • 自动备份
 • 文件加密/解密
 • 恶意文件扫描
 • 文件隔离
 • 备份恢复
 • 安全报告生成
 
 ✅ 文件安全团队已配置完成。
 
 💡 **核心优势：** 
 • 🛡️ 全方位文件保护 - 从监控到加密的完整防护链
 • 🔍 实时威胁检测 - 及时发现文件异常和恶意行为
 • 📋 权限精细管控 - 确保只有授权用户可以访问敏感文件
 • 💾 智能备份策略 - 自动备份重要文件，支持快速恢复
 • 🔐 强化加密保护 - 对敏感文件进行加密，防止数据泄露
 
 🎯 **特别适用于：**
 • E:/test/ 等重要目录的安全保护
 • 敏感文档的完整性监控
 • 防止文件被恶意篡改或删除
 • 建立完善的文件安全管理体系"""
    
    def _generate_comprehensive_security_response(self, message, security_needs, threat_level, scope):
        """生成综合安全方案"""
        agents = []
        tools = []
        
        # 根据需求组合不同领域的专家
        if "network" in security_needs:
            agents.extend([
                {"id": "network_specialist", "name": "网络安全专家", "role": "网络威胁检测与防护"},
                {"id": "traffic_analyst", "name": "流量分析师", "role": "网络流量深度分析"}
            ])
            tools.extend(["NetworkMonitoring", "TrafficAnalysis", "IntrusionDetection"])
            
        if "process" in security_needs:
            agents.extend([
                {"id": "process_guardian", "name": "进程守护者", "role": "恶意进程实时监控"},
                {"id": "malware_hunter", "name": "恶意软件猎手", "role": "高级威胁检测"}
            ])
            tools.extend(["ProcessMonitoring", "MalwareDetection", "BehaviorAnalysis"])
            
        if "file" in security_needs:
            agents.extend([
                {"id": "file_guardian", "name": "文件守护者", "role": "文件完整性保护"},
                {"id": "data_protector", "name": "数据保护专家", "role": "敏感数据安全管理"}
            ])
            tools.extend(["FileIntegrityCheck", "DataEncryption", "AccessControl"])
            
        if "log" in security_needs:
            agents.append({"id": "log_detective", "name": "日志侦探", "role": "安全事件追踪分析"})
            tools.extend(["LogAnalysis", "EventCorrelation", "ThreatIntelligence"])
            
        # 添加协调角色
        agents.append({"id": "security_commander", "name": "安全指挥官", "role": "多领域安全统筹指挥"})
        
        group = {"id": "integrated_security_team", "name": "综合安全防护团队", "agents": [a["id"] for a in agents]}
        
        threat_desc = {"high": "🚨 高威胁", "medium": "⚠️ 中等威胁", "low": "🔍 预防性"}
        scope_desc = {"comprehensive": "全面防护", "realtime": "实时监控", "periodic": "定期检查", "targeted": "精准防护"}
        
        self._update_pending_lists(agents, [group], tools)
        
        return f"""🛡️ 智能综合安全方案

📊 **需求分析结果：**
• 安全领域：{', '.join(security_needs)}
• 威胁级别：{threat_desc.get(threat_level, '未知')}
• 防护范围：{scope_desc.get(scope, '标准')}

👥 **智能团队配置：**
{chr(10).join([f'• {agent["name"]} - {agent["role"]}' for agent in agents])}

🔧 **工具矩阵：**
{', '.join(tools)}

✅ 已为您量身定制综合安全团队。

💡 **方案优势：**
• 🎯 多维度威胁覆盖
• 🔄 跨领域协同作战
• 📈 智能威胁评估
• ⚡ 快速响应机制"""
        
    def _generate_adaptive_network_response(self, threat_level, scope):
        """生成自适应网络安全响应"""
        if threat_level == "high":
            agents = [
                {"id": "emergency_network_responder", "name": "网络应急响应专家", "role": "紧急网络威胁处置"},
                {"id": "advanced_threat_hunter", "name": "高级威胁猎手", "role": "APT攻击检测与分析"},
                {"id": "network_forensics_expert", "name": "网络取证专家", "role": "攻击路径还原分析"}
            ]
            tools = ["EmergencyResponse", "ThreatHunting", "NetworkForensics", "RealTimeBlocking"]
        elif threat_level == "medium":
            agents = [
                {"id": "network_analyst", "name": "网络分析师", "role": "网络异常检测分析"},
                {"id": "security_monitor", "name": "安全监控员", "role": "持续安全监控"}
            ]
            tools = ["AnomalyDetection", "ContinuousMonitoring", "AlertManagement"]
        else:
            agents = [
                {"id": "network_observer", "name": "网络观察员", "role": "基础网络监控"}
            ]
            tools = ["BasicMonitoring", "PeriodicScanning"]
            
        group = {"id": "adaptive_network_team", "name": "自适应网络安全团队", "agents": [a["id"] for a in agents]}
        self._update_pending_lists(agents, [group], tools)
        
        return f"""🌐 自适应网络安全方案

📊 **智能配置：**
• 威胁级别：{threat_level.upper()}
• 防护范围：{scope}

👥 **精准团队：**
{chr(10).join([f'• {agent["name"]} - {agent["role"]}' for agent in agents])}

🔧 **匹配工具：**
{', '.join(tools)}

✅ 团队已根据威胁级别智能调整。"""
        
    def _generate_adaptive_file_response(self, threat_level, scope):
        """生成自适应文件安全响应"""
        base_agents = [
            {"id": "file_monitor", "name": "文件监控专家", "role": "文件系统实时监控"}
        ]
        
        if threat_level == "high":
            base_agents.extend([
                {"id": "data_recovery_specialist", "name": "数据恢复专家", "role": "紧急数据恢复"},
                {"id": "encryption_expert", "name": "加密防护专家", "role": "高强度数据加密"},
                {"id": "forensic_analyst", "name": "数字取证分析师", "role": "文件篡改取证"}
            ])
            tools = ["EmergencyBackup", "AdvancedEncryption", "ForensicAnalysis", "RealTimeProtection"]
        elif threat_level == "medium":
            base_agents.extend([
                {"id": "integrity_checker", "name": "完整性检查员", "role": "文件完整性验证"},
                {"id": "backup_manager", "name": "备份管理员", "role": "智能备份管理"}
            ])
            tools = ["IntegrityCheck", "SmartBackup", "AccessMonitoring"]
        else:
            base_agents.append({"id": "permission_manager", "name": "权限管理员", "role": "基础权限管理"})
            tools = ["BasicMonitoring", "PermissionControl"]
            
        group = {"id": "adaptive_file_team", "name": "自适应文件安全团队", "agents": [a["id"] for a in base_agents]}
        self._update_pending_lists(base_agents, [group], tools)
        
        return f"""🗂️ 自适应文件安全方案

📊 **智能评估：**
• 威胁级别：{threat_level.upper()}
• 保护范围：{scope}

👥 **专业团队：**
{chr(10).join([f'• {agent["name"]} - {agent["role"]}' for agent in base_agents])}

🔧 **安全工具：**
{', '.join(tools)}

✅ 已根据威胁情况优化文件保护策略。

🎯 **特别适用于 E:/test/ 目录的智能保护**"""
        
    def _generate_adaptive_process_response(self, threat_level, scope):
        """生成自适应进程安全响应"""
        if threat_level == "high":
            agents = [
                {"id": "malware_terminator", "name": "恶意软件终结者", "role": "紧急恶意进程处置"},
                {"id": "behavior_analyst", "name": "行为分析专家", "role": "进程行为深度分析"},
                {"id": "system_defender", "name": "系统防护专家", "role": "系统完整性保护"}
            ]
            tools = ["EmergencyTermination", "BehaviorAnalysis", "SystemProtection", "QuarantineProcess"]
        elif threat_level == "medium":
            agents = [
                {"id": "process_monitor", "name": "进程监控员", "role": "进程活动监控"},
                {"id": "anomaly_detector", "name": "异常检测员", "role": "进程异常识别"}
            ]
            tools = ["ProcessMonitoring", "AnomalyDetection", "AlertGeneration"]
        else:
            agents = [
                {"id": "basic_monitor", "name": "基础监控员", "role": "基础进程监控"}
            ]
            tools = ["BasicProcessScan", "PeriodicCheck"]
            
        group = {"id": "adaptive_process_team", "name": "自适应进程安全团队", "agents": [a["id"] for a in agents]}
        self._update_pending_lists(agents, [group], tools)
        
        return f"""⚙️ 自适应进程安全方案

📊 **智能配置：**
• 威胁级别：{threat_level.upper()}
• 监控范围：{scope}

👥 **专业团队：**
{chr(10).join([f'• {agent["name"]} - {agent["role"]}' for agent in agents])}

🔧 **安全工具：**
{', '.join(tools)}

✅ 进程安全策略已智能优化。"""
        
    def _generate_adaptive_log_response(self, threat_level, scope):
        """生成自适应日志分析响应"""
        if threat_level == "high":
            agents = [
                {"id": "incident_investigator", "name": "事件调查专家", "role": "安全事件深度调查"},
                {"id": "threat_correlator", "name": "威胁关联分析师", "role": "多源威胁关联分析"},
                {"id": "forensic_logger", "name": "取证日志专家", "role": "数字取证日志分析"}
            ]
            tools = ["IncidentInvestigation", "ThreatCorrelation", "ForensicAnalysis", "RealTimeAlerts"]
        elif threat_level == "medium":
            agents = [
                {"id": "log_analyst", "name": "日志分析师", "role": "日志模式分析"},
                {"id": "event_correlator", "name": "事件关联员", "role": "事件关联分析"}
            ]
            tools = ["LogAnalysis", "EventCorrelation", "PatternDetection"]
        else:
            agents = [
                {"id": "log_collector", "name": "日志收集员", "role": "基础日志收集"}
            ]
            tools = ["BasicLogCollection", "SimpleReporting"]
            
        group = {"id": "adaptive_log_team", "name": "自适应日志分析团队", "agents": [a["id"] for a in agents]}
        self._update_pending_lists(agents, [group], tools)
        
        return f"""📊 自适应日志分析方案

📊 **智能配置：**
• 威胁级别：{threat_level.upper()}
• 分析范围：{scope}

👥 **专业团队：**
{chr(10).join([f'• {agent["name"]} - {agent["role"]}' for agent in agents])}

🔧 **分析工具：**
{', '.join(tools)}

✅ 日志分析策略已智能调整。"""
        
    def _generate_adaptive_service_response(self, threat_level, scope):
        """生成自适应服务安全响应"""
        if threat_level == "high":
            agents = [
                {"id": "service_guardian", "name": "服务守护者", "role": "关键服务安全防护"},
                {"id": "vulnerability_scanner", "name": "漏洞扫描专家", "role": "服务漏洞深度扫描"},
                {"id": "service_hardener", "name": "服务加固专家", "role": "服务安全加固"}
            ]
            tools = ["ServiceProtection", "VulnerabilityScanning", "SecurityHardening", "ServiceIsolation"]
        elif threat_level == "medium":
            agents = [
                {"id": "service_monitor", "name": "服务监控员", "role": "服务状态监控"},
                {"id": "config_auditor", "name": "配置审计员", "role": "服务配置审计"}
            ]
            tools = ["ServiceMonitoring", "ConfigurationAudit", "ComplianceCheck"]
        else:
            agents = [
                {"id": "service_observer", "name": "服务观察员", "role": "基础服务监控"}
            ]
            tools = ["BasicServiceCheck", "StatusReporting"]
            
        group = {"id": "adaptive_service_team", "name": "自适应服务安全团队", "agents": [a["id"] for a in agents]}
        self._update_pending_lists(agents, [group], tools)
        
        return f"""⚙️ 自适应服务安全方案

📊 **智能配置：**
• 威胁级别：{threat_level.upper()}
• 管理范围：{scope}

👥 **专业团队：**
{chr(10).join([f'• {agent["name"]} - {agent["role"]}' for agent in agents])}

🔧 **管理工具：**
{', '.join(tools)}

✅ 服务安全策略已智能优化。"""
        
    def _generate_adaptive_team_response(self, threat_level, scope):
        """生成自适应团队协作响应"""
        if threat_level == "high":
            agents = [
                {"id": "crisis_commander", "name": "危机指挥官", "role": "紧急事件统一指挥"},
                {"id": "tactical_coordinator", "name": "战术协调员", "role": "多团队战术协调"},
                {"id": "decision_accelerator", "name": "决策加速器", "role": "快速决策支持"}
            ]
            tools = ["CrisisManagement", "TacticalCoordination", "RapidDecision", "EmergencyProtocol"]
        elif threat_level == "medium":
            agents = [
                {"id": "team_coordinator", "name": "团队协调员", "role": "跨部门协调管理"},
                {"id": "workflow_optimizer", "name": "流程优化师", "role": "工作流程优化"}
            ]
            tools = ["TeamCoordination", "WorkflowOptimization", "ProgressTracking"]
        else:
            agents = [
                {"id": "basic_coordinator", "name": "基础协调员", "role": "基础团队协调"}
            ]
            tools = ["BasicCoordination", "SimpleReporting"]
            
        group = {"id": "adaptive_coordination_team", "name": "自适应协调团队", "agents": [a["id"] for a in agents]}
        self._update_pending_lists(agents, [group], tools)
        
        return f"""🎯 自适应团队协作方案

📊 **智能配置：**
• 威胁级别：{threat_level.upper()}
• 协作范围：{scope}

👥 **指挥团队：**
{chr(10).join([f'• {agent["name"]} - {agent["role"]}' for agent in agents])}

🔧 **协调工具：**
{', '.join(tools)}

✅ 团队协作策略已智能调整。"""
        
    def _generate_intelligent_general_response(self, message):
        """生成智能通用响应"""
        return f"""🤖 智能安全顾问分析

📝 **您的需求：** "{message}"

🧠 **AI分析建议：**
我正在使用先进的语义分析来理解您的安全需求。为了提供最精准的解决方案，请考虑以下几个维度：

🎯 **安全目标明确化：**
• 您最担心的安全威胁是什么？
• 需要保护的核心资产有哪些？
• 期望的安全防护强度如何？

⚡ **响应速度要求：**
• 需要实时监控还是定期检查？
• 发现威胁后的响应时间要求？

🔧 **技术偏好：**
• 倾向于自动化处理还是人工干预？
• 对误报的容忍度如何？

💡 **智能建议：**
基于您的描述，我推荐从以下方面入手：
• 建立基础安全监控体系
• 配置适度的自动化响应
• 设置分层防护机制

请提供更多具体信息，我将为您设计最适合的智能安全方案！"""
        
    def _generate_team_coordination_response(self):
        """生成团队协作相关响应"""
        agents = [
            {"id": "coordinator", "name": "安全协调员", "role": "统筹安全响应流程"},
            {"id": "decision_maker", "name": "决策分析师", "role": "安全决策支持"}
        ]
        
        group = {"id": "coordination_team", "name": "协调指挥团队", "agents": [a["id"] for a in agents]}
        
        tools = [
            "CoordinateResponse - 协调响应流程",
            "PrioritizeTasks - 任务优先级排序",
            "GenerateActionPlan - 生成行动计划",
            "MonitorProgress - 监控执行进度",
            "GenerateCoordinationReport - 生成协调报告"
        ]
        
        self._update_pending_lists(agents, [group], tools)
        
        return """🎯 团队协调指挥方案：

👥 **指挥团队：**
• 安全协调员 - 统筹各部门协作
• 决策分析师 - 提供决策支持

🔧 **协调工具：**
• 响应流程协调
• 任务优先级管理
• 行动计划生成
• 进度监控
• 协调报告

✅ 指挥协调体系已配置。

💡 **核心：** 实现各安全团队的高效协作，确保应急响应的统一指挥。"""
        
    def _generate_general_response(self, message):
        """生成通用响应"""
        return f"""🤔 我理解您提到了："{message}"

为了为您提供最精准的团队配置方案，请告诉我更多细节：

🎯 **请明确您的需求：**
• 主要关注哪个安全领域？（网络/进程/日志/服务/文件）
• 期望的响应速度？（实时/定期/按需）
• 团队规模偏好？（精简/标准/全面）
• 特殊要求？（自动化程度/报告格式等）

💡 **常见场景示例：**
• "我需要监控网络入侵"
• "帮我检测恶意进程"
• "分析系统日志中的异常"
• "管理系统服务安全"
• "保护E:/test/目录下的文件安全"
• "监控文件完整性和权限变化"
• "建立文件备份和加密保护"
• "建立完整的安全响应团队"

请提供更具体的描述，我将为您量身定制最适合的AI安全团队！"""
        
    def _update_pending_lists(self, agents, groups, tools):
        """更新待创建列表"""
        # 更新Agent列表
        for agent in agents:
            if agent not in self.pending_agents:
                self.pending_agents.append(agent)
                self.after(0, lambda a=agent: self.agent_listbox.insert(tk.END, f"{a['name']} ({a['role']})"))
        
        # 更新角色组列表
        for group in groups:
            if group not in self.pending_groups:
                self.pending_groups.append(group)
                self.after(0, lambda g=group: self.group_listbox.insert(tk.END, f"{g['name']} ({len(g['agents'])}个成员)"))
        
        # 更新工具列表
        for tool in tools:
            if tool not in self.required_tools:
                self.required_tools.append(tool)
                self.after(0, lambda t=tool: self.tools_listbox.insert(tk.END, t))
                
    def _create_agents(self):
        """创建Agent"""
        if not self.pending_agents:
            messagebox.showwarning("提示", "没有待创建的Agent")
            return
            
        try:
            # 加载现有配置
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      "config", "json", "agents_config.json")
            
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    agents_config = json.load(f)
            else:
                agents_config = {"default_group": {}}
            
            # 添加新Agent
            for agent in self.pending_agents:
                agents_config["default_group"][agent["id"]] = {
                    "role": agent["name"],
                    "goal": agent["role"],
                    "backstory": f"你是一名专业的{agent['name']}，专门负责{agent['role']}相关的安全任务。",
                    "tools": [],  # 工具列表暂时为空，需要后续配置
                    "department": "hr_created"  # 标记为人事部门创建
                }
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(agents_config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"已成功创建 {len(self.pending_agents)} 个Agent")
            self._clear_agents()
            
        except Exception as e:
            messagebox.showerror("错误", f"创建Agent失败：{str(e)}")
            
    def _create_groups(self):
        """创建角色组"""
        if not self.pending_groups:
            messagebox.showwarning("提示", "没有待创建的角色组")
            return
            
        try:
            # 这里可以扩展角色组的创建逻辑
            group_info = "\n".join([f"• {g['name']}: {len(g['agents'])}个成员" for g in self.pending_groups])
            messagebox.showinfo("角色组创建", f"以下角色组配置已准备就绪：\n\n{group_info}\n\n请在角色组管理界面中完成最终配置。")
            self._clear_groups()
            
        except Exception as e:
            messagebox.showerror("错误", f"创建角色组失败：{str(e)}")
            
    def _request_tools(self):
        """请求工具（发送到工具仓库）"""
        if self.required_tools:
            if self.tool_warehouse:
                # 发送工具请求到工具仓库
                self.tool_warehouse.receive_tool_request(self.required_tools.copy())
                messagebox.showinfo("提示", f"已向工具仓库发送 {len(self.required_tools)} 个工具请求")
                
                # 添加系统消息
                self._add_message("系统", f"📤 已向工具仓库发送 {len(self.required_tools)} 个工具请求", "system")
                
                self.required_tools.clear()
                self.tools_listbox.delete(0, tk.END)
            else:
                messagebox.showerror("错误", "工具仓库连接失败")
        else:
            messagebox.showwarning("提示", "没有待请求的工具")
            
    def _clear_agents(self):
        """清空Agent列表"""
        self.pending_agents.clear()
        self.agent_listbox.delete(0, tk.END)
        
    def _clear_groups(self):
        """清空角色组列表"""
        self.pending_groups.clear()
        self.group_listbox.delete(0, tk.END)
        
    def _clear_tools(self):
        """清空工具列表"""
        self.required_tools.clear()
        self.tools_listbox.delete(0, tk.END)