# Quality Filters Reference — scrAPE
> Detailed specification of the asset evaluation, relevance scoring, low-resolution pre-filtering, and quality rejection pipeline.

---

## 1. Filter Execution Order

Every discovered media asset candidate passes through an 8-stage evaluation pipeline in strict order:

```mermaid
flowchart TD
    A["Discovered Asset Candidate"] --> C1{"1. Duplicate Check<br/>(Normalized Key)"}
    C1 -- Yes --> R1["Reject: duplicate"]
    C1 -- No --> C2["2. Relevance Scoring<br/>(weighted_subject_score)"]

    C2 --> C3{"3. Low-Res Detection<br/>(Query Param or Path)"}
    C3 -- Yes --> R3["Reject: low_resolution_hint"]
    C3 -- No --> C4{"4. Archive / Index Penalty<br/>(-15 Score Penalty)"}

    C4 --> C5{"5. Preview Markers<br/>(thumb, preview, small)"}
    C5 -- Yes --> R5["Reject: preview_or_thumbnail"]
    C5 -- No --> C6{"6. Placeholder Rejection<br/>(Generic Path + No Tokens)"}

    C6 -- Yes --> R6["Reject: placeholder_asset"]
    C6 -- No --> C7{"7. Relevance Threshold<br/>(Score >= 1)"}
    C7 -- No --> R7["Reject: low_subject_relevance"]
    C7 -- Yes --> C8{"8. Max Results Cap"}
    C8 -- Full --> R8["Reject: max_results_limit"]
    C8 -- Space Available --> Keep["KEPT ASSET"]
```

---

## 2. Relevance Scoring Formula

Relevance scoring is calculated via `weighted_subject_score()` and media-specific functions in `src/core/relevance_scorer.py`.

### 2.1 Base Token Score (`weighted_subject_score`)
A base token score is calculated by concatenating all available asset metadata (URL, page title, alt text, anchor text) and searching for keyword and entity tokens:

- **Exact Token Matches**: `+2` points per exact token match (bounded by word boundaries `\b`).
- **Partial/Substring Matches**: `+1` point if the token appears as a substring.

### 2.2 Image Asset Scoring Modifiers (`score_image_relevance`)

| Condition | Score Adjustment |
|---|---|
| Has Alt Text | `+1` |
| Has Page Title | `+1` |
| Domain profile expects `image` type | `+3` |
| Is probable image (by extension: `.jpg`, `.png`, `.webp`, etc.) | `+2` |
| Contains image term (`photo`, `gallery`, `pic`, `img`, etc.) | `+1` |
| Contains generic asset term (`bg`, `logo`, `banner`, `texture`, etc.) | `-3` |
| Contains placeholder term (`captcha`, `blank`, `empty`, etc.) | `-4` |
| Contains preview markers (`thumb`, `small`, etc.) | `-3` (per marker) |
| URL contains dimension queries (`w=`, `size=`, etc.) | `-3` |
| Found in layout container (`layout` in URL) | `-20` |
| Width or Height < 300px | `-20` |
| Width or Height > 3000px | `-20` |
| Archive/Index page without direct subject match | `-15` |

### 2.3 Video Asset Scoring Modifiers (`score_video_relevance`)

| Condition | Score Adjustment |
|---|---|
| Has Page Title | `+1` |
| Domain profile expects `video` type | `+3` |
| Known video provider (`youtube`, `vimeo`, `hls`, `m3u8`, etc.) | `+2` |
| Is probable video (by extension: `.mp4`, `.webm`, `.mkv`, etc.) | `+2` |
| Contains video term (`video`, `clip`, `watch`, `stream`, etc.) | `+1` |
| Contains preview markers (`thumb`, `small`, etc.) | `-3` (per marker) |
| Explicit 'preview' keyword in URL | `-2` |
| Found in layout container (`layout` in URL) | `-20` |
| Archive/Index page without direct subject match | `-15` |

### 2.4 Score Acceptance Thresholds

| Media Kind | Minimum Required Score | Exception |
|---|---|---|
| **All Assets** | `Score >= 1` | Whitelisted CDN host asset (bypasses archive penalty) |

---

## 3. Low-Resolution Detection & Pre-Filtering

Low-resolution media items are detected and rejected using complementary mechanisms:

### 3.1 Dimension Query Params (`has_low_res_query_param`)
Scans URL query parameters for dimension hints:
- Keys checked: `w=150`, `h=100`, `width=200`, `height=200`, `sz=small`.
- Numeric values smaller than `400px` (or `min_size` override) trigger immediate rejection.

### 3.2 Dimension Regex Patterns (`has_low_res_path_pattern`)
Scans URL path strings for dimension regex patterns:

| Pattern Type | Example Matches | Threshold |
|---|---|---|
| **Double Dimensions** | `-150x150.jpg`, `_200x300/`, `/150x150/` | Width < 400px OR Height < 300px |
| **Resizer Paths** | `/resize/150/200`, `/w_150,h_150/`, `/fit/100/200` | Width < 400px OR Height < 300px |
| **Single Width Suffix** | `_150x.jpg` | Width < 400px |
| **Single Height Suffix** | `_x150.jpg` | Height < 300px |

### 3.3 Early Link Discovery & Upscaling (`transform_to_highres`)
Inside `is_thumbnail_url()`, candidate links matching low-resolution path patterns (e.g., `/320x180/` frame screenshots) are rejected **during early link discovery**.

When valid thumbnails are enqueued, `transform_to_highres(url)` heuristically predicts the original high-resolution asset URL:
- **Erome**: Replaces directories `/t/` or `/th/` with high-res `/v/`.
- **WordPress**: Strips `-scaled.jpg` and dimension patterns (`-1024x768.png`).
- **Twitter**: Replaces `name=small` or `name=medium` with `name=large`.
- **Generic Thumbnails**: Replaces `/thumbs/` with `/images/`, and `/video_thumbs/` with `/video_sources/`.

---

## 4. Archive & Index Page Penalties

Pages matching archive or index path patterns (`/`, `/index.html`, `/page/`, `/archive/`, `/tag/`, `/category/`, `/search/`) receive a **-15 score penalty** unless they explicitly contain a subject keyword match in their URL or title. 

### CDN Whitelist Bypass
Assets hosted on domain profiles annotated with `# [CDN] hostname` in the seed manifest **bypass archive penalties entirely**, ensuring dedicated media hosts keep legitimate assets regardless of page layout.

---

## 5. Safe String Utilities (`None`-Safe)

All filter evaluation routines use `safe_join(items, sep=" ")` to join token lists cleanly, preventing `TypeError` crashes when processing candidates with missing metadata:

```python
def safe_join(items: list[str | None], sep: str = " ") -> str:
    """Safely join strings ignoring None values."""
    return sep.join(s for s in items if s is not None)
```
