#!/usr/bin/env python3
"""
简化的 Weaviate 连接测试
"""

import requests
import json
import os

def detect_environment():
    """检测运行环境"""
    if os.path.exists('/.dockerenv'):
        return 'docker'
    else:
        return 'local'

def get_weaviate_url():
    """根据环境获取 Weaviate URL"""
    env = detect_environment()
    if env == 'docker':
        return 'http://weaviate:8080'
    else:
        return 'http://localhost:8080'

def test_weaviate_connection():
    """测试 Weaviate 连接"""
    print("🔧 Weaviate 简单连接测试")
    print("=" * 40)
    
    # 检测环境
    env = detect_environment()
    weaviate_url = get_weaviate_url()
    print(f"🌍 运行环境: {'Docker容器' if env == 'docker' else '本地宿主机'}")
    print(f"🔗 Weaviate URL: {weaviate_url}")
    print()
    
    # 测试基本连接
    try:
        print("1️⃣ 测试基本连接...")
        response = requests.get(f'{weaviate_url}/v1/.well-known/ready', timeout=5)
        if response.status_code == 200:
            print("✅ Weaviate 连接正常")
        else:
            print(f"⚠️ 连接异常，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    # 测试 Schema
    try:
        print("\n2️⃣ 检查 Schema...")
        response = requests.get(f'{weaviate_url}/v1/schema', timeout=5)
        if response.status_code == 200:
            schema = response.json()
            classes = schema.get('classes', [])
            print(f"✅ Schema 正常，包含 {len(classes)} 个类")
            if classes:
                for cls in classes:
                    print(f"   📋 类名: {cls.get('class', 'Unknown')}")
            else:
                print("   ℹ️ 暂无数据类（这是正常的，需要先导入数据）")
        else:
            print(f"⚠️ Schema 检查失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ Schema 检查失败: {e}")
    
    # 测试服务信息
    try:
        print("\n3️⃣ 获取服务信息...")
        response = requests.get(f'{weaviate_url}/v1/meta', timeout=5)
        if response.status_code == 200:
            meta = response.json()
            print(f"✅ Weaviate 版本: {meta.get('version', 'Unknown')}")
            print(f"   主机名: {meta.get('hostname', 'Unknown')}")
        else:
            print(f"⚠️ 服务信息获取失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 服务信息获取失败: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Weaviate 服务运行正常！")
    return True

if __name__ == "__main__":
    test_weaviate_connection()