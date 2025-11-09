# -*- coding: utf-8 -*-
"""
增强日志查看器界面
支持按角色组查看详细的报告和操作记录
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class EnhancedLogViewer(ttk.Frame):
    """
    增强日志查看器
    支持按角色组、角色、日期查看日志
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # 初始化日志目录
        self.base_log_dir = self._get_log_directory()
        self.enhanced_log_dir = self.base_log_dir / "enhanced"
        
        # 创建界面
        self._create_widgets()
        
        # 加载初始数据
        self._load_initial_data()
    
    def _get_log_directory(self) -> Path:
        """
        获取日志目录路径
        """
        try:
            # 获取项目根目录
            current_dir = Path(__file__).parent
            while current_dir.parent != current_dir:
                if (current_dir / "config").exists():
                    return current_dir / "config" / "log"
                current_dir = current_dir.parent
            
            # 如果找不到，使用默认路径
            return Path.cwd() / "config" / "log"
        except Exception:
            return Path.cwd() / "config" / "log"
    
    def _create_widgets(self):
        """
        创建界面组件
        """
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="增强日志查看器", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="筛选条件", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行：角色组和日期选择
        row1_frame = ttk.Frame(control_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 角色组选择
        ttk.Label(row1_frame, text="角色组:").pack(side=tk.LEFT, padx=(0, 5))
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(row1_frame, textvariable=self.group_var, width=20)
        self.group_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.group_combo.bind('<<ComboboxSelected>>', self._on_group_changed)
        
        # 日期选择
        ttk.Label(row1_frame, text="日期:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_combo = ttk.Combobox(row1_frame, textvariable=self.date_var, width=15)
        self.date_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 刷新按钮
        ttk.Button(row1_frame, text="刷新", command=self._refresh_data).pack(side=tk.LEFT, padx=(0, 10))
        
        # 导出按钮
        ttk.Button(row1_frame, text="导出日志", command=self._export_logs).pack(side=tk.LEFT)
        
        # 第二行：角色和报告类型选择
        row2_frame = ttk.Frame(control_frame)
        row2_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 角色选择
        ttk.Label(row2_frame, text="角色:").pack(side=tk.LEFT, padx=(0, 5))
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(row2_frame, textvariable=self.role_var, width=20)
        self.role_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.role_combo.bind('<<ComboboxSelected>>', self._on_role_changed)
        
        # 报告类型选择
        ttk.Label(row2_frame, text="类型:").pack(side=tk.LEFT, padx=(0, 5))
        self.type_var = tk.StringVar(value="全部")
        self.type_combo = ttk.Combobox(row2_frame, textvariable=self.type_var, 
                                      values=["全部", "执行前报告", "执行后报告", "操作记录"], width=15)
        self.type_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)
        
        # 搜索框
        ttk.Label(row2_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(row2_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self._on_search_changed)
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：日志列表
        left_frame = ttk.LabelFrame(content_frame, text="日志列表", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 日志列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ('时间', '角色', '类型', '摘要')
        self.log_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.log_tree.heading('时间', text='时间')
        self.log_tree.heading('角色', text='角色')
        self.log_tree.heading('类型', text='类型')
        self.log_tree.heading('摘要', text='摘要')
        
        self.log_tree.column('时间', width=150)
        self.log_tree.column('角色', width=120)
        self.log_tree.column('类型', width=100)
        self.log_tree.column('摘要', width=300)
        
        # 滚动条
        log_scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        log_scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=log_scrollbar_y.set, xscrollcommand=log_scrollbar_x.set)
        
        # 布局
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        log_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定选择事件
        self.log_tree.bind('<<TreeviewSelect>>', self._on_log_selected)
        
        # 右侧：详细内容
        right_frame = ttk.LabelFrame(content_frame, text="详细内容", padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 详细内容显示
        detail_frame = ttk.Frame(right_frame)
        detail_frame.pack(fill=tk.BOTH, expand=True)
        
        self.detail_text = tk.Text(detail_frame, wrap=tk.WORD, font=('Consolas', 10))
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)
        
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
        
        # 统计信息
        self.stats_label = ttk.Label(status_frame, text="")
        self.stats_label.pack(side=tk.RIGHT)
    
    def _load_initial_data(self):
        """
        加载初始数据
        """
        try:
            # 加载角色组列表
            self._load_groups()
            
            # 加载日期列表
            self._load_dates()
            
            # 设置默认选择
            if self.group_combo['values']:
                self.group_var.set(self.group_combo['values'][0])
                self._on_group_changed()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载初始数据失败: {str(e)}")
    
    def _load_groups(self):
        """
        加载角色组列表
        """
        groups = []
        
        if self.enhanced_log_dir.exists():
            groups_dir = self.enhanced_log_dir / "groups"
            if groups_dir.exists():
                for group_dir in groups_dir.iterdir():
                    if group_dir.is_dir():
                        groups.append(group_dir.name)
        
        # 添加"全部"选项
        groups.insert(0, "全部")
        self.group_combo['values'] = groups
    
    def _load_dates(self):
        """
        加载可用日期列表
        """
        dates = set()
        
        # 从增强日志中获取日期
        if self.enhanced_log_dir.exists():
            for log_file in self.enhanced_log_dir.rglob("*.json"):
                # 从文件名中提取日期
                filename = log_file.name
                if "_" in filename:
                    parts = filename.split("_")
                    for part in parts:
                        if len(part) == 10 and part.count("-") == 2:
                            try:
                                datetime.strptime(part, "%Y-%m-%d")
                                dates.add(part)
                            except ValueError:
                                continue
        
        # 添加最近7天的日期
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            dates.add(date)
        
        # 排序并设置到下拉框
        sorted_dates = sorted(list(dates), reverse=True)
        self.date_combo['values'] = sorted_dates
    
    def _on_group_changed(self, event=None):
        """
        角色组选择改变事件
        """
        group_id = self.group_var.get()
        
        # 加载该角色组的角色列表
        self._load_roles(group_id)
        
        # 刷新日志列表
        self._refresh_logs()
    
    def _load_roles(self, group_id: str):
        """
        加载指定角色组的角色列表
        """
        roles = []
        
        if group_id == "全部":
            # 加载所有角色
            if self.enhanced_log_dir.exists():
                roles_dir = self.enhanced_log_dir / "roles"
                if roles_dir.exists():
                    for role_dir in roles_dir.iterdir():
                        if role_dir.is_dir():
                            roles.append(role_dir.name)
        else:
            # 加载特定角色组的角色
            group_dir = self.enhanced_log_dir / "groups" / group_id
            if group_dir.exists():
                # 从日志文件中提取角色信息
                for log_file in group_dir.rglob("*.json"):
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            records = json.load(f)
                            for record in records:
                                role_name = record.get('role_name')
                                if role_name and role_name not in roles:
                                    roles.append(role_name)
                    except Exception:
                        continue
        
        # 添加"全部"选项
        roles.insert(0, "全部")
        self.role_combo['values'] = roles
        self.role_var.set("全部")
    
    def _on_role_changed(self, event=None):
        """
        角色选择改变事件
        """
        self._refresh_logs()
    
    def _on_type_changed(self, event=None):
        """
        类型选择改变事件
        """
        self._refresh_logs()
    
    def _on_search_changed(self, event=None):
        """
        搜索内容改变事件
        """
        self._refresh_logs()
    
    def _refresh_data(self):
        """
        刷新所有数据
        """
        self._load_groups()
        self._load_dates()
        self._refresh_logs()
    
    def _refresh_logs(self):
        """
        刷新日志列表
        """
        try:
            # 清空现有列表
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)
            
            # 获取筛选条件
            group_id = self.group_var.get()
            role_name = self.role_var.get()
            log_type = self.type_var.get()
            date = self.date_var.get()
            search_text = self.search_var.get().lower()
            
            # 加载日志记录
            logs = self._load_logs(group_id, role_name, log_type, date, search_text)
            
            # 添加到列表
            for log in logs:
                self.log_tree.insert('', 'end', values=(
                    log.get('timestamp', ''),
                    log.get('role_name', ''),
                    log.get('display_type', ''),
                    log.get('summary', '')
                ), tags=(log.get('record_type', ''),))
            
            # 更新统计信息
            self.stats_label.config(text=f"共 {len(logs)} 条记录")
            self.status_label.config(text="日志加载完成")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新日志失败: {str(e)}")
            self.status_label.config(text=f"加载失败: {str(e)}")
    
    def _load_logs(self, group_id: str, role_name: str, log_type: str, date: str, search_text: str) -> List[Dict]:
        """
        加载日志记录
        """
        logs = []
        
        try:
            # 确定搜索路径
            search_paths = []
            
            if group_id == "全部":
                # 搜索所有组
                if self.enhanced_log_dir.exists():
                    groups_dir = self.enhanced_log_dir / "groups"
                    if groups_dir.exists():
                        for group_dir in groups_dir.iterdir():
                            if group_dir.is_dir():
                                search_paths.append(group_dir)
            else:
                # 搜索特定组
                group_dir = self.enhanced_log_dir / "groups" / group_id
                if group_dir.exists():
                    search_paths.append(group_dir)
            
            # 从每个路径加载日志
            for path in search_paths:
                logs.extend(self._load_logs_from_path(path, role_name, log_type, date, search_text))
            
            # 按时间排序
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            print(f"加载日志失败: {e}")
        
        return logs
    
    def _load_logs_from_path(self, path: Path, role_name: str, log_type: str, date: str, search_text: str) -> List[Dict]:
        """
        从指定路径加载日志记录
        """
        logs = []
        
        try:
            # 查找匹配的日志文件
            pattern = f"*{date}.json" if date else "*.json"
            
            for log_file in path.rglob(pattern):
                if not log_file.is_file():
                    continue
                
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                        
                        for record in records:
                            # 应用筛选条件
                            if not self._match_filters(record, role_name, log_type, search_text):
                                continue
                            
                            # 添加显示信息
                            display_record = record.copy()
                            display_record['display_type'] = self._get_display_type(record)
                            display_record['summary'] = self._get_summary(record)
                            display_record['record_type'] = record.get('report_type', record.get('operation_type', 'unknown'))
                            
                            logs.append(display_record)
                            
                except Exception as e:
                    print(f"读取日志文件失败 {log_file}: {e}")
                    continue
        
        except Exception as e:
            print(f"从路径加载日志失败 {path}: {e}")
        
        return logs
    
    def _match_filters(self, record: Dict, role_name: str, log_type: str, search_text: str) -> bool:
        """
        检查记录是否匹配筛选条件
        """
        # 角色筛选
        if role_name != "全部" and record.get('role_name') != role_name:
            return False
        
        # 类型筛选
        if log_type != "全部":
            record_type = record.get('report_type', record.get('operation_type', ''))
            if log_type == "执行前报告" and record_type != "pre_execution":
                return False
            elif log_type == "执行后报告" and record_type != "post_execution":
                return False
            elif log_type == "操作记录" and 'operation' not in record:
                return False
        
        # 搜索文本筛选
        if search_text:
            searchable_text = (
                record.get('content', '') + ' ' +
                record.get('operation', '') + ' ' +
                record.get('role_name', '') + ' ' +
                str(record.get('result', ''))
            ).lower()
            
            if search_text not in searchable_text:
                return False
        
        return True
    
    def _get_display_type(self, record: Dict) -> str:
        """
        获取显示类型
        """
        if 'report_type' in record:
            type_map = {
                'pre_execution': '执行前报告',
                'post_execution': '执行后报告',
                'analysis': '分析报告'
            }
            return type_map.get(record['report_type'], record['report_type'])
        elif 'operation' in record:
            return '操作记录'
        else:
            return '未知类型'
    
    def _get_summary(self, record: Dict) -> str:
        """
        获取记录摘要
        """
        if 'content' in record:
            content = record['content'][:100].replace('\n', ' ').strip()
            return content + '...' if len(record['content']) > 100 else content
        elif 'operation' in record:
            return record['operation'][:100]
        else:
            return '无摘要'
    
    def _on_log_selected(self, event):
        """
        日志选择事件
        """
        selection = self.log_tree.selection()
        if not selection:
            return
        
        # 获取选中的记录
        item = self.log_tree.item(selection[0])
        values = item['values']
        
        if len(values) >= 4:
            timestamp = values[0]
            role_name = values[1]
            
            # 查找完整记录
            record = self._find_record_by_timestamp_and_role(timestamp, role_name)
            if record:
                self._display_record_detail(record)
    
    def _find_record_by_timestamp_and_role(self, timestamp: str, role_name: str) -> Optional[Dict]:
        """
        根据时间戳和角色名查找完整记录
        """
        try:
            # 从时间戳中提取日期
            date = timestamp.split(' ')[0]
            
            # 搜索所有可能的日志文件
            search_paths = []
            if self.enhanced_log_dir.exists():
                search_paths.extend(self.enhanced_log_dir.rglob(f"*{date}.json"))
            
            for log_file in search_paths:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                        for record in records:
                            if (record.get('timestamp') == timestamp and 
                                record.get('role_name') == role_name):
                                return record
                except Exception:
                    continue
        
        except Exception as e:
            print(f"查找记录失败: {e}")
        
        return None
    
    def _display_record_detail(self, record: Dict):
        """
        显示记录详细信息
        """
        self.detail_text.delete(1.0, tk.END)
        
        # 格式化显示内容
        detail_content = self._format_record_detail(record)
        
        self.detail_text.insert(1.0, detail_content)
        
        # 设置只读
        self.detail_text.config(state=tk.DISABLED)
    
    def _format_record_detail(self, record: Dict) -> str:
        """
        格式化记录详细信息
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"时间: {record.get('timestamp', 'N/A')}")
        lines.append(f"角色: {record.get('role_name', 'N/A')}")
        lines.append(f"角色组: {record.get('group_id', 'N/A')}")
        
        if 'report_type' in record:
            lines.append(f"报告类型: {record['report_type']}")
            lines.append("=" * 60)
            lines.append("报告内容:")
            lines.append(record.get('content', 'N/A'))
            
            if 'metadata' in record and record['metadata']:
                lines.append("\n" + "=" * 60)
                lines.append("元数据:")
                for key, value in record['metadata'].items():
                    lines.append(f"  {key}: {value}")
        
        elif 'operation' in record:
            lines.append(f"操作类型: {record.get('operation_type', 'N/A')}")
            lines.append("=" * 60)
            lines.append(f"操作描述: {record.get('operation', 'N/A')}")
            lines.append("\n操作结果:")
            lines.append(str(record.get('result', 'N/A')))
            
            if 'metadata' in record and record['metadata']:
                lines.append("\n" + "=" * 60)
                lines.append("元数据:")
                for key, value in record['metadata'].items():
                    lines.append(f"  {key}: {value}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def _export_logs(self):
        """
        导出日志
        """
        try:
            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                title="导出日志",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if not filename:
                return
            
            # 获取当前显示的日志
            group_id = self.group_var.get()
            role_name = self.role_var.get()
            log_type = self.type_var.get()
            date = self.date_var.get()
            search_text = self.search_var.get().lower()
            
            logs = self._load_logs(group_id, role_name, log_type, date, search_text)
            
            # 根据文件扩展名选择导出格式
            if filename.endswith('.json'):
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    for log in logs:
                        f.write(self._format_record_detail(log))
                        f.write("\n\n")
            
            messagebox.showinfo("成功", f"日志已导出到: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出日志失败: {str(e)}")

# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("增强日志查看器")
    root.geometry("1200x800")
    
    viewer = EnhancedLogViewer(root)
    viewer.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()