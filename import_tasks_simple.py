#!/usr/bin/env python3
"""
简化的任务数据导入脚本
只导入任务数据到PostgreSQL，不依赖Ollama
"""

import os
import sys
import json
import logging

# 添加backend目录到路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

from db.sql_repo import initialize_db, insert_task, insert_task_steps, get_db_session, Task, TaskStep

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_task_data():
    """导入任务数据"""
    
    print("=== 简化任务数据导入 ===")
    
    # 初始化数据库
    if not initialize_db():
        print("✗ 数据库初始化失败")
        return False
    
    print("✓ 数据库初始化成功")
    
    # 数据目录
    data_dir = os.path.join(backend_dir, "data", "initial_data")
    
    if not os.path.exists(data_dir):
        print(f"✗ 数据目录不存在: {data_dir}")
        return False
    
    print(f"数据目录: {data_dir}")
    
    # 获取所有JSON文件
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    print(f"找到 {len(json_files)} 个JSON文件")
    
    success_count = 0
    
    for json_file in json_files:
        file_path = os.path.join(data_dir, json_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # 验证必要字段
            if 'task_id' not in task_data or 'task_name' not in task_data:
                print(f"✗ 跳过无效文件: {json_file}")
                continue
            
            # 如果缺少description字段，添加默认值
            if 'description' not in task_data:
                task_data['description'] = task_data.get('task_name', '默认任务描述')
            
            # 导入任务
            if insert_task(task_data):
                # 导入步骤数据
                if 'steps' in task_data and task_data['steps']:
                    print(f"   处理 {len(task_data['steps'])} 个步骤...")
                    
                    # 为步骤添加screenshot_path
                    processed_steps = []
                    for i, step in enumerate(task_data['steps']):
                        # 确保步骤数据结构正确
                        if isinstance(step, dict):
                            processed_step = step.copy()
                            
                            # 添加图片路径
                            if 'element_id' in step and step['element_id']:
                                processed_step['screenshot_path'] = f"/images/{step['element_id']}.png"
                                print(f"     步骤 {i+1}: {step.get('step_name', '未知步骤')} -> 图片: {step['element_id']}.png")
                            else:
                                print(f"     步骤 {i+1}: {step.get('step_name', '未知步骤')} -> 无图片")
                            
                            processed_steps.append(processed_step)
                        else:
                            print(f"     ⚠ 步骤 {i+1} 数据格式错误: {step}")
                    
                    try:
                        if insert_task_steps(task_data['task_id'], processed_steps):
                            print(f"✓ 导入成功: {task_data['task_id']} (包含 {len(processed_steps)} 个步骤)")
                        else:
                            print(f"⚠ 任务导入成功但步骤导入失败: {task_data['task_id']}")
                    except Exception as e:
                        print(f"✗ 步骤导入异常: {task_data['task_id']} - {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"✓ 导入成功: {task_data['task_id']} (无步骤数据)")
                success_count += 1
            else:
                print(f"✗ 导入失败: {task_data['task_id']}")
                
        except Exception as e:
            print(f"✗ 处理文件失败 {json_file}: {e}")
    
    print(f"\n导入完成: {success_count}/{len(json_files)} 个任务")
    
    # 验证导入结果
    session = get_db_session()
    try:
        task_count = session.query(Task).count()
        print(f"数据库中任务总数: {task_count}")
        
        # 检查特定任务
        target_task = session.query(Task).filter(
            Task.task_id == "task_view_signal_processing_analysis"
        ).first()
        
        if target_task:
            print(f"✓ 找到目标任务: {target_task.task_name}")
        else:
            print("✗ 未找到目标任务")
            
    except Exception as e:
        print(f"验证失败: {e}")
    finally:
        session.close()
    
    return success_count > 0

if __name__ == "__main__":
    import_task_data()