#!/usr/bin/env python3
"""
测试步骤导入功能
"""

import sys
import os
import json

# 添加backend目录到路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

from db.sql_repo import insert_task_steps, get_db_session, TaskStep

def test_step_import():
    """测试步骤导入"""
    
    print("=== 测试步骤导入功能 ===")
    
    # 测试数据
    task_id = "task_view_signal_processing_analysis"
    test_steps = [
        {
            "step": 1,
            "step_name": "切换到分析模式",
            "element_id": "btn_nav_analysis",
            "action": "click",
            "dialogue_copy_id": "task_step1_switch_to_analysis",
            "screenshot_path": "/images/btn_nav_analysis.png"
        },
        {
            "step": 2,
            "step_name": "点击信号处理按钮",
            "element_id": "btn_subnav_signal_processing",
            "action": "click",
            "dialogue_copy_id": "task_step2_click_signal_processing",
            "screenshot_path": "/images/btn_subnav_signal_processing.png"
        }
    ]
    
    print(f"任务ID: {task_id}")
    print(f"步骤数量: {len(test_steps)}")
    
    # 尝试导入步骤
    try:
        result = insert_task_steps(task_id, test_steps)
        print(f"导入结果: {result}")
        
        if result:
            # 验证导入结果
            session = get_db_session()
            try:
                steps = session.query(TaskStep).filter(
                    TaskStep.task_id == task_id
                ).order_by(TaskStep.step_number).all()
                
                print(f"数据库中的步骤数量: {len(steps)}")
                
                for step in steps:
                    print(f"  步骤 {step.step_number}: {step.step_name}")
                    print(f"    element_id: {step.element_id}")
                    print(f"    screenshot_path: {step.screenshot_path}")
                    print(f"    action: {step.action}")
                    
            finally:
                session.close()
        
    except Exception as e:
        print(f"导入失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_step_import()