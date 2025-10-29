#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG测试指南和环境检测
统一的测试入口点
"""

import os
import requests
import json

def detect_environment():
    """检测运行环境"""
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV'):
        return "docker"
    else:
        return "local"

def check_backend_health(base_url="http://localhost:8000"):
    """检查后端健康状态"""
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'healthy',
                'modules_initialized': data.get('modules_initialized', False),
                'message': data.get('message', '')
            }
        else:
            return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'status': 'unreachable', 'error': str(e)}

def main():
    """主函数 - 提供测试指南"""
    print("🔧 RAG系统测试指南")
    print("=" * 50)
    
    # 检测环境
    env = detect_environment()
    print(f"🌍 当前环境: {env.upper()}")
    
    # 检查后端状态
    print("\n🔍 检查后端状态...")
    health = check_backend_health()
    
    if health['status'] == 'healthy':
        print("✅ 后端服务正常")
        if health['modules_initialized']:
            print("✅ 所有模块已初始化")
        else:
            print("⚠️  模块正在初始化中...")
    else:
        print(f"❌ 后端服务问题: {health.get('error', '未知错误')}")
    
    print("\n📋 可用的测试选项:")
    print("1. 快速RAG测试: python quick_rag_test.py")
    print("2. 完整RAG测试: python test_rag_effectiveness.py")
    print("3. 后端状态检查: python check_backend_status.py")
    
    if env == "docker":
        print("\n🐳 Docker环境提示:")
        print("- 在容器内运行: docker-compose exec backend python quick_rag_test.py")
        print("- 查看日志: docker-compose logs backend")
    else:
        print("\n💻 本地环境提示:")
        print("- 启动后端: python backend/app.py")
        print("- 或使用Docker: docker-compose up -d")
    
    print("\n🎯 推荐测试流程:")
    print("1. 先运行快速测试验证基本功能")
    print("2. 如果快速测试通过，运行完整测试")
    print("3. 如果测试失败，运行状态检查诊断问题")

if __name__ == "__main__":
    main()