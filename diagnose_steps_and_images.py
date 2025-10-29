#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断任务步骤和图片状态
检查数据库中的步骤数据和对应的图片文件
"""

import os
import sys
from dotenv import load_dotenv

# 加载本地环境配置
env_local_path = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(env_local_path):
    load_dotenv(env_local_path)

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

def check_task_steps_and_images():
    """检查任务步骤和图片状态"""
    print("🔍 检查任务步骤和图片状态")
    print("=" * 60)
    
    try:
        from db.sql_repo import get_all_tasks, get_task_details
        
        # 获取所有任务
        tasks = get_all_tasks()
        print(f"✅ 数据库中共有 {len(tasks)} 个任务")
        
        # 图片目录
        images_dir = os.path.join(backend_dir, 'data', 'images')
        print(f"📁 图片目录: {images_dir}")
        print(f"📁 图片目录存在: {'✅' if os.path.exists(images_dir) else '❌'}")
        
        if os.path.exists(images_dir):
            image_files = [f for f in os.listdir(images_dir) if f.endswith('.png')]
            print(f"📷 图片文件数量: {len(image_files)}")
        else:
            image_files = []
        
        # 检查特定任务
        target_tasks = [
            "task_view_signal_processing_analysis",
            "task_realtime_signal_processing",
            "task_signal_add_spectrum_analysis"
        ]
        
        print(f"\n🎯 检查目标任务:")
        for task_id in target_tasks:
            print(f"\n--- {task_id} ---")
            
            # 检查任务是否存在
            task_exists = any(task['task_id'] == task_id for task in tasks)
            print(f"任务存在: {'✅' if task_exists else '❌'}")
            
            if task_exists:
                # 获取任务详情
                task_details = get_task_details(task_id)
                if task_details:
                    print(f"任务名称: {task_details['task_name']}")
                    print(f"任务描述: {task_details['description']}")
                    
                    steps = task_details.get('steps', [])
                    print(f"步骤数量: {len(steps)}")
                    
                    if steps:
                        print("步骤详情:")
                        for i, step in enumerate(steps):
                            step_num = step.get('step', i + 1)
                            step_name = step.get('step_name', '未知步骤')
                            element_id = step.get('element_id', '')
                            screenshot_path = step.get('screenshot_path', '')
                            
                            print(f"  {step_num}. {step_name}")
                            print(f"     元素ID: {element_id}")
                            print(f"     截图路径: {screenshot_path}")
                            
                            # 检查对应的图片文件
                            if element_id:
                                image_filename = f"{element_id}.png"
                                image_exists = image_filename in image_files
                                print(f"     图片文件: {image_filename} {'✅' if image_exists else '❌'}")
                            else:
                                print(f"     图片文件: 无元素ID")
                    else:
                        print("❌ 无步骤数据")
                else:
                    print("❌ 无法获取任务详情")
        
        # 统计信息
        print(f"\n📊 统计信息:")
        total_steps = 0
        steps_with_images = 0
        missing_images = []
        
        for task in tasks:
            task_details = get_task_details(task['task_id'])
            if task_details and 'steps' in task_details:
                steps = task_details['steps']
                total_steps += len(steps)
                
                for step in steps:
                    element_id = step.get('element_id', '')
                    if element_id:
                        image_filename = f"{element_id}.png"
                        if image_filename in image_files:
                            steps_with_images += 1
                        else:
                            missing_images.append(image_filename)
        
        print(f"总步骤数: {total_steps}")
        print(f"有图片的步骤: {steps_with_images}")
        print(f"缺失图片的步骤: {total_steps - steps_with_images}")
        
        if missing_images:
            print(f"\n❌ 缺失的图片文件 (前10个):")
            for img in missing_images[:10]:
                print(f"   - {img}")
            if len(missing_images) > 10:
                print(f"   ... 还有 {len(missing_images) - 10} 个")
        
        # 检查意图识别器
        print(f"\n🧠 检查意图识别器:")
        try:
            from workflow.intent_recognizer import IntentRecognizer
            recognizer = IntentRecognizer()
            print(f"✅ 意图识别器加载成功")
            print(f"📋 加载的任务数量: {len(recognizer.task_data)}")
            
            # 测试特定输入
            test_input = "我想添加分析方法进行信号处理"
            result = recognizer.recognize(test_input)
            print(f"\n🧪 测试输入: '{test_input}'")
            print(f"识别结果: {result['recognized_task_id']}")
            print(f"置信度: {result['confidence']:.2f}")
            
            # 检查识别到的任务是否有步骤
            task_id = result['recognized_task_id']
            if task_id and task_id in recognizer.task_data:
                task_info = recognizer.task_data[task_id]
                steps = task_info.get('steps', [])
                print(f"任务步骤数量: {len(steps)}")
                if steps:
                    print("前3个步骤:")
                    for i, step in enumerate(steps[:3]):
                        print(f"  {i+1}. {step}")
            
        except Exception as e:
            print(f"❌ 意图识别器测试失败: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🔧 任务步骤和图片诊断工具")
    print("=" * 60)
    
    check_task_steps_and_images()
    
    print("=" * 60)
    print("🎉 诊断完成")
    print("\n💡 如果发现问题，请运行以下命令修复:")
    print("   python import_tasks_simple.py  # 重新导入任务数据")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 诊断过程中出现错误: {e}")
        import traceback
        traceback.print_exc()