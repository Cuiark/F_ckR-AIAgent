# -*- coding: utf-8 -*-

import json
import os
from typing import Dict, List

class AgentTemplateManager:
    """Agent模板管理器"""
    
    def __init__(self):
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict:
        """加载默认模板"""
        return {
            "process_collector": {
                "name": "进程数据收集师",
                "description": "专门收集和过滤系统进程数据",
                "config": {
                    "role": "进程数据收集师",
                    "goal": "收集系统进程数据，并基于历史记录过滤已分析的进程",
                    "backstory": "你是进程部门的数据收集专家，负责收集进程信息并利用部门历史记录优化数据收集效率。",
                    "tools": ["GetProcessDetails", "LoadProcessHistory", "FilterProcessesByTime"],
                    "department": "process_department"
                }
            },
            "process_analyzer": {
                "name": "进程安全分析师",
                "description": "分析进程行为，识别可疑或恶意进程",
                "config": {
                    "role": "进程安全分析师",
                    "goal": "分析系统进程，识别可疑或恶意进程，并将结果存入部门历史",
                    "backstory": "你是进程部门的安全分析专家，擅长识别系统中的可疑进程和恶意软件，并维护部门分析历史。",
                    "tools": ["CompareWithBaseline", "AnalyzeProcessBehavior", "SaveProcessAnalysis"],
                    "department": "process_department"
                }
            },
            "log_collector": {
                "name": "日志数据收集师",
                "description": "收集和过滤Windows事件日志",
                "config": {
                    "role": "日志数据收集师",
                    "goal": "收集Windows事件日志，并基于历史记录过滤已分析的日志",
                    "backstory": "你是日志部门的数据收集专家，负责收集事件日志并利用部门历史记录优化数据收集效率。",
                    "tools": ["GetWindowsLogs", "LoadLogHistory", "FilterLogsByTime"],
                    "department": "log_department"
                }
            },
            "log_analyzer": {
                "name": "日志安全分析师",
                "description": "分析事件日志，识别安全威胁",
                "config": {
                    "role": "日志安全分析师",
                    "goal": "分析Windows事件日志，识别潜在安全威胁，并将结果存入部门历史",
                    "backstory": "你是日志部门的安全分析专家，擅长从复杂的事件日志中发现安全威胁的蛛丝马迹，并维护部门分析历史。",
                    "tools": ["AnalyzeSecurityLogs", "CorrelateEvents", "SaveLogAnalysis"],
                    "department": "log_department"
                }
            },
            "service_collector": {
                "name": "服务数据收集师",
                "description": "收集和过滤系统服务数据",
                "config": {
                    "role": "服务数据收集师",
                    "goal": "收集系统服务数据，并基于历史记录过滤已分析的服务",
                    "backstory": "你是服务部门的数据收集专家，负责收集服务信息并利用部门历史记录优化数据收集效率。",
                    "tools": ["GetServices", "LoadServiceHistory", "FilterServicesByTime"],
                    "department": "service_department"
                }
            },
            "service_analyzer": {
                "name": "服务安全分析师",
                "description": "分析系统服务，识别可疑服务",
                "config": {
                    "role": "服务安全分析师",
                    "goal": "分析系统服务，识别可疑或恶意服务，并将结果存入部门历史",
                    "backstory": "你是服务部门的安全分析专家，擅长识别系统中的可疑服务和恶意程序，并维护部门分析历史。",
                    "tools": ["AnalyzeServiceSecurity", "CheckServiceIntegrity", "SaveServiceAnalysis"],
                    "department": "service_department"
                }
            },
            "network_collector": {
                "name": "网络数据收集师",
                "description": "收集网络连接和流量数据",
                "config": {
                    "role": "网络数据收集师",
                    "goal": "收集网络连接和流量数据，并基于历史记录过滤已分析的连接",
                    "backstory": "你是网络部门的数据收集专家，负责收集网络信息并利用部门历史记录优化数据收集效率。",
                    "tools": ["GetNetworkConnections", "LoadNetworkHistory", "FilterConnectionsByTime"],
                    "department": "network_department"
                }
            },
            "network_analyzer": {
                "name": "网络安全分析师",
                "description": "分析网络流量，识别可疑活动",
                "config": {
                    "role": "网络安全分析师",
                    "goal": "分析网络连接和流量，识别可疑的网络活动，并将结果存入部门历史",
                    "backstory": "你是网络部门的安全分析专家，擅长识别可疑的网络连接和恶意流量，并维护部门分析历史。",
                    "tools": ["AnalyzeNetworkTraffic", "DetectSuspiciousConnections", "SaveNetworkAnalysis"],
                    "department": "network_department"
                }
            },
            "incident_responder": {
                "name": "安全应急响应专家",
                "description": "执行应急响应措施和威胁处置",
                "config": {
                    "role": "安全应急响应专家",
                    "goal": "根据各部门分析结果执行应急响应措施",
                    "backstory": "你是一名经验丰富的安全应急响应专家，擅长处理各类安全事件并采取有效的应对措施。",
                    "tools": ["TerminateProcess", "BlockIP", "AddToWhitelist", "LoadAllDepartmentHistory"],
                    "department": "response_department"
                }
            },
            "security_secretary": {
                "name": "安全情报秘书",
                "description": "整理汇总分析结果，生成综合报告",
                "config": {
                    "role": "安全情报秘书",
                    "goal": "整理和汇总各部门安全分析结果，生成综合报告",
                    "backstory": "你是一名专业的安全情报秘书，擅长将各部门的技术分析结果转化为清晰、准确的综合安全报告。",
                    "tools": ["GenerateSecurityReport", "LoadAllDepartmentHistory"],
                    "department": "coordination_department"
                }
            },
            "comprehensive_analyst": {
                "name": "综合安全分析专家",
                "description": "跨部门综合分析，识别复杂威胁",
                "config": {
                    "role": "综合安全分析专家",
                    "goal": "综合分析各部门数据，识别潜在威胁",
                    "backstory": "你是一名全面的安全分析专家，擅长从多个维度分析系统安全状况并识别潜在威胁。",
                    "tools": ["AnalyzeSecurityData", "GenerateSecurityReport", "LoadAllDepartmentHistory"],
                    "department": "coordination_department"
                }
            },
            "threat_hunter": {
                "name": "威胁狩猎专家",
                "description": "主动搜寻和识别高级持续威胁",
                "config": {
                    "role": "威胁狩猎专家",
                    "goal": "主动搜寻系统中的高级威胁和异常行为",
                    "backstory": "你是一名经验丰富的威胁狩猎专家，擅长发现隐藏的高级持续威胁(APT)和零日攻击。",
                    "tools": ["AnalyzeProcessBehavior", "AnalyzeNetworkTraffic", "CorrelateEvents", "LoadAllDepartmentHistory"],
                    "department": "coordination_department"
                }
            },
            "forensic_analyst": {
                "name": "数字取证分析师",
                "description": "进行深度取证分析和证据收集",
                "config": {
                    "role": "数字取证分析师",
                    "goal": "对安全事件进行深度取证分析，收集和保存数字证据",
                    "backstory": "你是一名专业的数字取证分析师，擅长从系统中提取和分析数字证据，重建攻击时间线。",
                    "tools": ["GetProcessDetails", "GetWindowsLogs", "GetNetworkConnections", "LoadAllDepartmentHistory"],
                    "department": "coordination_department"
                }
            }
        }
    
    def get_templates(self) -> Dict:
        """获取所有模板"""
        return self.templates
    
    def get_template(self, template_id: str) -> Dict:
        """获取指定模板"""
        return self.templates.get(template_id, {})
    
    def get_templates_by_department(self, department: str) -> Dict:
        """根据部门获取模板"""
        result = {}
        for template_id, template in self.templates.items():
            if template["config"].get("department") == department:
                result[template_id] = template
        return result
    
    def get_department_list(self) -> List[str]:
        """获取所有部门列表"""
        departments = set()
        for template in self.templates.values():
            departments.add(template["config"].get("department", ""))
        return sorted(list(departments))
    
    def add_custom_template(self, template_id: str, template_data: Dict):
        """添加自定义模板"""
        self.templates[template_id] = template_data
    
    def remove_template(self, template_id: str):
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
    
    def save_templates_to_file(self, file_path: str):
        """保存模板到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)
    
    def load_templates_from_file(self, file_path: str):
        """从文件加载模板"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.templates.update(json.load(f))