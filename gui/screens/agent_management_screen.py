# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import threading
from typing import Dict, List
from gui.utils.agent_template_manager import AgentTemplateManager

class AgentManagementScreen(ttk.Frame):
    """Agent角色管理界面"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.agents_config = {}
        self.current_group = "default_group"
        self.selected_agent = None
        self.template_manager = AgentTemplateManager()
        
        # 创建界面
        self._create_widgets()
        
        # 加载配置
        self._load_agents_config()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Agent角色管理", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 工具栏
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 角色组选择
        ttk.Label(toolbar_frame, text="角色组:").pack(side=tk.LEFT, padx=(0, 5))
        self.group_var = tk.StringVar(value=self.current_group)
        self.group_combo = ttk.Combobox(toolbar_frame, textvariable=self.group_var, 
                                       values=["default_group", "custom_group"],
                                       state="readonly", width=15)
        self.group_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_changed)
        
        # 操作按钮
        ttk.Button(toolbar_frame, text="新建Agent", command=self._create_new_agent).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="从模板创建", command=self._create_from_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="复制Agent", command=self._copy_agent).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="删除Agent", command=self._delete_agent).pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        ttk.Button(toolbar_frame, text="保存配置", command=self._save_config).pack(side=tk.RIGHT, padx=5)
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：Agent列表
        left_frame = ttk.LabelFrame(content_frame, text="Agent列表")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), ipadx=10, ipady=10)
        
        # Agent列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.agent_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=25)
        self.agent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.agent_listbox.yview)
        
        self.agent_listbox.bind("<<ListboxSelect>>", self._on_agent_selected)
        
        # 右侧：Agent详情编辑
        right_frame = ttk.LabelFrame(content_frame, text="Agent详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, ipadx=10, ipady=10)
        
        # 创建详情编辑区域
        self._create_detail_widgets(right_frame)
        
    def _create_detail_widgets(self, parent):
        """创建详情编辑区域"""
        # 滚动框架
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Agent基本信息
        basic_frame = ttk.LabelFrame(scrollable_frame, text="基本信息")
        basic_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Agent ID
        ttk.Label(basic_frame, text="Agent ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.agent_id_var = tk.StringVar()
        self.agent_id_entry = ttk.Entry(basic_frame, textvariable=self.agent_id_var, width=30)
        self.agent_id_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 角色名称
        ttk.Label(basic_frame, text="角色名称:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.role_var = tk.StringVar()
        self.role_entry = ttk.Entry(basic_frame, textvariable=self.role_var, width=30)
        self.role_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 目标
        ttk.Label(basic_frame, text="目标:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.goal_text = tk.Text(basic_frame, width=40, height=3)
        self.goal_text.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 背景故事
        ttk.Label(basic_frame, text="背景故事:").grid(row=3, column=0, sticky=tk.NW, padx=5, pady=5)
        self.backstory_text = tk.Text(basic_frame, width=40, height=4)
        self.backstory_text.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 部门
        ttk.Label(basic_frame, text="所属部门:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.department_var = tk.StringVar()
        self.department_combo = ttk.Combobox(basic_frame, textvariable=self.department_var,
                                           values=["process_department", "log_department", 
                                                  "service_department", "network_department",
                                                  "response_department", "coordination_department"],
                                           width=27)
        self.department_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 工具配置
        tools_frame = ttk.LabelFrame(scrollable_frame, text="工具配置")
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        
        # 可用工具列表
        available_frame = ttk.Frame(tools_frame)
        available_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(available_frame, text="可用工具:").pack(anchor=tk.W)
        self.available_tools_listbox = tk.Listbox(available_frame, height=8)
        self.available_tools_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 中间按钮
        button_frame = ttk.Frame(tools_frame)
        button_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="→", command=self._add_tool, width=5).pack(pady=2)
        ttk.Button(button_frame, text="←", command=self._remove_tool, width=5).pack(pady=2)
        
        # 已选工具列表
        selected_frame = ttk.Frame(tools_frame)
        selected_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(selected_frame, text="已选工具:").pack(anchor=tk.W)
        self.selected_tools_listbox = tk.Listbox(selected_frame, height=8)
        self.selected_tools_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 加载可用工具
        self._load_available_tools()
        
    def _load_available_tools(self):
        """加载可用工具列表"""
        tools = [
            "GetProcessDetails", "GetServices", "GetWindowsLogs", "GetNetworkConnections",
            "CompareWithBaseline", "AnalyzeProcessBehavior", "AnalyzeSecurityLogs",
            "AnalyzeServiceSecurity", "AnalyzeNetworkTraffic", "DetectSuspiciousConnections",
            "CorrelateEvents", "CheckServiceIntegrity", "TerminateProcess", "BlockIP",
            "AddToWhitelist", "CheckWhitelist", "LoadProcessHistory", "LoadLogHistory",
            "LoadServiceHistory", "LoadNetworkHistory", "LoadAllDepartmentHistory",
            "SaveProcessAnalysis", "SaveLogAnalysis", "SaveServiceAnalysis",
            "SaveNetworkAnalysis", "FilterProcessesByTime", "FilterLogsByTime",
            "FilterServicesByTime", "FilterConnectionsByTime", "GenerateSecurityReport",
            "AddSuggestionNote", "GetSuggestionNotes", "LogAgentReport"
        ]
        
        for tool in tools:
            self.available_tools_listbox.insert(tk.END, tool)
    
    def _load_agents_config(self):
        """加载Agent配置"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      "config", "json", "agents_config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                self.agents_config = json.load(f)
            self._refresh_agent_list()
        except Exception as e:
            messagebox.showerror("错误", f"加载Agent配置失败: {str(e)}")
            self.agents_config = {"default_group": {}, "custom_group": {}}
    
    def _refresh_agent_list(self):
        """刷新Agent列表"""
        self.agent_listbox.delete(0, tk.END)
        if self.current_group in self.agents_config:
            for agent_id in self.agents_config[self.current_group].keys():
                self.agent_listbox.insert(tk.END, agent_id)
    
    def _on_group_changed(self, event=None):
        """角色组改变事件"""
        self.current_group = self.group_var.get()
        self._refresh_agent_list()
        self._clear_detail_form()
    
    def _on_agent_selected(self, event=None):
        """Agent选择事件"""
        selection = self.agent_listbox.curselection()
        if selection:
            agent_id = self.agent_listbox.get(selection[0])
            self.selected_agent = agent_id
            self._load_agent_details(agent_id)
    
    def _load_agent_details(self, agent_id):
        """加载Agent详情"""
        if self.current_group in self.agents_config and agent_id in self.agents_config[self.current_group]:
            agent_config = self.agents_config[self.current_group][agent_id]
            
            # 填充基本信息
            self.agent_id_var.set(agent_id)
            self.role_var.set(agent_config.get("role", ""))
            
            self.goal_text.delete(1.0, tk.END)
            self.goal_text.insert(1.0, agent_config.get("goal", ""))
            
            self.backstory_text.delete(1.0, tk.END)
            self.backstory_text.insert(1.0, agent_config.get("backstory", ""))
            
            self.department_var.set(agent_config.get("department", ""))
            
            # 填充工具列表
            self.selected_tools_listbox.delete(0, tk.END)
            for tool in agent_config.get("tools", []):
                self.selected_tools_listbox.insert(tk.END, tool)
    
    def _clear_detail_form(self):
        """清空详情表单"""
        self.agent_id_var.set("")
        self.role_var.set("")
        self.goal_text.delete(1.0, tk.END)
        self.backstory_text.delete(1.0, tk.END)
        self.department_var.set("")
        self.selected_tools_listbox.delete(0, tk.END)
        self.selected_agent = None
    
    def _add_tool(self):
        """添加工具"""
        selection = self.available_tools_listbox.curselection()
        if selection:
            tool = self.available_tools_listbox.get(selection[0])
            # 检查是否已存在
            tools = [self.selected_tools_listbox.get(i) for i in range(self.selected_tools_listbox.size())]
            if tool not in tools:
                self.selected_tools_listbox.insert(tk.END, tool)
    
    def _remove_tool(self):
        """移除工具"""
        selection = self.selected_tools_listbox.curselection()
        if selection:
            self.selected_tools_listbox.delete(selection[0])
    
    def _create_new_agent(self):
        """创建新Agent"""
        agent_id = simpledialog.askstring("新建Agent", "请输入Agent ID:")
        if agent_id:
            if agent_id in self.agents_config.get(self.current_group, {}):
                messagebox.showerror("错误", "Agent ID已存在!")
                return
            
            # 创建默认配置
            default_config = {
                "role": "新建角色",
                "goal": "执行安全分析任务",
                "backstory": "你是一名安全分析专家",
                "tools": [],
                "department": "process_department"
            }
            
            if self.current_group not in self.agents_config:
                self.agents_config[self.current_group] = {}
            
            self.agents_config[self.current_group][agent_id] = default_config
            self._refresh_agent_list()
            
            # 选中新创建的Agent
            for i in range(self.agent_listbox.size()):
                if self.agent_listbox.get(i) == agent_id:
                    self.agent_listbox.selection_set(i)
                    self._on_agent_selected()
                    break
    
    def _create_from_template(self):
        """从模板创建Agent"""
        # 创建模板选择对话框
        template_dialog = TemplateSelectionDialog(self, self.template_manager)
        self.wait_window(template_dialog)
        
        if hasattr(template_dialog, 'selected_template') and template_dialog.selected_template:
            template_id = template_dialog.selected_template
            template = self.template_manager.get_template(template_id)
            
            if template:
                agent_id = simpledialog.askstring("从模板创建Agent", "请输入Agent ID:")
                if agent_id:
                    if agent_id in self.agents_config.get(self.current_group, {}):
                        messagebox.showerror("错误", "Agent ID已存在!")
                        return
                    
                    # 使用模板配置
                    agent_config = template["config"].copy()
                    
                    if self.current_group not in self.agents_config:
                        self.agents_config[self.current_group] = {}
                    
                    self.agents_config[self.current_group][agent_id] = agent_config
                    self._refresh_agent_list()
                    
                    # 选中新创建的Agent
                    for i in range(self.agent_listbox.size()):
                        if self.agent_listbox.get(i) == agent_id:
                            self.agent_listbox.selection_set(i)
                            self._on_agent_selected()
                            break
    
    def _copy_agent(self):
        """复制Agent"""
        if not self.selected_agent:
            messagebox.showwarning("警告", "请先选择要复制的Agent!")
            return
        
        new_agent_id = simpledialog.askstring("复制Agent", "请输入新Agent ID:")
        if new_agent_id:
            if new_agent_id in self.agents_config.get(self.current_group, {}):
                messagebox.showerror("错误", "Agent ID已存在!")
                return
            
            # 复制配置
            original_config = self.agents_config[self.current_group][self.selected_agent].copy()
            self.agents_config[self.current_group][new_agent_id] = original_config
            self._refresh_agent_list()
    
    def _delete_agent(self):
        """删除Agent"""
        if not self.selected_agent:
            messagebox.showwarning("警告", "请先选择要删除的Agent!")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除Agent '{self.selected_agent}' 吗?"):
            del self.agents_config[self.current_group][self.selected_agent]
            self._refresh_agent_list()
            self._clear_detail_form()
    
    def _create_new_group(self):
        """创建新角色组"""
        group_name = simpledialog.askstring("新建角色组", "请输入角色组名称:")
        if group_name:
            if group_name in self.agents_config:
                messagebox.showerror("错误", "角色组已存在!")
                return
            
            self.agents_config[group_name] = {}
            
            # 更新下拉框
            values = list(self.group_combo['values'])
            values.append(group_name)
            self.group_combo['values'] = values
            
            # 切换到新组
            self.group_var.set(group_name)
            self._on_group_changed()
    
    def _save_current_agent(self):
        """保存当前Agent配置"""
        if not self.selected_agent:
            return
        
        # 获取表单数据
        new_agent_id = self.agent_id_var.get().strip()
        if not new_agent_id:
            messagebox.showerror("错误", "Agent ID不能为空!")
            return
        
        # 如果ID改变了，需要重命名
        if new_agent_id != self.selected_agent:
            if new_agent_id in self.agents_config[self.current_group]:
                messagebox.showerror("错误", "Agent ID已存在!")
                return
            
            # 删除旧的，创建新的
            config = self.agents_config[self.current_group].pop(self.selected_agent)
            self.agents_config[self.current_group][new_agent_id] = config
            self.selected_agent = new_agent_id
        
        # 更新配置
        config = self.agents_config[self.current_group][self.selected_agent]
        config["role"] = self.role_var.get().strip()
        config["goal"] = self.goal_text.get(1.0, tk.END).strip()
        config["backstory"] = self.backstory_text.get(1.0, tk.END).strip()
        config["department"] = self.department_var.get()
        
        # 更新工具列表
        tools = []
        for i in range(self.selected_tools_listbox.size()):
            tools.append(self.selected_tools_listbox.get(i))
        config["tools"] = tools
        
        self._refresh_agent_list()
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            # 先保存当前编辑的Agent
            self._save_current_agent()
            
            # 保存到文件
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      "config", "json", "agents_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.agents_config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "配置保存成功!")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def on_show(self):
        """屏幕显示时调用"""
        self._load_agents_config()
    
    def on_hide(self):
        """屏幕隐藏时调用"""
        pass


