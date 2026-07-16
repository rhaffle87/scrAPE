import json
import logging
from pathlib import Path
from datetime import datetime

LOGGER = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watchdog Scraper Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-color: #3b82f6;
            --accent-hover: #60a5fa;
            --danger: #ef4444;
            --success: #10b981;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
        }

        header {
            background-color: var(--surface-color);
            padding: 1.5rem 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .stat-card {
            background-color: var(--surface-color);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        }

        .stat-card .label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .gallery-container {
            padding: 0 2rem 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .gallery-container h2 {
            margin-bottom: 1rem;
            font-weight: 600;
            font-size: 1.25rem;
            color: var(--text-secondary);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
        }

        .media-card {
            background-color: var(--surface-color);
            border-radius: 8px;
            overflow: hidden;
            position: relative;
            aspect-ratio: 1;
            border: 1px solid rgba(255,255,255,0.05);
            transition: transform 0.2s;
        }

        .media-card:hover {
            transform: scale(1.02);
            z-index: 10;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }

        .media-card img, .media-card video {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .media-card .overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
            padding: 1rem 0.5rem 0.5rem;
            font-size: 0.75rem;
            color: #fff;
            opacity: 0;
            transition: opacity 0.2s;
        }

        .media-card:hover .overlay {
            opacity: 1;
        }

        .last-updated {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding: 0 2rem;
            max-width: 1400px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .tab {
            padding: 0.5rem 1rem;
            background-color: var(--surface-color);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 6px;
            cursor: pointer;
            color: var(--text-secondary);
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .tab:hover {
            color: var(--text-primary);
        }
        
        .tab.active {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }
    </style>
</head>
<body>
    <header>
        <h1>Watchdog Scraper</h1>
        <div class="last-updated" id="last-updated">Last Updated: {last_updated}</div>
    </header>

    <div class="stats-container">
        <div class="stat-card">
            <div class="label">Total Runs</div>
            <div class="value">{total_runs}</div>
        </div>
        <div class="stat-card">
            <div class="label">Total Images</div>
            <div class="value">{total_images}</div>
        </div>
        <div class="stat-card">
            <div class="label">Total Videos</div>
            <div class="value">{total_videos}</div>
        </div>
        <div class="stat-card">
            <div class="label">Total Scanned</div>
            <div class="value">{total_scanned_pages}</div>
        </div>
    </div>
    
    <div class="tabs">
        <button class="tab active" onclick="showTab('images')">Images</button>
        <button class="tab" onclick="showTab('videos')">Videos</button>
    </div>

    <div class="gallery-container" id="images-tab">
        <h2>Recent Images</h2>
        <div class="grid">
            {image_cards}
        </div>
    </div>
    
    <div class="gallery-container" id="videos-tab" style="display: none;">
        <h2>Recent Videos</h2>
        <div class="grid">
            {video_cards}
        </div>
    </div>

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.gallery-container').forEach(c => c.style.display = 'none');
            
            if(tabName === 'images') {
                document.getElementById('images-tab').style.display = 'block';
                event.target.classList.add('active');
            } else {
                document.getElementById('videos-tab').style.display = 'block';
                event.target.classList.add('active');
            }
        }
    </script>
</body>
</html>
"""


def _build_media_card(file_path: str, is_video: bool = False) -> str:
    # URL safe path
    web_path = file_path.replace("\\", "/")
    if is_video:
        return f'''
        <div class="media-card">
            <video src="{web_path}" controls preload="metadata" muted></video>
            <div class="overlay">{file_path}</div>
        </div>
        '''
    else:
        return f'''
        <div class="media-card">
            <img src="{web_path}" loading="lazy" alt="Scraped image">
            <div class="overlay">{file_path}</div>
        </div>
        '''


def build_dashboard(output_dir: str | Path):
    """Parses output directories and generates an index.html dashboard."""
    output_path = Path(output_dir)
    if not output_path.exists():
        LOGGER.warning(
            f"Output directory {output_dir} does not exist. Skipping dashboard build."
        )
        return

    # 1. Aggregate Stats
    total_runs = 0
    total_images = 0
    total_videos = 0
    total_scanned = 0

    for json_file in output_path.glob("*/runs/*/results.json"):
        total_runs += 1
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                total_images += data.get("download_stats", {}).get("images_saved", 0)
                total_videos += data.get("download_stats", {}).get("videos_saved", 0)
                total_scanned += data.get("page_count", 0)
        except Exception:
            pass

    # 2. Get recent images and videos directly from the subfolders
    image_cards = []
    video_cards = []

    img_files = sorted(
        output_path.glob("*/runs/*/images/*.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:50]
    for img in img_files:
        if img.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            # Get relative path for web src
            rel_path = img.relative_to(output_path).as_posix()
            image_cards.append(_build_media_card(rel_path, is_video=False))

    vid_files = sorted(
        output_path.glob("*/runs/*/videos/*.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:50]
    for vid in vid_files:
        if vid.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]:
            rel_path = vid.relative_to(output_path).as_posix()
            video_cards.append(_build_media_card(rel_path, is_video=True))

    html_content = HTML_TEMPLATE
    html_content = html_content.replace(
        "{last_updated}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    html_content = html_content.replace("{total_runs}", str(total_runs))
    html_content = html_content.replace("{total_images}", str(total_images))
    html_content = html_content.replace("{total_videos}", str(total_videos))
    html_content = html_content.replace("{total_scanned_pages}", str(total_scanned))
    html_content = html_content.replace(
        "{image_cards}", "".join(image_cards) or "<p>No images found yet.</p>"
    )
    html_content = html_content.replace(
        "{video_cards}", "".join(video_cards) or "<p>No videos found yet.</p>"
    )

    index_file = output_path / "index.html"
    index_file.write_text(html_content, encoding="utf-8")
    LOGGER.info(f"Dashboard successfully built at {index_file}")
