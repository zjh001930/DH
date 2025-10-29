#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG有效性验证测试脚本
用于验证RAG系统是否真正从知识库检索信息，而不是依赖大模型自身知识
支持本地和Docker环境
"""

import requests
import json
import time
import os
from typing import List, Dict, Any

class RAGEffectivenessTest:
    def __init__(self, base_url: str = None):
        # 自动检测运行环境
        if base_url is None:
            # 检查是否在Docker容器内
            if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV'):
                self.base_url = "http://localhost:8000"  # Docker内部
                print("🐳 检测到Docker环境")
            else:
                self.base_url = "http://localhost:8000"  # 本地环境
                print("💻 检测到本地环境")
        else:
            self.base_url = base_url
        
        self.test_results = []
        print(f"🔗 使用后端地址: {self.base_url}")
        
    def test_specific_knowledge_questions(self) -> List[Dict[str, Any]]:
        """
        测试特定知识问题 - 这些问题的答案只能从RAG知识库中获得
        """
        # 从知识库中提取的特定问题，大模型不太可能知道这些具体信息
        specific_questions = [
            {
                "question": "东华测试软件安装对电脑配置有什么要求？",
                "expected_keywords": ["I5处理器", "16G内存", "高配置"],
                "category": "软件配置要求"
            },
            {
                "question": "应变片最常用的桥路方式是哪种？",
                "expected_keywords": ["1/4桥", "方式一", "方便简单便捷"],
                "category": "应变片技术"
            },
            {
                "question": "东华测试软件的采样频率应该设置多大？",
                "expected_keywords": ["香农定律", "2.56倍", "10-20倍", "分析频率"],
                "category": "采样频率设置"
            },
            {
                "question": "东华测试软件的抗混滤波是什么？",
                "expected_keywords": ["低通滤波器", "混叠", "默认打开"],
                "category": "滤波器设置"
            },
            {
                "question": "东华测试软件信号触发的负延迟是什么意思？",
                "expected_keywords": ["触发量级前", "200个点", "完整", "触发信号"],
                "category": "信号触发"
            },
            {
                "question": "为什么谱线数加大后需要更久才刷新FFT？",
                "expected_keywords": ["谱线数", "傅里叶", "数据量", "采样率"],
                "category": "FFT分析"
            }
        ]
        
        print("🔍 开始测试特定知识问题...")
        results = []
        
        for i, test_case in enumerate(specific_questions, 1):
            print(f"\n📝 测试 {i}/{len(specific_questions)}: {test_case['category']}")
            print(f"问题: {test_case['question']}")
            
            try:
                response = self._send_question(test_case['question'])
                result = self._analyze_response(test_case, response)
                results.append(result)
                
                # 打印结果
                status = "✅ 通过" if result['rag_effective'] else "❌ 失败"
                print(f"结果: {status}")
                print(f"响应类型: {result['response_type']}")
                print(f"置信度: {result['confidence']}")
                print(f"关键词匹配: {result['keyword_matches']}/{len(test_case['expected_keywords'])}")
                if result['sources_found']:
                    print(f"检索到知识源: ✅")
                else:
                    print(f"检索到知识源: ❌")
                    
            except Exception as e:
                print(f"❌ 测试失败: {str(e)}")
                results.append({
                    'question': test_case['question'],
                    'category': test_case['category'],
                    'error': str(e),
                    'rag_effective': False
                })
                
            time.sleep(1)  # 避免请求过快
            
        return results
    
    def test_general_vs_specific_knowledge(self) -> Dict[str, Any]:
        """
        对比测试：通用知识 vs 特定知识
        通用知识问题应该被识别为任务指导，特定知识问题应该走RAG
        """
        print("\n🔄 开始对比测试...")
        
        # 通用问题（应该被识别为任务指导）
        general_question = "如何安装软件？"
        
        # 特定问题（应该走RAG）
        specific_question = "东华测试软件安装对电脑配置有什么要求？"
        
        try:
            general_response = self._send_question(general_question)
            specific_response = self._send_question(specific_question)
            
            result = {
                'general_question': {
                    'question': general_question,
                    'response_type': general_response.get('response_type'),
                    'confidence': general_response.get('confidence'),
                    'is_task_guidance': general_response.get('response_type') == 'task_guidance'
                },
                'specific_question': {
                    'question': specific_question,
                    'response_type': specific_response.get('response_type'),
                    'confidence': specific_response.get('confidence'),
                    'is_rag_response': specific_response.get('response_type') == 'open_qa',
                    'has_sources': bool(specific_response.get('data', {}).get('sources'))
                }
            }
            
            print(f"通用问题 '{general_question}':")
            print(f"  响应类型: {result['general_question']['response_type']}")
            print(f"  置信度: {result['general_question']['confidence']}")
            
            print(f"特定问题 '{specific_question}':")
            print(f"  响应类型: {result['specific_question']['response_type']}")
            print(f"  置信度: {result['specific_question']['confidence']}")
            print(f"  有知识源: {result['specific_question']['has_sources']}")
            
            return result
            
        except Exception as e:
            print(f"❌ 对比测试失败: {str(e)}")
            return {'error': str(e)}
    
    def test_knowledge_base_dependency(self) -> Dict[str, Any]:
        """
        测试知识库依赖性 - 问一些知识库中没有的问题
        """
        print("\n🚫 测试知识库外问题...")
        
        # 这些问题不在知识库中，应该返回通用回答或无法回答
        out_of_scope_questions = [
            "东华测试软件的价格是多少？",
            "东华公司的历史是什么？",
            "如何做红烧肉？",
            "今天天气怎么样？"
        ]
        
        results = []
        for question in out_of_scope_questions:
            try:
                response = self._send_question(question)
                result = {
                    'question': question,
                    'response_type': response.get('response_type'),
                    'confidence': response.get('confidence'),
                    'answer': response.get('data', {}).get('answer', ''),
                    'sources': response.get('data', {}).get('sources', [])
                }
                results.append(result)
                
                print(f"问题: {question}")
                print(f"  响应类型: {result['response_type']}")
                print(f"  有具体答案: {'是' if result['answer'] else '否'}")
                print(f"  知识源数量: {len(result['sources'])}")
                
            except Exception as e:
                print(f"❌ 问题 '{question}' 测试失败: {str(e)}")
                
        return results
    
    def _send_question(self, question: str) -> Dict[str, Any]:
        """发送问题到后端API"""
        url = f"{self.base_url}/assistant"
        payload = {"user_input": question}
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def _analyze_response(self, test_case: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """分析响应结果"""
        data = response.get('data', {})
        answer = data.get('answer', '').lower()
        sources = data.get('sources', [])
        
        # 检查关键词匹配
        keyword_matches = 0
        for keyword in test_case['expected_keywords']:
            if keyword.lower() in answer:
                keyword_matches += 1
        
        # 判断RAG是否有效
        rag_effective = (
            response.get('response_type') == 'open_qa' and  # 是问答类型
            response.get('confidence', 1.0) < 0.75 and      # 置信度低（走RAG）
            keyword_matches > 0 and                          # 包含预期关键词
            len(sources) > 0 and                            # 有知识源
            not any('mock' in str(source).lower() for source in sources)  # 不是模拟数据
        )
        
        return {
            'question': test_case['question'],
            'category': test_case['category'],
            'response_type': response.get('response_type'),
            'confidence': response.get('confidence'),
            'keyword_matches': keyword_matches,
            'total_keywords': len(test_case['expected_keywords']),
            'sources_found': len(sources) > 0,
            'sources_count': len(sources),
            'answer_length': len(answer),
            'rag_effective': rag_effective,
            'full_response': response
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行综合测试"""
        print("🚀 开始RAG有效性综合测试")
        print("=" * 60)
        
        # 1. 特定知识问题测试
        specific_tests = self.test_specific_knowledge_questions()
        
        # 2. 对比测试
        comparison_test = self.test_general_vs_specific_knowledge()
        
        # 3. 知识库外问题测试
        out_of_scope_tests = self.test_knowledge_base_dependency()
        
        # 统计结果
        effective_count = sum(1 for test in specific_tests if test.get('rag_effective', False))
        total_specific_tests = len(specific_tests)
        
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        
        print(f"特定知识问题测试: {effective_count}/{total_specific_tests} 通过")
        print(f"RAG有效率: {effective_count/total_specific_tests*100:.1f}%")
        
        if comparison_test.get('general_question', {}).get('is_task_guidance') and \
           comparison_test.get('specific_question', {}).get('is_rag_response'):
            print("对比测试: ✅ 通过 (正确区分通用问题和特定问题)")
        else:
            print("对比测试: ❌ 失败 (未能正确区分问题类型)")
        
        # 判断整体RAG有效性
        overall_effective = (
            effective_count >= total_specific_tests * 0.7 and  # 70%以上特定问题通过
            comparison_test.get('specific_question', {}).get('is_rag_response', False)
        )
        
        if overall_effective:
            print("\n🎉 结论: RAG系统运行有效！")
            print("✅ 能够从知识库检索相关信息")
            print("✅ 能够正确回答特定领域问题")
            print("✅ 能够区分通用问题和特定问题")
        else:
            print("\n⚠️  结论: RAG系统可能存在问题！")
            print("❌ 建议检查:")
            print("   - Weaviate向量数据库连接")
            print("   - 知识库数据是否正确导入")
            print("   - Ollama嵌入模型是否正常")
            print("   - 检索阈值设置是否合理")
        
        return {
            'specific_tests': specific_tests,
            'comparison_test': comparison_test,
            'out_of_scope_tests': out_of_scope_tests,
            'summary': {
                'effective_count': effective_count,
                'total_tests': total_specific_tests,
                'effectiveness_rate': effective_count/total_specific_tests,
                'overall_effective': overall_effective
            }
        }

