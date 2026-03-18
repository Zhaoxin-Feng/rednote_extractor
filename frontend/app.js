// ==========================================
// Global State
// ==========================================
let currentPost = null;
let currentMarkdown = '';
let analysisIntensity = 'detailed';
let currentImageIndex = 0;
let allImages = [];

// ==========================================
// Initialize App
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    initializeAPIKey();
    setupEventListeners();
    setupIntensitySelector();
});

// ==========================================
// API Key Management
// ==========================================
function initializeAPIKey() {
    const savedKey = localStorage.getItem('openrouter_api_key');
    if (savedKey) {
        document.getElementById('apiKey').value = savedKey;
    }
}

function saveAPIKey() {
    const apiKey = document.getElementById('apiKey').value.trim();
    if (apiKey) {
        localStorage.setItem('openrouter_api_key', apiKey);
        showNotification('API Key 已保存', 'success');
    } else {
        showNotification('请输入有效的 API Key', 'error');
    }
}

// ==========================================
// Event Listeners
// ==========================================
function setupEventListeners() {
    // Save API Key
    document.getElementById('saveKey').addEventListener('click', saveAPIKey);

    // Extract Content
    document.getElementById('extractBtn').addEventListener('click', extractContent);

    // Analyze Button
    document.getElementById('analyzeBtn').addEventListener('click', analyzeWithAI);

    // View Toggle
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => toggleView(btn.dataset.view));
    });

    // Copy Markdown
    document.getElementById('copyMdBtn').addEventListener('click', copyMarkdown);

    // Download Markdown
    document.getElementById('downloadMdBtn').addEventListener('click', downloadMarkdown);

    // Reanalyze
    document.getElementById('reanalyzeBtn').addEventListener('click', () => {
        document.getElementById('resultsSection').style.display = 'none';
        currentMarkdown = '';
    });

    // Enter key on link input
    document.getElementById('xhsLink').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            extractContent();
        }
    });

    // Download all images
    document.getElementById('downloadAllBtn').addEventListener('click', downloadAllImages);

    // Lightbox controls
    document.getElementById('imageLightbox').addEventListener('click', (e) => {
        if (e.target.id === 'imageLightbox') {
            closeLightbox();
        }
    });

    document.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
    document.querySelector('.lightbox-prev').addEventListener('click', () => navigateLightbox(-1));
    document.querySelector('.lightbox-next').addEventListener('click', () => navigateLightbox(1));

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        const lightbox = document.getElementById('imageLightbox');
        if (lightbox.style.display === 'flex') {
            if (e.key === 'Escape') {
                closeLightbox();
            } else if (e.key === 'ArrowLeft') {
                navigateLightbox(-1);
            } else if (e.key === 'ArrowRight') {
                navigateLightbox(1);
            }
        }
    });
}

function setupIntensitySelector() {
    document.querySelectorAll('.intensity-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.intensity-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            analysisIntensity = btn.dataset.intensity;
        });
    });
}

// ==========================================
// Extract Content Function
// ==========================================
async function extractContent() {
    const linkInput = document.getElementById('xhsLink').value.trim();

    if (!linkInput) {
        showNotification('请输入小红书链接', 'error');
        return;
    }

    // Extract note_id from URL
    const noteId = extractNoteId(linkInput);
    if (!noteId) {
        showNotification('无法识别的链接格式', 'error');
        return;
    }

    // Load post data (this would normally fetch from posts.json)
    // For now, using demo data
    loadDemoPost(noteId);
}

function extractNoteId(url) {
    // Match /explore/ or /discovery/item/ patterns
    const match = url.match(/\/(?:explore|discovery\/item)\/([a-f0-9]+)/);
    if (match) return match[1];

    // Check if it's already a note_id
    if (/^[a-f0-9]{24}$/.test(url)) return url;

    return null;
}

async function loadDemoPost(noteId) {
    try {
        // 从 posts.json 加载真实数据
        const response = await fetch('posts.json');
        if (!response.ok) {
            throw new Error('无法加载帖子数据');
        }

        const postsData = await response.json();
        currentPost = postsData[noteId];

        if (!currentPost) {
            showNotification(`找不到帖子 ID: ${noteId}`, 'error');
            return;
        }

        displayPost(currentPost);
    } catch (error) {
        console.error('加载帖子失败:', error);
        showNotification('加载帖子失败，请检查网络连接', 'error');
    }
}

