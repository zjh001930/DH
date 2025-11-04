#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库导入工具 - 将TXT文件处理为简单知识库
"""

import os
import sys
import json
import logging
import shutil
from typing import List, Dict

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_knowledge_from_txt(file_path: str) -> int:
    """
    从TXT文件导入知识到简单知识库（流式解析，避免内存溢出）
    写入 knowledge/knowledge_base.jsonl，每行一个JSON对象
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return 0

    knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
    os.makedirs(knowledge_dir, exist_ok=True)
    jsonl_path = os.path.join(knowledge_dir, 'knowledge_base.jsonl')

    logger.info(f"正在读取文件: {file_path}")
    count = 0
    current_chunk_lines = []

    # 先清空旧的 jsonl（可重复运行）
    try:
        with open(jsonl_path, 'w', encoding='utf-8') as _:
            pass
    except Exception as e:
        logger.error(f"初始化知识库文件失败: {e}")
        return 0

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_in, \
             open(jsonl_path, 'a', encoding='utf-8') as f_out:

            for line in f_in:
                # 开始新的问答块
                if line.startswith('问：'):
                    if current_chunk_lines:
                        obj = {
                            "id": f"chunk_{count+1}",
                            "content": ''.join(current_chunk_lines).strip(),
                            "source": os.path.basename(file_path),
                            "category": "general"
                        }
                        f_out.write(json.dumps(obj, ensure_ascii=False) + '\n')
                        count += 1
                        if count % 100 == 0:
                            logger.info(f"已导入 {count} 个块...")
                        current_chunk_lines = []
                    # 开始记录当前块
                    current_chunk_lines.append(line)
                else:
                    current_chunk_lines.append(line)

            # 写入最后一个块
            if current_chunk_lines:
                obj = {
                    "id": f"chunk_{count+1}",
                    "content": ''.join(current_chunk_lines).strip(),
                    "source": os.path.basename(file_path),
                    "category": "general"
                }
                f_out.write(json.dumps(obj, ensure_ascii=False) + '\n')
                count += 1

    except Exception as e:
        logger.error(f"处理知识库时出错: {e}")
        return 0

    # 可选：同步生成一个小型 JSON（前几百条），便于前端或调试
    try:
        preview_json_path = os.path.join(knowledge_dir, 'knowledge_base.json')
        preview_items = []
        with open(jsonl_path, 'r', encoding='utf-8') as f_in:
            for i, line in enumerate(f_in):
                if i >= 500:  # 取前500条作为预览
                    break
                preview_items.append(json.loads(line))
        with open(preview_json_path, 'w', encoding='utf-8') as f_out:
            json.dump(preview_items, f_out, ensure_ascii=False, indent=2)
        logger.info(f"预览JSON生成完成: {preview_json_path}（{len(preview_items)} 条）")
    except Exception as e:
        logger.warning(f"生成预览JSON失败（忽略）：{e}")

    logger.info(f"知识库导入完成，共 {count} 个块。写入: {jsonl_path}")
    return count

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python import_knowledge_base.py <知识库文件路径.txt>")
        return
    file_path = sys.argv[1]
    count = import_knowledge_from_txt(file_path)
    if count > 0:
        print(f"成功导入 {count} 个知识块")
        print("请重启后端以加载最新知识库")
    else:
        print("知识库导入失败")

if __name__ == "__main__":
    main()