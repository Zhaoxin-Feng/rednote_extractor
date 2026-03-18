#!/usr/bin/env python3
"""
Automated RedNote post addition script
One-click completion: Crawl → Upload to R2 → Update frontend
"""

import sys
import json
import os
import re
from pathlib import Path
import boto3
from botocore.config import Config
import httpx
from datetime import datetime


# ============================================
# R2 Configuration (Auto-filled)
# ============================================
R2_ACCESS_KEY_ID = "3aa9a60a838e3424ec5cbb9a605a1c47"
R2_SECRET_ACCESS_KEY = "7c567a1ed64185059c5c1e6da5ba8be79d77cdd6b48c47f0f61fc3faf3c269eb"
R2_ENDPOINT_URL = "https://97cfcf941717980caaaf12b7645f4b33.r2.cloudflarestorage.com"
R2_BUCKET_NAME = "xiaohongshu-post"
PUBLIC_URL_PREFIX = "https://pub-91c19942a97440f2b22cdc57caa6d4d8.r2.dev"


def extract_note_id(url):
    """Extract note_id from URL"""
    match = re.search(r'/(?:explore|discovery/item)/([a-f0-9]+)', url)
    if match:
        return match.group(1)
    if re.match(r'^[a-f0-9]{24}$', url):
        return url
    return None


def find_latest_jsonl():
    """Find the latest MediaCrawler data file"""
    jsonl_dir = Path("../MediaCrawler/data/xhs/jsonl")
    if not jsonl_dir.exists():
        return None

    content_files = list(jsonl_dir.glob("detail_contents_*.jsonl"))
    if not content_files:
        return None

    # Return the latest file
    return max(content_files, key=lambda p: p.stat().st_mtime)


def read_post_from_jsonl(jsonl_file, note_id):
    """Read specified post from JSONL file"""
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            post = json.loads(line.strip())
            if post.get('note_id') == note_id:
                return post
    return None


def download_images(image_urls, note_id, save_dir="downloads"):
    """Download images to local"""
    note_dir = Path(save_dir) / note_id
    note_dir.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.xiaohongshu.com/"
    }

    downloaded_files = []

    with httpx.Client(headers=headers, timeout=30.0, follow_redirects=True) as client:
        for i, img_url in enumerate(image_urls, 1):
            try:
                print(f"  Downloading image {i}/{len(image_urls)}...", end=" ")
                resp = client.get(img_url)
                resp.raise_for_status()

                file_path = note_dir / f"{note_id}_{i}.jpg"
                with open(file_path, "wb") as f:
                    f.write(resp.content)

                downloaded_files.append(file_path)
                print("✓")

            except Exception as e:
                print(f"✗ ({e})")

    return downloaded_files


def upload_to_r2(local_files, note_id):
    """Upload images to R2"""
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

    uploaded_urls = []

    for local_file in local_files:
        r2_key = f"{note_id}/{local_file.name}"

        try:
            with open(local_file, 'rb') as f:
                s3_client.upload_fileobj(
                    f,
                    R2_BUCKET_NAME,
                    r2_key,
                    ExtraArgs={
                        'ContentType': 'image/jpeg',
                        'CacheControl': 'public, max-age=31536000'
                    }
                )

            public_url = f"{PUBLIC_URL_PREFIX}/{r2_key}"
            uploaded_urls.append(public_url)
            print(f"  Upload {local_file.name} ✓")

        except Exception as e:
            print(f"  Upload {local_file.name} ✗ ({e})")

    return uploaded_urls


