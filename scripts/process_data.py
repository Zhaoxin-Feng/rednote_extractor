"""
处理 MediaCrawler 生成的 JSONL 数据
解析帖子信息并下载图片
"""

import json
import httpx
from pathlib import Path


def parse_jsonl_and_download(jsonl_file: str, save_dir: str = "downloads"):
    """
    解析 JSONL 文件并下载图片

    Args:
        jsonl_file: JSONL 文件路径
        save_dir: 图片保存目录
    """
    save_path = Path(save_dir)
    save_path.mkdir(exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.xiaohongshu.com/"
    }

    print(f"正在读取文件: {jsonl_file}\n")

    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # 解析每一行 JSON
            post = json.loads(line.strip())

            note_id = post.get("note_id")
            title = post.get("title", "无标题")
            desc = post.get("desc", "")
            liked_count = post.get("liked_count", "0")
            collected_count = post.get("collected_count", "0")
            comment_count = post.get("comment_count", "0")

            # 图片列表是逗号分隔的字符串
            image_list_str = post.get("image_list", "")
            image_urls = [url.strip() for url in image_list_str.split(",") if url.strip()]

            print(f"{'='*60}")
            print(f"帖子 #{line_num}")
            print(f"{'='*60}")
            print(f"ID: {note_id}")
            print(f"标题: {title}")
            print(f"内容: {desc[:100]}{'...' if len(desc) > 100 else ''}")
            print(f"点赞: {liked_count} | 收藏: {collected_count} | 评论: {comment_count}")
            print(f"图片数量: {len(image_urls)}")
            print()

            # 创建帖子专属目录
            if image_urls:
                note_dir = save_path / note_id
                note_dir.mkdir(exist_ok=True)

                # 保存帖子信息到文本文件
                info_file = note_dir / "info.txt"
                with open(info_file, 'w', encoding='utf-8') as info_f:
                    info_f.write(f"标题: {title}\n")
                    info_f.write(f"内容:\n{desc}\n\n")
                    info_f.write(f"点赞: {liked_count}\n")
                    info_f.write(f"收藏: {collected_count}\n")
                    info_f.write(f"评论: {comment_count}\n")
                    info_f.write(f"链接: {post.get('note_url', '')}\n")

                print(f"开始下载 {len(image_urls)} 张图片...")

                # 下载图片
                with httpx.Client(headers=headers, timeout=30.0, follow_redirects=True) as client:
                    for i, img_url in enumerate(image_urls, 1):
                        try:
                            print(f"  [{i}/{len(image_urls)}] 下载中...", end=" ")
                            resp = client.get(img_url)
                            resp.raise_for_status()

                            # 保存图片
                            file_path = note_dir / f"{note_id}_{i}.jpg"
                            with open(file_path, "wb") as img_f:
                                img_f.write(resp.content)

                            print(f"✓ 已保存: {file_path}")

                        except Exception as e:
                            print(f"✗ 失败: {e}")

                print(f"\n帖子 {note_id} 处理完成！")
                print(f"保存位置: {note_dir}")
                print()

    print(f"\n{'='*60}")
    print(f"全部处理完成！图片保存在: {save_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    # MediaCrawler 生成的数据文件路径
    jsonl_file = "MediaCrawler/data/xhs/jsonl/detail_contents_2026-03-18.jsonl"

    # 开始处理
    parse_jsonl_and_download(jsonl_file, save_dir="downloads")
