#!/bin/bash

# ============================================
# One-click RedNote post addition script
# Usage: ./fetch_post.sh "RedNote link"
# ============================================

set -e  # Exit immediately on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_step() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_error() {
    echo -e "${RED}❌ Error: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}"
    echo "📖 Usage:"
    echo "   ./fetch_post.sh \"RedNote link\""
    echo ""
    echo "Example:"
    echo "   ./fetch_post.sh \"https://www.xiaohongshu.com/explore/abc123...\""
    echo ""
    echo "💡 This script will automatically:"
    echo "   1. Update ../MediaCrawler configuration"
    echo "   2. Run ../MediaCrawler to crawl data"
    echo "   3. Download images and upload to R2"
    echo "   4. Update frontend posts.json"
    echo -e "${NC}"
    exit 1
fi

XHS_URL="$1"

# Check ../MediaCrawler directory
if [ ! -d "../MediaCrawler" ]; then
    print_error "Cannot find ../MediaCrawler directory"
    echo "Please install ../MediaCrawler first:"
    echo "  git clone https://github.com/NanmiCoder/../MediaCrawler.git"
    exit 1
fi

# ============================================
# Step 1: Update ../MediaCrawler config
# ============================================
print_step "Step 1/4: Update ../MediaCrawler configuration"

CONFIG_FILE="../MediaCrawler/config/xhs_config.py"

# Backup original config
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    print_success "Original config file backed up"
fi

# Create temporary config
cat > "$CONFIG_FILE" << EOF
# ============================================
# RedNote crawler configuration (auto-generated)
# ============================================

# Specified post URL list
XHS_SPECIFIED_NOTE_URL_LIST = [
    "$XHS_URL"
]

# Other default configurations
CRAWLER_TYPE = "detail"
EOF

print_success "Config file updated"
echo "   Link: $XHS_URL"

# ============================================
# Step 2: Run ../MediaCrawler
# ============================================
print_step "Step 2/4: Run ../MediaCrawler to crawl data"

cd ../MediaCrawler

print_warning "Please scan QR code in the browser window to login (first time only)"
echo ""

# Run ../MediaCrawler
if command -v uv &> /dev/null; then
    uv run main.py --platform xhs --lt qrcode --type detail
else
    print_error "Cannot find uv command"
    echo "Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

cd ..

print_success "../MediaCrawler crawling complete"

# ============================================
# Step 3: Process data and upload
# ============================================
print_step "Step 3/4: Process data and upload to R2"

python3 add_post.py "$XHS_URL"

if [ $? -eq 0 ]; then
    print_success "Data processing complete"
else
    print_error "Data processing failed"
    exit 1
fi

# ============================================
# Step 4: Complete
# ============================================
print_step "🎉 All done!"

echo ""
echo -e "${GREEN}✨ New post added successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Refresh browser: http://localhost:8000"
echo "   2. Enter post link or note_id"
echo "   3. Click 'Extract Content'"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Restore config file
if [ -f "$CONFIG_FILE.backup" ]; then
    mv "$CONFIG_FILE.backup" "$CONFIG_FILE"
fi
