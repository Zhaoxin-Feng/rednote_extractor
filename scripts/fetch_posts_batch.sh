#!/bin/bash

# ============================================
# Batch add RedNote posts script
# Usage: ./fetch_posts_batch.sh urls.txt
# urls.txt format: One RedNote link per line
# ============================================

set -e  # Exit immediately on error

# Check arguments
if [ $# -eq 0 ]; then
    echo "❌ Error: Please provide file path containing URLs"
    echo ""
    echo "Usage: ./fetch_posts_batch.sh urls.txt"
    echo ""
    echo "urls.txt format example:"
    echo "  https://www.xiaohongshu.com/discovery/item/68f3694c00000000070364a9"
    echo "  https://www.xiaohongshu.com/discovery/item/68f47b9e0000000007000b06"
    echo "  ..."
    exit 1
fi

URL_FILE="$1"

# Check if file exists
if [ ! -f "$URL_FILE" ]; then
    echo "❌ Error: File does not exist: $URL_FILE"
    exit 1
fi

# Read all URLs
echo "📖 Reading URL list..."
mapfile -t URLS < "$URL_FILE"

# Filter empty lines
FILTERED_URLS=()
for url in "${URLS[@]}"; do
    # Remove whitespace
    url=$(echo "$url" | xargs)
    # Skip empty lines and comment lines
    if [ -n "$url" ] && [[ ! "$url" =~ ^# ]]; then
        FILTERED_URLS+=("$url")
    fi
done

URL_COUNT=${#FILTERED_URLS[@]}

if [ $URL_COUNT -eq 0 ]; then
    echo "❌ Error: No valid URLs in file"
    exit 1
fi

echo "✅ Found $URL_COUNT post links"
echo ""

# Display URLs to be processed
echo "📋 Posts to be processed:"
for i in "${!FILTERED_URLS[@]}"; do
    echo "  $((i+1)). ${FILTERED_URLS[$i]}"
done
echo ""

# Config file path
CONFIG_FILE="../MediaCrawler/config/base_config.py"

# Backup original config
if [ ! -f "${CONFIG_FILE}.backup" ]; then
    echo "💾 Backing up original configuration..."
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
fi

# Generate Python list format URL config
echo "⚙️  Updating ../MediaCrawler configuration..."
URL_LIST="["
for i in "${!FILTERED_URLS[@]}"; do
    URL_LIST+="\"${FILTERED_URLS[$i]}\""
    if [ $i -lt $((URL_COUNT - 1)) ]; then
        URL_LIST+=", "
    fi
done
URL_LIST+="]"

# Update config file
cat > "$CONFIG_FILE" << EOF
# -*- coding: utf-8 -*-

# Platform configuration
PLATFORM = "xhs"
KEYWORDS = ""
LOGIN_TYPE = "qrcode"
CRAWLER_TYPE = "detail"

# RedNote specified note URL list (batch processing)
XHS_SPECIFIED_NOTE_URL_LIST = $URL_LIST

# Other configurations remain default
CRAWLER_MAX_NOTES_COUNT = 100
ENABLE_GET_COMMENTS = False
ENABLE_GET_SUB_COMMENTS = False
SAVE_DATA_OPTION = "json"
EOF

echo "✅ Configuration updated with $URL_COUNT post links"
echo ""

# Run ../MediaCrawler (only need to scan QR code once!)
echo "🚀 Starting ../MediaCrawler..."
echo "⚠️  If QR code appears, please scan to login (only once needed)"
echo ""

cd ../MediaCrawler
uv run main.py --platform xhs --lt qrcode --type detail
cd ..

echo ""
echo "✅ ../MediaCrawler crawling complete"
echo ""

# Process each post sequentially
echo "📦 Starting to process post data..."
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_URLS=()

for i in "${!FILTERED_URLS[@]}"; do
    url="${FILTERED_URLS[$i]}"
    echo "[$((i+1))/$URL_COUNT] Processing: $url"

    if python3 add_post.py "$url"; then
        echo "✅ Success"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "❌ Failed"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_URLS+=("$url")
    fi
    echo ""
done

# Restore original config
echo "🔄 Restoring original configuration..."
mv "${CONFIG_FILE}.backup" "$CONFIG_FILE"

echo ""
echo "========================================="
echo "📊 Batch processing complete"
echo "========================================="
echo "✅ Success: $SUCCESS_COUNT"
if [ $FAIL_COUNT -gt 0 ]; then
    echo "❌ Failed: $FAIL_COUNT"
    echo ""
    echo "Failed URLs:"
    for url in "${FAILED_URLS[@]}"; do
        echo "  - $url"
    done
fi
echo "========================================="
echo ""
echo "🎉 All posts added to frontend!"
echo "🌐 Visit: http://localhost:8000"
