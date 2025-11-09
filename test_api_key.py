#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API密钥测试脚本
用于验证DeepSeek API密钥的有效性
"""

import requests
import json
from config.constants import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE

def test_deepseek_api():
    """
    测试DeepSeek API密钥是否有效
    """
    print("=== DeepSeek API 密钥测试 ===")
    print(f"API Base: {DEEPSEEK_API_BASE}")
    print(f"API Key: {DEEPSEEK_API_KEY[:10]}...{DEEPSEEK_API_KEY[-4:]}")
    
    # 构建请求
    url = f"{DEEPSEEK_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test message. Please respond with 'API test successful'."
            }
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        print("\n发送测试请求...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API密钥有效！")
            print(f"响应内容: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
            return True
        elif response.status_code == 401:
            print("❌ API密钥无效或已过期")
            print(f"错误信息: {response.text}")
            return False
        elif response.status_code == 402:
            print("❌ API余额不足")
            print(f"错误信息: {response.text}")
            return False
        elif response.status_code == 429:
            print("❌ API请求频率限制")
            print(f"错误信息: {response.text}")
            return False
        else:
            print(f"❌ 其他错误 (状态码: {response.status_code})")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False

def check_api_balance():
    """
    检查API余额（如果API提供此功能）
    """
    print("\n=== API余额检查 ===")
    
    # DeepSeek可能没有公开的余额查询接口，但我们可以尝试
    url = f"{DEEPSEEK_API_BASE}/usage"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"余额信息: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"无法获取余额信息 (状态码: {response.status_code})")
            print("注意：DeepSeek可能不提供公开的余额查询接口")
    except Exception as e:
        print(f"余额查询失败: {str(e)}")
        print("注意：DeepSeek可能不提供公开的余额查询接口")

def main():
    """
    主函数
    """
    print("开始API密钥测试...\n")
    
    # 测试API密钥
    api_valid = test_deepseek_api()
    
    # 检查余额
    check_api_balance()
    
    print("\n=== 测试总结 ===")
    if api_valid:
        print("✅ API密钥测试通过")
        print("建议：如果系统仍然报告余额不足，请检查：")
        print("  1. 账户余额是否充足")
        print("  2. API密钥是否有使用限制")
        print("  3. 是否达到了API调用频率限制")
    else:
        print("❌ API密钥测试失败")
        print("建议：")
        print("  1. 检查API密钥是否正确")
        print("  2. 确认账户余额是否充足")
        print("  3. 联系DeepSeek客服确认账户状态")
        print("  4. 考虑使用其他可用的API密钥")

if __name__ == "__main__":
    main()