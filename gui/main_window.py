#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json

from gui.screens.task_execution_screen import TaskExecutionScreen
from gui.screens.settings_screen import SettingsScreen
from gui.screens.report_screen import ReportScreen
from gui.screens.agent_management_screen import AgentManagementScreen
from gui.screens.group_management_screen import GroupManagementScreen
from gui.screens.hr_department_screen import HRDepartmentScreen
from gui.screens.tool_warehouse_screen import ToolWarehouseScreen
from gui.screens.enhanced_log_viewer import EnhancedLogViewer

# matplotlib配置已移除，因为仪表盘功能已被删除

class MainWindow(tk.Tk):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.title("AI安全应急响应系统")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # 创建样式
        self.style = ttk.Style()
        self.style.theme_use("clam")  # 使用clam主题
        
        # 现代化自定义样式
        # 主色调：深蓝色系
        primary_color = "#1e3a8a"  # 深蓝色
        secondary_color = "#3b82f6"  # 亮蓝色
        accent_color = "#06b6d4"  # 青色
        background_color = "#f8fafc"  # 浅灰白
        card_color = "#ffffff"  # 纯白
        text_primary = "#1f2937"  # 深灰
        text_secondary = "#6b7280"  # 中灰
        
        # 基础样式
        self.style.configure("TFrame", background=background_color)
        self.style.configure("TLabel", background=background_color, foreground=text_primary)
        self.style.configure("TButton", 
                            padding=(12, 8),
                            font=("Segoe UI", 9),
                            borderwidth=1,
                            relief="flat")
        
        # 侧边栏样式 - 现代渐变效果
        self.style.configure("Sidebar.TFrame", background=primary_color)
        self.style.configure("Sidebar.TButton", 
                            background=primary_color, 
                            foreground="white",
                            borderwidth=0,
                            font=("Segoe UI", 10, "normal"),
                            padding=(15, 12),
                            relief="flat")
        self.style.map("Sidebar.TButton",
                      background=[("active", secondary_color), ("!active", primary_color)],
                      foreground=[("active", "white"), ("!active", "#e2e8f0")],
                      relief=[("active", "flat"), ("!active", "flat")])
        
        # 活跃按钮样式
        self.style.configure("SidebarActive.TButton", 
                            background=accent_color, 
                            foreground="white",
                            borderwidth=0,
                            font=("Segoe UI", 10, "bold"),
                            padding=(15, 12),
                            relief="flat")
        
        # 卡片样式
        self.style.configure("Card.TFrame", 
                            background=card_color,
                            relief="flat",
                            borderwidth=1)
        
        # 标题样式
        self.style.configure("Title.TLabel", 
                            background=background_color,
                            foreground=text_primary,
                            font=("Segoe UI", 18, "bold"))
        
        # 副标题样式
        self.style.configure("Subtitle.TLabel", 
                            background=background_color,
                            foreground=text_secondary,
                            font=("Segoe UI", 11))
        
        # 强调按钮样式
        self.style.configure("Accent.TButton", 
                            background=accent_color,
                            foreground="white",
                            borderwidth=0,
                            font=("Segoe UI", 10, "bold"),
                            padding=(16, 10),
                            relief="flat")
        self.style.map("Accent.TButton",
                      background=[("active", secondary_color), ("!active", accent_color)],
                      foreground=[("active", "white"), ("!active", "white")])
        
        # 输入框样式
        self.style.configure("Modern.TEntry", 
                            fieldbackground=card_color,
                            borderwidth=1,
                            relief="solid",
                            padding=8)
        
        # 组合框样式
        self.style.configure("Modern.TCombobox", 
                            fieldbackground=card_color,
                            borderwidth=1,
                            relief="solid",
                            padding=8)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建侧边栏和内容区域
        self.sidebar = ttk.Frame(self.main_frame, style="Sidebar.TFrame", width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        self.content = ttk.Frame(self.main_frame)
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 固定侧边栏宽度
        self.sidebar.pack_propagate(False)
        
        # 创建侧边栏按钮
        self.create_sidebar()
        
        # 创建屏幕
        self.screens = {}
        self.current_screen = None
        self.create_screens()
        
        # 显示默认屏幕
        self.show_screen("task_execution")
        
    def create_sidebar(self):
        """创建现代化侧边栏"""
        # 顶部品牌区域
        brand_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        brand_frame.pack(fill=tk.X, pady=(20, 30))
        
        # 系统图标和标题
        title_label = ttk.Label(brand_frame, text="🛡️ AI安全响应", 
                              foreground="white", background="#1e3a8a",
                              font=("Segoe UI", 14, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(brand_frame, text="智能应急响应系统", 
                                 foreground="#e2e8f0", background="#1e3a8a",
                                 font=("Segoe UI", 9))
        subtitle_label.pack(pady=(5, 0))
        
        # 导航分隔线
        separator = ttk.Frame(self.sidebar, style="Sidebar.TFrame", height=1)
        separator.pack(fill=tk.X, pady=(0, 20))
        
        # 添加带图标的按钮
        buttons = [
            ("⚡ 任务执行", "task_execution", self.show_task_execution),
            ("📊 报告查看", "report", self.show_report),
            ("📋 增强日志", "enhanced_log", self.show_enhanced_log),
            ("👤 角色管理", "agent_management", self.show_agent_management),
            ("👥 角色组管理", "group_management", self.show_group_management),
            ("🏢 人事部门", "hr_department", self.show_hr_department),
            ("🔧 工具仓库", "tool_warehouse", self.show_tool_warehouse),
            ("⚙️ 系统设置", "settings", self.show_settings)
        ]
        
        self.sidebar_buttons = {}
        for text, name, command in buttons:
            btn = ttk.Button(self.sidebar, text=text, style="Sidebar.TButton", command=command)
            btn.pack(fill=tk.X, pady=1, padx=8)
            self.sidebar_buttons[name] = btn
            
        # 底部状态区域
        status_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        
        # 状态指示器
        status_label = ttk.Label(status_frame, text="🟢 系统运行正常", 
                               foreground="#10b981", background="#1e3a8a",
                               font=("Segoe UI", 8))
        status_label.pack()
        
        # 版本信息
        version_label = ttk.Label(status_frame, text="v1.0.0 Beta", 
                                foreground="#94a3b8", background="#1e3a8a",
                                font=("Segoe UI", 8))
        version_label.pack(pady=(5, 0))
        
    def create_screens(self):
        """创建各个屏幕"""
        # 创建任务执行屏幕
        self.screens["task_execution"] = TaskExecutionScreen(self.content, self)
        
        # 创建报告查看屏幕
        self.screens["report"] = ReportScreen(self.content, self)
        
        # 创建角色管理屏幕
        self.screens["agent_management"] = AgentManagementScreen(self.content, self)
        
        # 创建角色组管理屏幕
        self.screens["group_management"] = GroupManagementScreen(self.content, self)
        
        # 创建设置屏幕
        self.screens["settings"] = SettingsScreen(self.content, self)
        
        # 创建人事部门屏幕
        self.screens["hr_department"] = HRDepartmentScreen(self.content, self)
        
        # 创建工具仓库屏幕
        self.screens["tool_warehouse"] = ToolWarehouseScreen(self.content, self)
        
        # 创建增强日志查看器屏幕
        self.screens["enhanced_log"] = EnhancedLogViewer(self.content)
        
        # 建立人事部门和工具仓库之间的连接
        self.screens["hr_department"].set_tool_warehouse(self.screens["tool_warehouse"])
        self.screens["tool_warehouse"].hr_department = self.screens["hr_department"]
        
    def show_screen(self, screen_name):
        """显示指定屏幕"""
        # 隐藏当前屏幕
        if self.current_screen:
            if hasattr(self.screens[self.current_screen], "on_hide"):
                self.screens[self.current_screen].on_hide()
            self.screens[self.current_screen].pack_forget()
            
            # 重置按钮样式
            self.sidebar_buttons[self.current_screen].configure(style="Sidebar.TButton")
        
        # 显示新屏幕
        self.screens[screen_name].pack(fill=tk.BOTH, expand=True)
        self.current_screen = screen_name
        
        # 设置活跃按钮样式
        self.sidebar_buttons[screen_name].configure(style="SidebarActive.TButton")
        
        # 调用屏幕的on_show方法
        if hasattr(self.screens[screen_name], "on_show"):
            self.screens[screen_name].on_show()
        
    def show_task_execution(self):
        """显示任务执行屏幕"""
        self.show_screen("task_execution")
        
    def show_report(self):
        """显示报告查看屏幕"""
        self.show_screen("report")
        
    def show_agent_management(self):
        """显示角色管理屏幕"""
        self.show_screen("agent_management")
        
    def show_group_management(self):
        """显示角色组管理屏幕"""
        self.show_screen("group_management")
        
    def show_settings(self):
        """显示设置屏幕"""
        self.show_screen("settings")
        
    def show_hr_department(self):
        """显示人事部门屏幕"""
        self.show_screen("hr_department")
        
    def show_tool_warehouse(self):
        """显示工具仓库屏幕"""
        self.show_screen("tool_warehouse")
        
    def show_enhanced_log(self):
        """显示增强日志查看器屏幕"""
        self.show_screen("enhanced_log")
        
    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出吗?"):
            # 停止所有线程
            for screen_name, screen in self.screens.items():
                if hasattr(screen, "on_hide"):
                    screen.on_hide()
            
            self.destroy()