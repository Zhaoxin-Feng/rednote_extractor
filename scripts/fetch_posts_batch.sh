#!/bin/bash

# ============================================
# 批量添加小红书帖子脚本
# 用法: ./scripts/fetch_posts_batch.sh urls.txt
# urls.txt 格式: 每行一个小红书链接
# ============================================

set -e  # 遇到错误立即退出

# 切换到项目根目录（脚本所在目录的上一级）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供包含 URL 的文件路径"
    echo ""
    echo "用法: ./fetch_posts_batch.sh urls.txt"
    echo ""
    echo "urls.txt 格式示例:"
    echo "  https://www.xiaohongshu.com/discovery/item/68f3694c00000000070364a9"
    echo "  https://www.xiaohongshu.com/discovery/item/68f47b9e0000000007000b06"
    echo "  ..."
    exit 1
fi

URL_FILE="$1"

# 检查文件是否存在
if [ ! -f "$URL_FILE" ]; then
    echo "❌ 错误: 文件不存在: $URL_FILE"
    exit 1
fi

# 读取所有 URL (兼容 macOS bash 3.x)
echo "📖 读取 URL 列表..."
FILTERED_URLS=()
while IFS= read -r url || [ -n "$url" ]; do
    # 去除空白字符
    url=$(echo "$url" | xargs)
    # 跳过空行和注释行
    if [ -n "$url" ] && [[ ! "$url" =~ ^# ]]; then
        FILTERED_URLS+=("$url")
    fi
done < "$URL_FILE"

URL_COUNT=${#FILTERED_URLS[@]}

if [ $URL_COUNT -eq 0 ]; then
    echo "❌ 错误: 文件中没有有效的 URL"
    exit 1
fi

echo "✅ 找到 $URL_COUNT 个帖子链接"
echo ""

# 显示将要处理的 URL
echo "📋 将要处理的帖子:"
for i in "${!FILTERED_URLS[@]}"; do
    echo "  $((i+1)). ${FILTERED_URLS[$i]}"
done
echo ""

# 配置文件路径 (修改为 xhs_config.py，避免覆盖整个 base_config.py)
CONFIG_FILE="MediaCrawler/config/xhs_config.py"

# 备份原配置
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    echo "💾 已备份原配置文件"
fi

# 生成 Python 列表格式的 URL 配置
echo "⚙️  更新 MediaCrawler 配置..."
URL_LIST="["
for i in "${!FILTERED_URLS[@]}"; do
    URL_LIST+="\"${FILTERED_URLS[$i]}\""
    if [ $i -lt $((URL_COUNT - 1)) ]; then
        URL_LIST+=", "
    fi
done
URL_LIST+="]"

# 更新配置文件 (只修改 xhs_config.py)
cat > "$CONFIG_FILE" << EOF
# ============================================
# 小红书爬虫配置 (批量处理 - 自动生成)
# ============================================

# 指定帖子 URL 列表
XHS_SPECIFIED_NOTE_URL_LIST = $URL_LIST

# 其他默认配置
CRAWLER_TYPE = "detail"
EOF

echo "✅ 配置已更新，包含 $URL_COUNT 个帖子链接"
echo ""

# 运行 MediaCrawler（只需要扫码一次！）
echo "🚀 启动 MediaCrawler..."
echo "⚠️  如果弹出二维码，请扫码登录（只需要扫一次）"
echo ""

cd MediaCrawler
uv run main.py --platform xhs --lt qrcode --type detail
cd ..

echo ""
echo "✅ MediaCrawler 爬取完成"
echo ""

# 依次处理每个帖子
echo "📦 开始处理帖子数据..."
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_URLS=()

for i in "${!FILTERED_URLS[@]}"; do
    url="${FILTERED_URLS[$i]}"
    echo "[$((i+1))/$URL_COUNT] 处理: $url"

    if python3 scripts/add_post.py "$url"; then
        echo "✅ 成功"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "❌ 失败"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_URLS+=("$url")
    fi
    echo ""
done

# 恢复原配置
echo "🔄 恢复原始配置..."
if [ -f "$CONFIG_FILE.backup" ]; then
    mv "$CONFIG_FILE.backup" "$CONFIG_FILE"
fi

echo ""
echo "========================================="
echo "📊 批量处理完成"
echo "========================================="
echo "✅ 成功: $SUCCESS_COUNT"
if [ $FAIL_COUNT -gt 0 ]; then
    echo "❌ 失败: $FAIL_COUNT"
    echo ""
    echo "失败的 URL:"
    for url in "${FAILED_URLS[@]}"; do
        echo "  - $url"
    done
fi
echo "========================================="
echo ""
echo "🎉 所有帖子已添加到前端！"
echo "🌐 访问: http://localhost:8000"
