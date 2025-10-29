#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama连接诊断脚本
"""

import os
import sys
import requests
import json
from pathlib import Path

# 设置环境变量使用本地配置
os.environ['OLLAMA_API_URL'] = 'http://localhost:11434'
os.environ['LLM_MODEL_NAME'] = 'qwen2.5:3b-instruct'
os.environ['EMBEDDING_MODEL_NAME'] = 'bge-m3'

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_ollama_connection():
    """检查Ollama连接"""
    print("🔍 诊断Ollama连接问题")
    print("=" * 50)
    
    # 测试不同的URL
    urls_to_test = [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://ollama_service:11434",
        "http://ollama_host:11434"
    ]
    
    for url in urls_to_test:
        print(f"\n🔗 测试连接: {url}")
        try:
            # 测试基本连接
            response = requests.get(f"{url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                print(f"✅ 连接成功!")
                print(f"📋 可用模型:")
                if 'models' in models and models['models']:
                    for model in models['models']:
                        name = model.get('name', 'Unknown')
                        print(f"   - {name}")
                        if 'qwen' in name.lower():
                            print(f"     ✅ 找到qwen模型!")
                else:
                    print("   ⚠️  没有找到任何模型")
                return url
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 连接错误: 无法连接到服务")
        except requests.exceptions.Timeout as e:
            print(f"❌ 超时错误: 连接超时")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
    
    print(f"\n❌ 无法连接到任何Ollama服务")
    return None

def check_docker_containers():
    """检查Docker容器状态"""
    print(f"\n🐳 检查Docker容器状态")
    print("=" * 30)
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps', '--filter', 'name=ollama'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout
            if 'ollama' in output.lower():
                print("✅ 找到Ollama容器:")
                lines = output.strip().split('\n')
                for line in lines[1:]:  # 跳过标题行
                    if 'ollama' in line.lower():
                        print(f"   {line}")
            else:
                print("❌ 没有找到运行中的Ollama容器")
        else:
            print(f"❌ Docker命令执行失败: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("❌ Docker命令执行超时")
    except FileNotFoundError:
        print("❌ 未找到Docker命令，请确保Docker已安装")
    except Exception as e:
        print(f"❌ 检查Docker容器时出错: {e}")

def test_ollama_client():
    """测试OllamaClient"""
    print(f"\n🧪 测试OllamaClient")
    print("=" * 30)
    
    try:
        from llm.ollama_client import OllamaClient
        
        client = OllamaClient()
        print(f"✅ OllamaClient初始化成功")
        print(f"📍 API URL: {client.api_url}")
        print(f"🤖 LLM模型: {client.llm_model}")
        print(f"🔤 嵌入模型: {client.embed_model}")
        
        # 测试embedding
        print(f"\n🔤 测试embedding功能...")
        try:
            embedding = client.get_embedding("测试文本")
            print(f"✅ Embedding成功，向量维度: {len(embedding)}")
        except Exception as e:
            print(f"❌ Embedding失败: {e}")
        
        # 测试生成
        print(f"\n💬 测试生成功能...")
        try:
            response = client.generate_response("你好，请简单回答")
            print(f"✅ 生成成功")
            print(f"📝 响应: {response[:100]}...")
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            
    except Exception as e:
        print(f"❌ OllamaClient初始化失败: {e}")

def provide_solutions():
    """提供解决方案"""
    print(f"\n💡 解决方案建议")
    print("=" * 50)
    
    print("1. 🔧 确保Ollama容器正在运行:")
    print("   docker-compose up -d ollama_service")
    print()
    
    print("2. 📥 确保qwen模型已下载:")
    print("   docker exec -it ollama_host ollama pull qwen2.5:3b-instruct")
    print("   docker exec -it ollama_host ollama pull bge-m3")
    print()
    
    print("3. 🔍 检查容器日志:")
    print("   docker logs ollama_host")
    print()
    
    print("4. 🌐 测试端口连接:")
    print("   curl http://localhost:11434/api/tags")
    print()
    
    print("5. 🔄 重启Ollama服务:")
    print("   docker-compose restart ollama_service")

def main():
    """主函数"""
    print("🚀 Ollama连接诊断工具")
    print("=" * 60)
    
    # 检查Docker容器
    check_docker_containers()
    
    # 检查Ollama连接
    working_url = check_ollama_connection()
    
    if working_url:
        # 如果连接成功，测试OllamaClient
        test_ollama_client()
    else:
        # 如果连接失败，提供解决方案
        provide_solutions()
    
    print(f"\n" + "=" * 60)
    print("🏁 诊断完成")

if __name__ == "__main__":
    main()