# Quality filtering and media selection

## Goals

**scrAPE** favors substantive media assets for the target keyword rather than generic site decorations, thumbnails, or low-resolution previews.

## What is filtered out

- Thumbnail-like URLs that contain terms such as `thumb`, `thumbnail`, `preview`, `avatar`, `icon`, `sprite`, or `small`
- Tiny assets indicated by low content-length values during download
- Low-resolution size hints in URLs such as `width=120` or `height=120`
- Generic site assets that are clearly decorative, such as logos, icons, badges, avatars, and placeholders

## What is kept

- Media URLs that are clearly related to the target keyword
- Images and videos whose surrounding page context suggests a real gallery, post, media, cosplay, or video entry
- Higher-signal assets that are not obviously decorative thumbnails
- Assets served from domain-associated CDN hosts (which bypass the index/archive page score penalties)

## How the pipeline works

1. Candidate media URLs are collected from pages and discovered links.
2. Each item is filtered by media type expectations against its parent domain profile (e.g. discarding videos on image-only domains).
3. The relevance scoring system evaluates keywords/entity tokens, layout locations, and URL metadata.
4. Media items hosted on registered CDN allow-lists bypass archive-page score penalties.
5. The filter rejects low-value assets (final score < 1) before they are stored in the final result set.
6. The downloader reevaluates the media before writing files to disk and skips tiny or poor-quality assets.

## 1. Thumbnail and Decorative-asset Filters

**scrAPE** implements multiple heuristics to avoid collecting decorative site elements.

### Thumbnail / preview heuristics

- **Directory names**: skips paths containing `thumb`, `thumbnail`, `preview`, `prev`, `thumb_full`, `thumb_hr`, etc.
- **Filename patterns**: rejects `t_`, `tn_`, `preview-`, `thumbnail-` prefixes
- **Width/height tokens**: rejects URLs where `w=` or `h=` are set to small values (default thresholds in `IMG_SIZE_THRESHOLDS`, configurable via env vars)
- **Placeholder names**: rejects `placeholder` or `dummy` in paths or query params

### Logo and icon filtering

- **File extensions**: Skips `.ico`, `.svg`, `.png`, `.gif` assets where `filename` or `path_segment` match common icon patterns.
- **Filename terms**: Skips paths containing `logo`, `icon`, `badge`, `avatar`, `profile_pic`, etc.
- **Query params**: Rejects tokens like `format=icon` or `size=small`.

### Decorative asset scoring

- Decorative images get an automatic `decorational_score` penalty (between -0.5 and -1.0).
- This penalty is subtracted from the final relevance score **before** the `final_score < 1` filter.
