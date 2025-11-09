#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading

class SettingsScreen(ttk.Frame):
    """设置界面"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # 创建界面
        self._create_widgets()
        
        # 加载设置
        self._load_settings()
        
    def _create_widgets(self):
        """创建现代化界面组件"""
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 页面标题区域
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="⚙️ 系统设置", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, text="配置与个性化选项", style="Subtitle.TLabel")
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # 设置卡片容器
        settings_card = ttk.Frame(main_container, style="Card.TFrame")
        settings_card.pack(fill=tk.BOTH, expand=True)
        
        # 设置卡片标题
        card_header = ttk.Frame(settings_card)
        card_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        card_title = ttk.Label(card_header, text="🔧 配置管理", 
                              font=("Segoe UI", 12, "bold"))
        card_title.pack(side=tk.LEFT)
        
        card_status = ttk.Label(card_header, text="✅ 已同步", 
                               font=("Segoe UI", 10),
                               foreground="#10b981")
        card_status.pack(side=tk.RIGHT)
        
        # 选项卡容器
        tab_container = ttk.Frame(settings_card)
        tab_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # 创建选项卡
        self.notebook = ttk.Notebook(tab_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 常规设置选项卡
        general_tab = ttk.Frame(self.notebook)
        self.notebook.add(general_tab, text="常规设置")
        
        # 模型设置选项卡
        model_tab = ttk.Frame(self.notebook)
        self.notebook.add(model_tab, text="模型设置")
        
        # 安全设置选项卡
        security_tab = ttk.Frame(self.notebook)
        self.notebook.add(security_tab, text="安全设置")
        
        # 日志设置选项卡
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text="日志设置")
        
        # 创建各选项卡的内容
        self._create_general_settings(general_tab)
        self._create_model_settings(model_tab)
        self._create_security_settings(security_tab)
        self._create_log_settings(log_tab)
        
        # 底部按钮
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="保存设置", command=self._save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        reset_button = ttk.Button(button_frame, text="重置设置", command=self._reset_settings)
        reset_button.pack(side=tk.RIGHT, padx=5)
        
    def _create_general_settings(self, parent):
        """创建常规设置内容"""
        # 自动启动设置
        auto_start_frame = ttk.LabelFrame(parent, text="启动设置")
        auto_start_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.auto_start_var = tk.BooleanVar(value=False)
        auto_start_check = ttk.Checkbutton(auto_start_frame, text="系统启动时自动运行", 
                                          variable=self.auto_start_var)
        auto_start_check.pack(anchor=tk.W, pady=5, padx=10)
        
        # 界面设置
        ui_frame = ttk.LabelFrame(parent, text="界面设置")
        ui_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(ui_frame, text="主题:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.theme_var = tk.StringVar(value="默认")
        theme_combo = ttk.Combobox(ui_frame, textvariable=self.theme_var, 
                                  values=["默认", "暗色", "亮色"])
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(ui_frame, text="字体大小:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.font_size_var = tk.StringVar(value="中")
        font_size_combo = ttk.Combobox(ui_frame, textvariable=self.font_size_var, 
                                      values=["小", "中", "大"])
        font_size_combo.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 语言设置
        language_frame = ttk.LabelFrame(parent, text="语言设置")
        language_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(language_frame, text="界面语言:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.language_var = tk.StringVar(value="中文")
        language_combo = ttk.Combobox(language_frame, textvariable=self.language_var, 
                                     values=["中文", "英文"])
        language_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
    def _create_model_settings(self, parent):
        """创建模型设置内容"""
        # 模型选择
        model_frame = ttk.LabelFrame(parent, text="模型设置")
        model_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(model_frame, text="默认模型:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.model_var = tk.StringVar(value="deepseek-chat")
        model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                  values=["deepseek-chat", "gpt-4", "gpt-3.5-turbo", "claude-3"])
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # API设置
        api_frame = ttk.LabelFrame(parent, text="API设置")
        api_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(api_frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.api_key_var = tk.StringVar()
        api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=30)
        api_key_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(api_frame, text="API基础URL:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.api_url_var = tk.StringVar(value="https://api.deepseek.com")
        api_url_entry = ttk.Entry(api_frame, textvariable=self.api_url_var, width=30)
        api_url_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
 
        
    def _create_security_settings(self, parent):
        """创建安全设置内容"""
        # 白名单设置
        whitelist_frame = ttk.LabelFrame(parent, text="白名单设置")
        whitelist_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(whitelist_frame, text="白名单文件路径:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.whitelist_path_var = tk.StringVar()
        whitelist_path_entry = ttk.Entry(whitelist_frame, textvariable=self.whitelist_path_var, width=30)
        whitelist_path_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        browse_button = ttk.Button(whitelist_frame, text="浏览...", 
                                  command=lambda: self._browse_file(self.whitelist_path_var))
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=10, pady=5)
        
        # 基线设置
        baseline_frame = ttk.LabelFrame(parent, text="基线设置")
        baseline_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(baseline_frame, text="基线文件路径:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.baseline_path_var = tk.StringVar()
        baseline_path_entry = ttk.Entry(baseline_frame, textvariable=self.baseline_path_var, width=30)
        baseline_path_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        browse_button = ttk.Button(baseline_frame, text="浏览...", 
                                  command=lambda: self._browse_file(self.baseline_path_var))
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=10, pady=5)
        
        # 自动响应设置
        response_frame = ttk.LabelFrame(parent, text="自动响应设置")
        response_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.auto_response_var = tk.BooleanVar(value=False)
        auto_response_check = ttk.Checkbutton(response_frame, text="启用自动响应", 
                                             variable=self.auto_response_var)
        auto_response_check.pack(anchor=tk.W, pady=5, padx=10)
        
        self.auto_terminate_var = tk.BooleanVar(value=False)
        auto_terminate_check = ttk.Checkbutton(response_frame, text="允许自动终止可疑进程", 
                                              variable=self.auto_terminate_var)
        auto_terminate_check.pack(anchor=tk.W, pady=5, padx=10)
        
    def _create_log_settings(self, parent):
        """创建日志设置内容"""
        # 日志级别设置
        log_level_frame = ttk.LabelFrame(parent, text="日志级别")
        log_level_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(log_level_frame, text="日志级别:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_level_frame, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_level_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 日志文件设置
        log_file_frame = ttk.LabelFrame(parent, text="日志文件")
        log_file_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(log_file_frame, text="日志文件路径:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.log_path_var = tk.StringVar(value="logs")
        log_path_entry = ttk.Entry(log_file_frame, textvariable=self.log_path_var, width=30)
        log_path_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        browse_button = ttk.Button(log_file_frame, text="浏览...", 
                                  command=lambda: self._browse_directory(self.log_path_var))
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=10, pady=5)
        
        # 日志保留设置
        log_retention_frame = ttk.LabelFrame(parent, text="日志保留")
        log_retention_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(log_retention_frame, text="保留天数:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.log_retention_var = tk.IntVar(value=30)
        log_retention_entry = ttk.Entry(log_retention_frame, textvariable=self.log_retention_var, width=10)
        log_retention_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 清理日志按钮
        clean_log_button = ttk.Button(log_retention_frame, text="清理过期日志", command=self._clean_logs)
        clean_log_button.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
    def _browse_file(self, var):
        """浏览文件对话框"""
        filename = filedialog.askopenfilename(
            title="选择文件",
            filetypes=(("JSON文件", "*.json"), ("所有文件", "*.*"))
        )
        if filename:
            var.set(filename)
            
    def _browse_directory(self, var):
        """浏览目录对话框"""
        directory = filedialog.askdirectory(title="选择目录")
        if directory:
            var.set(directory)
            
    def _load_settings(self):
        """加载设置"""
        settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "config", "settings.json")
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                # 常规设置
                if "general" in settings:
                    general = settings["general"]
                    self.auto_start_var.set(general.get("auto_start", False))
                    self.theme_var.set(general.get("theme", "默认"))
                    self.font_size_var.set(general.get("font_size", "中"))
                    self.language_var.set(general.get("language", "中文"))
                    
                # 模型设置
                if "model" in settings:
                    model = settings["model"]
                    self.model_var.set(model.get("default_model", "deepseek-chat"))
                    self.api_key_var.set(model.get("api_key", ""))
                    self.api_url_var.set(model.get("api_url", "https://api.deepseek.com"))
                    
                # 安全设置
                if "security" in settings:
                    security = settings["security"]
                    self.whitelist_path_var.set(security.get("whitelist_path", ""))
                    self.baseline_path_var.set(security.get("baseline_path", ""))
                    self.auto_response_var.set(security.get("auto_response", False))
                    self.auto_terminate_var.set(security.get("auto_terminate", False))
                    
                # 日志设置
                if "log" in settings:
                    log = settings["log"]
                    self.log_level_var.set(log.get("level", "INFO"))
                    self.log_path_var.set(log.get("path", "logs"))
                    self.log_retention_var.set(log.get("retention_days", 30))
                    
            except Exception as e:
                messagebox.showerror("加载设置失败", f"无法加载设置: {str(e)}")
                
    def _save_settings(self):
        """保存设置"""
        settings = {
            "general": {
                "auto_start": self.auto_start_var.get(),
                "theme": self.theme_var.get(),
                "font_size": self.font_size_var.get(),
                "language": self.language_var.get()
            },
            "model": {
                "default_model": self.model_var.get(),
                "api_key": self.api_key_var.get(),
                "api_url": self.api_url_var.get()
            },
            "security": {
                "whitelist_path": self.whitelist_path_var.get(),
                "baseline_path": self.baseline_path_var.get(),
                "auto_response": self.auto_response_var.get(),
                "auto_terminate": self.auto_terminate_var.get()
            },
            "log": {
                "level": self.log_level_var.get(),
                "path": self.log_path_var.get(),
                "retention_days": self.log_retention_var.get()
            }
        }
        
        settings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        settings_file = os.path.join(settings_dir, "settings.json")
        
        try:
            # 确保目录存在
            os.makedirs(settings_dir, exist_ok=True)
            
            # 保存设置
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
            messagebox.showinfo("保存成功", "设置已成功保存")
            
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存设置: {str(e)}")
            
    def _reset_settings(self):
        """重置设置"""
        if messagebox.askyesno("确认重置", "确定要重置所有设置吗？"):
            # 常规设置
            self.auto_start_var.set(False)
            self.theme_var.set("默认")
            self.font_size_var.set("中")
            self.language_var.set("中文")
            
            # 模型设置
            self.model_var.set("deepseek-chat")
            self.api_key_var.set("")
            self.api_url_var.set("https://api.deepseek.com")

            
            # 安全设置
            self.whitelist_path_var.set("")
            self.baseline_path_var.set("")
            self.auto_response_var.set(False)
            self.auto_terminate_var.set(False)
            
            # 日志设置
            self.log_level_var.set("INFO")
            self.log_path_var.set("logs")
            self.log_retention_var.set(30)
            
    def _clean_logs(self):
        """清理过期日志"""
        log_path = self.log_path_var.get()
        retention_days = self.log_retention_var.get()
        
        if not os.path.exists(log_path):
            messagebox.showinfo("清理日志", "日志目录不存在")
            return
            
        try:
            # 启动清理线程
            threading.Thread(target=self._clean_logs_thread, 
                           args=(log_path, retention_days)).start()
            
            messagebox.showinfo("清理日志", "日志清理已开始，请稍候...")
            
        except Exception as e:
            messagebox.showerror("清理日志失败", f"无法清理日志: {str(e)}")
            
    def _clean_logs_thread(self, log_path, retention_days):
        """清理日志线程"""
        import time
        from datetime import datetime, timedelta
        
        try:
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_timestamp = cutoff_date.timestamp()
            
            # 遍历日志目录
            cleaned_count = 0
            for root, dirs, files in os.walk(log_path):
                for file in files:
                    if file.endswith(".log"):
                        file_path = os.path.join(root, file)
                        file_time = os.path.getmtime(file_path)
                        
                        # 如果文件早于截止日期，则删除
                        if file_time < cutoff_timestamp:
                            os.remove(file_path)
                            cleaned_count += 1
                            
            # 在主线程中显示结果
            self.after(0, lambda: messagebox.showinfo("清理完成", f"已清理 {cleaned_count} 个过期日志文件"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("清理失败", f"清理日志时出错: {str(e)}"))
            
    def on_show(self):
        """显示界面时调用"""
        # 重新加载设置
        self._load_settings()
        
    def on_hide(self):
        """隐藏界面时调用"""
        pass