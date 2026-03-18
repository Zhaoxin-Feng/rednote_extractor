"""
上传图片到 Cloudflare R2
使用 S3 兼容 API
"""

import os
import boto3
from pathlib import Path
from botocore.config import Config


def upload_to_r2():
    """
    上传 downloads 文件夹中的所有图片到 Cloudflare R2
    """

    # ============================================
    # 配置信息 - 已自动填写
    # ============================================
    R2_ACCESS_KEY_ID = "3aa9a60a838e3424ec5cbb9a605a1c47"
    R2_SECRET_ACCESS_KEY = "7c567a1ed64185059c5c1e6da5ba8be79d77cdd6b48c47f0f61fc3faf3c269eb"
    R2_ENDPOINT_URL = "https://97cfcf941717980caaaf12b7645f4b33.r2.cloudflarestorage.com"
    R2_BUCKET_NAME = "xiaohongshu-post"

    # 公开访问 URL 前缀
    PUBLIC_URL_PREFIX = "https://pub-91c19942a97440f2b22cdc57caa6d4d8.r2.dev"

    # ============================================
    # 检查配置
    # ============================================
    if "YOUR_" in R2_ACCESS_KEY_ID or "YOUR_" in R2_SECRET_ACCESS_KEY:
        print("❌ 错误：请先在脚本中填写你的 R2 API 凭证！")
        print("\n📝 如何获取凭证：")
        print("1. 进入 Cloudflare Dashboard → R2")
        print("2. 点击 'Manage R2 API Tokens'")
        print("3. 创建 API Token (权限选择 Edit)")
        print("4. 复制 Access Key ID 和 Secret Access Key")
        print("5. 将凭证填写到本脚本的配置部分\n")
        return

    # ============================================
    # 初始化 S3 客户端（R2 兼容 S3 API）
    # ============================================
    print("🔗 正在连接到 Cloudflare R2...\n")

    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

    # ============================================
    # 扫描 downloads 文件夹
    # ============================================
    downloads_dir = Path("downloads")

    if not downloads_dir.exists():
        print(f"❌ 错误：找不到 {downloads_dir} 文件夹")
        return

    # 收集所有图片文件
    image_files = []
    for note_dir in downloads_dir.iterdir():
        if note_dir.is_dir():
            for img_file in note_dir.glob("*.jpg"):
                image_files.append(img_file)

    if not image_files:
        print("❌ 错误：downloads 文件夹中没有找到图片")
        return

    print(f"📁 找到 {len(image_files)} 张图片\n")

    # ============================================
    # 上传图片
    # ============================================
    uploaded_count = 0
    failed_count = 0
    uploaded_urls = []

    for img_path in image_files:
        # 构建 R2 中的路径（保持目录结构）
        # 例如：68f3694c00000000070364a9/68f3694c00000000070364a9_1.jpg
        relative_path = img_path.relative_to(downloads_dir)
        r2_key = str(relative_path).replace("\\", "/")  # Windows 兼容

        try:
            # 上传文件
            with open(img_path, 'rb') as f:
                s3_client.upload_fileobj(
                    f,
                    R2_BUCKET_NAME,
                    r2_key,
                    ExtraArgs={
                        'ContentType': 'image/jpeg',
                        'CacheControl': 'public, max-age=31536000'  # 缓存 1 年
                    }
                )

            # 生成公开访问 URL
            public_url = f"{PUBLIC_URL_PREFIX}/{r2_key}"
            uploaded_urls.append({
                'file': img_path.name,
                'url': public_url
            })

            uploaded_count += 1
            print(f"✅ [{uploaded_count}/{len(image_files)}] {img_path.name}")
            print(f"   → {public_url}\n")

        except Exception as e:
            failed_count += 1
            print(f"❌ 上传失败: {img_path.name}")
            print(f"   错误: {e}\n")

    # ============================================
    # 总结
    # ============================================
    print("="*60)
    print(f"✅ 上传完成！")
    print(f"   成功: {uploaded_count} 张")
    print(f"   失败: {failed_count} 张")
    print("="*60)

    # 保存 URL 列表到文件
    if uploaded_urls:
        output_file = "uploaded_urls.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("上传成功的图片 URL 列表\n")
            f.write("="*60 + "\n\n")
            for item in uploaded_urls:
                f.write(f"{item['file']}\n")
                f.write(f"{item['url']}\n\n")

        print(f"\n📝 URL 列表已保存到: {output_file}")

        # 显示第一张图片的 URL（用于测试）
        if uploaded_urls:
            print(f"\n🎨 测试访问第一张图片：")
            print(f"   {uploaded_urls[0]['url']}")


if __name__ == "__main__":
    upload_to_r2()