def main():
    """主函数"""
    print("🔧 RAG有效性验证测试")
    print("此测试将验证RAG系统是否真正从知识库检索信息")
    print("而不是依赖大模型自身知识回答问题\n")
    
    # 创建测试实例（自动检测环境）
    tester = RAGEffectivenessTest()
    
    # 检查后端服务
    print("🔍 检查后端服务状态...")
    try:
        response = requests.get(f"{tester.base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 后端服务连接正常")
            if not data.get('modules_initialized', False):
                print("⚠️  警告: 后端模块未完全初始化，测试可能失败")
                print("   请等待几秒钟让服务完全启动...")
                time.sleep(5)
        else:
            print(f"❌ 后端服务响应异常: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接后端服务: {str(e)}")
        if os.path.exists('/.dockerenv'):
            print("💡 Docker环境提示:")
            print("   请确保在Docker容器内运行此脚本")
            print("   或使用: docker-compose exec backend python test_rag_effectiveness.py")
        else:
            print("💡 本地环境提示:")
            print("   请确保后端服务正在运行")
            print("   启动命令: python backend/app.py")
            print("   或使用Docker: docker-compose up -d")
        return
    
    # 运行测试
    print("\n🚀 开始运行RAG有效性测试...")
    results = tester.run_comprehensive_test()
    
    # 保存详细结果
    try:
        with open('rag_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细测试结果已保存到: rag_test_results.json")
    except Exception as e:
        print(f"⚠️  无法保存结果文件: {str(e)}")

if __name__ == "__main__":
    main()