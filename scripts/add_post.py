#!/usr/bin/env python3
"""
自动化添加小红书帖子脚本
一键完成：爬取 → 上传 R2 → 更新前端
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
# R2 配置（自动填写）
# ============================================
R2_ACCESS_KEY_ID = "3aa9a60a838e3424ec5cbb9a605a1c47"
R2_SECRET_ACCESS_KEY = "7c567a1ed64185059c5c1e6da5ba8be79d77cdd6b48c47f0f61fc3faf3c269eb"
R2_ENDPOINT_URL = "https://97cfcf941717980caaaf12b7645f4b33.r2.cloudflarestorage.com"
R2_BUCKET_NAME = "xiaohongshu-post"
PUBLIC_URL_PREFIX = "https://pub-91c19942a97440f2b22cdc57caa6d4d8.r2.dev"


def extract_note_id(url):
    """从 URL 中提取 note_id"""
    match = re.search(r'/(?:explore|discovery/item)/([a-f0-9]+)', url)
    if match:
        return match.group(1)
    if re.match(r'^[a-f0-9]{24}$', url):
        return url
    return None


def find_latest_jsonl():
    """查找最新的 MediaCrawler 数据文件"""
    jsonl_dir = Path("MediaCrawler/data/xhs/jsonl")
    if not jsonl_dir.exists():
        return None

    content_files = list(jsonl_dir.glob("detail_contents_*.jsonl"))
    if not content_files:
        return None

    # 返回最新的文件
    return max(content_files, key=lambda p: p.stat().st_mtime)


def read_post_from_jsonl(jsonl_file, note_id):
    """从 JSONL 文件中读取指定帖子"""
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            post = json.loads(line.strip())
            if post.get('note_id') == note_id:
                return post
    return None


def download_images(image_urls, note_id, save_dir="downloads"):
    """下载图片到本地"""
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
                print(f"  下载图片 {i}/{len(image_urls)}...", end=" ")
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
    """上传图片到 R2"""
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
            print(f"  上传 {local_file.name} ✓")

        except Exception as e:
            print(f"  上传 {local_file.name} ✗ ({e})")

    return uploaded_urls


def update_posts_json(post_data, frontend_dir="frontend"):
    """更新 frontend/posts.json"""
    posts_file = Path(frontend_dir) / "posts.json"

    # 读取现有数据
    if posts_file.exists():
        with open(posts_file, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    else:
        posts = {}

    # 添加新帖子
    note_id = post_data['note_id']
    posts[note_id] = post_data

    # 保存
    with open(posts_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已更新 {posts_file}")
    print(f"   当前共有 {len(posts)} 个帖子")


def process_post(note_id_or_url):
    """处理单个帖子的完整流程"""
    print("="*60)
    print("🚀 开始处理小红书帖子")
    print("="*60)

    # 1. 提取 note_id
    note_id = extract_note_id(note_id_or_url)
    if not note_id:
        print(f"❌ 错误：无法识别的链接格式: {note_id_or_url}")
        return False

    print(f"\n📝 Note ID: {note_id}")

    # 2. 查找 MediaCrawler 数据
    print("\n🔍 步骤 1: 查找 MediaCrawler 数据...")
    jsonl_file = find_latest_jsonl()

    if not jsonl_file:
        print("❌ 错误：找不到 MediaCrawler 数据文件")
        print("\n💡 请先运行 MediaCrawler 爬取帖子：")
        print("   1. cd MediaCrawler")
        print("   2. 编辑 config/xhs_config.py，添加链接")
        print("   3. uv run main.py --platform xhs --lt qrcode --type detail")
        return False

    print(f"   找到数据文件: {jsonl_file.name}")

    # 3. 读取帖子数据
    post = read_post_from_jsonl(jsonl_file, note_id)
    if not post:
        print(f"❌ 错误：在数据文件中找不到 note_id: {note_id}")
        print("\n💡 请确保已用 MediaCrawler 爬取了这个帖子")
        return False

    print(f"   标题: {post.get('title', 'N/A')}")

    # 4. 处理图片 URL
    print("\n📥 步骤 2: 下载图片...")
    image_list_str = post.get('image_list', '')
    image_urls = [url.strip() for url in image_list_str.split(',') if url.strip()]

    if not image_urls:
        print("⚠️  警告：这个帖子没有图片")
        image_urls = []
    else:
        print(f"   找到 {len(image_urls)} 张图片")
        downloaded_files = download_images(image_urls, note_id)

        # 5. 上传到 R2
        print(f"\n☁️  步骤 3: 上传到 Cloudflare R2...")
        r2_urls = upload_to_r2(downloaded_files, note_id)

    # 6. 准备前端数据
    print("\n📝 步骤 4: 更新前端数据...")
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

    # 7. 更新 posts.json
    update_posts_json(frontend_data)

    # 8. 完成
    print("\n" + "="*60)
    print("🎉 处理完成！")
    print("="*60)
    print(f"\n📊 帖子信息：")
    print(f"   标题: {frontend_data['title']}")
    print(f"   作者: {frontend_data['nickname']}")
    print(f"   图片: {len(frontend_data['images'])} 张")
    print(f"   点赞: {frontend_data['liked_count']}")

    if frontend_data['images']:
        print(f"\n🎨 第一张图片 URL：")
        print(f"   {frontend_data['images'][0]}")

    print(f"\n💡 下一步：")
    print(f"   1. 刷新浏览器: http://localhost:8000")
    print(f"   2. 输入链接或 note_id: {note_id}")
    print(f"   3. 点击「提取内容」")

    return True


def main():
    if len(sys.argv) < 2:
        print("📖 使用方法：")
        print("   python add_post.py <小红书链接或note_id>")
        print("\n示例：")
        print("   python add_post.py 'https://www.xiaohongshu.com/explore/abc123...'")
        print("   python add_post.py 'abc123...'")
        print("\n⚠️  注意：")
        print("   请先用 MediaCrawler 爬取帖子，然后运行本脚本处理数据")
        sys.exit(1)

    note_id_or_url = sys.argv[1]
    success = process_post(note_id_or_url)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
