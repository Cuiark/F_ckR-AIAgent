# 查找类似这样的代码
def run_workflow(self, workflow_name):
    try:
        # 可能的错误代码
        workflow_data = self.get_workflow_data(workflow_name)
        agent_name = workflow_data.get('agent_name')  # 错误：如果workflow_data是列表
        
        # 修改为：
        workflow_data = self.get_workflow_data(workflow_name)
        
        # 检查数据类型并正确处理
        if isinstance(workflow_data, list):
            # 如果是列表，根据实际数据结构进行处理
            if workflow_data and isinstance(workflow_data[0], dict):
                # 假设列表的第一个元素是我们需要的字典
                agent_name = workflow_data[0].get('agent_name', 'unknown')
            else:
                agent_name = 'unknown'
        elif isinstance(workflow_data, dict):
            # 如果是字典，可以直接使用get方法
            agent_name = workflow_data.get('agent_name', 'unknown')
        else:
            # 其他情况
            agent_name = 'unknown'
            
        # ... 继续处理 ...
        
    except Exception as e:
        logger.error(f"运行工作流失败: {str(e)}")


def get_workflow_data(self, workflow_name):
    """获取工作流程配置数据"""
    try:
        # 加载工作流配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                  "config", "json", "workflows.json")
        
        with open(config_path, "r", encoding="utf-8") as f:
            workflows = json.load(f)
        
        if workflow_name not in workflows:
            self.logger.error(f"未找到工作流程: {workflow_name}")
            return {}  # 返回空字典而不是None，保持一致的返回类型
        
        workflow = workflows[workflow_name]
        
        # 加载模块配置
        modules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   "config", "json", "modules.json")
        
        with open(modules_path, "r", encoding="utf-8") as f:
            modules = json.load(f)
        
        # 构建工作流数据
        # 确保返回一个字典而不是列表，避免类型不一致
        workflow_data = {
            "name": workflow.get("name", "未命名工作流"),
            "description": workflow.get("description", ""),
            "modules": []
        }
        
        # 添加模块信息
        for module_name in workflow.get("modules", []):
            if module_name in modules:
                module = modules[module_name]
                workflow_data["modules"].append({
                    "name": module.get("name", "未命名模块"),
                    "description": module.get("description", ""),
                    "agent": module.get("agent", ""),
                    "tools": module.get("tools", []),
                    "module_id": module_name
                })
        
        return workflow_data
        
    except Exception as e:
        self.logger.error(f"获取工作流数据失败: {str(e)}")
        return {}  # 返回空字典而不是None，保持一致的返回类型


def run_workflow(self, workflow_name):
    """运行指定的工作流程"""
    try:
        # 获取工作流配置
        workflow_data = self.get_workflow_data(workflow_name)
        
        # 检查数据类型并正确处理
        if isinstance(workflow_data, list):
            # 如果是列表（旧版本可能返回列表），转换为字典格式
            if workflow_data and isinstance(workflow_data[0], dict):
                # 假设列表的第一个元素是我们需要的字典
                modules = workflow_data
                workflow_info = {
                    "name": workflow_name,
                    "modules": modules
                }
            else:
                self.logger.error("工作流数据格式错误")
                return {"status": "error", "message": "工作流数据格式错误"}
        elif isinstance(workflow_data, dict):
            # 如果是字典（新版本返回字典），直接使用
            workflow_info = workflow_data
        else:
            self.logger.error(f"工作流数据类型错误: {type(workflow_data)}")
            return {"status": "error", "message": "工作流数据类型错误"}
        
        # 使用统一的字典格式处理工作流
        modules = workflow_info.get("modules", [])
        if not modules:
            self.logger.warning(f"工作流 {workflow_name} 没有模块")
            return {"status": "completed", "message": "工作流没有模块", "results": {}}
        
        # 初始化工作流引擎
        from workflow.engine import WorkflowEngine
        engine = WorkflowEngine(self.model_type)
        
        # 设置回调函数
        engine.set_callbacks(
            report_callback=self.report_callback,
            tool_callback=self.tool_callback,
            log_callback=self.log_callback,
            role_callback=self.role_callback,
            decision_callback=self.decision_callback,
            completion_callback=self.completion_callback
        )
        
        # 执行工作流
        result = engine.execute_workflow(workflow_name, self.group_name)
        return result
        
    except Exception as e:
        self.logger.error(f"运行工作流失败: {str(e)}")
        return {"status": "error", "message": f"运行工作流失败: {str(e)}"}