function displayPost(post) {
    // Update DOM with post data
    document.getElementById('authorAvatar').src = post.avatar;
    document.getElementById('authorName').textContent = post.nickname;
    document.getElementById('postTime').textContent = post.time;
    document.getElementById('postTitle').textContent = post.title;
    document.getElementById('postContent').textContent = post.desc;
    document.getElementById('likeCount').textContent = post.liked_count;
    document.getElementById('collectCount').textContent = post.collected_count;
    document.getElementById('commentCount').textContent = post.comment_count;
    document.getElementById('shareCount').textContent = post.share_count;

    // Store images for lightbox
    allImages = post.images;

    // Update image count
    document.getElementById('imageCount').textContent = post.images.length;

    // Show download all button
    const downloadBtn = document.getElementById('downloadAllBtn');
    downloadBtn.style.display = 'inline-flex';

    // Display images
    const gallery = document.getElementById('imageGallery');
    gallery.innerHTML = '';
    post.images.forEach((imgUrl, index) => {
        const img = document.createElement('img');
        img.src = imgUrl;
        img.alt = `Image ${index + 1}`;
        img.className = 'gallery-image';
        img.style.animationDelay = `${index * 0.1}s`;
        img.style.animation = 'cardFadeIn 0.5s ease forwards';

        // Add click event to open lightbox
        img.addEventListener('click', () => openLightbox(index));

        gallery.appendChild(img);
    });

    // Show post display section
    document.getElementById('postDisplay').style.display = 'block';

    // Smooth scroll to post
    setTimeout(() => {
        document.getElementById('postDisplay').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
}

// ==========================================
// AI Analysis Function
// ==========================================
async function analyzeWithAI() {
    const apiKey = localStorage.getItem('openrouter_api_key');
    if (!apiKey) {
        showNotification('请先配置 OpenRouter API Key', 'error');
        document.getElementById('apiKey').focus();
        return;
    }

    if (!currentPost) {
        showNotification('请先提取小红书内容', 'error');
        return;
    }

    // Get analysis parameters
    const model = document.getElementById('modelSelect').value;
    const customPrompt = document.getElementById('customPrompt').value;

    // Show progress
    document.getElementById('progressIndicator').style.display = 'block';
    document.getElementById('analyzeBtn').disabled = true;
    document.getElementById('analyzeBtn').style.opacity = '0.6';

    try {
        // Prepare messages for OpenRouter API
        const messages = [
            {
                role: 'user',
                content: [
                    {
                        type: 'text',
                        text: customPrompt
                    },
                    ...currentPost.images.map(url => ({
                        type: 'image_url',
                        image_url: { url }
                    }))
                ]
            }
        ];

        // Call OpenRouter API
        const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
                'HTTP-Referer': window.location.href,
                'X-Title': 'RedExtract Pro'
            },
            body: JSON.stringify({
                model: model,
                messages: messages,
                temperature: 0.7,
                max_tokens: 4000
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error?.message || response.statusText;

            // 提供更详细的错误信息
            let userMessage = `API 错误 (${response.status}): ${errorMessage}`;

            if (response.status === 403) {
                userMessage = `❌ API 访问被拒绝 (403)\n\n可能原因：\n1. API Key 无效或格式错误\n2. 账户余额不足\n3. 所选模型不支持图片分析\n4. API Key 权限不足\n\n请检查您的 OpenRouter 账户：\n- 访问 https://openrouter.ai/keys\n- 确认 API Key 有效\n- 检查账户余额\n- 尝试使用支持 vision 的模型`;
            } else if (response.status === 401) {
                userMessage = '❌ API Key 无效 (401)\n\n请检查：\n1. API Key 格式是否正确（应以 sk-or-v1- 开头）\n2. 是否已在 OpenRouter 控制台创建了有效的 API Key';
            } else if (response.status === 429) {
                userMessage = '❌ 请求过于频繁 (429)\n\n请稍后再试，或升级您的 OpenRouter 套餐';
            }

            throw new Error(userMessage);
        }

        const data = await response.json();
        currentMarkdown = data.choices[0].message.content;

        // Display results
        displayResults(currentMarkdown);
        showNotification('分析完成！', 'success');

    } catch (error) {
        console.error('Analysis error:', error);
        showNotification(`分析失败: ${error.message}`, 'error');
    } finally {
        // Hide progress
        document.getElementById('progressIndicator').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
        document.getElementById('analyzeBtn').style.opacity = '1';
    }
}

function displayResults(markdown) {
    // Render markdown
    const html = marked.parse(markdown);
    document.getElementById('markdownPreview').innerHTML = html;
    document.getElementById('sourceCode').textContent = markdown;

    // Show results section
    document.getElementById('resultsSection').style.display = 'block';

    // Smooth scroll to results
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
}

// ==========================================
// View Toggle
// ==========================================
function toggleView(view) {
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    if (view === 'preview') {
        document.getElementById('markdownPreview').style.display = 'block';
        document.getElementById('rawSource').style.display = 'none';
    } else {
        document.getElementById('markdownPreview').style.display = 'none';
        document.getElementById('rawSource').style.display = 'block';
    }
}

// ==========================================
// Copy & Download Functions
// ==========================================
async function copyMarkdown() {
    if (!currentMarkdown) {
        showNotification('没有可复制的内容', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(currentMarkdown);
        showNotification('Markdown 已复制到剪贴板', 'success');
    } catch (error) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = currentMarkdown;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('Markdown 已复制到剪贴板', 'success');
    }
}

function downloadMarkdown() {
    if (!currentMarkdown) {
        showNotification('没有可下载的内容', 'error');
        return;
    }

    const blob = new Blob([currentMarkdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentPost.note_id}_analysis.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showNotification('Markdown 文件已下载', 'success');
}

// ==========================================
// Notification System
// ==========================================
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    // Support multi-line messages
    notification.style.whiteSpace = 'pre-line';
    notification.textContent = message;

    // Style the notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '24px',
        right: '24px',
        padding: '16px 24px',
        background: type === 'success' ? 'var(--color-terracotta)' :
                    type === 'error' ? '#E74C3C' :
                    'var(--color-brown)',
        color: 'white',
        borderRadius: 'var(--radius-sm)',
        boxShadow: 'var(--shadow-lg)',
        zIndex: '10000',
        fontSize: '14px',
        fontWeight: type === 'error' ? '500' : '600',
        animation: 'slideInRight 0.3s ease',
        maxWidth: '500px',
        lineHeight: '1.6',
        textAlign: 'left'
    });

    document.body.appendChild(notification);

    // Remove after duration (longer for errors)
    const duration = type === 'error' ? 8000 : 3000;
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, duration);
}

