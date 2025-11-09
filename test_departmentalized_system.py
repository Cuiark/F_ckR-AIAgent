#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部门化安全分析系统测试脚本

此脚本用于测试新的部门化架构是否正常工作，包括：
1. 部门历史文件的创建和读取
2. 新增工具函数的功能
3. GUI界面的部门化显示
4. 主工作流程的部门化执行
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_department_history():
    """测试部门历史文件"""
    print("=== 测试部门历史文件 ===")
    
    departments = ['process_department', 'log_department', 'service_department', 'network_department']
    base_path = 'data/department_history'
    
    for dept in departments:
        history_file = os.path.join(base_path, dept, 'history.json')
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✓ {dept} 历史文件读取成功")
                print(f"  - 部门: {data.get('department')}")
                print(f"  - 创建时间: {data.get('created_at')}")
                print(f"  - 分析历史数量: {len(data.get('analysis_history', []))}")
            except Exception as e:
                print(f"✗ {dept} 历史文件读取失败: {e}")
        else:
            print(f"✗ {dept} 历史文件不存在: {history_file}")
    
    print()

def test_security_tools():
    """测试安全工具函数"""
    print("=== 测试安全工具函数 ===")
    
    try:
        from tools.security_tools import (
            load_department_history,
            save_department_analysis,
            filter_processes_by_time,
            get_network_connections,
            analyze_network_security
        )
        
        # 测试历史加载
        print("测试历史加载功能...")
        history = load_department_history('process_department')
        if history:
            print(f"✓ 进程部门历史加载成功: {history.get('department')}")
        else:
            print("✗ 进程部门历史加载失败")
        
        # 测试网络连接获取
        print("测试网络连接获取...")
        connections = get_network_connections()
        if connections:
            print(f"✓ 网络连接获取成功，共 {len(connections)} 个连接")
            if connections:
                print(f"  示例连接: {connections[0]}")
        else:
            print("✗ 网络连接获取失败")
        
        # 测试网络安全分析
        print("测试网络安全分析...")
        if connections:
            analysis = analyze_network_security(connections)
            if analysis:
                print(f"✓ 网络安全分析成功")
                print(f"  分析结果长度: {len(analysis)}")
            else:
                print("✗ 网络安全分析失败")
        
        print("✓ 安全工具函数测试完成")
        
    except ImportError as e:
        print(f"✗ 导入安全工具失败: {e}")
    except Exception as e:
        print(f"✗ 安全工具测试失败: {e}")
    
    print()

def test_agents():
    """测试代理工具创建"""
    print("=== 测试代理工具创建 ===")
    
    try:
        from agents.security_agents import create_tools
        
        tools = create_tools()
        
        # 检查新增的工具
        new_tools = [
            'load_process_history',
            'save_process_analysis',
            'filter_processes_by_time',
            'get_network_connections',
            'analyze_network_security',
            'analyze_service_security'
        ]
        
        for tool_name in new_tools:
            if tool_name in tools:
                print(f"✓ 工具 {tool_name} 已成功添加")
            else:
                print(f"✗ 工具 {tool_name} 未找到")
        
        print(f"✓ 总共 {len(tools)} 个工具可用")
        
    except Exception as e:
        print(f"✗ 代理工具测试失败: {e}")
    
    print()

def test_gui_import():
    """测试GUI导入"""
    print("=== 测试GUI导入 ===")
    
    # 仪表盘功能已被移除，跳过相关测试
    print("ℹ 仪表盘功能已被移除，相关测试已跳过")
    
    # 测试其他GUI组件
    try:
        from gui.screens.task_execution_screen import TaskExecutionScreen
        print("✓ 任务执行界面导入成功")
        
        from gui.screens.settings_screen import SettingsScreen
        print("✓ 设置界面导入成功")
        
    except Exception as e:
        print(f"✗ GUI导入测试失败: {e}")
    
    print()

def test_main_workflow():
    """测试主工作流程导入"""
    print("=== 测试主工作流程 ===")
    
    try:
        # 只测试导入，不执行
        import main
        print("✓ 主程序导入成功")
        
        # 检查关键函数是否存在
        if hasattr(main, 'run_default_workflow'):
            print("✓ run_default_workflow 函数存在")
        else:
            print("✗ run_default_workflow 函数不存在")
            
        if hasattr(main, 'run_custom_workflow'):
            print("✓ run_custom_workflow 函数存在")
        else:
            print("✗ run_custom_workflow 函数不存在")
        
    except Exception as e:
        print(f"✗ 主工作流程测试失败: {e}")
    
    print()

def create_test_data():
    """创建测试数据"""
    print("=== 创建测试数据 ===")
    
    try:
        from tools.security_tools import save_department_analysis
        
        # 为每个部门创建测试分析数据
        departments = ['process_department', 'log_department', 'service_department', 'network_department']
        
        for dept in departments:
            test_result = {
                'timestamp': datetime.now().isoformat(),
                'department': dept,
                'analysis_type': 'test_analysis',
                'threats_detected': 0,
                'status': '正常',
                'details': f'这是 {dept} 的测试分析结果',
                'recommendations': ['继续监控', '保持当前安全策略']
            }
            
            success = save_department_analysis(dept, test_result)
            if success:
                print(f"✓ {dept} 测试数据创建成功")
            else:
                print(f"✗ {dept} 测试数据创建失败")
        
    except Exception as e:
        print(f"✗ 测试数据创建失败: {e}")
    
    print()

def main():
    """主测试函数"""
    print("部门化安全分析系统测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行所有测试
    test_department_history()
    test_security_tools()
    test_agents()
    test_gui_import()
    test_main_workflow()
    create_test_data()
    
    print("=" * 50)
    print("测试完成！")
    print()
    print("如果所有测试都通过，说明部门化架构已成功实现。")
    print("您现在可以运行 main.py 来启动完整的部门化安全分析系统。")

if __name__ == "__main__":
    main()