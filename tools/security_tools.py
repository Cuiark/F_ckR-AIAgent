#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import subprocess
import uuid  # 添加uuid模块用于生成唯一ID
from config import logger
from crewai.tools import tool
from config import logger
import re
import logging
from datetime import datetime, timedelta

# -------------------------------
# 安全工具实现
# -------------------------------
# 在文件顶部添加
try:
    import psutil
except ImportError:
    print("警告: psutil 库未安装，进程相关功能将不可用")
    psutil = None

# 修改 GetProcessDetails 工具
@tool("GetProcessDetails")
def get_process_details() -> str:
    """获取当前系统进程详情"""
    _log_tool_output("正在获取系统进程详情...")
    try:
        if psutil is None:
            return "获取进程详情时出错: psutil 库未安装"
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'create_time']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'username': pinfo['username'],
                    'cmdline': ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else '',
                    'create_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pinfo['create_time']))
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        _log_tool_output(f"成功获取到 {len(processes)} 个进程信息")
        return json.dumps(processes, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"获取进程详情时出错: {str(e)}"
        _log_tool_output(error_msg)
        return error_msg
    try:  # 这里有一个额外的 try 块，永远不会执行
        result = subprocess.run(
            ['wmic', 'process', 'get', 'ProcessId,ExecutablePath,Name'],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        lines = result.stdout.strip().splitlines()
        headers = [h.strip() for h in lines[0].split()]
        processes = []
        
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.strip().split(None, len(headers)-1)
            if len(parts) == len(headers):
                proc_info = dict(zip(headers, parts))
                processes.append(proc_info)
                
        return json.dumps(processes, ensure_ascii=False)
    except Exception as e:
        logger.error(f"获取进程详情失败: {str(e)}")
        return f"错误: {str(e)}"

@tool("GetWindowsLogs")
def get_windows_logs() -> str:
    """获取Windows安全事件日志，包括登录失败、权限提升和进程创建事件"""
    logs = []
    event_ids = ["4625", "4672", "4688"]  # 关注的事件ID
    
    for event_id in event_ids:
        cmd = f'powershell -Command "Get-WinEvent -FilterHashtable @{{LogName=\'Security\';ID=\'{event_id}\'}} -MaxEvents 5 | Format-List"'
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            logs.append(result.stdout)
        except Exception as e:
            logger.error(f"获取事件日志失败: {str(e)}")
    
    return "\n".join(logs)

@tool("GetServices")
def get_services() -> str:
    """获取当前系统中运行的服务列表"""
    try:
        result = subprocess.run(["sc", "query"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        return result.stdout
    except Exception as e:
        logger.error(f"获取服务列表失败: {str(e)}")
        return f"错误: {str(e)}"

# 定义基准进程文件路径
BASELINE_PROCESSES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      "config", "json", "baseline_processes.json")

@tool("LoadBaselineProcesses")
def load_baseline_processes() -> str:
    """从配置文件加载基准进程列表"""
    if os.path.exists(BASELINE_PROCESSES_FILE):
        try:
            with open(BASELINE_PROCESSES_FILE, "r", encoding="utf-8") as f:
                baseline = json.load(f)
                return json.dumps(baseline)
        except Exception as e:
            logger.error(f"加载基准进程失败: {str(e)}")
            return json.dumps({"status": "error", "message": f"加载基准进程失败: {str(e)}", "data": []})
    else:
        logger.warning(f"未找到基准进程文件: {BASELINE_PROCESSES_FILE}")
        # 创建空的基准文件
        try:
            with open(BASELINE_PROCESSES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return json.dumps({
                "status": "no_baseline", 
                "message": "没有基准文件的情况下，已创建空基准文件，直接进行分析", 
                "data": []
            })
        except Exception as e:
            logger.error(f"创建基准进程文件失败: {str(e)}")
            return json.dumps({"status": "error", "message": f"创建基准进程文件失败: {str(e)}", "data": []})

@tool("TerminateProcess")
def terminate_process(process_name: str) -> str:
    """终止指定的进程"""
    try:
        subprocess.run(["taskkill", "/F", "/IM", process_name])
        return f"已尝试终止进程: {process_name}"
    except Exception as e:
        logger.error(f"终止进程失败: {str(e)}")
        return f"错误: {str(e)}"

@tool("BlockIP")
def block_ip(ip_address: str) -> str:
    """在Windows防火墙中阻止指定的IP地址"""
    try:
        rule_name = f"Block_{ip_address}"
        subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={rule_name}", "dir=in", "action=block", 
            f"remoteip={ip_address}"
        ])
        return f"已在防火墙中阻止IP: {ip_address}"
    except Exception as e:
        logger.error(f"阻止IP失败: {str(e)}")
        return f"错误: {str(e)}"

@tool("GenerateSecurityReport")
def generate_security_report(threat_info: str, response_info: str) -> str:
    """
    生成客观的安全分析报告
    
    参数:
        threat_info: 威胁信息JSON字符串
        response_info: 响应措施信息JSON字符串
        
    返回:
        格式化的技术安全报告
    """
    try:
        threats = json.loads(threat_info)
        responses = json.loads(response_info)
        
        # 获取当前时间作为报告生成时间
        report_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 威胁等级定义 - 使用标准的安全风险分级
        threat_levels = {
            "critical": "严重",
            "high": "高危",
            "medium": "中危", 
            "low": "低危",
            "info": "信息"
        }
        
        # 生成报告头部 - 简洁明了
        report = f"""
=================================================================
                      系统安全分析报告
                  {report_time}
=================================================================

## 1. 摘要

"""
        
        # 添加威胁摘要 - 客观陈述事实
        if threats:
            threat_count = len(threats)
            critical_count = sum(1 for t in threats if t.get("level") == "critical")
            high_count = sum(1 for t in threats if t.get("level") == "high")
            
            report += f"系统检测到 {threat_count} 个潜在安全问题，其中严重级别 {critical_count} 个，高危级别 {high_count} 个。\n\n"
        else:
            report += "当前扫描未发现明显安全问题。\n\n"
        
        # 添加威胁详情 - 结构化呈现
        report += "## 2. 详细分析\n\n"
        if threats:
            for i, threat in enumerate(threats, 1):
                level = threat_levels.get(threat.get("level", "info"), "未分类")
                report += f"### 2.{i} [{level}] {threat.get('name', '未命名问题')}\n"
                report += f"- **描述**: {threat.get('description', '无详细描述')}\n"
                report += f"- **来源**: {threat.get('source', '未确定')}\n"
                if 'evidence' in threat:
                    report += f"- **证据**: {threat.get('evidence', '无')}\n"
                report += "\n"
        else:
            report += "本次分析未发现需要关注的安全问题。\n\n"
        
        # 添加已执行措施 - 清晰列出具体操作
        report += "## 3. 已执行操作\n\n"
        if responses:
            for i, response in enumerate(responses, 1):
                report += f"### 3.{i} {response.get('action', '未命名操作')}\n"
                report += f"- **目标**: {response.get('target', '未指定')}\n"
                report += f"- **结果**: {response.get('result', '未知')}\n"
                if 'timestamp' in response:
                    report += f"- **时间**: {response.get('timestamp', '')}\n"
                report += "\n"
        else:
            report += "未执行自动响应操作。\n\n"
        
        # 添加建议 - 基于事实的具体建议
        report += "## 4. 建议措施\n\n"
        
        # 根据威胁自动生成建议，而不是硬编码
        suggestions = []
        
        # 基于威胁类型生成相应建议
        if threats:
            for threat in threats:
                level = threat.get("level", "low")
                threat_type = threat.get("type", "unknown")
                
                if level in ["critical", "high"]:
                    if "process" in threat_type.lower():
                        suggestions.append({
                            "priority": "高",
                            "action": f"终止可疑进程 {threat.get('name', '未知进程')}"
                        })
                    elif "network" in threat_type.lower():
                        suggestions.append({
                            "priority": "高",
                            "action": f"阻止可疑IP {threat.get('source', '未知IP')}"
                        })
                    else:
                        suggestions.append({
                            "priority": "高",
                            "action": f"进一步分析 {threat.get('name', '未知威胁')}"
                        })
                else:
                    suggestions.append({
                        "priority": "中",
                        "action": f"监控 {threat.get('name', '未知项目')} 的活动"
                    })
        
        # 添加通用建议
        if not suggestions:
            suggestions = [
                {"priority": "中", "action": "定期更新系统安全补丁"},
                {"priority": "中", "action": "检查系统日志中的异常活动"},
                {"priority": "低", "action": "更新基准进程列表"}
            ]
        
        # 去重建议 - 防止重复输出相同建议
        unique_suggestions = []
        unique_actions = set()
        for suggestion in suggestions:
            action = suggestion['action']
            if action not in unique_actions:
                unique_actions.add(action)
                unique_suggestions.append(suggestion)
        
        # 使用去重后的建议列表
        for i, suggestion in enumerate(unique_suggestions, 1):
            report += f"### 4.{i} [{suggestion['priority']}优先级] {suggestion['action']}\n"
        
        report += "\n=================================================================\n"
        
        # 在报告末尾添加时间信息
        report += f"""
## 5. 时间信息

- **报告生成时间**: {report_time}
- **响应开始时间**: {responses[0].get('timestamp', report_time) if responses else report_time}
- **响应结束时间**: {responses[-1].get('timestamp', report_time) if responses else report_time}

=================================================================
"""
        
        return report
        
    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        return f"生成报告时发生错误: {str(e)}"

@tool("FindNetstate")  # 修改这里，将 @tools 改为 @tool
def FindNetstate() -> str:
    """获取当前系统中网络连接的详细信息"""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        return str(result.stdout)
    except Exception as e:
        logger.error(f"获取网络连接信息失败: {str(e)}")
        return f"错误: {str(e)}"

# 白名单和建议记录工具
@tool("ReadWhitelist")
def read_whitelist() -> str:
    """读取白名单文件，获取已记录的安全项目"""
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                whitelist = json.load(f)
                return json.dumps(whitelist, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"读取白名单失败: {str(e)}")
            return json.dumps({"status": "error", "message": f"读取白名单失败: {str(e)}", "items": []})
    else:
        # 如果文件不存在，创建一个空白名单
        try:
            with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
                empty_whitelist = {"processes": [], "ips": [], "services": []}
                json.dump(empty_whitelist, f, ensure_ascii=False, indent=2)
            return json.dumps(empty_whitelist, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"创建白名单失败: {str(e)}")
            return json.dumps({"status": "error", "message": f"创建白名单失败: {str(e)}", "items": []})

@tool("AddToWhitelist")
def add_to_whitelist(item_type: str, item_name: str, reason: str, response_time: str = None) -> str:
    """
    添加项目到白名单
    
    参数:
        item_type: 项目类型，可以是 'process', 'ip', 或 'service'
        item_name: 项目名称或标识
        reason: 添加到白名单的原因
        response_time: 响应时间，如果为None则使用当前时间
        
    返回:
        添加结果
    """
    # 确保白名单文件存在
    if not os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
            json.dump({"processes": [], "ips": [], "services": []}, f, ensure_ascii=False, indent=2)
    
    try:
        # 读取现有白名单
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            whitelist = json.load(f)
        
        # 确保所有必要的键存在
        if "processes" not in whitelist:
            whitelist["processes"] = []
        if "ips" not in whitelist:
            whitelist["ips"] = []
        if "services" not in whitelist:
            whitelist["services"] = []
        
        # 根据项目类型添加到相应列表
        if item_type == "process":
            target_list = whitelist["processes"]
            item_key = "name"
        elif item_type == "ip":
            target_list = whitelist["ips"]
            item_key = "address"
        elif item_type == "service":
            target_list = whitelist["services"]
            item_key = "name"
        else:
            return json.dumps({"status": "error", "message": f"未知的项目类型: {item_type}"})
        
        # 检查项目是否已存在
        for item in target_list:
            if item.get(item_key) == item_name:
                return json.dumps({"status": "exists", "message": f"{item_type} '{item_name}' 已在白名单中"})
        
        # 设置响应时间和记录时间
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        if response_time is None:
            response_time = current_time
            
        # 添加新项目
        new_item = {
            item_key: item_name,
            "reason": reason,
            "response_time": response_time,  # 响应时间
            "record_time": current_time      # 记录时间
        }
        target_list.append(new_item)
        
        # 保存更新后的白名单
        with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
            json.dump(whitelist, f, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "status": "success", 
            "message": f"已将 {item_type} '{item_name}' 添加到白名单",
            "response_time": response_time,
            "record_time": current_time
        })
        
    except Exception as e:
        logger.error(f"添加到白名单失败: {str(e)}")
        return json.dumps({"status": "error", "message": f"添加到白名单失败: {str(e)}"})

@tool("CheckWhitelist")
def check_whitelist(item_type: str, item_name: str) -> str:
    """
    检查项目是否在白名单中
    
    参数:
        item_type: 项目类型，可以是 'process', 'ip', 或 'service'
        item_name: 项目名称或标识
        
    返回:
        检查结果
    """
    if not os.path.exists(WHITELIST_FILE):  # 修改这里
        return json.dumps({"status": "not_found", "message": "白名单文件不存在"})
    
    try:
        # 读取白名单
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:  # 修改这里
            whitelist = json.load(f)
        
        # 根据项目类型选择相应列表
        if item_type == "process":
            target_list = whitelist.get("processes", [])
            item_key = "name"
        elif item_type == "ip":
            target_list = whitelist.get("ips", [])
            item_key = "address"
        elif item_type == "service":
            target_list = whitelist.get("services", [])
            item_key = "name"
        else:
            return json.dumps({"status": "error", "message": f"未知的项目类型: {item_type}"})
        
        # 检查项目是否存在
        for item in target_list:
            if item.get(item_key) == item_name:
                return json.dumps({
                    "status": "found", 
                    "message": f"{item_type} '{item_name}' 在白名单中",
                    "details": item
                })
        
        return json.dumps({"status": "not_found", "message": f"{item_type} '{item_name}' 不在白名单中"})
        
    except Exception as e:
        logger.error(f"检查白名单失败: {str(e)}")
        return json.dumps({"status": "error", "message": f"检查白名单失败: {str(e)}"})

@tool("AddSuggestionNote")
def add_suggestion_note(suggestion: str, source: str = "系统", response_time: str = None) -> str:
    """
    添加建议到记事本
    
    参数:
        suggestion: 建议内容
        source: 建议来源
        response_time: 响应时间，如果为None则使用当前时间
        
    返回:
        添加结果
    """
    # 确保记事本文件存在
    if not os.path.exists(SUGGESTION_NOTES_FILE):
        with open(SUGGESTION_NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump({"suggestions": []}, f, ensure_ascii=False, indent=2)
    
    try:
        # 读取现有记事本
        with open(SUGGESTION_NOTES_FILE, "r", encoding="utf-8") as f:
            notes = json.load(f)
        
        # 确保suggestions键存在
        if "suggestions" not in notes:
            notes["suggestions"] = []
        
        # 设置响应时间和记录时间
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        if response_time is None:
            response_time = current_time
            
        # 添加新建议
        new_suggestion = {
            "content": suggestion,
            "source": source,
            "response_time": response_time,  # 响应时间
            "record_time": current_time,     # 记录时间
            "id": str(uuid.uuid4())[:8]      # 生成短ID
        }
        notes["suggestions"].append(new_suggestion)
        
        # 保存更新后的记事本
        with open(SUGGESTION_NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "status": "success", 
            "message": "建议已添加到记事本", 
            "id": new_suggestion["id"],
            "response_time": response_time,
            "record_time": current_time
        })
        
    except Exception as e:
        logger.error(f"添加建议失败: {str(e)}")
        return json.dumps({"status": "error", "message": f"添加建议失败: {str(e)}"})

@tool("GetSuggestionNotes")
def get_suggestion_notes() -> str:
    """获取所有记录的建议"""
    if not os.path.exists(SUGGESTION_NOTES_FILE):
        # 如果文件不存在，创建一个空记事本
        try:
            with open(SUGGESTION_NOTES_FILE, "w", encoding="utf-8") as f:
                empty_notes = {"suggestions": []}
                json.dump(empty_notes, f, ensure_ascii=False, indent=2)
            return json.dumps(empty_notes, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"创建记事本失败: {str(e)}")
            return json.dumps({"status": "error", "message": f"创建记事本失败: {str(e)}", "suggestions": []})
    
    try:
        # 读取记事本
        with open(SUGGESTION_NOTES_FILE, "r", encoding="utf-8") as f:
            notes = json.load(f)
            return json.dumps(notes, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"读取记事本失败: {str(e)}")
        return json.dumps({"status": "error", "message": f"读取记事本失败: {str(e)}", "suggestions": []})

@tool("TimeViewer")
def TimeViewer() -> str:
    """获取当前时间"""
    return time.strftime("%Y-%m-%d %H:%M:%S")


@tool("LogAgentReport")
def log_agent_report(content: str, report_type: str, agent_name: str, include_suggestion: str = None, previous_report: str = None) -> str:
    """
    将Agent报告记录到日志文件
    
    参数:
        content: 报告内容
        report_type: 报告类型，'pre'表示执行前报告，'post'表示执行后报告
        agent_name: Agent名称
        include_suggestion: 可选的建议内容
        previous_report: 上一位角色的报告内容
        
    返回:
        记录结果
    """
    # 直接定义日志目录路径
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "log")
    os.makedirs(log_dir, exist_ok=True)
    
    # 获取当前时间
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    current_date = time.strftime("%Y-%m-%d")
    
    # 创建上下文传递文件，用于存储角色之间传递的信息
    context_file = os.path.join(log_dir, "agent_context.json")
    
    # 根据报告类型选择不同的日志文件
    if report_type == "pre":
        log_file = os.path.join(log_dir, f"pre_execution_{current_date}.log")
        # 从报告中提取工具与方法部分
        tools_section = extract_section(content, "工具与方法", "预期结果")
        if not tools_section:
            tools_section = extract_section(content, "可能使用的工具和方法", "预期的执行结果")
        if not tools_section:
            tools_section = "未找到工具与方法部分"
        
        # 提取任务描述
        task_description = extract_task_description(content)
        
        log_content = f"""
=================================================================
【{agent_name} - 执行前报告】- {current_time}
=================================================================
【任务描述】
{task_description}

【工具与方法】
{tools_section}
"""
        # 如果有上一位角色的报告，提取关键信息并添加到日志中
        if previous_report:
            previous_results = extract_section(previous_report, "结果分析", "建议措施")
            if not previous_results:
                previous_results = extract_section(previous_report, "详细分析", "已执行操作")
            if not previous_results:
                previous_results = extract_section(previous_report, "执行结果")
            
            if previous_results:
                log_content += f"""
【上一角色的关键发现】
{previous_results}
"""
                
                # 保存上下文信息到JSON文件，供下一个角色使用
                try:
                    context_data = {
                        "previous_agent": agent_name,
                        "key_findings": previous_results,
                        "task_description": task_description,
                        "timestamp": current_time
                    }
                    with open(context_file, "w", encoding="utf-8") as f:
                        json.dump(context_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.error(f"保存上下文信息失败: {str(e)}")
    else:  # post execution report
        log_file = os.path.join(log_dir, f"post_execution_{current_date}.log")
        # 从报告中提取结果分析与评估部分
        results_section = extract_section(content, "结果分析", "建议措施")
        if not results_section:
            results_section = extract_section(content, "详细分析", "已执行操作")
        if not results_section:
            results_section = "未找到结果分析部分"
        
        log_content = f"""
=================================================================
【{agent_name} - 执行后报告】- {current_time}
=================================================================
【结果分析与评估】
{results_section}
"""
    
    # 如果有建议，添加到日志中
    if include_suggestion:
        log_content += f"""
【用户建议】
{include_suggestion}
"""
    
    log_content += "=================================================================\n\n"
    
    # 写入日志文件
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_content)
        
        return json.dumps({
            "status": "success", 
            "message": f"已将{report_type}报告记录到日志", 
            "log_file": log_file,
            "time": current_time
        })
        
    except Exception as e:
        logger.error(f"记录报告失败: {str(e)}")
        return json.dumps({"status": "error", "message": f"记录报告失败: {str(e)}"})

