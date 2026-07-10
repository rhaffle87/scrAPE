# Quality Filters — scrAPE

## Pipeline Order

For each discovered image/video asset, the filter pipeline runs in this order:

1. **Duplicate check** — Already seen via normalized key → `"duplicate"`
2. **Relevance scoring** — `weighted_subject_score()` with field-weighted tokens
3. **Low-resolution detection** — URL query params OR path pattern → `"low_resolution_hint"`
4. **Archive/index page penalty** — Source page detected as archive/index → score affected
5. **Preview thumbnail penalty** — URL contains preview markers → `"preview_or_thumbnail"`
6. **Placeholder rejection** — Generic path pattern + no subject keywords → `"placeholder_asset"`
7. **Subject relevance threshold** — Score below minimum → `"low_subject_relevance"`
8. **Max results limit** — Collection full → `"max_results_limit"`

## Low-Resolution Detection

Two complementary functions:

### `has_low_res_query_param(url, min_size=400)`

Checks URL query parameters for dimension hints:

- `w=150`, `h=100`, `width=200`, `height=200`, `sz=small`
- Parameters with numeric values < `min_size`

### `has_low_res_path_pattern(url, min_width=400, min_height=300)`

Checks URL path for dimension patterns:

 | Pattern | Example | Matches |
 | --- | --- | --- |
 | Double dimensions | `-150x150.jpg`, `_200x300/`, `/150x150/` | Width < 400 OR height < 300 |
 | Resizer paths | `/resize/150/200`, `/w_150,h_150/`, `/fit/100/200` | Same thresholds |
 | Single width | `_150x.jpg` | Width < 400 |
 | Single height | `_x150.jpg` | Height < 300 |

## Preview / Thumbnail Detection

Negative markers checked in URL and context text:

```text
# From _preview_penalty():
'thumb', 'thumbs', 'thumbnail', '_th', '/th/', '-th-',
'preview', 'small', '150x150', '100x100', '200x200',
'tiny', 'icon', 'micro', 'mini', 'sq.', '/sq/'
```

If ≥ 4 points worth of markers detected → `"preview_or_thumbnail"`

## Archive / Index Page Detection

`is_archive_or_index_page(url, title)` — checks path for:

- Empty or root path (`/`, `/index.html`)
- `/page/`, `/post/`, `/article/`, `/gallery/`, `/photo/`, `/image/`
- Archive patterns: date segments, `/tag/`, `/category/`, `/author/`, `/search/`
- Query parameters: `?page=`, `?s=`, `?tag=`

Assets on archive/index pages get a **-3 score penalty** unless the domain is a registered CDN.

## CDN Bypass

Domains listed as `[CDN]` in seed manifests bypass the archive/index page penalty entirely. This allows image hosts (e.g., `example-cdn.net`) to keep their assets regardless of source page structure.

## `safe_join` Helper

```python
def safe_join(items: list[str | None], sep: str = " ") -> str:
    return sep.join(s for s in items if s is not None)
```

All filter functions use `safe_join` instead of `" ".join([...])` to avoid `TypeError` when processing items with `None` fields (e.g., missing alt text, page title).

## Thresholds

 | Field | Score Condition |
 | --- | --- |
 | Image min score | `score >= 3` (or CDN and not archive) |
 | Video min score | `score >= 2` (or CDN and not archive) |
 | Token weights | URL: 3×, alt: 2×, source/title: 1× |
 | Entity bonus | 2× when matched in URL or alt text |