// ==========================================
// Image Lightbox Functions
// ==========================================
function openLightbox(index) {
    currentImageIndex = index;
    updateLightboxImage();
    document.getElementById('imageLightbox').style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closeLightbox() {
    document.getElementById('imageLightbox').style.display = 'none';
    document.body.style.overflow = ''; // Restore scrolling
}

function navigateLightbox(direction) {
    currentImageIndex += direction;

    // Loop around
    if (currentImageIndex < 0) {
        currentImageIndex = allImages.length - 1;
    } else if (currentImageIndex >= allImages.length) {
        currentImageIndex = 0;
    }

    updateLightboxImage();
}

function updateLightboxImage() {
    const img = document.getElementById('lightboxImage');
    const counter = document.getElementById('lightboxCounter');

    img.src = allImages[currentImageIndex];
    counter.textContent = `${currentImageIndex + 1} / ${allImages.length}`;
}

// ==========================================
// Download All Images Function
// ==========================================
async function downloadAllImages() {
    if (!currentPost || !allImages || allImages.length === 0) {
        showNotification('没有可下载的图片', 'error');
        return;
    }

    const btn = document.getElementById('downloadAllBtn');
    const originalText = btn.innerHTML;

    try {
        // Disable button and show loading state
        btn.disabled = true;
        btn.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="animation: spin 1s linear infinite;">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="2" fill="none"/>
            </svg>
            下载中...
        `;

        // Add spin animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);

        showNotification(`正在下载 ${allImages.length} 张图片...`, 'info');

        // Create new JSZip instance
        const zip = new JSZip();
        const imageFolder = zip.folder('images');

        // Download all images
        const downloadPromises = allImages.map(async (imageUrl, index) => {
            try {
                const response = await fetch(imageUrl);
                if (!response.ok) throw new Error(`Failed to fetch image ${index + 1}`);

                const blob = await response.blob();
                const extension = imageUrl.split('.').pop().split('?')[0] || 'jpg';
                const filename = `${currentPost.note_id}_${index + 1}.${extension}`;

                imageFolder.file(filename, blob);
            } catch (error) {
                console.error(`Error downloading image ${index + 1}:`, error);
                throw error;
            }
        });

        // Wait for all downloads to complete
        await Promise.all(downloadPromises);

        // Generate zip file
        const zipBlob = await zip.generateAsync({
            type: 'blob',
            compression: 'DEFLATE',
            compressionOptions: { level: 6 }
        });

        // Create download link
        const url = URL.createObjectURL(zipBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentPost.title || currentPost.note_id}_images.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification(`成功下载 ${allImages.length} 张图片！`, 'success');

    } catch (error) {
        console.error('Download error:', error);
        showNotification(`下载失败: ${error.message}`, 'error');
    } finally {
        // Restore button state
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Add notification animations to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);