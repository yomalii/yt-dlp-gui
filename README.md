<div align="center">

# ⚡ YT-DLP Premium GUI
### The Ultimate High-Performance Video Downloader


[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-FFE873?style=for-the-badge&logo=python&logoColor=3776AB)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/Powered_By-yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Made By](https://img.shields.io/badge/Made_By-Shiraken12T-D4AF37?style=for-the-badge)](https://github.com/Shiraken12T)

<br/>

**A stunning, modern, and ultra-fast GUI for `yt-dlp`.**  

yt-dlp GUI is a modern, high-performance video downloader GUI for yt-dlp, allowing users to download videos and audio from YouTube, Instagram, TikTok, and thousands of supported websites with maximum quality and speed.

Download videos from YouTube, Instagram, TikTok, and thousands of other sites with a single click.  
Engineered for speed, aesthetics, and simplicity.

[Features](#-key-features) • [Installation](#-installation) • [Usage](#-how-to-use) • [Credits](#-credits)

---
</div>

## ✨ Key Features

### 🎨 Premium "Midnight Gold" UI
Experience a sleek, dark-themed interface (`#050505`) with metallic gold accents (`#D4AF37`). Minimalist, distraction-free, and beautiful.

### 🚀 Super Turbo Mode
Enable **Turbo Mode** to unleash the full power of your connection.
-   **16x Parallel Connections**: Downloads chunks simultaneously for max speed.
-   **Optimized Buffer**: Custom buffer resizing to prevent throttles.
-   **No Speed Limits**: Bypasses average bandwidth restrictions.

### 💎 Maximum Quality Engine
-   **Smart Selection**: Automatically grabs the **absolute highest resolution** (4K, 8K, Original).
-   **Auto-Merge**: Intelligent logic combines the best video stream (VP9/AV1) with the best audio (Opus/AAC).
-   **Premiere Compat Mode**: Need to edit? One checkbox forces **MP4 (H.264)** for compatibility with Premiere Pro & DaVinci Resolve.

### 🔗 Universal Support & Robustness
-   **Instagram Reels & TikTok**: Downloads high-quality vertical videos with **generic URL support**.
-   **Smart Thumbnails**: Automatically detects and displays the **highest-resolution thumbnail** (no more blurry covers!).
-   **Crash-Proof**: Built-in auto-retry mechanisms for generic streams and timeout handling for slow servers.

### 🛠️ Advanced Tools
-   **One-Click Installer**: Click **INSTALL** (top-right) to automatically install/update `yt-dlp`, dependencies, and check for FFmpeg.
-   **Real-time Stats**: Live Speed, Size, and ETA tracking.
-   **Thumbnail Saver**: Dedicated button to download the cover art.

---

## 📥 Installation

### Prerequisites
1.  **Python 3.10+**: [Download Here](https://www.python.org/downloads/)
2.  **FFmpeg**: Required for merging video+audio. [Download Here](https://ffmpeg.org/download.html) (Add to PATH).
3.  **Deno** (JavaScript Runtime): Required for YouTube downloads. Install via:
    ```bash
    # Windows (PowerShell)
    winget install DenoLand.Deno
    
    # macOS/Linux
    curl -fsSL https://deno.land/install.sh | sh
    ```

> [!IMPORTANT]
> **YouTube now requires a JavaScript runtime** (like Deno) to solve download challenges. Without Deno, you'll get HTTP 403 Forbidden errors. See [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#dependencies) for more details.

### Setup
1.  **Clone the Repo** (or download zip):
    ```bash
    git clone https://github.com/yomalii/yt-dlp-gui.git
    cd yt-dlp-gui
    ```
2.  **Install Dependencies**:
    ```bash
    pip install "yt-dlp[default]" requests pillow
    ```
    > The `[default]` extras include the necessary JavaScript components for YouTube.
3.  **Run the App**:
    ```bash
    python ytdlp.py
    ```

---

## 🎮 How to Use

1.  **Paste & Fetch**: Copy any video URL (YouTube, Insta, etc.) and click **SEARCH**.
2.  **Customize**:
    -   Select **Format** (MP4, MP3, etc.).
    -   Choose **Quality** (Select "Best Available" for max res).
    -   Toggle **🚀 Turbo Mode** for speed.
3.  **Download**: Click the big gold **START DOWNLOAD** button.
4.  **Enjoy**: Your file (and thumbnail!) will appear in your chosen folder.

---

## 👨‍💻 Credits

**Made with by [Shiraken12T](https://github.com/yomalii)**

This project is **Free to Use** and Open Source.
*Powered by the incredible [yt-dlp](https://github.com/yt-dlp/yt-dlp) project.*