# -*- coding: utf-8 -*-
"""
增强的日志管理器
支持按角色组分类保存详细的报告和操作记录
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedLogger:
    """
    增强的日志管理器
    - 按角色组分类保存日志
    - 详细记录角色报告和操作
    - 支持结构化日志存储
    - 提供日志查询和分析功能
    """
    
    def __init__(self, base_log_dir: str = None):
        """
        初始化增强日志管理器
        
        Args:
            base_log_dir: 基础日志目录，默认为config/log
        """
        if base_log_dir is None:
            # 获取项目根目录下的config/log目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_log_dir = os.path.join(project_root, "config", "log")
        
        self.base_log_dir = Path(base_log_dir)
        self.enhanced_log_dir = self.base_log_dir / "enhanced"
        
        # 创建目录结构
        self._create_directory_structure()
        
        # 加载角色组配置
        self.work_groups = self._load_work_groups()
        
    def _create_directory_structure(self):
        """
        创建增强日志的目录结构
        """
        directories = [
            self.enhanced_log_dir,
            self.enhanced_log_dir / "groups",
            self.enhanced_log_dir / "roles",
            self.enhanced_log_dir / "operations",
            self.enhanced_log_dir / "reports",
            self.enhanced_log_dir / "analysis"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _load_work_groups(self) -> Dict:
        """
        加载工作组配置
        """
        try:
            config_path = self.base_log_dir.parent / "json" / "work_groups.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载工作组配置失败: {e}")
        
        return {}
    
    def log_role_report(self, 
                       role_name: str, 
                       group_id: str,
                       report_content: str, 
                       report_type: str,
                       metadata: Optional[Dict] = None) -> Dict:
        """
        记录角色报告
        
        Args:
            role_name: 角色名称
            group_id: 角色组ID
            report_content: 报告内容
            report_type: 报告类型 (pre_execution, post_execution, analysis)
            metadata: 额外的元数据
            
        Returns:
            记录结果
        """
        try:
            timestamp = datetime.now()
            date_str = timestamp.strftime("%Y-%m-%d")
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建报告记录
            report_record = {
                "timestamp": time_str,
                "role_name": role_name,
                "group_id": group_id,
                "report_type": report_type,
                "content": report_content,
                "metadata": metadata or {}
            }
            
            # 按角色组保存
            group_dir = self.enhanced_log_dir / "groups" / group_id
            group_dir.mkdir(exist_ok=True)
            
            # 角色组日志文件
            group_log_file = group_dir / f"{report_type}_{date_str}.json"
            self._append_json_record(group_log_file, report_record)
            
            # 按角色保存
            role_dir = self.enhanced_log_dir / "roles" / role_name
            role_dir.mkdir(exist_ok=True)
            
            # 角色日志文件
            role_log_file = role_dir / f"{report_type}_{date_str}.json"
            self._append_json_record(role_log_file, report_record)
            
            # 保存到总报告目录
            report_file = self.enhanced_log_dir / "reports" / f"{report_type}_{date_str}.json"
            self._append_json_record(report_file, report_record)
            
            # 生成可读的文本日志
            self._generate_readable_log(report_record, group_id, role_name)
            
            return {
                "status": "success",
                "message": f"角色 {role_name} 的 {report_type} 报告已记录",
                "timestamp": time_str,
                "files": {
                    "group_log": str(group_log_file),
                    "role_log": str(role_log_file),
                    "report_log": str(report_file)
                }
            }
            
        except Exception as e:
            logger.error(f"记录角色报告失败: {e}")
            return {
                "status": "error",
                "message": f"记录角色报告失败: {str(e)}"
            }
    
    def log_operation(self, 
                     role_name: str,
                     group_id: str,
                     operation: str,
                     operation_type: str,
                     result: Any,
                     metadata: Optional[Dict] = None) -> Dict:
        """
        记录角色操作
        
        Args:
            role_name: 角色名称
            group_id: 角色组ID
            operation: 操作描述
            operation_type: 操作类型 (tool_call, decision, analysis)
            result: 操作结果
            metadata: 额外的元数据
            
        Returns:
            记录结果
        """
        try:
            timestamp = datetime.now()
            date_str = timestamp.strftime("%Y-%m-%d")
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建操作记录
            operation_record = {
                "timestamp": time_str,
                "role_name": role_name,
                "group_id": group_id,
                "operation": operation,
                "operation_type": operation_type,
                "result": result,
                "metadata": metadata or {}
            }
            
            # 按角色组保存操作日志
            group_ops_dir = self.enhanced_log_dir / "groups" / group_id / "operations"
            group_ops_dir.mkdir(exist_ok=True)
            
            group_ops_file = group_ops_dir / f"operations_{date_str}.json"
            self._append_json_record(group_ops_file, operation_record)
            
            # 按角色保存操作日志
            role_ops_dir = self.enhanced_log_dir / "roles" / role_name / "operations"
            role_ops_dir.mkdir(exist_ok=True)
            
            role_ops_file = role_ops_dir / f"operations_{date_str}.json"
            self._append_json_record(role_ops_file, operation_record)
            
            # 保存到总操作目录
            ops_file = self.enhanced_log_dir / "operations" / f"operations_{date_str}.json"
            self._append_json_record(ops_file, operation_record)
            
            return {
                "status": "success",
                "message": f"角色 {role_name} 的操作已记录",
                "timestamp": time_str
            }
            
        except Exception as e:
            logger.error(f"记录角色操作失败: {e}")
            return {
                "status": "error",
                "message": f"记录角色操作失败: {str(e)}"
            }
    
    def _append_json_record(self, file_path: Path, record: Dict):
        """
        向JSON文件追加记录
        """
        records = []
        
        # 如果文件存在，读取现有记录
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                records = []
        
        # 添加新记录
        records.append(record)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    
    def _generate_readable_log(self, record: Dict, group_id: str, role_name: str):
        """
        生成可读的文本日志
        """
        try:
            timestamp = record['timestamp']
            date_str = timestamp.split(' ')[0]
            
            # 角色组可读日志
            group_readable_dir = self.enhanced_log_dir / "groups" / group_id / "readable"
            group_readable_dir.mkdir(exist_ok=True)
            
            group_readable_file = group_readable_dir / f"{record['report_type']}_{date_str}.log"
            
            readable_content = f"""
