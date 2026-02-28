#!/usr/bin/env python3
"""
dingtalk-ai-table-insights - OpenClaw 会话包装器

在 OpenClaw 会话中运行，使用 sessions_spawn 调用大模型进行分析。

使用方法：
    在 OpenClaw 会话中直接运行：
    python3 scripts/analyze_with_llm.py --keyword "仪表盘"
"""

import argparse
import json
import subprocess
import sys
import os
import tempfile
from datetime import datetime

# 导入主分析脚本的函数
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_tables import (
    get_accessible_tables,
    read_all_sheets_data,
    DEFAULT_LIMIT,
    MCP_CONFIG_PATH,
    run_dingtalk_command
)


def analyze_with_llm_in_session(tables_data: list, keyword: str = "") -> str:
    """
    在 OpenClaw 会话中使用大模型分析表格数据
    
    通过 sessions_spawn 调用子代理进行分析
    """
    print("🤖 使用 OpenClaw 大模型进行分析...")
    
    # 构建分析 Prompt
    system_prompt = """你是一个数据分析专家，擅长从企业数据中发现洞察和风险。

## 分析维度
1. **数据一致性检查** - 跨表格对比相同指标，发现矛盾
2. **趋势洞察** - 从多个表格中发现关联和模式
3. **风险预警** - 识别异常和高风险项（按优先级排序）
4. **行动建议** - 给出具体可执行的建议（做什么 + 谁来做 + 何时完成）

## 输出格式
- 使用 Markdown 格式
- 适当使用 emoji 增强可读性
- 字数控制在 800-1500 字
- 适合在钉钉中查看
"""
    
    # 构建数据摘要
    data_summary = []
    for table in tables_data:
        table_name = table.get("table_name", "未知表格")
        sheets = table.get("sheets", [])
        records = table.get("records", [])
        
        table_info = {
            "表格名称": table_name,
            "数据表数": len(sheets),
            "总记录数": len(records),
            "数据表详情": []
        }
        
        for sheet in sheets:
            sheet_info = {
                "数据表名称": sheet.get("sheet_name", "未知"),
                "记录数": len(sheet.get("records", []))
            }
            table_info["数据表详情"].append(sheet_info)
        
        if records:
            table_info["数据示例"] = []
            for record in records[:5]:
                fields = record.get("fields", {})
                sample = {}
                for key in ["标题", "问题", "任务", "名称", "优先级", "状态", "处理人", "创建时间"]:
                    if key in fields:
                        value = fields[key]
                        if isinstance(value, dict):
                            value = value.get("name", value.get("text", str(value)))
                        sample[key] = value
                table_info["数据示例"].append(sample)
        
        data_summary.append(table_info)
    
    user_prompt = f"""请分析以下钉钉 AI 表格数据，生成洞察分析报告。

## 分析范围
- **筛选关键词**: {keyword if keyword else "全量扫描"}
- **分析表格数**: {len(tables_data)} 个
- **总记录数**: {sum(len(t.get("records", [])) for t in tables_data)} 条

## 表格数据摘要
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

## 请生成报告，包含以下内容
1. 执行摘要（关键指标）
2. 详细数据分析（每个表格的数据表详情、示例、洞察）
3. 风险与异常识别（自动发现数据问题）
4. 行动建议（具体可执行，包含优先级和时间）

请开始生成报告：
"""
    
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    # 使用 openclaw sessions_send 发送到当前会话
    # 注意：这需要在 OpenClaw 会话环境中运行
    try:
        print("   🔄 调用 OpenClaw 大模型...")
        
        # 尝试通过 subprocess 调用 openclaw agent
        result = subprocess.run(
            ["openclaw", "agent", "--message", full_prompt[:10000], "--json"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0 and result.stdout.strip():
            output = json.loads(result.stdout.strip())
            reply = output.get("reply", "")
            if reply:
                print("   ✅ 大模型分析完成")
                return reply
        
        print(f"   ⚠️  调用失败：{result.stderr[:200] if result.stderr else '无响应'}")
    except Exception as e:
        print(f"   ⚠️  调用异常：{e}")
    
    # 降级方案：返回简单报告
    print("   ⚠️  使用简化分析...")
    return generate_simple_report(tables_data, keyword)


def generate_simple_report(tables_data: list, keyword: str = "") -> str:
    """生成简化报告（降级方案）"""
    from datetime import datetime
    
    total_tables = len(tables_data)
    total_sheets = sum(len(table.get("sheets", [{}])) for table in tables_data)
    total_records = sum(len(table.get("records", [])) for table in tables_data)
    
    report = f"""# 📊 {keyword if keyword else 'AI 表格'}洞察分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**分析工具**: dingtalk-ai-table-insights v1.3.0  
**筛选关键词**: {keyword if keyword else '全量扫描'}

---

## 📋 执行摘要

| 指标 | 数值 |
|------|------|
| **分析表格数** | {total_tables} 个 |
| **数据表总数** | {total_sheets} 个 |
| **总记录数** | **{total_records} 条** |

---

## 📊 数据概览

"""
    
    for table in tables_data:
        table_name = table.get("table_name", "未知表格")
        records = len(table.get("records", []))
        report += f"- **{table_name}**: {records} 条记录\n"
    
    report += f"\n---\n\n*报告生成：dingtalk-ai-table-insights v1.3.0*\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(description='dingtalk-ai-table-insights - OpenClaw 会话分析')
    parser.add_argument('--keyword', type=str, default='', help='表格名称关键词筛选')
    parser.add_argument('--output', type=str, default='', help='输出文件路径')
    parser.add_argument('--limit', type=int, default=DEFAULT_LIMIT, help='每个表格抽样记录数')
    
    args = parser.parse_args()
    
    if args.keyword:
        print(f"🔍 开始分析 AI 表格... (关键词：{args.keyword})")
    else:
        print(f"🔍 开始分析 AI 表格... (全量扫描)")
    
    # 1. 获取表格列表
    print("📋 获取表格列表...")
    tables = get_accessible_tables(args.keyword)
    print(f"   找到 {len(tables)} 个表格")
    
    if not tables:
        print("⚠️  未找到匹配的表格")
        return
    
    # 2. 读取表格数据
    print("📊 读取表格数据...")
    tables_data = []
    total_records = 0
    
    for i, table in enumerate(tables, 1):
        table_name = table.get("docName") or table.get("name") or "未知表格"
        doc_id = table.get("docId") or ""
        
        if not doc_id:
            continue
        
        print(f"   [{i}/{len(tables)}] 读取 {table_name}...")
        
        all_sheets_data = read_all_sheets_data(doc_id, args.limit)
        
        if all_sheets_data:
            all_records = []
            for sheet_data in all_sheets_data:
                all_records.extend(sheet_data.get("records", []))
            
            tables_data.append({
                "table_name": table_name,
                "doc_id": doc_id,
                "records": all_records,
                "sheets": all_sheets_data
            })
            total_records += len(all_records)
            print(f"      ✅ {len(all_records)} 条记录")
    
    print(f"\n📊 读取完成：{len(tables_data)} 个表格，共 {total_records} 条记录")
    
    # 3. 使用大模型分析
    print("\n🤖 分析中...")
    report = analyze_with_llm_in_session(tables_data, args.keyword)
    
    # 4. 输出报告
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n✅ 报告已保存到：{args.output}")
    else:
        print("\n" + "="*60)
        print(report)
        print("="*60)


if __name__ == "__main__":
    main()
