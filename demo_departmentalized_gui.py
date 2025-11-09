#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部门化安全分析系统GUI演示

此脚本用于演示新的部门化GUI界面，不依赖OpenAI API调用
展示部门化仪表盘的功能和布局
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class DemoMainWindow:
    """演示主窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("部门化安全分析系统 - 演示模式")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 配置样式
        self.style.configure('Sidebar.TFrame', background='#2c3e50')
        self.style.configure('SidebarButton.TButton', 
                           background='#34495e', 
                           foreground='white',
                           font=('Microsoft YaHei', 10),
                           padding=(10, 8))
        self.style.map('SidebarButton.TButton',
                      background=[('active', '#3498db')])
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 侧边栏
        sidebar = ttk.Frame(main_frame, style='Sidebar.TFrame', width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar.pack_propagate(False)
        
        # 内容区域
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建侧边栏
        self.create_sidebar(sidebar)
        
        # 默认显示仪表盘
        self.show_dashboard()
        
    def create_sidebar(self, parent):
        """创建侧边栏"""
        # 标题
        title_label = tk.Label(parent, text="安全分析系统", 
                              font=('Microsoft YaHei', 14, 'bold'),
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=(20, 30))
        
        # 按钮
        buttons = [
            ("部门化仪表盘", self.show_dashboard),
            ("任务执行", self.show_task_execution),
            ("报告查看", self.show_reports),
            ("系统设置", self.show_settings)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(parent, text=text, 
                           style='SidebarButton.TButton',
                           command=command)
            btn.pack(fill=tk.X, padx=10, pady=5)
    
    def clear_content(self):
        """清空内容区域"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """显示部门化仪表盘"""
        self.clear_content()
        
        # 仪表盘功能已被移除
        info_label = tk.Label(self.content_frame, 
                             text="仪表盘功能已被移除\n请使用其他功能模块",
                             font=('Microsoft YaHei', 14),
                             fg='blue')
        info_label.pack(pady=50)
    
    def show_task_execution(self):
        """显示任务执行界面"""
        self.clear_content()
        
        # 创建任务执行演示界面
        title = tk.Label(self.content_frame, text="任务执行 - 部门化工作流程",
                        font=('Microsoft YaHei', 16, 'bold'))
        title.pack(pady=20)
        
        # 部门工作流程展示
        workflow_frame = ttk.LabelFrame(self.content_frame, text="部门化工作流程", padding=20)
        workflow_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        departments = [
            ("进程部门", "负责进程监控和分析", "#3498db"),
            ("日志部门", "负责日志收集和分析", "#e74c3c"),
            ("服务部门", "负责服务状态监控", "#2ecc71"),
            ("网络部门", "负责网络安全分析", "#f39c12"),
            ("威胁整合部门", "负责综合安全分析和报告生成", "#9b59b6")
        ]
        
        for i, (name, desc, color) in enumerate(departments):
            dept_frame = tk.Frame(workflow_frame, bg=color, relief=tk.RAISED, bd=2)
            dept_frame.pack(fill=tk.X, pady=5)
            
            name_label = tk.Label(dept_frame, text=f"{i+1}. {name}", 
                                 font=('Microsoft YaHei', 12, 'bold'),
                                 bg=color, fg='white')
            name_label.pack(anchor=tk.W, padx=10, pady=5)
            
            desc_label = tk.Label(dept_frame, text=desc,
                                 font=('Microsoft YaHei', 10),
                                 bg=color, fg='white')
            desc_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
    
    def show_reports(self):
        """显示报告界面"""
        self.clear_content()
        
        title = tk.Label(self.content_frame, text="部门化安全报告",
                        font=('Microsoft YaHei', 16, 'bold'))
        title.pack(pady=20)
        
        # 报告列表
        report_frame = ttk.LabelFrame(self.content_frame, text="最近的部门报告", padding=20)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建报告树形视图
        columns = ('部门', '时间', '状态', '威胁数量')
        tree = ttk.Treeview(report_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # 添加示例数据
        sample_reports = [
            ('进程部门', '2024-01-15 10:30', '正常', '0'),
            ('日志部门', '2024-01-15 10:25', '警告', '2'),
            ('服务部门', '2024-01-15 10:20', '正常', '0'),
            ('网络部门', '2024-01-15 10:15', '正常', '1'),
            ('威胁整合部门', '2024-01-15 10:35', '已完成', '3')
        ]
        
        for report in sample_reports:
            tree.insert('', tk.END, values=report)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_settings(self):
        """显示设置界面"""
        self.clear_content()
        
        title = tk.Label(self.content_frame, text="系统设置",
                        font=('Microsoft YaHei', 16, 'bold'))
        title.pack(pady=20)
        
        settings_frame = ttk.LabelFrame(self.content_frame, text="部门化配置", padding=20)
        settings_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 设置选项
        settings = [
            ("启用进程部门", True),
            ("启用日志部门", True),
            ("启用服务部门", True),
            ("启用网络部门", True),
            ("自动生成综合报告", True),
            ("实时监控模式", False)
        ]
        
        for setting, default in settings:
            var = tk.BooleanVar(value=default)
            cb = ttk.Checkbutton(settings_frame, text=setting, variable=var)
            cb.pack(anchor=tk.W, pady=5)
    
    def run(self):
        """运行应用"""
        self.root.mainloop()

def main():
    """主函数"""
    print("启动部门化安全分析系统GUI演示...")
    print("注意：这是演示模式，不会进行实际的安全分析")
    print("主要展示新的部门化界面布局和功能")
    
    app = DemoMainWindow()
    app.run()

if __name__ == "__main__":
    main()