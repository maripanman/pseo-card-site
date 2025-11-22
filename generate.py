import csv
from pathlib import Path

# 公開後にあなたのドメインに書き換える
BASE_URL = "https://example.pages.dev"

root = Path(__file__).parent
csv_path = root / "pages.csv"
template_path = root / "template.html"

# 出力先（今回はリポジトリのルートにそのまま出力）
output_dir = root

template = template_path.read_text(encoding="utf-8")

pages = []

with csv_path.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        slug = row["slug"]
        html = template
        # {{key}} を row[key] で置換
        for key, value in row.items():
            placeholder = f"{{{{{key}}}}}"
            html = html.replace(placeholder, value or "")

        out_path = output_dir / f"{slug}.html"
        out_path.write_text(html, encoding="utf-8")
        pages.append({
            "slug": slug,
            "title": row["title"]
        })

# index.html を作る
index_items = "\n".join(
    f'<li><a href="/{p["slug"]}.html">{p["title"]}</a></li>'
    for p in pages
)

index_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>カードポイントLab｜トップ</title>
  <meta name="description" content="クレジットカードとポイントの基礎知識をわかりやすく整理するサイトです。" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <h1>カードポイントLab</h1>
  <p>クレジットカード選びとポイント活用の情報をまとめたデータベース的サイトです。</p>
  <ul>
    {index_items}
  </ul>
</body>
</html>
"""

(root / "index.html").write_text(index_html, encoding="utf-8")

# sitemap.xml を作る
sitemap_entries = "\n".join(
    f"  <url><loc>{BASE_URL}/{p['slug']}.html</loc></url>"
    for p in pages
)
sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{BASE_URL}/index.html</loc></url>
{sitemap_entries}
</urlset>
"""

(root / "sitemap.xml").write_text(sitemap, encoding="utf-8")

print(f"{len(pages)} ページを生成しました。")