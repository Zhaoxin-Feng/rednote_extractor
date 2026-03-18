# 🌸 RedExtract Pro

RedNote Content Extraction Tool - Image Download · Cloud Storage · AI Analysis

---

## ✨ Key Features

- 🔗 **Content Extraction** - Extract posts and images from RedNote sharing links
- ☁️ **Cloud Storage** - Auto-upload images to Cloudflare R2
- 📦 **Batch Processing** - Add multiple posts at once, scan QR code only once
- 💾 **One-Click Download** - Batch download all images as zip file
- 🤖 **AI Analysis** - Smart content analysis using OpenRouter API
- 📝 **Markdown Export** - Generate formatted analysis documents

---

## 🚀 Quick Start

### 1️⃣ Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# MediaCrawler (web scraper)
git clone https://github.com/NanmiCoder/MediaCrawler.git
cd MediaCrawler
uv sync
uv run playwright install chromium
cd ..
```

### 2️⃣ Configure Cloudflare R2

1. Sign up for a [Cloudflare](https://dash.cloudflare.com/) account
2. Create an R2 bucket
3. Get Access Key and Secret Key
4. Edit `upload_to_r2.py` and fill in your credentials

### 3️⃣ Usage

#### Add Single Post

```bash
./scripts/fetch_post.sh "https://www.xiaohongshu.com/discovery/item/POST_ID"
```

#### Batch Add Posts (Recommended)

```bash
# 1. Create URL list
cat > urls.txt << EOF
https://www.xiaohongshu.com/discovery/item/POST_1
https://www.xiaohongshu.com/discovery/item/POST_2
EOF

# 2. Batch process
./scripts/fetch_posts_batch.sh urls.txt
```

#### Launch Frontend

```bash
python3 -m http.server 8000
# Visit http://localhost:8000
```

---

## 📂 Project Structure

```
xhs_post/
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
├── urls_example.txt           # URL list example
├── .gitignore                 # Git ignore rules
├── MediaCrawler/              # Web scraper tool
├── frontend/                  # Web interface
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── posts.json
├── docs/                      # Complete documentation
│   ├── INSTALL.md
│   ├── BATCH_USAGE.md
│   └── LOGIN_TIPS.md
└── scripts/                   # All scripts
    ├── fetch_post.sh          # Single post add
    ├── fetch_posts_batch.sh   # Batch add (recommended)
    ├── add_post.py            # Data processing core
    ├── upload_to_r2.py        # R2 upload
    ├── process_data.py        # Manual data processing
    └── xhs_crawler.py         # Crawler class (backup)
```

---

## 📚 Documentation

- [Installation Guide](docs/INSTALL.md) - Detailed installation steps
- [Batch Processing Guide](docs/BATCH_USAGE.md) - How to batch add posts
- [Login Management Guide](docs/LOGIN_TIPS.md) - Reduce QR code scanning frequency

---

## 💡 Usage Tips

- ✅ **After first QR scan, no need to scan again for 1-2 weeks**
- ✅ **Using batch scripts increases efficiency by 3-5x**
- ✅ **Regular usage keeps login session active**
- ✅ **Recommended max 10 posts per batch**

---

## 🛠️ Tech Stack

- **Scraper**: MediaCrawler (Playwright)
- **Storage**: Cloudflare R2 (Free 10GB)
- **Frontend**: HTML + CSS + JavaScript
- **Backend**: Python 3.8+
- **AI**: OpenRouter API

---
