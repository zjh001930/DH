#!/usr/bin/env python3
"""
检查模型配置和 Ollama 可用模型的脚本
"""

import os
import sys
import requests
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import LLM_MODEL_NAME, EMBEDDING_MODEL_NAME, OLLAMA_API_URL

def check_current_config():
    """检查当前配置"""
    print("=== 当前配置 ===")
    print(f"LLM_MODEL_NAME: {LLM_MODEL_NAME}")
    print(f"EMBEDDING_MODEL_NAME: {EMBEDDING_MODEL_NAME}")
    print(f"OLLAMA_API_URL: {OLLAMA_API_URL}")
    print()
    
    # 检查环境变量
    print("=== 环境变量 ===")
    print(f"LLM_MODEL_NAME (env): {os.getenv('LLM_MODEL_NAME', 'Not set')}")
    print(f"EMBEDDING_MODEL_NAME (env): {os.getenv('EMBEDDING_MODEL_NAME', 'Not set')}")
    print(f"OLLAMA_API_URL (env): {os.getenv('OLLAMA_API_URL', 'Not set')}")
    print()

def check_ollama_models():
    """检查 Ollama 中可用的模型"""
    print("=== 检查 Ollama 服务 ===")
    
    # 尝试不同的 URL
    urls_to_try = [
        OLLAMA_API_URL,
        "http://localhost:11434",
        "http://ollama_service:11434",
        "http://ollama_host:11434"
    ]
    
    for url in urls_to_try:
        try:
            print(f"尝试连接: {url}")
            response = requests.get(f"{url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                print(f"✅ 连接成功: {url}")
                print("可用模型:")
                if 'models' in models:
                    for model in models['models']:
                        print(f"  - {model['name']}")
                        if 'qwen' in model['name'].lower():
                            print(f"    ✅ 找到 qwen 模型: {model['name']}")
                else:
                    print("  没有找到模型")
                print()
                return url
            else:
                print(f"❌ 连接失败: {url} (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ 连接失败: {url} (错误: {e})")
    
    print("❌ 无法连接到任何 Ollama 服务")
    return None

def test_model_usage():
    """测试模型使用"""
    print("=== 测试模型使用 ===")
    
    try:
        from llm.ollama_client import OllamaClient
        
        client = OllamaClient()
        print(f"OllamaClient 初始化成功")
        print(f"使用的 LLM 模型: {client.llm_model}")
        print(f"使用的嵌入模型: {client.embed_model}")
        
        # 测试简单的生成
        try:
            response = client.generate_response("你好")
            print(f"✅ 模型响应测试成功")
            print(f"响应: {response[:100]}...")
        except Exception as e:
            print(f"❌ 模型响应测试失败: {e}")
            
    except Exception as e:
        print(f"❌ OllamaClient 初始化失败: {e}")

def main():
    print("检查模型配置和可用性")
    print("=" * 50)
    
    check_current_config()
    ollama_url = check_ollama_models()
    
    if ollama_url:
        test_model_usage()
    
    print("\n=== 建议 ===")
    if LLM_MODEL_NAME != "qwen2.5:3b-instruct":
        print("⚠️  配置文件中的模型不是 qwen2.5:3b-instruct")
        print("   请检查环境变量是否正确设置")
    
    print("\n如果需要安装 qwen 模型，请运行:")
    print("docker exec -it ollama_host ollama pull qwen2.5:3b-instruct")

if __name__ == "__main__":
    main()