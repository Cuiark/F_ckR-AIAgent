#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版决策模板管理器

此模块提供了一个简化的决策模板管理系统，用于在GUI中显示和处理决策选项。
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_decision_template_manager")

class SimpleDecisionTemplateManager:
    """简化版决策模板管理器
    
    负责加载、管理和提供决策模板，用于在GUI中显示和处理决策选项。
    """
    
    def __init__(self, template_file: str = None):
        """初始化决策模板管理器
        
        参数:
            template_file: 模板配置文件路径，如果为None，则使用默认路径
        """
        self.templates = {}
        self.agent_mappings = {}
        
        # 设置默认模板文件路径
        if template_file is None:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 向上一级到项目根目录，然后到配置目录
            template_file = os.path.join(current_dir, "..", "config", "json", "simple_decision_templates.json")
        
        # 加载模板
        self.load_templates(template_file)
    
    def load_templates(self, template_file: str) -> bool:
        """从文件加载模板
        
        参数:
            template_file: 模板配置文件路径
            
        返回:
            bool: 是否成功加载
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(template_file):
                logger.error(f"模板文件不存在: {template_file}")
                return False
            
            # 读取并解析JSON文件
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 解析模板
            if "templates" in data:
                for template in data["templates"]:
                    template_id = template.get("id")
                    if template_id:
                        self.templates[template_id] = template
            
            # 解析代理映射
            if "agent_mappings" in data:
                self.agent_mappings = data["agent_mappings"]
            
            logger.info(f"成功加载 {len(self.templates)} 个模板和 {len(self.agent_mappings)} 个代理映射")
            return True
            
        except Exception as e:
            logger.error(f"加载模板时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """获取指定ID的模板
        
        参数:
            template_id: 模板ID
            
        返回:
            Dict: 模板对象，如果不存在则返回None
        """
        return self.templates.get(template_id)
    
    def get_template_for_agent(self, agent_name: str, stage: str) -> str:
        """获取适合指定代理和阶段的模板ID
        
        参数:
            agent_name: 代理名称
            stage: 阶段名称（如"执行前"、"执行后"）
            
        返回:
            str: 模板ID
        """
        # 检查代理是否有映射
        if agent_name in self.agent_mappings:
            agent_map = self.agent_mappings[agent_name]
            if stage in agent_map:
                return agent_map[stage]
        
        # 使用默认映射
        if "default" in self.agent_mappings:
            default_map = self.agent_mappings["default"]
            if stage in default_map:
                return default_map[stage]
        
        # 如果没有找到映射，返回第一个模板ID或空字符串
        return next(iter(self.templates.keys())) if self.templates else ""
    
    def get_option(self, template_id: str, option_id: str) -> Optional[Dict]:
        """获取指定模板中的指定选项
        
        参数:
            template_id: 模板ID
            option_id: 选项ID
            
        返回:
            Dict: 选项对象，如果不存在则返回None
        """
        template = self.get_template(template_id)
        if not template:
            return None
        
        options = template.get("options", [])
        for option in options:
            if option.get("id") == option_id:
                return option
        
        return None
    
    def get_action_for_option(self, template_id: str, option_id: str) -> str:
        """获取指定选项对应的操作
        
        参数:
            template_id: 模板ID
            option_id: 选项ID
            
        返回:
            str: 操作名称（"approved", "rejected", "feedback"）
        """
        option = self.get_option(template_id, option_id)
        if option and "action" in option:
            return option["action"]
        
        # 默认返回approved
        return "approved"

# 创建全局实例
simple_template_manager = SimpleDecisionTemplateManager()