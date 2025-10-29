#!/usr/bin/env python3
"""
调试任务数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from db.sql_repo import get_task_details, get_db_session, Task, TaskStep

def debug_task_data():
    """调试任务数据"""
    
    print("=== 调试任务数据 ===")
    
    # 测试数据库连接
    try:
        session = get_db_session()
        print("✓ 数据库连接成功")
        
        # 检查任务总数
        task_count = session.query(Task).count()
        print(f"数据库中任务总数: {task_count}")
        
        # 检查步骤总数
        step_count = session.query(TaskStep).count()
        print(f"数据库中步骤总数: {step_count}")
        
        # 查找特定任务
        target_task_id = "task_view_print_interface"
        print(f"\n查找任务: {target_task_id}")
        
        task = session.query(Task).filter(Task.task_id == target_task_id).first()
        if task:
            print(f"✓ 找到任务: {task.task_name}")
            
            # 获取步骤
            steps = session.query(TaskStep).filter(
                TaskStep.task_id == target_task_id
            ).order_by(TaskStep.step_number).all()
            
            print(f"步骤数量: {len(steps)}")
            for step in steps:
                print(f"  步骤 {step.step_number}: {step.step_name}")
                print(f"    element_id: {step.element_id}")
                print(f"    action: {step.action}")
        else:
            print("✗ 未找到任务")
            
            # 列出所有任务
            all_tasks = session.query(Task).limit(10).all()
            print(f"\n前10个任务:")
            for task in all_tasks:
                print(f"  - {task.task_id}: {task.task_name}")
        
        # 测试 get_task_details 函数
        print(f"\n测试 get_task_details 函数:")
        task_details = get_task_details(target_task_id)
        if task_details:
            print("✓ get_task_details 返回数据:")
            print(f"  任务名: {task_details['task_name']}")
            print(f"  步骤数: {len(task_details.get('steps', []))}")
            for step in task_details.get('steps', []):
                print(f"    步骤 {step['step']}: {step['step_name']}")
                print(f"      element_id: {step['element_id']}")
        else:
            print("✗ get_task_details 返回 None")
        
        session.close()
        
    except Exception as e:
        print(f"✗ 数据库操作失败: {e}")

if __name__ == "__main__":
    debug_task_data()