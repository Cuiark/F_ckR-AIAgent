# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from typing import Dict, List

class GroupManagementScreen(ttk.Frame):
    """角色组管理界面"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.groups_config = {}
        self.selected_group = None
        
        # 创建界面
        self._create_widgets()
        
        # 加载配置
        self._load_groups_config()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="角色组管理", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 工具栏
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 操作按钮
        ttk.Button(toolbar_frame, text="新建角色组", command=self._create_new_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="复制角色组", command=self._copy_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="删除角色组", command=self._delete_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="导入角色组", command=self._import_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="导出角色组", command=self._export_group).pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        ttk.Button(toolbar_frame, text="保存配置", command=self._save_config).pack(side=tk.RIGHT, padx=5)
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：角色组列表
        left_frame = ttk.LabelFrame(content_frame, text="角色组列表")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), ipadx=10, ipady=10)
        
        # 角色组列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.group_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=25)
        self.group_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.group_listbox.yview)
        
        self.group_listbox.bind("<<ListboxSelect>>", self._on_group_selected)
        
        # 右侧：角色组详情
        right_frame = ttk.LabelFrame(content_frame, text="角色组详情")
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
        
        # 基本信息
        info_frame = ttk.LabelFrame(scrollable_frame, text="基本信息")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 角色组名称
        ttk.Label(info_frame, text="角色组名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.group_name_var = tk.StringVar()
        self.group_name_entry = ttk.Entry(info_frame, textvariable=self.group_name_var, width=30)
        self.group_name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 描述
        ttk.Label(info_frame, text="描述:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.description_text = tk.Text(info_frame, height=3, width=40)
        self.description_text.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        info_frame.columnconfigure(1, weight=1)
        
        # 角色组成员
        members_frame = ttk.LabelFrame(scrollable_frame, text="角色组成员")
        members_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 部门和角色树形视图
        tree_frame = ttk.Frame(members_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建树形视图
        self.members_tree = ttk.Treeview(tree_frame, columns=("role", "goal"), show="tree headings")
        self.members_tree.heading("#0", text="部门/角色")
        self.members_tree.heading("role", text="角色名称")
        self.members_tree.heading("goal", text="目标")
        
        self.members_tree.column("#0", width=200)
        self.members_tree.column("role", width=150)
        self.members_tree.column("goal", width=300)
        
        # 树形视图滚动条
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.members_tree.yview)
        self.members_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.members_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 成员操作按钮
        member_buttons_frame = ttk.Frame(members_frame)
        member_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(member_buttons_frame, text="添加角色", command=self._add_member).pack(side=tk.LEFT, padx=5)
        ttk.Button(member_buttons_frame, text="移除角色", command=self._remove_member).pack(side=tk.LEFT, padx=5)
        ttk.Button(member_buttons_frame, text="编辑角色", command=self._edit_member).pack(side=tk.LEFT, padx=5)
        
        # 工作流配置
        workflow_frame = ttk.LabelFrame(scrollable_frame, text="工作流配置")
        workflow_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工作流基本信息
        workflow_info_frame = ttk.Frame(workflow_frame)
        workflow_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(workflow_info_frame, text="工作流描述:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.workflow_desc_var = tk.StringVar()
        self.workflow_desc_entry = ttk.Entry(workflow_info_frame, textvariable=self.workflow_desc_var, width=50)
        self.workflow_desc_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        workflow_info_frame.columnconfigure(1, weight=1)
        
        # 任务流程展示
        workflow_steps_frame = ttk.LabelFrame(workflow_frame, text="任务流程")
        workflow_steps_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 流程步骤树形视图
        steps_tree_frame = ttk.Frame(workflow_steps_frame)
        steps_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.workflow_steps_tree = ttk.Treeview(steps_tree_frame, columns=("agent", "department", "dependencies", "outputs"), show="tree headings")
        self.workflow_steps_tree.heading("#0", text="步骤名称")
        self.workflow_steps_tree.heading("agent", text="执行角色")
        self.workflow_steps_tree.heading("department", text="所属部门")
        self.workflow_steps_tree.heading("dependencies", text="依赖项")
        self.workflow_steps_tree.heading("outputs", text="输出")
        
        self.workflow_steps_tree.column("#0", width=150)
        self.workflow_steps_tree.column("agent", width=120)
        self.workflow_steps_tree.column("department", width=100)
        self.workflow_steps_tree.column("dependencies", width=150)
        self.workflow_steps_tree.column("outputs", width=150)
        
        # 流程步骤滚动条
        steps_scrollbar = ttk.Scrollbar(steps_tree_frame, orient="vertical", command=self.workflow_steps_tree.yview)
        self.workflow_steps_tree.configure(yscrollcommand=steps_scrollbar.set)
        
        self.workflow_steps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        steps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 流程操作按钮
        workflow_buttons_frame = ttk.Frame(workflow_steps_frame)
        workflow_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(workflow_buttons_frame, text="添加步骤", command=self._add_workflow_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(workflow_buttons_frame, text="编辑步骤", command=self._edit_workflow_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(workflow_buttons_frame, text="删除步骤", command=self._remove_workflow_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(workflow_buttons_frame, text="上移", command=self._move_step_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(workflow_buttons_frame, text="下移", command=self._move_step_down).pack(side=tk.LEFT, padx=5)
        ttk.Button(workflow_buttons_frame, text="刷新流程", command=self._refresh_workflow_steps).pack(side=tk.RIGHT, padx=5)
        
        # 更新按钮
        update_frame = ttk.Frame(scrollable_frame)
        update_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(update_frame, text="更新角色组", command=self._update_group).pack(side=tk.RIGHT, padx=5)
        
        # 配置滚动
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _load_groups_config(self):
        """加载角色组配置"""
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
            # 加载agents配置
            agents_config_path = os.path.join(project_root, "config", "json", "agents_config.json")
            if os.path.exists(agents_config_path):
                with open(agents_config_path, 'r', encoding='utf-8') as f:
                    self.groups_config = json.load(f)
            
            # 加载workflows配置
            workflows_config_path = os.path.join(project_root, "config", "json", "workflows.json")
            if os.path.exists(workflows_config_path):
                with open(workflows_config_path, 'r', encoding='utf-8') as f:
                    self.workflows_config = json.load(f)
            else:
                self.workflows_config = {}
            
            self._refresh_group_list()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def _refresh_group_list(self):
        """刷新角色组列表"""
        self.group_listbox.delete(0, tk.END)
        for group_name in self.groups_config.keys():
            self.group_listbox.insert(tk.END, group_name)
    
    def _on_group_selected(self, event):
        """角色组选择事件"""
        selection = self.group_listbox.curselection()
        if selection:
            group_name = self.group_listbox.get(selection[0])
            self.selected_group = group_name
            self._load_group_details(group_name)
    
    def _load_group_details(self, group_name):
        """加载角色组详情"""
        if group_name not in self.groups_config:
            return
        
        # 设置基本信息
        self.group_name_var.set(group_name)
        
        # 设置工作流描述
        if group_name in self.workflows_config:
            workflow_desc = self.workflows_config[group_name].get("description", "")
            self.workflow_desc_var.set(workflow_desc)
        
        # 清空并重新填充成员树
        self.members_tree.delete(*self.members_tree.get_children())
        
        # 按部门组织角色
        departments = {}
        group_agents = self.groups_config[group_name]
        
        for agent_id, agent_config in group_agents.items():
            dept = agent_config.get("department", "未分类")
            if dept not in departments:
                departments[dept] = []
            departments[dept].append((agent_id, agent_config))
        
        # 添加部门和角色到树中
        for dept_name, agents in departments.items():
            dept_item = self.members_tree.insert("", "end", text=dept_name, values=("", ""))
            
            for agent_id, agent_config in agents:
                role = agent_config.get("role", "")
                goal = agent_config.get("goal", "")
                self.members_tree.insert(dept_item, "end", text=agent_id, values=(role, goal))
            
            # 展开部门节点
            self.members_tree.item(dept_item, open=True)
        
        # 加载工作流步骤
        self._load_workflow_steps(group_name)
    
    def _create_new_group(self):
        """创建新角色组"""
        group_name = simpledialog.askstring("新建角色组", "请输入角色组名称:")
        if group_name and group_name not in self.groups_config:
            self.groups_config[group_name] = {}
            self.workflows_config[group_name] = {
                "description": f"{group_name}工作流",
                "modules": []
            }
            self._refresh_group_list()
            messagebox.showinfo("成功", f"角色组 '{group_name}' 创建成功")
        elif group_name:
            messagebox.showerror("错误", "角色组名称已存在")
    
    def _copy_group(self):
        """复制角色组"""
        if not self.selected_group:
            messagebox.showwarning("警告", "请先选择要复制的角色组")
            return
        
        new_name = simpledialog.askstring("复制角色组", "请输入新角色组名称:")
        if new_name and new_name not in self.groups_config:
            # 深拷贝配置
            import copy
            self.groups_config[new_name] = copy.deepcopy(self.groups_config[self.selected_group])
            if self.selected_group in self.workflows_config:
                self.workflows_config[new_name] = copy.deepcopy(self.workflows_config[self.selected_group])
            
            self._refresh_group_list()
            messagebox.showinfo("成功", f"角色组 '{new_name}' 复制成功")
        elif new_name:
            messagebox.showerror("错误", "角色组名称已存在")
    
    def _delete_group(self):
        """删除角色组"""
        if not self.selected_group:
            messagebox.showwarning("警告", "请先选择要删除的角色组")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除角色组 '{self.selected_group}' 吗？"):
            del self.groups_config[self.selected_group]
            if self.selected_group in self.workflows_config:
                del self.workflows_config[self.selected_group]
            
            self.selected_group = None
            self._refresh_group_list()
            self._clear_details()
            messagebox.showinfo("成功", "角色组删除成功")
    
    def _clear_details(self):
        """清空详情显示"""
        self.group_name_var.set("")
        self.description_text.delete(1.0, tk.END)
        self.workflow_desc_var.set("")
        self.members_tree.delete(*self.members_tree.get_children())
        self.workflow_steps_tree.delete(*self.workflow_steps_tree.get_children())
    
    def _add_member(self):
        """添加角色成员"""
        if not self.selected_group:
            messagebox.showwarning("警告", "请先选择角色组")
            return
        
        # 打开角色选择对话框
        dialog = MemberSelectionDialog(self, self.groups_config)
        if dialog.result:
            agent_id, agent_config = dialog.result
            self.groups_config[self.selected_group][agent_id] = agent_config
            self._load_group_details(self.selected_group)
    
    def _remove_member(self):
        """移除角色成员"""
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移除的角色")
            return
        
        item = selection[0]
        agent_id = self.members_tree.item(item, "text")
        
        # 检查是否是角色节点（不是部门节点）
        parent = self.members_tree.parent(item)
        if parent:  # 有父节点，说明是角色节点
            if messagebox.askyesno("确认移除", f"确定要移除角色 '{agent_id}' 吗？"):
                if agent_id in self.groups_config[self.selected_group]:
                    del self.groups_config[self.selected_group][agent_id]
                    self._load_group_details(self.selected_group)
        else:
            messagebox.showinfo("提示", "请选择具体的角色，而不是部门")
    
    def _edit_member(self):
        """编辑角色成员"""
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的角色")
            return
        
        item = selection[0]
        agent_id = self.members_tree.item(item, "text")
        
        # 检查是否是角色节点
        parent = self.members_tree.parent(item)
        if parent and agent_id in self.groups_config[self.selected_group]:
            # 打开角色编辑对话框
            agent_config = self.groups_config[self.selected_group][agent_id]
            dialog = AgentEditDialog(self, agent_id, agent_config)
            if dialog.result:
                self.groups_config[self.selected_group][agent_id] = dialog.result
                self._load_group_details(self.selected_group)
        else:
            messagebox.showinfo("提示", "请选择具体的角色进行编辑")
    
    def _update_group(self):
        """更新角色组信息"""
        if not self.selected_group:
            messagebox.showwarning("警告", "请先选择角色组")
            return
        
        # 更新工作流描述
        if self.selected_group in self.workflows_config:
            self.workflows_config[self.selected_group]["description"] = self.workflow_desc_var.get()
        else:
            # 如果工作流配置不存在，创建一个新的
            self.workflows_config[self.selected_group] = {
                "description": self.workflow_desc_var.get(),
                "modules": []
            }
        
        messagebox.showinfo("成功", "角色组信息更新成功")
    
    def _import_group(self):
        """导入角色组"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="选择角色组配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # 验证配置格式
                if isinstance(imported_config, dict):
                    for group_name, group_config in imported_config.items():
                        if group_name not in self.groups_config:
                            self.groups_config[group_name] = group_config
                        else:
                            if messagebox.askyesno("角色组已存在", f"角色组 '{group_name}' 已存在，是否覆盖？"):
                                self.groups_config[group_name] = group_config
                    
                    self._refresh_group_list()
                    messagebox.showinfo("成功", "角色组导入成功")
                else:
                    messagebox.showerror("错误", "配置文件格式不正确")
            
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def _export_group(self):
        """导出角色组"""
        if not self.selected_group:
            messagebox.showwarning("警告", "请先选择要导出的角色组")
            return
        
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="保存角色组配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                export_config = {self.selected_group: self.groups_config[self.selected_group]}
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_config, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", "角色组导出成功")
            
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def _save_config(self):
        """保存配置"""
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
            # 保存agents配置
            agents_config_path = os.path.join(project_root, "config", "json", "agents_config.json")
            with open(agents_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.groups_config, f, ensure_ascii=False, indent=2)
            
            # 保存workflows配置
            workflows_config_path = os.path.join(project_root, "config", "json", "workflows.json")
            with open(workflows_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.workflows_config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "配置保存成功")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")