def update_posts_json(post_data, frontend_dir="../frontend"):
    """Update frontend/posts.json"""
    posts_file = Path(frontend_dir) / "posts.json"

    # Read existing data
    if posts_file.exists():
        with open(posts_file, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    else:
        posts = {}

    # Add new post
    note_id = post_data['note_id']
    posts[note_id] = post_data

    # Save
    with open(posts_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Updated {posts_file}")
    print(f"   Currently {len(posts)} posts in total")


def process_post(note_id_or_url):
    """Complete workflow for processing a single post"""
    print("="*60)
    print("🚀 Starting to process RedNote post")
    print("="*60)

    # 1. Extract note_id
    note_id = extract_note_id(note_id_or_url)
    if not note_id:
        print(f"❌ Error: Unrecognizable link format: {note_id_or_url}")
        return False

    print(f"\n📝 Note ID: {note_id}")

    # 2. Find MediaCrawler data
    print("\n🔍 Step 1: Finding MediaCrawler data...")
    jsonl_file = find_latest_jsonl()

    if not jsonl_file:
        print("❌ Error: Cannot find MediaCrawler data file")
        print("\n💡 Please run MediaCrawler to crawl the post first:")
        print("   1. cd MediaCrawler")
        print("   2. Edit config/xhs_config.py, add the link")
        print("   3. uv run main.py --platform xhs --lt qrcode --type detail")
        return False

    print(f"   Found data file: {jsonl_file.name}")

    # 3. Read post data
    post = read_post_from_jsonl(jsonl_file, note_id)
    if not post:
        print(f"❌ Error: Cannot find note_id in data file: {note_id}")
        print("\n💡 Please make sure you've crawled this post with MediaCrawler")
        return False

    print(f"   Title: {post.get('title', 'N/A')}")

    # 4. Process image URLs
    print("\n📥 Step 2: Downloading images...")
    image_list_str = post.get('image_list', '')
    image_urls = [url.strip() for url in image_list_str.split(',') if url.strip()]

    if not image_urls:
        print("⚠️  Warning: This post has no images")
        image_urls = []
    else:
        print(f"   Found {len(image_urls)} images")
        downloaded_files = download_images(image_urls, note_id)

        # 5. Upload to R2
        print(f"\n☁️  Step 3: Uploading to Cloudflare R2...")
        r2_urls = upload_to_r2(downloaded_files, note_id)

    # 6. Prepare frontend data
    print("\n📝 Step 4: Updating frontend data...")
    frontend_data = {
        'note_id': note_id,
        'title': post.get('title', ''),
        'desc': post.get('desc', ''),
        'nickname': post.get('nickname', ''),
        'avatar': post.get('avatar', ''),
        'time': datetime.fromtimestamp(post.get('time', 0) / 1000).strftime('%Y-%m-%d') if post.get('time') else '',
        'liked_count': str(post.get('liked_count', '0')),
        'collected_count': str(post.get('collected_count', '0')),
        'comment_count': str(post.get('comment_count', '0')),
        'share_count': str(post.get('share_count', '0')),
        'images': r2_urls if image_urls else []
    }

    # 7. Update posts.json
    update_posts_json(frontend_data)

    # 8. Complete
    print("\n" + "="*60)
    print("🎉 Processing complete!")
    print("="*60)
    print(f"\n📊 Post information:")
    print(f"   Title: {frontend_data['title']}")
    print(f"   Author: {frontend_data['nickname']}")
    print(f"   Images: {len(frontend_data['images'])} images")
    print(f"   Likes: {frontend_data['liked_count']}")

    if frontend_data['images']:
        print(f"\n🎨 First image URL:")
        print(f"   {frontend_data['images'][0]}")

    print(f"\n💡 Next steps:")
    print(f"   1. Refresh browser: http://localhost:8000")
    print(f"   2. Enter link or note_id: {note_id}")
    print(f"   3. Click 'Extract Content'")

    return True


def main():
    if len(sys.argv) < 2:
        print("📖 Usage:")
        print("   python add_post.py <RedNote link or note_id>")
        print("\nExamples:")
        print("   python add_post.py 'https://www.xiaohongshu.com/explore/abc123...'")
        print("   python add_post.py 'abc123...'")
        print("\n⚠️  Note:")
        print("   Please crawl the post with MediaCrawler first, then run this script to process data")
        sys.exit(1)

    note_id_or_url = sys.argv[1]
    success = process_post(note_id_or_url)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
