#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import threading
import time
from datetime import datetime

class ReportScreen(ttk.Frame):
    """报告查看界面"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.reports = []
        self.current_report = None
        
        # 创建界面
        self._create_widgets()
        
        # 加载报告
        self._load_reports()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 主分割窗口
        self.main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧报告列表框架
        self.reports_frame = ttk.LabelFrame(self.main_paned, text="报告列表")
        self.main_paned.add(self.reports_frame, weight=1)
        
        # 报告列表
        self.reports_tree = ttk.Treeview(self.reports_frame, columns=("日期", "类型"), show="headings")
        self.reports_tree.heading("日期", text="日期")
        self.reports_tree.heading("类型", text="类型")
        self.reports_tree.column("日期", width=150)
        self.reports_tree.column("类型", width=100)
        self.reports_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 报告列表滚动条
        self.reports_scrollbar = ttk.Scrollbar(self.reports_tree, orient="vertical", command=self.reports_tree.yview)
        self.reports_tree.configure(yscrollcommand=self.reports_scrollbar.set)
        self.reports_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 报告列表选择事件
        self.reports_tree.bind("<<TreeviewSelect>>", self._on_report_selected)
        
        # 右侧报告详情框架
        self.details_frame = ttk.LabelFrame(self.main_paned, text="报告详情")
        self.main_paned.add(self.details_frame, weight=2)
        
        # 报告详情内容框架
        self.details_content = ttk.Frame(self.details_frame)
        self.details_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 报告标题
        self.report_title = ttk.Label(self.details_content, text="选择一个报告查看详情", font=("Arial", 12, "bold"))
        self.report_title.pack(fill=tk.X, pady=(0, 10))
        
        # 报告元数据
        self.metadata_frame = ttk.LabelFrame(self.details_content, text="报告信息")
        self.metadata_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建网格布局
        for i in range(3):
            self.metadata_frame.columnconfigure(i, weight=1)
            
        # 报告日期
        ttk.Label(self.metadata_frame, text="日期:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.report_date = ttk.Label(self.metadata_frame, text="")
        self.report_date.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 报告类型
        ttk.Label(self.metadata_frame, text="类型:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.report_type = ttk.Label(self.metadata_frame, text="")
        self.report_type.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 生成者
        ttk.Label(self.metadata_frame, text="生成者:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.report_generator = ttk.Label(self.metadata_frame, text="")
        self.report_generator.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 报告内容
        self.content_notebook = ttk.Notebook(self.details_content)
        self.content_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 摘要选项卡
        self.summary_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.summary_frame, text="摘要")
        
        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.config(state=tk.DISABLED)
        
        # 详细内容选项卡
        self.details_tab = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.details_tab, text="详细内容")
        
        self.details_text = scrolledtext.ScrolledText(self.details_tab, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.details_text.config(state=tk.DISABLED)
        
        # 建议选项卡
        self.recommendations_tab = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.recommendations_tab, text="建议")
        
        self.recommendations_text = scrolledtext.ScrolledText(self.recommendations_tab, wrap=tk.WORD)
        self.recommendations_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.recommendations_text.config(state=tk.DISABLED)
        
        # 按钮区域
        self.button_frame = ttk.Frame(self.details_content)
        self.button_frame.pack(fill=tk.X)
        
        self.export_button = ttk.Button(self.button_frame, text="导出报告", command=self._export_report)
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(self.button_frame, text="删除报告", command=self._delete_report)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # 禁用按钮
        self.export_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        
    def _load_reports(self):
        """加载报告列表"""
        # 清空报告列表
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
            
        # 加载报告
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
        
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
            return
            
        self.reports = []
        
        # 遍历报告目录
        for filename in os.listdir(reports_dir):
            if filename.endswith(".json"):
                try:
                    report_path = os.path.join(reports_dir, filename)
                    with open(report_path, "r", encoding="utf-8") as f:
                        report = json.load(f)
                        
                    # 添加文件路径
                    report["file_path"] = report_path
                    
                    # 添加到报告列表
                    self.reports.append(report)
                    
                    # 添加到树形视图
                    report_date = report.get("date", "未知日期")
                    report_type = report.get("type", "未知类型")
                    
                    self.reports_tree.insert("", "end", report_path, values=(report_date, report_type))
                    
                except Exception as e:
                    print(f"加载报告失败: {str(e)}")
                    
        # 按日期排序
        self.reports.sort(key=lambda x: x.get("date", ""), reverse=True)
        
    def _on_report_selected(self, event):
        """报告选择事件"""
        selected_items = self.reports_tree.selection()
        if not selected_items:
            return
            
        report_path = selected_items[0]
        self._display_report(report_path)
        
    def _display_report(self, report_path):
        """显示报告详情"""
        # 查找报告
        report = None
        for r in self.reports:
            if r.get("file_path") == report_path:
                report = r
                break
                
        if not report:
            return
            
        self.current_report = report
        
        # 更新报告标题
        self.report_title.config(text=report.get("title", "未命名报告"))
        
        # 更新报告元数据
        self.report_date.config(text=report.get("date", "未知日期"))
        self.report_type.config(text=report.get("type", "未知类型"))
        self.report_generator.config(text=report.get("generator", "未知生成者"))
        
        # 更新摘要
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, report.get("summary", "无摘要信息"))
        self.summary_text.config(state=tk.DISABLED)
        
        # 更新详细内容
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        details = report.get("details", [])
        if isinstance(details, list):
            for item in details:
                if isinstance(item, dict):
                    title = item.get("title", "")
                    content = item.get("content", "")
                    self.details_text.insert(tk.END, f"{title}\n\n")
                    self.details_text.insert(tk.END, f"{content}\n\n")
                    self.details_text.insert(tk.END, "-" * 50 + "\n\n")
                else:
                    self.details_text.insert(tk.END, f"{item}\n\n")
        else:
            self.details_text.insert(tk.END, str(details))
            
        self.details_text.config(state=tk.DISABLED)
        
        # 更新建议
        self.recommendations_text.config(state=tk.NORMAL)
        self.recommendations_text.delete(1.0, tk.END)
        
        recommendations = report.get("recommendations", [])
        if isinstance(recommendations, list):
            for i, item in enumerate(recommendations, 1):
                self.recommendations_text.insert(tk.END, f"{i}. {item}\n\n")
        else:
            self.recommendations_text.insert(tk.END, str(recommendations))
            
        self.recommendations_text.config(state=tk.DISABLED)
        
        # 启用按钮
        self.export_button.config(state=tk.NORMAL)
        self.delete_button.config(state=tk.NORMAL)
        
    def _export_report(self):
        """导出报告"""
        if not self.current_report:
            return
            
        # 选择导出路径
        filename = filedialog.asksaveasfilename(
            title="导出报告",
            defaultextension=".html",
            filetypes=(("HTML文件", "*.html"), ("文本文件", "*.txt"), ("所有文件", "*.*"))
        )
        
        if not filename:
            return
            
        try:
            # 根据文件扩展名选择导出格式
            if filename.endswith(".html"):
                self._export_as_html(filename)
            elif filename.endswith(".txt"):
                self._export_as_text(filename)
            else:
                self._export_as_html(filename)
                
            messagebox.showinfo("导出成功", f"报告已成功导出到: {filename}")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"导出报告失败: {str(e)}")
            
    def _export_as_html(self, filename):
        """导出为HTML格式"""
        if not self.current_report:
            return
            
        report = self.current_report
        
        # 预处理内容，将换行符替换为HTML换行标签
        summary = report.get("summary", "无摘要信息").replace("\n", "<br>")
        
        # 创建HTML内容
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report.get("title", "安全报告")}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; margin-top: 20px; }}
        .metadata {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        .metadata p {{ margin: 5px 0; }}
        .section {{ margin-bottom: 30px; }}
        .recommendation {{ background-color: #e8f4f8; padding: 10px; border-left: 4px solid #3498db; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <h1>{report.get("title", "安全报告")}</h1>
    
    <div class="metadata">
        <p><strong>日期:</strong> {report.get("date", "未知日期")}</p>
        <p><strong>类型:</strong> {report.get("type", "未知类型")}</p>
        <p><strong>生成者:</strong> {report.get("generator", "未知生成者")}</p>
    </div>
    
    <div class="section">
        <h2>摘要</h2>
        <p>{summary}</p>
    </div>
    
    <div class="section">
        <h2>详细内容</h2>
"""
        
        # 添加详细内容
        details = report.get("details", [])
        if isinstance(details, list):
            for item in details:
                if isinstance(item, dict):
                    title = item.get("title", "")
                    content = item.get("content", "").replace("\n", "<br>")
                    html += f"        <h3>{title}</h3>\n"
                    html += f"        <p>{content}</p>\n"
                    html += f"        <hr>\n"
                else:
                    item_str = str(item).replace("\n", "<br>")
                    html += f"        <p>{item_str}</p>\n"
        else:
            details_str = str(details).replace("\n", "<br>")
            html += f"        <p>{details_str}</p>\n"
            
        html += """    </div>
    
    <div class="section">
        <h2>建议</h2>
"""
        
        # 添加建议
        recommendations = report.get("recommendations", [])
        if isinstance(recommendations, list):
            for i, item in enumerate(recommendations, 1):
                item_str = str(item).replace("\n", "<br>")
                html += f'        <div class="recommendation">{i}. {item_str}</div>\n'
        else:
            rec_str = str(recommendations).replace("\n", "<br>")
            html += f'        <div class="recommendation">{rec_str}</div>\n'
            
        html += """    </div>
</body>
</html>"""
        
        # 写入文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
            
    def _export_as_text(self, filename):
        """导出为文本格式"""
        if not self.current_report:
            return
            
        report = self.current_report
        
        # 创建文本内容
        text = f"""{report.get("title", "安全报告")}
{"-" * 50}

日期: {report.get("date", "未知日期")}
类型: {report.get("type", "未知类型")}
生成者: {report.get("generator", "未知生成者")}

摘要:
{report.get("summary", "无摘要信息")}

详细内容:
"""
        
        # 添加详细内容
        details = report.get("details", [])
        if isinstance(details, list):
            for item in details:
                if isinstance(item, dict):
                    title = item.get("title", "")
                    content = item.get("content", "")
                    text += f"\n{title}\n\n"
                    text += f"{content}\n\n"
                    text += "-" * 50 + "\n"
                else:
                    text += f"\n{item}\n\n"
        else:
            text += f"\n{details}\n\n"
            
        text += "\n建议:\n"
        
        # 添加建议
        recommendations = report.get("recommendations", [])
        if isinstance(recommendations, list):
            for i, item in enumerate(recommendations, 1):
                text += f"\n{i}. {item}\n"
        else:
            text += f"\n{recommendations}\n"
            
        # 写入文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
            
    def _delete_report(self):
        """删除报告"""
        if not self.current_report:
            return
            
        if messagebox.askyesno("确认删除", "确定要删除此报告吗？此操作不可撤销。"):
            try:
                # 删除文件
                os.remove(self.current_report["file_path"])
                
                # 从树形视图中删除
                self.reports_tree.delete(self.current_report["file_path"])
                
                # 从报告列表中删除
                self.reports.remove(self.current_report)
                
                # 清除当前报告
                self.current_report = None
                
                # 重置界面
                self.report_title.config(text="选择一个报告查看详情")
                self.report_date.config(text="")
                self.report_type.config(text="")
                self.report_generator.config(text="")
                
                self.summary_text.config(state=tk.NORMAL)
                self.summary_text.delete(1.0, tk.END)
                self.summary_text.config(state=tk.DISABLED)
                
                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete(1.0, tk.END)
                self.details_text.config(state=tk.DISABLED)
                
                self.recommendations_text.config(state=tk.NORMAL)
                self.recommendations_text.delete(1.0, tk.END)
                self.recommendations_text.config(state=tk.DISABLED)
                
                # 禁用按钮
                self.export_button.config(state=tk.DISABLED)
                self.delete_button.config(state=tk.DISABLED)
                
                messagebox.showinfo("删除成功", "报告已成功删除")
                
            except Exception as e:
                messagebox.showerror("删除失败", f"删除报告失败: {str(e)}")
                
    def on_show(self):
        """显示界面时调用"""
        # 重新加载报告
        self._load_reports()
        
    def on_hide(self):
        """隐藏界面时调用"""
        pass