def extract_section(content: str, start_marker: str, end_marker: str = None) -> str:
    """从报告内容中提取指定部分"""
    try:
        # 如果没有指定结束标记，则提取到文档末尾
        if end_marker is None:
            if start_marker in content:
                parts = content.split(start_marker, 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return ""
            
        # 尝试查找标题格式 (## 2. 详细分析)
        pattern1 = rf"##\s*\d*\.*\s*{start_marker}(.*?)##\s*\d*\.*\s*{end_marker}"
        # 尝试查找普通文本格式
        pattern2 = rf"{start_marker}[：:](.*?){end_marker}[：:]"
        # 尝试查找列表项格式 (2. 详细分析:)
        pattern3 = rf"\d+\.\s*{start_marker}[：:](.*?)\d+\.\s*{end_marker}[：:]"
        # 尝试查找Markdown格式 (### 详细分析)
        pattern4 = rf"###\s+{start_marker}(.*?)###\s+{end_marker}"
        # 尝试查找【标记】格式
        pattern5 = rf"【{start_marker}】(.*?)【{end_marker}】"
        
        # 尝试不同的模式
        for pattern in [pattern1, pattern2, pattern3, pattern4, pattern5]:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # 如果没有找到精确匹配，尝试查找包含关键词的段落
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if start_marker in para:
                return para.strip()
                
        return ""
    except Exception as e:
        logger.error(f"提取报告部分失败: {str(e)}")
        return ""

# 新增函数：提取任务部分
def extract_task_description(content: str) -> str:
    """从报告中提取任务描述部分"""
    task_markers = ["任务内容", "任务描述", "执行任务", "将要执行的任务"]
    
    for marker in task_markers:
        # 修复：传递None作为end_marker参数
        task_section = extract_section(content, marker, None)
        if task_section:
            return task_section
    
    # 如果没有找到明确的任务部分，尝试提取第一部分
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if any(marker in line for marker in ["目的", "重要性", "工具", "方法"]):
            return '\n'.join(lines[:i]).strip()
    
    return ""

# 添加到文件顶部
# 添加全局回调函数变量
_tool_output_callback = None

def set_tool_output_callback(callback):
    """
    设置工具输出回调函数
    
    参数:
        callback: 回调函数，接收一个字符串参数
    """
    global _tool_output_callback
    _tool_output_callback = callback

def _log_tool_output(message):
    """
    记录工具输出
    
    参数:
        message: 输出消息
    """
    # 如果设置了回调函数，则调用回调函数
    if _tool_output_callback:
        _tool_output_callback(message)
    # 同时记录到日志
    logging.info(f"[工具输出] {message}")

@tool("CompareWithBaseline")
def compare_with_baseline(process_list: str = None) -> str:
    """
    将当前进程与基线进程进行比较，识别异常进程
    
    参数:
        process_list: 当前进程列表的JSON字符串，如果为None则自动获取
        
    返回:
        比较结果的字符串描述
    """
    try:
        # 如果没有提供进程列表，则获取当前进程
        if not process_list:
            process_list = get_process_details()
        
        # 解析进程列表
        if isinstance(process_list, str):
            try:
                current_processes = json.loads(process_list)
            except json.JSONDecodeError as e:
                return f"进程数据JSON解析失败: {str(e)}。原始数据: {process_list[:100]}..."
        else:
            current_processes = process_list
        
        # 确保current_processes是列表
        if not isinstance(current_processes, list):
            return "进程数据格式错误，期望列表格式"
            
        # 加载基线进程
        baseline_processes = []
        if os.path.exists(BASELINE_PROCESSES_FILE):
            try:
                with open(BASELINE_PROCESSES_FILE, 'r', encoding='utf-8') as f:
                    baseline_processes = json.load(f)
            except Exception as e:
                return f"加载基线进程文件失败: {str(e)}"
        else:
            return "基线进程文件不存在，无法进行比较"
        
        # 将基线进程转换为字典，便于查找
        baseline_dict = {}
        for p in baseline_processes:
            if isinstance(p, dict) and 'name' in p:
                baseline_dict[p['name'].lower()] = p
        
        # 比较进程
        suspicious_processes = []
        for process in current_processes:
            # 检查process是否为字典类型
            if isinstance(process, str):
                # 如果是字符串，跳过或尝试解析
                continue
            if not isinstance(process, dict) or 'name' not in process:
                # 如果不是字典或没有name字段，跳过
                continue
            process_name = process['name'].lower()
            
            # 检查进程是否在白名单中
            whitelist_result = check_whitelist("process", process_name)
            try:
                whitelist_status = json.loads(whitelist_result).get("status")
                if whitelist_status == "found":
                    continue
            except:
                pass
                
            # 检查进程是否在基线中
            if process_name not in baseline_dict:
                suspicious_processes.append({
                    'name': process['name'],
                    'pid': process['pid'],
                    'reason': '不在基线中的进程',
                    'details': process
                })
                continue
                
            # 检查进程路径是否与基线一致
            baseline_process = baseline_dict[process_name]
            if 'path' in process and 'path' in baseline_process:
                if process['path'].lower() != baseline_process['path'].lower():
                    suspicious_processes.append({
                        'name': process['name'],
                        'pid': process['pid'],
                        'reason': '进程路径与基线不一致',
                        'baseline_path': baseline_process['path'],
                        'current_path': process['path'],
                        'details': process
                    })
        
        # 生成报告
        if not suspicious_processes:
            return "未发现异常进程，所有进程均符合基线要求"
        
        report = f"发现 {len(suspicious_processes)} 个异常进程:\n\n"
        for i, proc in enumerate(suspicious_processes, 1):
            report += f"{i}. 进程名: {proc['name']} (PID: {proc['pid']})\n"
            report += f"   原因: {proc['reason']}\n"
            
            if 'baseline_path' in proc:
                report += f"   基线路径: {proc['baseline_path']}\n"
                report += f"   当前路径: {proc['current_path']}\n"
            
            report += f"   详情: {json.dumps(proc['details'], ensure_ascii=False, indent=2)}\n\n"
        
        return report
        
    except Exception as e:
        import traceback
        logger.error(f"比较基线进程时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return f"比较基线进程时出错: {str(e)}"

# -------------------------------
# 部门历史管理工具
# -------------------------------

# 部门历史文件路径
DEPARTMENT_HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     "data", "department_history")

def _get_department_history_file(department: str) -> str:
    """获取部门历史文件路径"""
    return os.path.join(DEPARTMENT_HISTORY_DIR, department, "analysis_history.json")

def _load_department_history(department: str) -> list:
    """加载部门历史记录"""
    history_file = _get_department_history_file(department)
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载部门历史失败: {str(e)}")
            return []
    return []

def _save_department_history(department: str, history: list) -> bool:
    """保存部门历史记录"""
    try:
        history_file = _get_department_history_file(department)
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存部门历史失败: {str(e)}")
        return False

@tool("LoadProcessHistory")
def load_process_history() -> str:
    """加载进程部门历史记录"""
    try:
        history = _load_department_history("process_department")
        return json.dumps(history, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"加载进程历史失败: {str(e)}"

@tool("LoadLogHistory")
def load_log_history() -> str:
    """加载日志部门历史记录"""
    try:
        history = _load_department_history("log_department")
        return json.dumps(history, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"加载日志历史失败: {str(e)}"

@tool("LoadServiceHistory")
def load_service_history() -> str:
    """加载服务部门历史记录"""
    try:
        history = _load_department_history("service_department")
        return json.dumps(history, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"加载服务历史失败: {str(e)}"

@tool("LoadNetworkHistory")
def load_network_history() -> str:
    """加载网络部门历史记录"""
    try:
        history = _load_department_history("network_department")
        return json.dumps(history, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"加载网络历史失败: {str(e)}"

@tool("LoadAllDepartmentHistory")
def load_all_department_history() -> str:
    """加载所有部门历史记录"""
    try:
        all_history = {}
        departments = ["process_department", "log_department", "service_department", 
                      "network_department", "response_department", "coordination_department"]
        
        for dept in departments:
            all_history[dept] = _load_department_history(dept)
        
        return json.dumps(all_history, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"加载所有部门历史失败: {str(e)}"

@tool("SaveProcessAnalysis")
def save_process_analysis(analysis_result: str) -> str:
    """保存进程分析结果到部门历史"""
    try:
        history = _load_department_history("process_department")
        
        # 创建新的历史记录
        new_record = {
            "timestamp": datetime.now().isoformat(),
            "analysis_id": str(uuid.uuid4()),
            "type": "process_analysis",
            "content": analysis_result
        }
        
        history.append(new_record)
        
        # 保持历史记录数量在合理范围内（最多保留1000条）
        if len(history) > 1000:
            history = history[-1000:]
        
        if _save_department_history("process_department", history):
            return f"成功保存进程分析结果，记录ID: {new_record['analysis_id']}"
        else:
            return "保存进程分析结果失败"
    except Exception as e:
        return f"保存进程分析结果失败: {str(e)}"

@tool("SaveLogAnalysis")
def save_log_analysis(analysis_result: str) -> str:
    """保存日志分析结果到部门历史"""
    try:
        history = _load_department_history("log_department")
        
        new_record = {
            "timestamp": datetime.now().isoformat(),
            "analysis_id": str(uuid.uuid4()),
            "type": "log_analysis",
            "content": analysis_result
        }
        
        history.append(new_record)
        
        if len(history) > 1000:
            history = history[-1000:]
        
        if _save_department_history("log_department", history):
            return f"成功保存日志分析结果，记录ID: {new_record['analysis_id']}"
        else:
            return "保存日志分析结果失败"
    except Exception as e:
        return f"保存日志分析结果失败: {str(e)}"

@tool("SaveServiceAnalysis")
def save_service_analysis(analysis_result: str) -> str:
    """保存服务分析结果到部门历史"""
    try:
        history = _load_department_history("service_department")
        
        new_record = {
            "timestamp": datetime.now().isoformat(),
            "analysis_id": str(uuid.uuid4()),
            "type": "service_analysis",
            "content": analysis_result
        }
        
        history.append(new_record)
        
        if len(history) > 1000:
            history = history[-1000:]
        
        if _save_department_history("service_department", history):
            return f"成功保存服务分析结果，记录ID: {new_record['analysis_id']}"
        else:
            return "保存服务分析结果失败"
    except Exception as e:
        return f"保存服务分析结果失败: {str(e)}"

@tool("SaveNetworkAnalysis")
def save_network_analysis(analysis_result: str) -> str:
    """保存网络分析结果到部门历史"""
    try:
        history = _load_department_history("network_department")
        
        new_record = {
            "timestamp": datetime.now().isoformat(),
            "analysis_id": str(uuid.uuid4()),
            "type": "network_analysis",
            "content": analysis_result
        }
        
        history.append(new_record)
        
        if len(history) > 1000:
            history = history[-1000:]
        
        if _save_department_history("network_department", history):
            return f"成功保存网络分析结果，记录ID: {new_record['analysis_id']}"
        else:
            return "保存网络分析结果失败"
    except Exception as e:
        return f"保存网络分析结果失败: {str(e)}"

# -------------------------------
# 时间过滤工具
# -------------------------------

@tool("FilterProcessesByTime")
def filter_processes_by_time(processes_data: str, hours_back: int = 24) -> str:
    """根据时间过滤进程数据，只返回指定时间内创建的进程"""
    try:
        processes = json.loads(processes_data)
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        filtered_processes = []
        for process in processes:
            if 'create_time' in process:
                try:
                    # 解析进程创建时间
                    proc_time = datetime.strptime(process['create_time'], '%Y-%m-%d %H:%M:%S')
                    if proc_time >= cutoff_time:
                        filtered_processes.append(process)
                except ValueError:
                    # 如果时间格式解析失败，保留该进程
                    filtered_processes.append(process)
            else:
                # 如果没有创建时间信息，保留该进程
                filtered_processes.append(process)
        
        return json.dumps(filtered_processes, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"过滤进程数据失败: {str(e)}"

@tool("FilterLogsByTime")
def filter_logs_by_time(logs_data: str, hours_back: int = 24) -> str:
    """根据时间过滤日志数据，只返回指定时间内的日志"""
    try:
        # 简单的时间过滤，实际实现可能需要根据日志格式调整
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # 这里简化处理，实际应该解析日志中的时间戳
        # 由于Windows事件日志格式复杂，这里返回原始数据
        # 在实际应用中，应该解析PowerShell返回的日志格式
        
        return logs_data  # 暂时返回原始数据
    except Exception as e:
        return f"过滤日志数据失败: {str(e)}"

@tool("FilterServicesByTime")
def filter_services_by_time(services_data: str, hours_back: int = 24) -> str:
    """根据时间过滤服务数据（服务通常不需要时间过滤，返回原始数据）"""
    try:
        # 服务信息通常不包含启动时间，这里返回原始数据
        return services_data
    except Exception as e:
        return f"过滤服务数据失败: {str(e)}"

@tool("FilterConnectionsByTime")
def filter_connections_by_time(connections_data: str, hours_back: int = 24) -> str:
    """根据时间过滤网络连接数据"""
    try:
        # 网络连接通常是实时数据，这里返回原始数据
        return connections_data
    except Exception as e:
        return f"过滤网络连接数据失败: {str(e)}"

# -------------------------------
# 新增网络和服务分析工具
# -------------------------------

@tool("GetNetworkConnections")
def get_network_connections() -> str:
    """获取当前系统网络连接信息"""
    try:
        if psutil is None:
            return "获取网络连接时出错: psutil 库未安装"
        
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            try:
                connections.append({
                    'family': conn.family.name if hasattr(conn.family, 'name') else str(conn.family),
                    'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                    'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                    'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                    'status': conn.status,
                    'pid': conn.pid
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return json.dumps(connections, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取网络连接失败: {str(e)}"

@tool("AnalyzeNetworkTraffic")
def analyze_network_traffic(connections_data: str) -> str:
    """分析网络流量，识别可疑连接"""
    try:
        connections = json.loads(connections_data)
        suspicious_connections = []
        
        for conn in connections:
            # 检查可疑端口
            if 'remote_address' in conn and conn['remote_address'] != "N/A":
                remote_port = conn['remote_address'].split(':')[-1]
                if remote_port in ['4444', '5555', '6666', '7777', '8888', '9999']:  # 常见后门端口
                    suspicious_connections.append({
                        'connection': conn,
                        'reason': f'连接到可疑端口: {remote_port}'
                    })
        
        if not suspicious_connections:
            return "未发现可疑网络连接"
        
        return json.dumps(suspicious_connections, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"分析网络流量失败: {str(e)}"

@tool("DetectSuspiciousConnections")
def detect_suspicious_connections(connections_data: str) -> str:
    """检测可疑网络连接"""
    try:
        connections = json.loads(connections_data)
        alerts = []
        
        for conn in connections:
            # 检查外部连接
            if 'remote_address' in conn and conn['remote_address'] != "N/A":
                remote_ip = conn['remote_address'].split(':')[0]
                # 简单的IP检查（实际应该使用更复杂的威胁情报）
                if not (remote_ip.startswith('192.168.') or 
                       remote_ip.startswith('10.') or 
                       remote_ip.startswith('172.') or
                       remote_ip == '127.0.0.1'):
                    alerts.append({
                        'type': 'external_connection',
                        'connection': conn,
                        'message': f'检测到外部连接: {remote_ip}'
                    })
        
        return json.dumps(alerts, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"检测可疑连接失败: {str(e)}"

@tool("AnalyzeServiceSecurity")
def analyze_service_security(services_data: str) -> str:
    """分析服务安全性"""
    try:
        # 解析服务数据并检查可疑服务
        suspicious_services = []
        
        # 简单的服务名检查
        suspicious_names = ['backdoor', 'trojan', 'malware', 'hack']
        
        lines = services_data.split('\n')
        for line in lines:
            if 'SERVICE_NAME:' in line:
                service_name = line.split('SERVICE_NAME:')[1].strip()
                for suspicious in suspicious_names:
                    if suspicious.lower() in service_name.lower():
                        suspicious_services.append({
                            'service_name': service_name,
                            'reason': f'服务名包含可疑关键词: {suspicious}'
                        })
        
        if not suspicious_services:
            return "未发现可疑服务"
        
        return json.dumps(suspicious_services, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"分析服务安全性失败: {str(e)}"

@tool("CheckServiceIntegrity")
def check_service_integrity(services_data: str) -> str:
    """检查服务完整性"""
    try:
        # 检查关键系统服务是否正常运行
        critical_services = ['Winlogon', 'csrss', 'lsass', 'services', 'winlogon']
        running_services = []
        
        lines = services_data.split('\n')
        current_service = {}
        
        for line in lines:
            if 'SERVICE_NAME:' in line:
                if current_service:
                    running_services.append(current_service)
                current_service = {'name': line.split('SERVICE_NAME:')[1].strip()}
            elif 'STATE' in line and 'RUNNING' in line:
                current_service['status'] = 'RUNNING'
        
        if current_service:
            running_services.append(current_service)
        
        # 检查关键服务状态
        missing_services = []
        for critical in critical_services:
            found = False
            for service in running_services:
                if critical.lower() in service.get('name', '').lower() and service.get('status') == 'RUNNING':
                    found = True
                    break
            if not found:
                missing_services.append(critical)
        
        if missing_services:
            return f"警告: 以下关键服务未运行: {', '.join(missing_services)}"
        else:
            return "所有关键系统服务正常运行"
    except Exception as e:
        return f"检查服务完整性失败: {str(e)}"
        return f"比较进程与基线时出错: {str(e)}\n{traceback.format_exc()}"