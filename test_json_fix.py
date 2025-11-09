#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON解析错误修复
"""

import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_json_parsing():
    """测试JSON解析的各种情况"""
    
    # 模拟compare_with_baseline函数的JSON解析逻辑
    def simulate_json_parsing(process_list):
        if isinstance(process_list, str):
            try:
                current_processes = json.loads(process_list)
                return f"成功解析: {len(current_processes)} 个进程"
            except json.JSONDecodeError as e:
                return f"进程数据JSON解析失败: {str(e)}。原始数据: {process_list[:100]}..."
        else:
            return f"非字符串输入: {type(process_list)}"
    
    print("=== JSON解析测试 ===")
    
    # 测试1: 正常的JSON字符串
    test1 = '[{"name": "test.exe", "pid": 1234}]'
    print(f"测试1 (正常JSON): {simulate_json_parsing(test1)}")
    
    # 测试2: 错误消息字符串
    test2 = "获取进程详情时出错: psutil 库未安装"
    print(f"测试2 (错误消息): {simulate_json_parsing(test2)}")
    
    # 测试3: 无效的JSON格式
    test3 = '{"name": "test.exe", "pid": 1234'
    print(f"测试3 (无效JSON): {simulate_json_parsing(test3)}")
    
    # 测试4: 空字符串
    test4 = ""
    print(f"测试4 (空字符串): {simulate_json_parsing(test4)}")
    
    # 测试5: 非字符串输入
    test5 = [{"name": "test.exe", "pid": 1234}]
    print(f"测试5 (列表输入): {simulate_json_parsing(test5)}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_json_parsing()