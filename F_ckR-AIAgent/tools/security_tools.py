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