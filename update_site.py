#!/usr/bin/env python3
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_URL = "https://compare-aything.com"
PAGES_DIR = "pages"
INDEX_FILE = "index.html"
SITEMAP_FILE = "sitemap.xml"
TAGS_DIR = "tags"


def parse_meta_from_html(filepath: Path):
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<!--\s*META(.*?)-->", text, re.IGNORECASE | re.DOTALL)
    meta = {}
    if m:
        block = m.group(1)
        for line in block.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip()
    return meta


def get_page_info(filepath: Path):
    # pages/ からの相対パス → URL パスに変換
    rel = filepath.relative_to(PAGES_DIR)
    rel_str = str(rel).replace(os.sep, "/")  # e.g. crypto/btc.html
    url_path = f"{PAGES_DIR}/{rel_str}"      # pages/crypto/btc.html
    url = f"{BASE_URL}/{url_path}"

    meta = parse_meta_from_html(filepath)

    title = meta.get("title") or rel.stem
    description = meta.get("description", "")
    tags = []
    if "tags" in meta:
        tags = [t.strip() for t in meta["tags"].split(",") if t.strip()]
    category = meta.get("category", "")

    # date: 指定なければ最終更新日時
    if "date" in meta:
        date_str = meta["date"].strip()
    else:
        ts = filepath.stat().st_mtime
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    return {
        "path": filepath,
        "rel_path": rel_str,
        "url_path": url_path,
        "url": url,
        "title": title,
        "description": description,
        "tags": tags,
        "category": category,
        "date": date_str,
    }


def collect_pages():
    pages = []
    for root, _, files in os.walk(PAGES_DIR):
        for name in files:
            if not name.lower().endswith(".html"):
                continue
            fp = Path(root) / name
            pages.append(get_page_info(fp))
    # 新しい日付順でソート
    pages.sort(key=lambda p: p["date"], reverse=True)
    return pages


def generate_index_html(pages):
    items = []
    for p in pages:
        tags_html = ""
        if p["tags"]:
            tags_html = " / ".join(
                f'<a href="/{TAGS_DIR}/{t}.html">{t}</a>' for t in p["tags"]
            )
            tags_html = f'<div class="tags">{tags_html}</div>'

        items.append(
            f'''    <article class="post">
      <h2><a href="/{p["url_path"]}">{p["title"]}</a></h2>
      <div class="meta">{p["date"]}  {tags_html}</div>
    </article>'''
        )

    items_html = "\n".join(items)
    updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>compare-aything.com – 比較記事の一覧</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="あらゆる商品・サービス・投資対象を比較するプログラマティックSEOサイト。最新記事一覧。">
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      max-width: 880px;
      margin: 2rem auto;
      padding: 0 1rem;
      line-height: 1.6;
    }}
    h1 {{
      font-size: 1.8rem;
      margin-bottom: 1.5rem;
    }}
    .post {{
      margin-bottom: 1.2rem;
      padding-bottom: 0.8rem;
      border-bottom: 1px solid #eee;
    }}
    .post h2 {{
      font-size: 1.15rem;
      margin: 0 0 0.2rem 0;
    }}
    .post a {{
      text-decoration: none;
    }}
    .post a:hover {{
      text-decoration: underline;
    }}
    .meta {{
      font-size: 0.85rem;
      color: #666;
    }}
    .tags a {{
      font-size: 0.8rem;
      margin-right: 0.3rem;
    }}
    footer {{
      margin-top: 2rem;
      font-size: 0.8rem;
      color: #888;
    }}
  </style>
</head>
<body>
  <h1>比較記事 一覧</h1>
{items_html}
  <footer>最終更新: {updated_at}</footer>
</body>
</html>
"""
    Path(INDEX_FILE).write_text(html, encoding="utf-8")
    print(f"Updated {INDEX_FILE}")


def generate_tag_pages(pages):
    # タグ → 記事の dict
    tags_map = defaultdict(list)
    for p in pages:
        for t in p["tags"]:
            tags_map[t].append(p)

    tags_dir = Path(TAGS_DIR)
    tags_dir.mkdir(exist_ok=True)

    for tag, tag_pages in tags_map.items():
        tag_pages.sort(key=lambda p: p["date"], reverse=True)
        items = []
        for p in tag_pages:
            items.append(
                f'''    <li><a href="/{p["url_path"]}">{p["title"]}</a> <span class="date">{p["date"]}</span></li>'''
            )
        items_html = "\n".join(items)

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>タグ: {tag} – compare-aything.com</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
  <h1>タグ: {tag}</h1>
  <ul>
{items_html}
  </ul>
  <p><a href="/">← 一覧に戻る</a></p>
</body>
</html>
"""
        out_path = tags_dir / f"{tag}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"Updated tag page {out_path}")


def generate_sitemap_xml(pages):
    urls = [f"  <url>\n    <loc>{BASE_URL}/</loc>\n  </url>"]

    # 記事 URL
    for p in pages:
        urls.append(f"  <url>\n    <loc>{p['url']}</loc>\n  </url>")

    # タグ URL
    tag_files = [f for f in Path(TAGS_DIR).glob("*.html")]
    for tf in tag_files:
        loc = f"{BASE_URL}/{TAGS_DIR}/{tf.name}"
        urls.append(f"  <url>\n    <loc>{loc}</loc>\n  </url>")

    body = "\n".join(urls)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""
    Path(SITEMAP_FILE).write_text(xml, encoding="utf-8")
    print(f"Updated {SITEMAP_FILE}")


def main():
    if not Path(PAGES_DIR).is_dir():
        print(f"ERROR: {PAGES_DIR} ディレクトリがありません。")
        return
    pages = collect_pages()
    print(f"Found {len(pages)} pages.")
    generate_index_html(pages)
    generate_tag_pages(pages)
    generate_sitemap_xml(pages)


if __name__ == "__main__":
    main()