class MemberSelectionDialog:
    """角色成员选择对话框"""
    
    def __init__(self, parent, groups_config):
        self.result = None
        self.groups_config = groups_config
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("选择角色")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._center_window()
    
    def _create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 角色列表
        list_frame = ttk.LabelFrame(main_frame, text="可用角色")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建树形视图显示所有角色
        self.roles_tree = ttk.Treeview(list_frame, columns=("role", "department", "goal"), show="tree headings")
        self.roles_tree.heading("#0", text="角色ID")
        self.roles_tree.heading("role", text="角色名称")
        self.roles_tree.heading("department", text="部门")
        self.roles_tree.heading("goal", text="目标")
        
        self.roles_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 填充角色数据
        self._populate_roles()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="选择", command=self._select_role).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT, padx=5)
    
    def _populate_roles(self):
        """填充角色数据"""
        # 收集所有角色
        all_roles = {}
        for group_name, group_config in self.groups_config.items():
            for agent_id, agent_config in group_config.items():
                if agent_id not in all_roles:
                    all_roles[agent_id] = agent_config
        
        # 添加到树中
        for agent_id, agent_config in all_roles.items():
            role = agent_config.get("role", "")
            department = agent_config.get("department", "")
            goal = agent_config.get("goal", "")
            
            self.roles_tree.insert("", "end", text=agent_id, values=(role, department, goal))
    
    def _select_role(self):
        """选择角色"""
        selection = self.roles_tree.selection()
        if selection:
            item = selection[0]
            agent_id = self.roles_tree.item(item, "text")
            
            # 从现有配置中获取角色配置
            for group_config in self.groups_config.values():
                if agent_id in group_config:
                    self.result = (agent_id, group_config[agent_id].copy())
                    break
            
            self.dialog.destroy()
        else:
            messagebox.showwarning("警告", "请选择一个角色")
    
    def _cancel(self):
        """取消选择"""
        self.dialog.destroy()
    
    def _center_window(self):
        """居中显示窗口"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")


# 工作流步骤管理方法（添加到GroupManagementScreen类中）
def _load_workflow_steps(self, group_name):
    """加载工作流步骤"""
    # 清空工作流步骤树
    self.workflow_steps_tree.delete(*self.workflow_steps_tree.get_children())
    
    if group_name not in self.workflows_config:
        return
    
    workflow_config = self.workflows_config[group_name]
    modules = workflow_config.get("modules", [])
    
    for i, module in enumerate(modules):
        name = module.get("name", f"步骤{i+1}")
        agent = module.get("agent", "")
        department = module.get("department", "")
        dependencies = ", ".join(module.get("dependencies", []))
        outputs = ", ".join(module.get("outputs", []))
        
        self.workflow_steps_tree.insert("", "end", text=name, 
                                       values=(agent, department, dependencies, outputs))

def _refresh_workflow_steps(self):
    """刷新工作流步骤"""
    if self.selected_group:
        self._load_workflow_steps(self.selected_group)

def _add_workflow_step(self):
    """添加工作流步骤"""
    if not self.selected_group:
        messagebox.showwarning("警告", "请先选择角色组")
        return
    
    dialog = WorkflowStepDialog(self, "添加步骤", self.groups_config[self.selected_group])
    if dialog.result:
        # 确保workflows_config中有该组的配置
        if self.selected_group not in self.workflows_config:
            self.workflows_config[self.selected_group] = {
                "description": f"{self.selected_group}工作流",
                "modules": []
            }
        
        self.workflows_config[self.selected_group]["modules"].append(dialog.result)
        self._load_workflow_steps(self.selected_group)
        messagebox.showinfo("成功", "工作流步骤添加成功")

def _edit_workflow_step(self):
    """编辑工作流步骤"""
    if not self.selected_group:
        messagebox.showwarning("警告", "请先选择角色组")
        return
    
    selection = self.workflow_steps_tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要编辑的步骤")
        return
    
    # 获取选中步骤的索引
    item = selection[0]
    step_index = self.workflow_steps_tree.index(item)
    
    if self.selected_group in self.workflows_config:
        modules = self.workflows_config[self.selected_group].get("modules", [])
        if step_index < len(modules):
            step_config = modules[step_index]
            dialog = WorkflowStepDialog(self, "编辑步骤", self.groups_config[self.selected_group], step_config)
            if dialog.result:
                modules[step_index] = dialog.result
                self._load_workflow_steps(self.selected_group)
                messagebox.showinfo("成功", "工作流步骤编辑成功")

def _remove_workflow_step(self):
    """删除工作流步骤"""
    if not self.selected_group:
        messagebox.showwarning("警告", "请先选择角色组")
        return
    
    selection = self.workflow_steps_tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要删除的步骤")
        return
    
    if messagebox.askyesno("确认删除", "确定要删除选中的工作流步骤吗？"):
        item = selection[0]
        step_index = self.workflow_steps_tree.index(item)
        
        if self.selected_group in self.workflows_config:
            modules = self.workflows_config[self.selected_group].get("modules", [])
            if step_index < len(modules):
                del modules[step_index]
                self._load_workflow_steps(self.selected_group)
                messagebox.showinfo("成功", "工作流步骤删除成功")

def _move_step_up(self):
    """上移工作流步骤"""
    if not self.selected_group:
        messagebox.showwarning("警告", "请先选择角色组")
        return
    
    selection = self.workflow_steps_tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要移动的步骤")
        return
    
    item = selection[0]
    step_index = self.workflow_steps_tree.index(item)
    
    if step_index > 0 and self.selected_group in self.workflows_config:
        modules = self.workflows_config[self.selected_group].get("modules", [])
        if step_index < len(modules):
            # 交换位置
            modules[step_index], modules[step_index-1] = modules[step_index-1], modules[step_index]
            self._load_workflow_steps(self.selected_group)
            # 重新选中移动后的项
            new_item = self.workflow_steps_tree.get_children()[step_index-1]
            self.workflow_steps_tree.selection_set(new_item)

def _move_step_down(self):
    """下移工作流步骤"""
    if not self.selected_group:
        messagebox.showwarning("警告", "请先选择角色组")
        return
    
    selection = self.workflow_steps_tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要移动的步骤")
        return
    
    item = selection[0]
    step_index = self.workflow_steps_tree.index(item)
    
    if self.selected_group in self.workflows_config:
        modules = self.workflows_config[self.selected_group].get("modules", [])
        if step_index < len(modules) - 1:
            # 交换位置
            modules[step_index], modules[step_index+1] = modules[step_index+1], modules[step_index]
            self._load_workflow_steps(self.selected_group)
            # 重新选中移动后的项
            new_item = self.workflow_steps_tree.get_children()[step_index+1]
            self.workflow_steps_tree.selection_set(new_item)

# 将这些方法添加到GroupManagementScreen类中
GroupManagementScreen._load_workflow_steps = _load_workflow_steps
GroupManagementScreen._refresh_workflow_steps = _refresh_workflow_steps
GroupManagementScreen._add_workflow_step = _add_workflow_step
GroupManagementScreen._edit_workflow_step = _edit_workflow_step
GroupManagementScreen._remove_workflow_step = _remove_workflow_step
GroupManagementScreen._move_step_up = _move_step_up
GroupManagementScreen._move_step_down = _move_step_down


class WorkflowStepDialog:
    """工作流步骤编辑对话框"""
    
    def __init__(self, parent, title, group_agents, step_config=None):
        self.result = None
        self.group_agents = group_agents
        self.step_config = step_config or {}
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._load_data()
        self._center_window()
    
    def _create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 步骤基本信息
        info_frame = ttk.LabelFrame(main_frame, text="步骤信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 步骤名称
        ttk.Label(info_frame, text="步骤名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 步骤描述
        ttk.Label(info_frame, text="步骤描述:").grid(row=1, column=0, sticky=tk.W+tk.N, padx=5, pady=5)
        self.description_text = tk.Text(info_frame, height=3, width=40)
        self.description_text.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 执行角色
        ttk.Label(info_frame, text="执行角色:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.agent_var = tk.StringVar()
        agent_combo = ttk.Combobox(info_frame, textvariable=self.agent_var, width=37)
        agent_combo.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 填充角色选项
        agent_list = list(self.group_agents.keys())
        agent_combo['values'] = agent_list
        
        # 所属部门（自动填充）
        ttk.Label(info_frame, text="所属部门:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.department_var = tk.StringVar()
        self.department_label = ttk.Label(info_frame, textvariable=self.department_var)
        self.department_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 绑定角色选择事件
        agent_combo.bind('<<ComboboxSelected>>', self._on_agent_selected)
        
        info_frame.columnconfigure(1, weight=1)
        
        # 依赖项
        deps_frame = ttk.LabelFrame(main_frame, text="依赖项")
        deps_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(deps_frame, text="依赖步骤（每行一个）:").pack(anchor=tk.W, padx=5, pady=5)
        self.dependencies_text = tk.Text(deps_frame, height=4)
        self.dependencies_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 输出项
        outputs_frame = ttk.LabelFrame(main_frame, text="输出项")
        outputs_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(outputs_frame, text="输出内容（每行一个）:").pack(anchor=tk.W, padx=5, pady=5)
        self.outputs_text = tk.Text(outputs_frame, height=4)
        self.outputs_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="保存", command=self._save_step).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT, padx=5)
    
    def _load_data(self):
        """加载步骤数据"""
        if self.step_config:
            self.name_var.set(self.step_config.get("name", ""))
            
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(1.0, self.step_config.get("description", ""))
            
            self.agent_var.set(self.step_config.get("agent", ""))
            self._on_agent_selected(None)  # 更新部门信息
            
            self.dependencies_text.delete(1.0, tk.END)
            deps = self.step_config.get("dependencies", [])
            self.dependencies_text.insert(1.0, "\n".join(deps))
            
            self.outputs_text.delete(1.0, tk.END)
            outputs = self.step_config.get("outputs", [])
            self.outputs_text.insert(1.0, "\n".join(outputs))
    
    def _on_agent_selected(self, event):
        """角色选择事件"""
        agent_id = self.agent_var.get()
        if agent_id in self.group_agents:
            department = self.group_agents[agent_id].get("department", "")
            self.department_var.set(department)
        else:
            self.department_var.set("")
    
    def _save_step(self):
        """保存步骤"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入步骤名称")
            return
        
        agent = self.agent_var.get().strip()
        if not agent:
            messagebox.showwarning("警告", "请选择执行角色")
            return
        
        # 构建步骤配置
        step_config = {
            "name": name,
            "description": self.description_text.get(1.0, tk.END).strip(),
            "agent": agent,
            "department": self.department_var.get(),
            "dependencies": [dep.strip() for dep in self.dependencies_text.get(1.0, tk.END).strip().split("\n") if dep.strip()],
            "outputs": [output.strip() for output in self.outputs_text.get(1.0, tk.END).strip().split("\n") if output.strip()]
        }
        
        self.result = step_config
        self.dialog.destroy()
    
    def _cancel(self):
        """取消编辑"""
        self.dialog.destroy()
    
    def _center_window(self):
        """居中显示窗口"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")


class AgentEditDialog:
    """角色编辑对话框"""
    
    def __init__(self, parent, agent_id, agent_config):
        self.result = None
        self.agent_id = agent_id
        self.agent_config = agent_config.copy()
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"编辑角色 - {agent_id}")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._load_data()
        self._center_window()
    
    def _create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 角色信息
        info_frame = ttk.LabelFrame(main_frame, text="角色信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 角色名称
        ttk.Label(info_frame, text="角色名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.role_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.role_var, width=40).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 部门
        ttk.Label(info_frame, text="部门:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.department_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.department_var, width=40).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 目标
        ttk.Label(info_frame, text="目标:").grid(row=2, column=0, sticky=tk.W+tk.N, padx=5, pady=5)
        self.goal_text = tk.Text(info_frame, height=3, width=40)
        self.goal_text.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 背景故事
        ttk.Label(info_frame, text="背景故事:").grid(row=3, column=0, sticky=tk.W+tk.N, padx=5, pady=5)
        self.backstory_text = tk.Text(info_frame, height=4, width=40)
        self.backstory_text.grid(row=3, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        info_frame.columnconfigure(1, weight=1)
        
        # 工具列表
        tools_frame = ttk.LabelFrame(main_frame, text="工具列表")
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.tools_text = tk.Text(tools_frame, height=6)
        self.tools_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="保存", command=self._save_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT, padx=5)
    
    def _load_data(self):
        """加载角色数据"""
        self.role_var.set(self.agent_config.get("role", ""))
        self.department_var.set(self.agent_config.get("department", ""))
        
        self.goal_text.delete(1.0, tk.END)
        self.goal_text.insert(1.0, self.agent_config.get("goal", ""))
        
        self.backstory_text.delete(1.0, tk.END)
        self.backstory_text.insert(1.0, self.agent_config.get("backstory", ""))
        
        self.tools_text.delete(1.0, tk.END)
        tools = self.agent_config.get("tools", [])
        self.tools_text.insert(1.0, "\n".join(tools))
    
    def _save_changes(self):
        """保存更改"""
        # 更新配置
        self.agent_config["role"] = self.role_var.get()
        self.agent_config["department"] = self.department_var.get()
        self.agent_config["goal"] = self.goal_text.get(1.0, tk.END).strip()
        self.agent_config["backstory"] = self.backstory_text.get(1.0, tk.END).strip()
        
        # 处理工具列表
        tools_text = self.tools_text.get(1.0, tk.END).strip()
        tools = [tool.strip() for tool in tools_text.split("\n") if tool.strip()]
        self.agent_config["tools"] = tools
        
        self.result = self.agent_config
        self.dialog.destroy()
    
    def _cancel(self):
        """取消编辑"""
        self.dialog.destroy()
    
    def _center_window(self):
        """居中显示窗口"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")