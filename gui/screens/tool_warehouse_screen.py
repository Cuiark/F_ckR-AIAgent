# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
from typing import Dict, List
from datetime import datetime

class ToolWarehouseScreen(ttk.Frame):
    """工具仓库界面 - 负责AI辅助工具创建"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conversation_history = []
        self.tool_requests = []  # 来自人事部门的工具请求
        self.generated_tools = []  # 生成的工具代码
        
        # 创建界面
        self._create_widgets()
        
        # 初始化对话
        self._init_conversation()
        
    def _create_widgets(self):
        """创建现代化界面组件"""
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 页面标题区域
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🔧 工具仓库", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, text="AI智能工具生成与管理平台", style="Subtitle.TLabel")
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # 主内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分：对话区域卡片
        chat_card = ttk.Frame(content_frame, style="Card.TFrame")
        chat_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 对话卡片标题
        chat_header = ttk.Frame(chat_card)
        chat_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        chat_title = ttk.Label(chat_header, text="💬 AI工具设计师", 
                              font=("Segoe UI", 12, "bold"))
        chat_title.pack(side=tk.LEFT)
        
        chat_status = ttk.Label(chat_header, text="🤖 就绪", 
                               font=("Segoe UI", 10),
                               foreground="#10b981")
        chat_status.pack(side=tk.RIGHT)
        
        # 对话内容区域
        top_frame = ttk.Frame(chat_card)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # 创建左右分栏
        chat_frame = ttk.Frame(top_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：对话历史
        left_chat_frame = ttk.Frame(chat_frame)
        left_chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 对话历史标题
        history_header = ttk.Frame(left_chat_frame)
        history_header.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(history_header, text="💭 对话历史", 
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        # 对话显示区域
        self.chat_display = scrolledtext.ScrolledText(
            left_chat_frame, 
            wrap=tk.WORD, 
            height=12, 
            state=tk.DISABLED,
            font=("Segoe UI", 9),
            bg="#ffffff",
            relief="flat",
            borderwidth=1
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # 右侧：工具请求列表
        right_chat_frame = ttk.Frame(chat_frame)
        right_chat_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 请求队列标题
        queue_header = ttk.Frame(right_chat_frame)
        queue_header.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(queue_header, text="📋 工具请求队列", 
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        queue_count = ttk.Label(queue_header, text="0", 
                               font=("Segoe UI", 9),
                               foreground="#6b7280")
        queue_count.pack(side=tk.RIGHT)
        self.queue_count_label = queue_count
        
        # 请求列表
        self.request_listbox = tk.Listbox(right_chat_frame, width=30, height=12,
                                         font=("Segoe UI", 9),
                                         relief="flat", borderwidth=1,
                                         bg="#f8fafc",
                                         selectbackground="#3b82f6",
                                         selectforeground="white")
        self.request_listbox.pack(fill=tk.BOTH, expand=True)
        self.request_listbox.bind("<<ListboxSelect>>", self._on_request_selected)
        
        # 输入区域
        input_area = ttk.Frame(chat_card)
        input_area.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # 输入标签
        input_label = ttk.Label(input_area, text="💡 描述您需要的工具功能：", 
                               font=("Segoe UI", 10, "bold"))
        input_label.pack(anchor=tk.W, pady=(0, 8))
        
        # 输入框
        self.input_entry = ttk.Entry(input_area, font=("Segoe UI", 10), style="Modern.TEntry")
        self.input_entry.pack(fill=tk.X, pady=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        
        # 按钮区域
        button_frame = ttk.Frame(input_area)
        button_frame.pack(fill=tk.X)
        
        self.send_button = ttk.Button(button_frame, text="🚀 发送请求", 
                                     command=self._send_message, style="Accent.TButton")
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ 清空对话", 
                                      command=self._clear_chat)
        self.clear_button.pack(side=tk.LEFT)
        
        # 下半部分：工具管理区域卡片
        tool_card = ttk.Frame(content_frame, style="Card.TFrame")
        tool_card.pack(fill=tk.BOTH, expand=True)
        
        # 工具管理卡片标题
        tool_header = ttk.Frame(tool_card)
        tool_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tool_title = ttk.Label(tool_header, text="🛠️ 工具管理中心", 
                              font=("Segoe UI", 12, "bold"))
        tool_title.pack(side=tk.LEFT)
        
        tool_status = ttk.Label(tool_header, text="⚡ 活跃", 
                               font=("Segoe UI", 10),
                               foreground="#f59e0b")
        tool_status.pack(side=tk.RIGHT)
        
        # 工具管理内容区域
        tool_frame = ttk.Frame(tool_card)
        tool_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # 左侧：工具代码显示
        left_tool_frame = ttk.Frame(tool_frame)
        left_tool_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 代码显示标题
        code_header = ttk.Frame(left_tool_frame)
        code_header.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(code_header, text="📝 生成的工具代码", 
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        # 工具信息栏
        info_frame = ttk.Frame(left_tool_frame)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(info_frame, text="工具名称：").pack(side=tk.LEFT)
        self.tool_name_var = tk.StringVar()
        self.tool_name_label = ttk.Label(info_frame, textvariable=self.tool_name_var, 
                                        font=("Arial", 10, "bold"), foreground="#2c3e50")
        self.tool_name_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(info_frame, text="插入位置：").pack(side=tk.LEFT)
        ttk.Label(info_frame, text="security_tools.py", 
                 font=("Arial", 10, "bold"), foreground="#e74c3c").pack(side=tk.LEFT, padx=(5, 0))
        
        # 代码显示区域
        self.code_display = scrolledtext.ScrolledText(
            left_tool_frame, 
            wrap=tk.NONE, 
            height=12,
            font=("Consolas", 10),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        self.code_display.pack(fill=tk.BOTH, expand=True)
        
        # 右侧：工具管理功能
        right_tool_frame = ttk.Frame(tool_frame)
        right_tool_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 工具操作标题
        operation_header = ttk.Frame(right_tool_frame)
        operation_header.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(operation_header, text="⚙️ 工具操作", 
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        tool_count = ttk.Label(operation_header, text="0", 
                              font=("Segoe UI", 9),
                              foreground="#6b7280")
        tool_count.pack(side=tk.RIGHT)
        self.tool_count_label = tool_count
        
        # 工具列表
        self.tool_listbox = tk.Listbox(right_tool_frame, width=25, height=8,
                                      font=("Segoe UI", 9),
                                      relief="flat", borderwidth=1,
                                      bg="#f8fafc",
                                      selectbackground="#3b82f6",
                                      selectforeground="white")
        self.tool_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.tool_listbox.bind("<<ListboxSelect>>", self._on_tool_selected)
        
        # 操作按钮
        button_frame = ttk.Frame(right_tool_frame)
        button_frame.pack(fill=tk.X)
        
        self.save_button = ttk.Button(button_frame, text="💾 保存工具", 
                                     command=self._save_tool, style="Accent.TButton")
        self.save_button.pack(fill=tk.X, pady=(0, 8))
        
        self.load_button = ttk.Button(button_frame, text="📂 加载工具", 
                                     command=self._load_tool)
        self.load_button.pack(fill=tk.X, pady=(0, 8))
        
        self.delete_button = ttk.Button(button_frame, text="🗑️ 删除工具", 
                                       command=self._delete_tool)
        self.delete_button.pack(fill=tk.X, pady=(0, 8))
        
        self.export_button = ttk.Button(button_frame, text="📤 导出工具", 
                                       command=self._export_tool)
        self.export_button.pack(fill=tk.X)
        
        # 底部操作按钮
        bottom_frame = ttk.Frame(tool_card)
        bottom_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="📋 复制代码", command=self._copy_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 保存到文件", command=self._save_to_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 重新生成", command=self._regenerate_tool).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📖 查看示例", command=self._show_examples).pack(side=tk.RIGHT, padx=5)
        
    def _init_conversation(self):
        """初始化对话"""
        welcome_msg = """🤖 欢迎来到AI工具仓库！

