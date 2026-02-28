#!/bin/bash
# 🔒 发布前安全检查脚本
# 用法：./pre-publish-check.sh

echo "🔒 发布前安全检查..."
echo

FAILED=0

# 1. 检查硬编码 URL（排除占位符）
echo "1. 检查硬编码 MCP URL..."
if grep -r "mcp-gw.dingtalk.com" scripts/ references/ 2>/dev/null | grep -v "YOUR_ID" | grep -v "YOUR_KEY"; then
    echo "❌ 发现硬编码 URL（非占位符）"
    FAILED=1
else
    echo "✅ 通过（仅发现占位符）"
fi
echo

# 2. 检查 Server ID（64 位十六进制）
echo "2. 检查 Server ID..."
if grep -rE "[a-f0-9]{64}" scripts/ references/ 2>/dev/null | grep -v "YOUR_ID"; then
    echo "❌ 发现可能的 Server ID"
    FAILED=1
else
    echo "✅ 通过"
fi
echo

# 3. 检查 Access Key（32 位十六进制）
echo "3. 检查 Access Key..."
if grep -rE "key=[a-f0-9]{32}" scripts/ references/ 2>/dev/null | grep -v "YOUR_KEY"; then
    echo "❌ 发现 Access Key"
    FAILED=1
else
    echo "✅ 通过"
fi
echo

# 4. 检查 .gitignore
echo "4. 检查 .gitignore 配置..."
if grep -q "config/mcporter.json" .gitignore 2>/dev/null; then
    echo "✅ 配置文件已添加到 .gitignore"
else
    echo "⚠️ 配置文件未添加到 .gitignore"
    FAILED=1
fi
echo

# 5. 检查真实配置文件
echo "5. 检查真实配置文件..."
if [ -f "../../config/mcporter.json" ]; then
    if grep -q "YOUR_ID" ../../config/mcporter.json 2>/dev/null; then
        echo "✅ 配置文件使用占位符"
    else
        echo "⚠️ 配置文件包含真实 URL（请确认已添加到 .gitignore）"
    fi
else
    echo "✅ 配置文件不存在（正常）"
fi
echo

# 6. 检查输出文件
echo "6. 检查输出文件..."
if [ -d "reports" ] && [ "$(ls -A reports/*.md 2>/dev/null)" ]; then
    echo "⚠️ reports/ 目录包含生成的报告（不应提交）"
else
    echo "✅ reports/ 目录干净"
fi
echo

# 总结
echo "================================"
if [ $FAILED -eq 0 ]; then
    echo "✅ 安全检查通过"
    exit 0
else
    echo "❌ 发现安全问题，请修复后再发布"
    exit 1
fi
