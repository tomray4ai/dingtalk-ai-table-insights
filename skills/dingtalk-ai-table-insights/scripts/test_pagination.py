#!/usr/bin/env python3
"""
测试分页读取功能

验证大数据表的正确读取
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_tables import read_sheet_data_paginated, read_all_sheets_data

def test_pagination():
    """测试分页读取功能"""
    
    print('=' * 70)
    print('🧪 测试分页读取功能')
    print('=' * 70)
    print()
    
    # 测试用例：仪表盘需求表
    doc_id = 'LeBq413JAOyAdGBMsYZqXxGYWDOnGvpb'
    table_name = '仪表盘需求表'
    
    print(f'测试表格：{table_name}')
    print(f'文档 ID: {doc_id}')
    print()
    
    # 测试 1: 分页读取单个 Sheet
    print('测试 1: 分页读取"反馈整理表"')
    records = read_sheet_data_paginated(doc_id, 'hERWDMS', page_limit=50)
    print(f'   记录数：{len(records)} 条')
    assert len(records) == 92, f"期望 92 条，实际 {len(records)} 条"
    print(f'   ✅ 通过（92 条）')
    print()
    
    # 测试 2: 分页读取另一个 Sheet
    print('测试 2: 分页读取"汇报"')
    records = read_sheet_data_paginated(doc_id, 'dnuzvD6', page_limit=50)
    print(f'   记录数：{len(records)} 条')
    assert len(records) == 93, f"期望 93 条，实际 {len(records)} 条"
    print(f'   ✅ 通过（93 条）')
    print()
    
    # 测试 3: 读取所有 Sheet（不限制数量）
    print('测试 3: 读取所有数据表')
    all_data = read_all_sheets_data(doc_id, limit_per_sheet=9999, use_pagination=True)
    total = sum(len(d['records']) for d in all_data)
    print(f'   数据表数：{len(all_data)} 个')
    print(f'   总记录数：{total} 条')
    assert total == 185, f"期望 185 条，实际 {total} 条"
    print(f'   ✅ 通过（185 条）')
    print()
    
    # 测试 4: 验证记录内容
    print('测试 4: 验证记录内容')
    if all_data:
        first_record = all_data[0]['records'][0]
        fields = first_record.get('fields', {})
        assert '标题' in fields, "缺少'标题'字段"
        print(f'   字段示例：{list(fields.keys())[:5]}')
        print(f'   ✅ 通过（字段完整）')
    print()
    
    print('=' * 70)
    print('✅ 所有测试通过！')
    print('=' * 70)

if __name__ == '__main__':
    test_pagination()
