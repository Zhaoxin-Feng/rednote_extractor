#!/bin/bash

# ============================================
# 一键添加小红书帖子脚本
# 使用方法: ./scripts/fetch_post.sh "小红书链接"
# ============================================

set -e  # 遇到错误立即退出

# 切换到项目根目录（脚本所在目录的上一级）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_step() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_error() {
    echo -e "${RED}❌ 错误: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}"
    echo "📖 使用方法："
    echo "   ./fetch_post.sh \"小红书链接\""
    echo ""
    echo "示例："
    echo "   ./fetch_post.sh \"https://www.xiaohongshu.com/explore/abc123...\""
    echo ""
    echo "💡 这个脚本会自动："
    echo "   1. 更新 MediaCrawler 配置"
    echo "   2. 运行 MediaCrawler 爬取数据"
    echo "   3. 下载图片并上传到 R2"
    echo "   4. 更新前端 posts.json"
    echo -e "${NC}"
    exit 1
fi

XHS_URL="$1"

# 检查 MediaCrawler 目录
if [ ! -d "MediaCrawler" ]; then
    print_error "找不到 MediaCrawler 目录"
    echo "请先安装 MediaCrawler："
    echo "  git clone https://github.com/NanmiCoder/MediaCrawler.git"
    exit 1
fi

# ============================================
# 步骤 1: 更新 MediaCrawler 配置
# ============================================
print_step "步骤 1/4: 更新 MediaCrawler 配置"

CONFIG_FILE="MediaCrawler/config/xhs_config.py"

# 备份原配置
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    print_success "已备份原配置文件"
fi

# 创建临时配置
cat > "$CONFIG_FILE" << EOF
# ============================================
# 小红书爬虫配置 (自动生成)
# ============================================

# 指定帖子 URL 列表
XHS_SPECIFIED_NOTE_URL_LIST = [
    "$XHS_URL"
]

# 其他默认配置
CRAWLER_TYPE = "detail"
EOF

print_success "配置文件已更新"
echo "   链接: $XHS_URL"

# ============================================
# 步骤 2: 运行 MediaCrawler
# ============================================
print_step "步骤 2/4: 运行 MediaCrawler 爬取数据"

cd MediaCrawler

print_warning "请在弹出的浏览器窗口中扫码登录（首次需要）"
echo ""

# 运行 MediaCrawler
if command -v uv &> /dev/null; then
    uv run main.py --platform xhs --lt qrcode --type detail
else
    print_error "找不到 uv 命令"
    echo "请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

cd ..

print_success "MediaCrawler 爬取完成"

# ============================================
# 步骤 3: 处理数据并上传
# ============================================
print_step "步骤 3/4: 处理数据并上传到 R2"

python3 scripts/add_post.py "$XHS_URL"

if [ $? -eq 0 ]; then
    print_success "数据处理完成"
else
    print_error "数据处理失败"
    exit 1
fi

# ============================================
# 步骤 4: 完成
# ============================================
print_step "🎉 全部完成！"

echo ""
echo -e "${GREEN}✨ 新帖子已添加成功！${NC}"
echo ""
echo "📝 下一步："
echo "   1. 刷新浏览器: http://localhost:8000"
echo "   2. 输入帖子链接或 note_id"
echo "   3. 点击「提取内容」"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 恢复配置文件
if [ -f "$CONFIG_FILE.backup" ]; then
    mv "$CONFIG_FILE.backup" "$CONFIG_FILE"
fi