class TemplateSelectionDialog(tk.Toplevel):
    """模板选择对话框"""
    
    def __init__(self, parent, template_manager):
        super().__init__(parent)
        self.template_manager = template_manager
        self.selected_template = None
        
        self.title("选择Agent模板")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # 设置为模态对话框
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._load_templates()
        
        # 居中显示
        self.center_window()
    
    def center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="选择Agent模板", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 部门过滤
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="按部门过滤:").pack(side=tk.LEFT, padx=(0, 5))
        self.department_filter_var = tk.StringVar(value="全部")
        self.department_filter_combo = ttk.Combobox(filter_frame, textvariable=self.department_filter_var,
                                                   state="readonly", width=20)
        self.department_filter_combo.pack(side=tk.LEFT)
        self.department_filter_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # 内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：模板列表
        left_frame = ttk.LabelFrame(content_frame, text="模板列表")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), ipadx=10, ipady=10)
        
        # 模板列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.template_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=30)
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.template_listbox.yview)
        
        self.template_listbox.bind("<<ListboxSelect>>", self._on_template_selected)
        
        # 右侧：模板详情
        right_frame = ttk.LabelFrame(content_frame, text="模板详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, ipadx=10, ipady=10)
        
        # 模板信息显示
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 模板名称
        ttk.Label(info_frame, text="模板名称:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.template_name_label = ttk.Label(info_frame, text="", foreground="blue")
        self.template_name_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 描述
        ttk.Label(info_frame, text="描述:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(info_frame, width=40, height=3, state=tk.DISABLED)
        self.description_text.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 角色
        ttk.Label(info_frame, text="角色:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.role_label = ttk.Label(info_frame, text="")
        self.role_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 部门
        ttk.Label(info_frame, text="部门:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.department_label = ttk.Label(info_frame, text="")
        self.department_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 目标
        ttk.Label(info_frame, text="目标:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.NW, pady=5)
        self.goal_text = tk.Text(info_frame, width=40, height=3, state=tk.DISABLED)
        self.goal_text.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 背景故事
        ttk.Label(info_frame, text="背景故事:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.backstory_text = tk.Text(info_frame, width=40, height=4, state=tk.DISABLED)
        self.backstory_text.grid(row=5, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 工具列表
        ttk.Label(info_frame, text="工具列表:", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky=tk.NW, pady=5)
        self.tools_text = tk.Text(info_frame, width=40, height=5, state=tk.DISABLED)
        self.tools_text.grid(row=6, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="选择", command=self._select).pack(side=tk.RIGHT, padx=5)
    
    def _load_templates(self):
        """加载模板列表"""
        templates = self.template_manager.get_templates()
        departments = ["全部"] + self.template_manager.get_department_list()
        self.department_filter_combo['values'] = departments
        
        self.all_templates = templates
        self._refresh_template_list()
    
    def _refresh_template_list(self):
        """刷新模板列表"""
        self.template_listbox.delete(0, tk.END)
        
        filter_dept = self.department_filter_var.get()
        
        for template_id, template in self.all_templates.items():
            if filter_dept == "全部" or template["config"].get("department") == filter_dept:
                display_name = f"{template['name']} ({template_id})"
                self.template_listbox.insert(tk.END, display_name)
    
    def _on_filter_changed(self, event=None):
        """过滤条件改变"""
        self._refresh_template_list()
        self._clear_template_details()
    
    def _on_template_selected(self, event=None):
        """模板选择事件"""
        selection = self.template_listbox.curselection()
        if selection:
            display_name = self.template_listbox.get(selection[0])
            # 从显示名称中提取模板ID
            template_id = display_name.split(" (")[-1].rstrip(")")
            self._show_template_details(template_id)
    
    def _show_template_details(self, template_id):
        """显示模板详情"""
        template = self.template_manager.get_template(template_id)
        if template:
            self.current_template_id = template_id
            
            # 更新显示
            self.template_name_label.config(text=template["name"])
            
            self._update_text_widget(self.description_text, template["description"])
            
            config = template["config"]
            self.role_label.config(text=config.get("role", ""))
            self.department_label.config(text=config.get("department", ""))
            
            self._update_text_widget(self.goal_text, config.get("goal", ""))
            self._update_text_widget(self.backstory_text, config.get("backstory", ""))
            
            tools_text = "\n".join(config.get("tools", []))
            self._update_text_widget(self.tools_text, tools_text)
    
    def _update_text_widget(self, widget, text):
        """更新文本组件内容"""
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(1.0, text)
        widget.config(state=tk.DISABLED)
    
    def _clear_template_details(self):
        """清空模板详情"""
        self.template_name_label.config(text="")
        self.role_label.config(text="")
        self.department_label.config(text="")
        
        for widget in [self.description_text, self.goal_text, self.backstory_text, self.tools_text]:
            self._update_text_widget(widget, "")
        
        self.current_template_id = None
    
    def _select(self):
        """选择模板"""
        if hasattr(self, 'current_template_id') and self.current_template_id:
            self.selected_template = self.current_template_id
            self.destroy()
        else:
            messagebox.showwarning("警告", "请先选择一个模板!")
    
    def _cancel(self):
        """取消选择"""
        self.selected_template = None
        self.destroy()