我是您的专属工具设计师，可以帮助您：
• 根据功能需求生成标准的@tool装饰器函数
• 提供符合security_tools.py格式的工具代码
• 自动生成完整的文档和错误处理
• 优化工具性能和安全性

💡 **使用方法：**
1. 描述您需要的工具功能
2. 我将生成完整的Python代码
3. 复制代码并插入到security_tools.py中
4. 在agents_config.json中配置给相应的Agent

🎯 **示例需求：**
• "创建一个检测USB设备的工具"
• "生成文件完整性校验工具"
• "制作网络端口扫描器"

请描述您需要的工具功能！"""
        
        self._add_message("AI工具设计师", welcome_msg, "system")
        
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
        self.chat_display.tag_config("system_sender", foreground="#8e44ad", font=("Arial", 9, "bold"))
        self.chat_display.tag_config("system_msg", foreground="#34495e")
        self.chat_display.tag_config("user_sender", foreground="#27ae60", font=("Arial", 9, "bold"))
        self.chat_display.tag_config("user_msg", foreground="#2c3e50")
        self.chat_display.tag_config("ai_sender", foreground="#e67e22", font=("Arial", 9, "bold"))
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
        
    def receive_tool_request(self, tool_requests):
        """接收来自人事部门的工具请求"""
        for tool_request in tool_requests:
            if tool_request not in self.tool_requests:
                self.tool_requests.append(tool_request)
                self.request_listbox.insert(tk.END, tool_request)
                
        # 更新计数标签
        self.queue_count_label.config(text=str(len(self.tool_requests)))
                
        # 添加提示消息
        if tool_requests:
            self._add_message("系统", f"📨 收到来自人事部门的 {len(tool_requests)} 个工具请求", "system")
            
    def _send_message(self):
        """发送消息"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            messagebox.showwarning("提示", "请输入工具需求描述")
            return
            
        # 显示用户请求
        self._add_message("您", user_input, "user")
        
        # 清空输入框
        self.input_entry.delete(0, tk.END)
        
        # 在新线程中生成工具
        threading.Thread(target=self._process_tool_generation, args=(user_input,), daemon=True).start()
        
    def _clear_chat(self):
        """清空对话历史"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.conversation_history.clear()
        # 重新初始化对话
        self._init_conversation()
        
    def _on_request_selected(self, event):
        """选择工具请求"""
        selection = self.request_listbox.curselection()
        if selection:
            selected_request = self.tool_requests[selection[0]]
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, selected_request)
            
    def _on_tool_selected(self, event):
        """选择工具"""
        selection = self.tool_listbox.curselection()
        if selection and hasattr(self, 'generated_tools'):
            if selection[0] < len(self.generated_tools):
                selected_tool = self.generated_tools[selection[0]]
                self.current_tool = selected_tool
                self.tool_name_var.set(selected_tool['name'])
                self.code_display.delete("1.0", tk.END)
                self.code_display.insert("1.0", selected_tool['code'])
                
    def _save_tool(self):
        """保存工具到列表"""
        if hasattr(self, 'current_tool'):
            # 检查是否已存在
            existing_names = [tool['name'] for tool in self.generated_tools]
            if self.current_tool['name'] not in existing_names:
                self.generated_tools.append(self.current_tool.copy())
                self.tool_listbox.insert(tk.END, self.current_tool['name'])
                self.tool_count_label.config(text=str(len(self.generated_tools)))
                messagebox.showinfo("成功", "工具已保存到列表")
            else:
                messagebox.showinfo("提示", "工具已存在于列表中")
        else:
            messagebox.showwarning("提示", "没有可保存的工具")
            
    def _load_tool(self):
        """加载工具"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    code = f.read()
                # 简单解析工具名称
                import re
                match = re.search(r'@tool\("([^"]+)"\)', code)
                tool_name = match.group(1) if match else os.path.basename(filename)
                
                self.current_tool = {
                    'name': tool_name,
                    'description': f'从文件加载: {filename}',
                    'code': code
                }
                self.tool_name_var.set(tool_name)
                self.code_display.delete("1.0", tk.END)
                self.code_display.insert("1.0", code)
                messagebox.showinfo("成功", "工具已加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败：{str(e)}")
                
    def _delete_tool(self):
        """删除工具"""
        selection = self.tool_listbox.curselection()
        if selection:
            if messagebox.askyesno("确认", "确定要删除选中的工具吗？"):
                index = selection[0]
                self.generated_tools.pop(index)
                self.tool_listbox.delete(index)
                self.tool_count_label.config(text=str(len(self.generated_tools)))
                messagebox.showinfo("成功", "工具已删除")
        else:
            messagebox.showwarning("提示", "请先选择要删除的工具")
            
    def _export_tool(self):
        """导出工具"""
        if hasattr(self, 'current_tool'):
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")],
                initialname=f"{self.current_tool['name']}.py"
            )
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.current_tool['code'])
                    messagebox.showinfo("成功", f"工具已导出到 {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"导出失败：{str(e)}")
        else:
            messagebox.showwarning("提示", "没有可导出的工具")
        
    def _process_tool_generation(self, user_request):
        """处理工具生成"""
        # 显示生成状态
        self.after(100, lambda: self._add_message("AI工具设计师", "🔨 正在分析需求并生成工具代码...", "ai"))
        
        # 模拟处理时间
        import time
        time.sleep(2)
        
        # 生成工具代码
        tool_code, tool_name, description = self._generate_tool_code(user_request)
        
        # 显示生成结果
        self.after(0, lambda: self._display_generated_tool(tool_code, tool_name, description))
        
    def _generate_tool_code(self, request):
        """根据请求生成工具代码"""
        request_lower = request.lower()
        
        # 根据关键词生成不同类型的工具
        if "usb" in request_lower or "设备" in request_lower:
            return self._generate_usb_detection_tool()
        elif "文件" in request_lower and ("完整性" in request_lower or "校验" in request_lower):
            return self._generate_file_integrity_tool()
        elif "端口" in request_lower or "扫描" in request_lower:
            return self._generate_port_scanner_tool()
        elif "注册表" in request_lower or "registry" in request_lower:
            return self._generate_registry_tool()
        elif "证书" in request_lower or "certificate" in request_lower:
            return self._generate_certificate_tool()
        elif "内存" in request_lower or "memory" in request_lower:
            return self._generate_memory_analysis_tool()
        else:
            return self._generate_custom_tool(request)
            
    def _generate_usb_detection_tool(self):
        """生成USB设备检测工具"""
        tool_name = "DetectUSBDevices"
        description = "检测系统中的USB设备并分析安全风险"
        
        code = '''@tool("DetectUSBDevices")
def detect_usb_devices() -> str:
    """检测系统中的USB设备并分析安全风险"""
    _log_tool_output("正在检测USB设备...")
    try:
        import subprocess
        import json
        
        # 使用wmic获取USB设备信息
        result = subprocess.run(
            ['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 
             'deviceid,volumename,size,freespace,filesystem'],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        
        usb_devices = []
        lines = result.stdout.strip().splitlines()
        
        if len(lines) > 1:
            headers = [h.strip() for h in lines[0].split()]
            for line in lines[1:]:
                if line.strip():
                    parts = line.strip().split(None, len(headers)-1)
                    if len(parts) >= len(headers):
                        device_info = dict(zip(headers, parts))
                        
                        # 添加安全风险评估
                        risk_level = "低"
                        risk_factors = []
                        
                        # 检查文件系统类型
                        if device_info.get('FileSystem', '').upper() in ['FAT32', 'FAT']:
                            risk_factors.append("使用较旧的文件系统")
                            risk_level = "中"
                        
                        # 检查设备大小（异常大的设备可能有风险）
                        try:
                            size = int(device_info.get('Size', 0))
                            if size > 1000000000000:  # 大于1TB
                                risk_factors.append("设备容量异常大")
                                risk_level = "中"
                        except:
                            pass
                        
                        device_info['RiskLevel'] = risk_level
                        device_info['RiskFactors'] = risk_factors
                        device_info['DetectionTime'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        usb_devices.append(device_info)
        
        # 获取USB设备的详细信息
        detailed_result = subprocess.run(
            ['wmic', 'path', 'win32_volume', 'where', 'drivetype=2', 'get', 
             'deviceid,label,capacity,filesystem'],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        
        result_data = {
            "status": "success",
            "device_count": len(usb_devices),
            "devices": usb_devices,
            "scan_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "security_summary": {
                "high_risk": len([d for d in usb_devices if d.get('RiskLevel') == '高']),
                "medium_risk": len([d for d in usb_devices if d.get('RiskLevel') == '中']),
                "low_risk": len([d for d in usb_devices if d.get('RiskLevel') == '低'])
            }
        }
        
        _log_tool_output(f"检测完成，发现 {len(usb_devices)} 个USB设备")
        return json.dumps(result_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"检测USB设备时出错: {str(e)}"
        _log_tool_output(error_msg)
        return json.dumps({"status": "error", "message": error_msg}, ensure_ascii=False)'''
        
        return code, tool_name, description
        
    def _generate_file_integrity_tool(self):
        """生成文件完整性校验工具"""
        tool_name = "CheckFileIntegrity"
        description = "检查关键系统文件的完整性"
        
        code = '''@tool("CheckFileIntegrity")
def check_file_integrity(file_path: str = "") -> str:
    """检查文件完整性，支持单个文件或系统关键文件批量检查"""
    _log_tool_output("正在检查文件完整性...")
    try:
        import hashlib
        import os
        import json
        
        def calculate_file_hash(filepath):
            """计算文件的SHA256哈希值"""
            sha256_hash = hashlib.sha256()
            try:
                with open(filepath, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                return sha256_hash.hexdigest()
            except Exception as e:
                return f"错误: {str(e)}"
        
        results = []
        
        if file_path:
            # 检查单个文件
            if os.path.exists(file_path):
                file_hash = calculate_file_hash(file_path)
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                
                results.append({
                    "file_path": file_path,
                    "exists": True,
                    "size": file_size,
                    "hash": file_hash,
                    "modified_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mtime)),
                    "status": "已计算" if not file_hash.startswith("错误") else "错误"
                })
            else:
                results.append({
                    "file_path": file_path,
                    "exists": False,
                    "status": "文件不存在"
                })
        else:
            # 检查系统关键文件
            critical_files = [
                "C:\\Windows\\System32\\kernel32.dll",
                "C:\\Windows\\System32\\ntdll.dll",
                "C:\\Windows\\System32\\user32.dll",
                "C:\\Windows\\System32\\advapi32.dll",
                "C:\\Windows\\System32\\shell32.dll",
                "C:\\Windows\\System32\\svchost.exe",
                "C:\\Windows\\System32\\winlogon.exe",
                "C:\\Windows\\System32\\explorer.exe"
            ]
            
            for file_path in critical_files:
                if os.path.exists(file_path):
                    file_hash = calculate_file_hash(file_path)
                    file_size = os.path.getsize(file_path)
                    file_mtime = os.path.getmtime(file_path)
                    
                    # 简单的异常检测
                    risk_level = "正常"
                    if file_size < 1000:  # 文件过小可能有问题
                        risk_level = "可疑"
                    
                    results.append({
                        "file_path": file_path,
                        "exists": True,
                        "size": file_size,
                        "hash": file_hash,
                        "modified_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mtime)),
                        "risk_level": risk_level,
                        "status": "已检查"
                    })
                else:
                    results.append({
                        "file_path": file_path,
                        "exists": False,
                        "risk_level": "高风险",
                        "status": "关键文件缺失"
                    })
        
        # 生成摘要
        total_files = len(results)
        existing_files = len([r for r in results if r.get('exists', False)])
        suspicious_files = len([r for r in results if r.get('risk_level') == '可疑'])
        missing_files = len([r for r in results if not r.get('exists', False)])
        
        result_data = {
            "status": "success",
            "scan_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "summary": {
                "total_files": total_files,
                "existing_files": existing_files,
                "suspicious_files": suspicious_files,
                "missing_files": missing_files
            },
            "files": results
        }
        
        _log_tool_output(f"完整性检查完成，检查了 {total_files} 个文件")
        return json.dumps(result_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"文件完整性检查时出错: {str(e)}"
        _log_tool_output(error_msg)
        return json.dumps({"status": "error", "message": error_msg}, ensure_ascii=False)'''
        
        return code, tool_name, description
        
    def _generate_port_scanner_tool(self):
        """生成端口扫描工具"""
        tool_name = "ScanNetworkPorts"
        description = "扫描指定主机的网络端口开放情况"
        
        code = '''@tool("ScanNetworkPorts")
def scan_network_ports(target_host: str = "localhost", port_range: str = "1-1000") -> str:
    """扫描指定主机的网络端口开放情况"""
    _log_tool_output(f"正在扫描 {target_host} 的端口...")
    try:
        import socket
        import threading
        import json
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def scan_port(host, port, timeout=1):
            """扫描单个端口"""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    # 尝试获取服务信息
                    try:
                        service = socket.getservbyport(port)
                    except:
                        service = "未知服务"
                    
                    return {
                        "port": port,
                        "status": "开放",
                        "service": service
                    }
                else:
                    return None
            except Exception:
                return None
        
        # 解析端口范围
        if "-" in port_range:
            start_port, end_port = map(int, port_range.split("-"))
        else:
            start_port = end_port = int(port_range)
        
        # 限制扫描范围以避免过度消耗资源
        if end_port - start_port > 10000:
            end_port = start_port + 10000
            _log_tool_output("端口范围过大，限制为10000个端口")
        
        open_ports = []
        total_ports = end_port - start_port + 1
        
        # 使用线程池进行并发扫描
        with ThreadPoolExecutor(max_workers=100) as executor:
            # 提交扫描任务
            future_to_port = {
                executor.submit(scan_port, target_host, port): port 
                for port in range(start_port, end_port + 1)
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_port):
                completed += 1
                if completed % 100 == 0:
                    _log_tool_output(f"扫描进度: {completed}/{total_ports}")
                
                result = future.result()
                if result:
                    open_ports.append(result)
        
        # 对开放端口进行风险评估
        for port_info in open_ports:
            port = port_info["port"]
            risk_level = "低"
            risk_factors = []
            
            # 高风险端口
            high_risk_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 3389, 5432]
            if port in high_risk_ports:
                risk_level = "高"
                risk_factors.append("常见攻击目标端口")
            
            # 中风险端口
            medium_risk_ports = [111, 512, 513, 514, 1024, 2049, 6000]
            if port in medium_risk_ports:
                risk_level = "中"
                risk_factors.append("需要关注的服务端口")
            
            port_info["risk_level"] = risk_level
            port_info["risk_factors"] = risk_factors
        
        # 生成扫描结果
        result_data = {
            "status": "success",
            "target_host": target_host,
            "port_range": f"{start_port}-{end_port}",
            "scan_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "summary": {
                "total_scanned": total_ports,
                "open_ports": len(open_ports),
                "high_risk_ports": len([p for p in open_ports if p.get('risk_level') == '高']),
                "medium_risk_ports": len([p for p in open_ports if p.get('risk_level') == '中']),
                "low_risk_ports": len([p for p in open_ports if p.get('risk_level') == '低'])
            },
            "open_ports": sorted(open_ports, key=lambda x: x['port'])
        }
        
        _log_tool_output(f"端口扫描完成，发现 {len(open_ports)} 个开放端口")
        return json.dumps(result_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"端口扫描时出错: {str(e)}"
        _log_tool_output(error_msg)
        return json.dumps({"status": "error", "message": error_msg}, ensure_ascii=False)'''
        
        return code, tool_name, description
        
    def _generate_custom_tool(self, request):
        """生成自定义工具"""
        tool_name = "CustomSecurityTool"
        description = f"根据需求生成的自定义安全工具: {request[:50]}..."
        
        code = f'''@tool("CustomSecurityTool")
def custom_security_tool(param: str = "") -> str:
    """根据需求生成的自定义安全工具: {request}"""
    _log_tool_output("正在执行自定义安全检查...")
    try:
        import json
        import subprocess
        import os
        
        # 这里是根据具体需求生成的工具逻辑
        # 请根据实际需求修改以下代码
        
        result_data = {{
            "status": "success",
            "tool_name": "CustomSecurityTool",
            "description": "{request}",
            "execution_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "parameter": param,
            "result": "工具执行成功，请根据具体需求实现相应逻辑",
            "suggestions": [
                "请根据具体安全需求实现工具逻辑",
                "添加适当的错误处理和日志记录",
                "确保工具的安全性和稳定性"
            ]
        }}
        
        _log_tool_output("自定义安全工具执行完成")
        return json.dumps(result_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"自定义工具执行时出错: {{str(e)}}"
        _log_tool_output(error_msg)
        return json.dumps({{"status": "error", "message": error_msg}}, ensure_ascii=False)'''
        
        return code, tool_name, description
        
    def _display_generated_tool(self, tool_code, tool_name, description):
        """显示生成的工具代码"""
        # 更新工具信息
        self.tool_name_var.set(tool_name)
        
        # 显示代码
        self.code_display.delete("1.0", tk.END)
        self.code_display.insert("1.0", tool_code)
        
        # 保存当前生成的工具
        self.current_tool = {
            "name": tool_name,
            "description": description,
            "code": tool_code
        }
        
        # 添加AI响应消息
        response_msg = f"""✅ 工具生成完成！

🔧 **工具名称：** {tool_name}
📝 **功能描述：** {description}

📋 **使用说明：**
1. 复制右侧生成的代码
2. 打开 security_tools.py 文件
3. 将代码插入到文件末尾（在其他@tool函数附近）
4. 保存文件
5. 在 agents_config.json 中将工具名称添加到相应Agent的tools列表中

💡 **提示：** 代码已包含完整的错误处理和日志记录功能，可以直接使用。"""
        
        self._add_message("AI工具设计师", response_msg, "ai")
        
    def _copy_code(self):
        """复制代码到剪贴板"""
        if hasattr(self, 'current_tool'):
            self.clipboard_clear()
            self.clipboard_append(self.current_tool['code'])
            messagebox.showinfo("成功", "代码已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "没有可复制的代码")
            
    def _save_to_file(self):
        """保存代码到文件"""
        if hasattr(self, 'current_tool'):
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")],
                initialname=f"{self.current_tool['name']}.py"
            )
            
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.current_tool['code'])
                    messagebox.showinfo("成功", f"代码已保存到 {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败：{str(e)}")
        else:
            messagebox.showwarning("提示", "没有可保存的代码")
            
    def _regenerate_tool(self):
        """重新生成工具"""
        current_input = self.input_entry.get().strip()
        if current_input:
            self._send_message()
        else:
            messagebox.showwarning("提示", "请先输入工具需求描述")
            
    def _show_examples(self):
        """显示工具示例"""
        examples_window = tk.Toplevel(self)
        examples_window.title("工具示例")
        examples_window.geometry("800x600")
        
        # 创建示例内容
        examples_text = scrolledtext.ScrolledText(examples_window, wrap=tk.WORD)
        examples_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        examples_content = """🔧 工具生成示例

1. **USB设备检测工具**
   需求描述："创建一个检测USB设备的工具"
   生成工具：DetectUSBDevices - 检测并分析USB设备安全风险

2. **文件完整性校验工具**
   需求描述："生成文件完整性校验工具"
   生成工具：CheckFileIntegrity - 检查系统关键文件完整性

3. **网络端口扫描工具**
   需求描述："制作网络端口扫描器"
   生成工具：ScanNetworkPorts - 扫描主机端口开放情况

4. **注册表监控工具**
   需求描述："创建注册表监控工具"
   生成工具：MonitorRegistry - 监控注册表关键项变化

5. **证书验证工具**
   需求描述："生成SSL证书验证工具"
   生成工具：ValidateSSLCertificate - 验证SSL证书有效性

💡 **编写技巧：**
• 使用具体的功能描述
• 包含关键词（如：检测、扫描、监控、分析等）
• 说明目标对象（如：USB、文件、端口、注册表等）
• 可以指定特殊需求（如：实时监控、批量处理等）

📝 **代码特点：**
• 使用@tool装饰器
• 包含完整的错误处理
• 提供详细的日志输出
• 返回JSON格式的结构化数据
• 包含安全风险评估
• 支持参数化配置"""
        
        examples_text.insert("1.0", examples_content)
        examples_text.config(state=tk.DISABLED)
        
    def _clear_input(self):
        """清空输入框"""
        self.input_entry.delete(0, tk.END)