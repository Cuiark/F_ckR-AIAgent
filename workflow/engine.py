#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工作流程引擎 - 根据配置文件动态执行任务
"""

import os
import json
import time
import logging
import traceback
from typing import Dict, List, Callable, Any, Optional

# 导入必要的模块
from models import setup_llm
from agents import create_agents
from config.constants import DECISION_TIMEOUT, ERROR_RETRY_INTERVAL

# 设置日志
logger = logging.getLogger("workflow_engine")

class WorkflowEngine:
    """工作流程引擎，根据配置文件动态执行任务"""
    
    # 在 WorkflowEngine 类的初始化方法中添加或修改加载工作流的代码
    def __init__(self, model_type: str = "deepseek-chat"):
        """初始化工作流程引擎"""
        self.model_type = model_type
        self.llm_for_direct = setup_llm(model_type=model_type, for_crewai=False)
        self.llm_for_agents = setup_llm(model_type=model_type, for_crewai=True)
        
        # 加载工作流配置
        self.workflows = self._load_workflows()
        self.modules = self._load_json_config("modules.json")
        
        # 回调函数
        self.report_callback = None
        self.tool_callback = None
        self.log_callback = None
        self.role_callback = None
        self.decision_callback = None
        self.completion_callback = None
    
    def _load_json_config(self, filename: str) -> Dict:
        """加载JSON配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "config", "json", filename)
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件 {filename} 失败: {str(e)}")
            return {}
    
    def set_callbacks(self, report_callback=None, tool_callback=None, 
                     log_callback=None, role_callback=None, 
                     decision_callback=None, completion_callback=None):
        """设置回调函数"""
        self.report_callback = report_callback
        self.tool_callback = tool_callback
        self.log_callback = log_callback
        self.role_callback = role_callback
        self.decision_callback = decision_callback
        self.completion_callback = completion_callback
        
        # 设置工具输出回调
        if tool_callback:
            from tools.security_tools import set_tool_output_callback
            set_tool_output_callback(tool_callback)
    
    def execute_workflow(self, workflow_name: str, group_name: str) -> Dict:
        """执行指定的工作流程"""
        if workflow_name not in self.workflows:
            error_msg = f"未找到工作流程: {workflow_name}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        workflow = self.workflows[workflow_name]
        
        if self.log_callback:
            self.log_callback(f"正在初始化工作流程: {workflow_name}...")
        
        # 创建agents
        agents = create_agents(self.llm_for_agents, group_name=group_name)
        secretary_agent = agents.get("secretary")
        
        if not secretary_agent and self.log_callback:
            self.log_callback("警告: 未找到秘书Agent，某些功能可能受限")
        
        # 执行工作流程中的每个模块
        results = {}
        previous_results = {}
        
        # 检查workflow是列表还是字典
        if isinstance(workflow, list):
            # 如果是列表（当前格式），直接遍历
            modules_to_execute = workflow
        else:
            # 如果是字典（旧格式），使用modules字段
            modules_to_execute = workflow.get("modules", [])
        
        for i, module in enumerate(modules_to_execute):
            module_name = f"module_{i}"
            
            # 更新角色
            if self.role_callback:
                self.role_callback(module.get("name", module_name))
            
            if self.log_callback:
                self.log_callback(f"正在执行模块: {module.get('name', module_name)}...")
            
            # 准备模块输入数据
            input_data = None
            if i > 0:  # 如果不是第一个模块，使用前一个模块的结果
                input_data = self._prepare_input_data([f"module_{i-1}"], previous_results)
            
            # 执行模块
            try:
                from main import execute_agent_with_approval
                
                agent_key = module.get("agent")
                if not agent_key or agent_key not in agents:
                    if self.log_callback:
                        self.log_callback(f"警告: 未找到Agent {agent_key}，跳过模块 {module.get('name', module_name)}")
                    continue
                
                # 修改：移除timeout参数，或者检查函数定义是否接受该参数
                try:
                    # 尝试获取函数签名
                    import inspect
                    sig = inspect.signature(execute_agent_with_approval)
                    
                    # 检查是否有timeout参数
                    if 'timeout' in sig.parameters:
                        # 如果有timeout参数，正常传递
                        result = execute_agent_with_approval(
                            agents[agent_key],
                            module.get("description", ""),
                            self.llm_for_direct,
                            secretary_agent,
                            raw_data=input_data,
                            get_decision_func=self._create_decision_adapter(module.get("name", module_name)),
                            timeout=module.get("timeout", DECISION_TIMEOUT)
                        )
                    else:
                        # 如果没有timeout参数，不传递
                        result = execute_agent_with_approval(
                            agents[agent_key],
                            module.get("description", ""),
                            self.llm_for_direct,
                            secretary_agent,
                            raw_data=input_data,
                            get_decision_func=self._create_decision_adapter(module.get("name", module_name))
                        )
                except Exception as e:
                    # 如果检查失败，尝试不带timeout参数调用
                    logger.warning(f"检查函数签名失败，尝试不带timeout参数调用: {str(e)}")
                    result = execute_agent_with_approval(
                        agents[agent_key],
                        module.get("description", ""),
                        self.llm_for_direct,
                        secretary_agent,
                        raw_data=input_data,
                        get_decision_func=self._create_decision_adapter(module.get("name", module_name))
                    )
                
                # 保存结果
                results[module_name] = result
                
                # 如果模块执行失败，根据工作流配置决定是否继续
                if result["status"] != "completed":
                    if self.log_callback:
                        self.log_callback(f"模块 {module.get('name', module_name)} 执行失败，中断工作流程")
                    break
                
                # 更新previous_results，用于后续模块
                if result["status"] == "completed":
                    previous_results[module_name] = result
            
            except Exception as e:
                error_msg = f"执行模块 {module.get('name', module_name)} 时出错: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                
                if self.log_callback:
                    self.log_callback(f"错误: {error_msg}")
                
                # 中断工作流程
                break
        
        # 工作流程完成
        if self.completion_callback:
            try:
                # 检查回调函数是否接受参数
                import inspect
                sig = inspect.signature(self.completion_callback)
                
                if len(sig.parameters) > 0:
                    # 如果接受参数，传递消息
                    self.completion_callback("工作流程执行完成")
                else:
                    # 如果不接受参数，不传递消息
                    self.completion_callback()
            except Exception as e:
                logger.warning(f"调用完成回调时出错: {str(e)}")
                # 尝试不带参数调用
                try:
                    self.completion_callback()
                except:
                    # 如果还是失败，尝试带参数调用
                    try:
                        self.completion_callback("工作流程执行完成")
                    except:
                        logger.error("无法调用完成回调函数")
        
        return {"status": "completed", "results": results}
    
    def _prepare_input_data(self, required_modules: List[str], previous_results: Dict) -> str:
        """准备模块输入数据"""
        input_data = ""
        for module_name in required_modules:
            if module_name in previous_results:
                result = previous_results[module_name]
                if "result" in result:
                    input_data += f"\n\n--- {self.modules[module_name]['name']} 结果 ---\n"
                    input_data += result["result"]
        
        return input_data if input_data else None
    
    def _create_decision_adapter(self, module_name: str) -> Callable:
        """创建决策适配器函数"""
        def decision_adapter(report, stage, agent_name):
            """决策适配器函数"""
            if self.log_callback:
                self.log_callback(f"请求决策: {module_name} - {stage}")
            
            # 显示报告
            if self.report_callback:
                report_header = f"【{module_name} - {stage}报告】"
                formatted_report = f"\n{report_header}\n{'='*80}\n{report}\n{'='*80}\n"
                self.report_callback(formatted_report, True)
            
            # 获取决策
            if self.decision_callback:
                try:
                    from gui.app import get_decision
                    decision = get_decision(DECISION_TIMEOUT)
                    
                    if decision is None:
                        logger.warning(f"{module_name} 的 {stage}决策为None，默认批准")
                        return {"status": "approved", "feedback": "自动批准（决策为None）"}
                    
                    return decision
                except Exception as e:
                    logger.error(f"获取决策时出错: {str(e)}")
                    return {"status": "approved", "feedback": "自动批准（获取决策出错）"}
            else:
                # 使用默认的命令行交互
                from main import get_user_decision
                return get_user_decision(report, stage, agent_name)
        
        return decision_adapter

    def _load_workflows(self):
        """加载所有工作流配置"""
        try:
            # 配置文件路径
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "config", "json", "workflows.json")
            
            # 检查文件是否存在
            if not os.path.exists(config_path):
                self.logger.error(f"工作流程配置文件不存在: {config_path}")
                return {}
            
            # 加载配置
            with open(config_path, "r", encoding="utf-8") as f:
                workflows = json.load(f)
            
            return workflows
        except Exception as e:
            self.logger.error(f"加载工作流配置时出错: {str(e)}")
            return {}