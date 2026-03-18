"""
Upload images to Cloudflare R2
Using S3 compatible API
"""

import os
import boto3
from pathlib import Path
from botocore.config import Config


def upload_to_r2():
    """
    Upload all images from downloads folder to Cloudflare R2
    """

    # ============================================
    # Configuration - Auto-filled
    # ============================================
    R2_ACCESS_KEY_ID = ""
    R2_SECRET_ACCESS_KEY = ""
    R2_ENDPOINT_URL = ""
    R2_BUCKET_NAME = ""

    # Public access URL prefix
    PUBLIC_URL_PREFIX = "https://pub-91c19942a97440f2b22cdc57caa6d4d8.r2.dev"

    # ============================================
    # Check configuration
    # ============================================
    if "YOUR_" in R2_ACCESS_KEY_ID or "YOUR_" in R2_SECRET_ACCESS_KEY:
        print("❌ Error: Please fill in your R2 API credentials in the script first!")
        print("\n📝 How to get credentials:")
        print("1. Go to Cloudflare Dashboard → R2")
        print("2. Click 'Manage R2 API Tokens'")
        print("3. Create API Token (select Edit permission)")
        print("4. Copy Access Key ID and Secret Access Key")
        print("5. Fill credentials in the configuration section of this script\n")
        return

    # ============================================
    # Initialize S3 client (R2 compatible with S3 API)
    # ============================================
    print("🔗 Connecting to Cloudflare R2...\n")

    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

    # ============================================
    # Scan downloads folder
    # ============================================
    downloads_dir = Path("downloads")

    if not downloads_dir.exists():
        print(f"❌ Error: Cannot find {downloads_dir} folder")
        return

    # Collect all image files
    image_files = []
    for note_dir in downloads_dir.iterdir():
        if note_dir.is_dir():
            for img_file in note_dir.glob("*.jpg"):
                image_files.append(img_file)

    if not image_files:
        print("❌ Error: No images found in downloads folder")
        return

    print(f"📁 Found {len(image_files)} images\n")

    # ============================================
    # Upload images
    # ============================================
    uploaded_count = 0
    failed_count = 0
    uploaded_urls = []

    for img_path in image_files:
        # Build path in R2 (maintain directory structure)
        # Example: 68f3694c00000000070364a9/68f3694c00000000070364a9_1.jpg
        relative_path = img_path.relative_to(downloads_dir)
        r2_key = str(relative_path).replace("\\", "/")  # Windows compatible

        try:
            # Upload file
            with open(img_path, 'rb') as f:
                s3_client.upload_fileobj(
                    f,
                    R2_BUCKET_NAME,
                    r2_key,
                    ExtraArgs={
                        'ContentType': 'image/jpeg',
                        'CacheControl': 'public, max-age=31536000'  # Cache for 1 year
                    }
                )

            # Generate public access URL
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
            print(f"❌ Upload failed: {img_path.name}")
            print(f"   Error: {e}\n")

    # ============================================
    # Summary
    # ============================================
    print("="*60)
    print(f"✅ Upload complete!")
    print(f"   Success: {uploaded_count} images")
    print(f"   Failed: {failed_count} images")
    print("="*60)

    # Save URL list to file
    if uploaded_urls:
        output_file = "uploaded_urls.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Successfully uploaded image URLs\n")
            f.write("="*60 + "\n\n")
            for item in uploaded_urls:
                f.write(f"{item['file']}\n")
                f.write(f"{item['url']}\n\n")

        print(f"\n📝 URL list saved to: {output_file}")

        # Display first image URL (for testing)
        if uploaded_urls:
            print(f"\n🎨 Test access to first image:")
            print(f"   {uploaded_urls[0]['url']}")


if __name__ == "__main__":
    upload_to_r2()
