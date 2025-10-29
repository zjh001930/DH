#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端状态检查脚本
用于诊断后端服务和模块初始化状态
支持本地和Docker环境
"""

import requests
import json
import os

def check_backend_status():
    """检查后端状态"""
    # 自动检测环境
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV'):
        base_url = "http://localhost:8000"
        print("🐳 Docker环境检测")
    else:
        base_url = "http://localhost:8000"
        print("💻 本地环境检测")
    
    print(f"🔗 使用后端地址: {base_url}")
    
    print("🔍 检查后端服务状态")
    print("=" * 40)
    
    try:
        # 1. 健康检查
        print("1. 健康检查...")
        response = requests.get(f"{base_url}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 后端服务运行正常")
            print(f"   状态: {data.get('status')}")
            print(f"   消息: {data.get('message')}")
            print(f"   模块初始化: {data.get('modules_initialized')}")
            print(f"   版本: {data.get('version')}")
            
            if not data.get('modules_initialized'):
                print("⚠️  模块未初始化，可能存在以下问题:")
                print("   - PostgreSQL数据库连接失败")
                print("   - Ollama服务未运行")
                print("   - Weaviate向量数据库未运行")
                return False
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 无法连接后端服务: {str(e)}")
        return False
    
    # 2. 测试简单API调用
    print("\n2. 测试API调用...")
    try:
        test_payload = {"user_input": "测试"}
        response = requests.post(
            f"{base_url}/assistant",
            json=test_payload,
            timeout=15
        )
        
        print(f"   API响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API调用成功")
            print(f"   响应类型: {data.get('response_type')}")
            print(f"   置信度: {data.get('confidence')}")
        elif response.status_code == 503:
            print(f"   ❌ 服务不可用 (503) - 模块初始化失败")
            try:
                error_data = response.json()
                print(f"   错误: {error_data.get('error')}")
                print(f"   详情: {error_data.get('details')}")
            except:
                pass
        else:
            print(f"   ❌ API调用失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误: {error_data.get('error')}")
            except:
                print(f"   响应内容: {response.text}")
                
    except Exception as e:
        print(f"   ❌ API调用异常: {str(e)}")
        return False
    
    return True

def check_services():
    """检查依赖服务状态"""
    print("\n🔧 检查依赖服务")
    print("=" * 40)
    
    services = [
        {"name": "Ollama", "url": "http://localhost:11434/api/tags", "desc": "大语言模型服务"},
        {"name": "Weaviate", "url": "http://localhost:8080/v1/meta", "desc": "向量数据库"}
    ]
    
    for service in services:
        print(f"检查 {service['name']} ({service['desc']})...")
        try:
            response = requests.get(service['url'], timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {service['name']} 运行正常")
            else:
                print(f"   ⚠️  {service['name']} 响应异常: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {service['name']} 连接失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 后端状态诊断工具")
    print("=" * 50)
    
    # 检查后端状态
    backend_ok = check_backend_status()
    
    # 检查依赖服务
    check_services()
    
    print("\n" + "=" * 50)
    print("📊 诊断结果")
    print("=" * 50)
    
    if backend_ok:
        print("🎉 后端服务运行正常，可以进行RAG测试")
        print("\n建议运行:")
        print("   python test_rag_effectiveness.py")
    else:
        print("⚠️  后端服务存在问题，建议:")
        print("   1. 检查Ollama是否运行: http://localhost:11434")
        print("   2. 检查Weaviate是否运行: http://localhost:8080")
        print("   3. 检查PostgreSQL数据库连接")
        print("   4. 查看后端启动日志")

if __name__ == "__main__":
    main()