=================================================================
【{role_name} - {record['report_type']}】- {timestamp}
=================================================================
{record['content']}
=================================================================

"""
            
            with open(group_readable_file, 'a', encoding='utf-8') as f:
                f.write(readable_content)
                
        except Exception as e:
            logger.error(f"生成可读日志失败: {e}")
    
    def get_group_reports(self, group_id: str, date: str = None) -> List[Dict]:
        """
        获取角色组的报告
        
        Args:
            group_id: 角色组ID
            date: 日期 (YYYY-MM-DD)，默认为今天
            
        Returns:
            报告列表
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        reports = []
        group_dir = self.enhanced_log_dir / "groups" / group_id
        
        if not group_dir.exists():
            return reports
        
        # 查找所有报告类型的文件
        for report_type in ["pre_execution", "post_execution", "analysis"]:
            report_file = group_dir / f"{report_type}_{date}.json"
            if report_file.exists():
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        file_reports = json.load(f)
                        reports.extend(file_reports)
                except Exception as e:
                    logger.error(f"读取报告文件失败: {e}")
        
        # 按时间排序
        reports.sort(key=lambda x: x.get('timestamp', ''))
        return reports
    
    def get_role_reports(self, role_name: str, date: str = None) -> List[Dict]:
        """
        获取特定角色的报告
        
        Args:
            role_name: 角色名称
            date: 日期 (YYYY-MM-DD)，默认为今天
            
        Returns:
            报告列表
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        reports = []
        role_dir = self.enhanced_log_dir / "roles" / role_name
        
        if not role_dir.exists():
            return reports
        
        # 查找所有报告类型的文件
        for report_type in ["pre_execution", "post_execution", "analysis"]:
            report_file = role_dir / f"{report_type}_{date}.json"
            if report_file.exists():
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        file_reports = json.load(f)
                        reports.extend(file_reports)
                except Exception as e:
                    logger.error(f"读取报告文件失败: {e}")
        
        # 按时间排序
        reports.sort(key=lambda x: x.get('timestamp', ''))
        return reports
    
    def generate_group_summary(self, group_id: str, date: str = None) -> Dict:
        """
        生成角色组的日志摘要
        
        Args:
            group_id: 角色组ID
            date: 日期 (YYYY-MM-DD)，默认为今天
            
        Returns:
            摘要信息
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        reports = self.get_group_reports(group_id, date)
        
        # 统计信息
        summary = {
            "group_id": group_id,
            "date": date,
            "total_reports": len(reports),
            "report_types": {},
            "roles_involved": set(),
            "timeline": []
        }
        
        for report in reports:
            # 统计报告类型
            report_type = report.get('report_type', 'unknown')
            summary['report_types'][report_type] = summary['report_types'].get(report_type, 0) + 1
            
            # 记录涉及的角色
            summary['roles_involved'].add(report.get('role_name', 'unknown'))
            
            # 添加到时间线
            summary['timeline'].append({
                "timestamp": report.get('timestamp'),
                "role": report.get('role_name'),
                "type": report_type
            })
        
        summary['roles_involved'] = list(summary['roles_involved'])
        
        # 保存摘要
        summary_file = self.enhanced_log_dir / "analysis" / f"group_{group_id}_summary_{date}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary

# 全局实例
enhanced_logger = EnhancedLogger()

# 便捷函数
def log_agent_report_enhanced(role_name: str, 
                             group_id: str,
                             content: str, 
                             report_type: str,
                             metadata: Optional[Dict] = None) -> Dict:
    """
    增强的Agent报告记录函数
    
    Args:
        role_name: 角色名称
        group_id: 角色组ID
        content: 报告内容
        report_type: 报告类型
        metadata: 额外的元数据
        
    Returns:
        记录结果
    """
    return enhanced_logger.log_role_report(role_name, group_id, content, report_type, metadata)

def log_agent_operation(role_name: str,
                       group_id: str,
                       operation: str,
                       operation_type: str,
                       result: Any,
                       metadata: Optional[Dict] = None) -> Dict:
    """
    记录Agent操作
    
    Args:
        role_name: 角色名称
        group_id: 角色组ID
        operation: 操作描述
        operation_type: 操作类型
        result: 操作结果
        metadata: 额外的元数据
        
    Returns:
        记录结果
    """
    return enhanced_logger.log_operation(role_name, group_id, operation, operation_type, result, metadata)