"""
小红书帖子爬取工具
从分享链接获取帖子标题、内容和图片
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import httpx
from urllib.parse import urlparse, parse_qs


class XHSPostCrawler:
    """小红书帖子爬取器"""

    def __init__(self, save_dir: str = "downloads"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/"
        }

    def extract_note_id(self, share_url: str) -> Optional[str]:
        """
        从分享链接中提取 note_id
        支持格式:
        - https://www.xiaohongshu.com/explore/65f...
        - https://xhslink.com/xxx
        - 直接的 note_id
        """
        # 如果是完整URL
        if share_url.startswith('http'):
            # 匹配 /explore/ 后面的ID
            match = re.search(r'/explore/([a-f0-9]+)', share_url)
            if match:
                return match.group(1)

            # 匹配 /discovery/item/ 后面的ID
            match = re.search(r'/discovery/item/([a-f0-9]+)', share_url)
            if match:
                return match.group(1)

        # 如果已经是note_id格式
        if re.match(r'^[a-f0-9]{24}$', share_url):
            return share_url

        return None

    def fetch_post_info(self, share_url: str) -> Dict:
        """
        获取帖子信息

        注意: 此方法使用简单的HTTP请求，可能受到小红书反爬限制
        建议使用 MediaCrawler 配合浏览器自动化获取更稳定的结果
        """
        note_id = self.extract_note_id(share_url)
        if not note_id:
            raise ValueError(f"无法从URL中提取note_id: {share_url}")

        print(f"提取到 note_id: {note_id}")

        # 这里返回提示信息，因为直接HTTP请求会被反爬
        return {
            "note_id": note_id,
            "url": share_url,
            "message": "建议使用 MediaCrawler 工具获取完整数据",
            "instruction": "请参考 fetch_with_mediacrawler() 方法"
        }

    def download_images(self, image_urls: List[str], note_id: str) -> List[str]:
        """下载图片到本地"""
        downloaded_files = []

        note_dir = self.save_dir / note_id
        note_dir.mkdir(exist_ok=True)

        with httpx.Client(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            for i, img_url in enumerate(image_urls):
                try:
                    print(f"正在下载第 {i+1}/{len(image_urls)} 张图片...")
                    resp = client.get(img_url)
                    resp.raise_for_status()

                    # 保存图片
                    ext = "jpg"
                    file_path = note_dir / f"{note_id}_{i+1}.{ext}"

                    with open(file_path, "wb") as f:
                        f.write(resp.content)

                    downloaded_files.append(str(file_path))
                    print(f"  ✓ 已保存: {file_path}")

                except Exception as e:
                    print(f"  ✗ 下载失败 {img_url}: {e}")

        return downloaded_files

    def parse_mediacrawler_json(self, json_file_path: str) -> List[Dict]:
        """
        解析 MediaCrawler 生成的 JSON 文件
        获取帖子的标题、内容和图片列表
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            notes = json.load(f)

        parsed_posts = []

        for note in notes:
            post_info = {
                "note_id": note.get("note_id"),
                "title": note.get("title", ""),
                "desc": note.get("desc", ""),  # 内容
                "type": note.get("type", ""),  # normal/video
                "liked_count": note.get("liked_count", 0),
                "collected_count": note.get("collected_count", 0),
                "comment_count": note.get("comment_count", 0),
                "share_count": note.get("share_count", 0),
                "image_list": [],
                "video_url": note.get("video_url", "")
            }

            # 提取图片URL
            images = note.get("image_list", [])
            for img_info in images:
                # 优先使用原图URL
                img_url = img_info.get("url") or img_info.get("url_default") or img_info.get("url_pre")
                if img_url:
                    post_info["image_list"].append(img_url)

            parsed_posts.append(post_info)

        return parsed_posts

    def fetch_with_mediacrawler(self, share_url: str) -> str:
        """
        使用 MediaCrawler 获取帖子信息的说明

        返回配置和运行步骤
        """
        note_id = self.extract_note_id(share_url)

        instructions = f"""
========================================
使用 MediaCrawler 获取小红书帖子信息
========================================

步骤 1: 安装 MediaCrawler
--------------------------
git clone https://github.com/NanmiCoder/MediaCrawler.git
cd MediaCrawler
uv sync
uv run playwright install chromium

步骤 2: 配置目标URL
--------------------------
编辑 config/xhs_config.py，添加:

XHS_SPECIFIED_NOTE_URL_LIST = [
    "{share_url}"
]

步骤 3: 运行爬虫
--------------------------
uv run main.py --platform xhs --lt qrcode --type detail

扫描二维码登录后，数据会保存到 data/xhs/ 目录

步骤 4: 解析和下载
--------------------------
使用本脚本解析JSON并下载图片:

from xhs_crawler import XHSPostCrawler

crawler = XHSPostCrawler()
posts = crawler.parse_mediacrawler_json("data/xhs/json/notes_xxx.json")

for post in posts:
    print(f"标题: {{post['title']}}")
    print(f"内容: {{post['desc']}}")
    print(f"图片数量: {{len(post['image_list'])}}")

    # 下载图片
    if post['image_list']:
        crawler.download_images(post['image_list'], post['note_id'])

========================================
提取到的 note_id: {note_id}
========================================
"""
        return instructions


def main():
    """主函数示例"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python xhs_crawler.py <小红书分享链接>")
        print("\n示例:")
        print("  python xhs_crawler.py 'https://www.xiaohongshu.com/explore/65f...'")
        print("  python xhs_crawler.py '65f1234567890abcdef12345'")
        return

    share_url = sys.argv[1]

    crawler = XHSPostCrawler()

    # 显示使用 MediaCrawler 的完整说明
    instructions = crawler.fetch_with_mediacrawler(share_url)
    print(instructions)

    # 如果已经有 MediaCrawler 生成的数据文件，可以这样使用:
    # posts = crawler.parse_mediacrawler_json("data/xhs/json/notes_2024-xx-xx.json")
    # for post in posts:
    #     print(f"\n标题: {post['title']}")
    #     print(f"内容: {post['desc'][:100]}...")
    #     if post['image_list']:
    #         crawler.download_images(post['image_list'], post['note_id'])


if __name__ == "__main__":
    main()