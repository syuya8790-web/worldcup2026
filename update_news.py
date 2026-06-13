#!/usr/bin/env python3
"""
W杯関連ニュース更新スクリプト（無料・Google News RSS使用）

「W杯に直結する情報」（怪我・メンバー変更・試合結果速報など）を
Google News RSSから取得して news.js を生成する。APIキー不要。

使い方:
  python3 update_news.py
"""
import re, json, urllib.request, urllib.parse, datetime, os
from email.utils import parsedate_to_datetime

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news.js")

QUERIES = [
    "W杯 日本代表",          # 日本代表の動向（怪我・メンバー・速報）
    "ワールドカップ 2026 速報",
]
MAX_ITEMS = 10
# ノイズ除去: W杯と関係薄い記事を弾くキーワード
NG_WORDS = ["バレーボール", "ラグビー", "野球", "バスケ", "卓球"]

def fetch_rss(query):
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(query)
           + "&hl=ja&gl=JP&ceid=JP:ja")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read()

def unesc(t):
    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'"), ("&apos;", "'")]:
        t = t.replace(a, b)
    return t.strip()

def parse_items(xml_bytes):
    """expatが無い環境でも動くよう正規表現でRSSをパース"""
    xml = xml_bytes.decode("utf-8", errors="ignore")
    out = []
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
        def tag(name):
            m = re.search(rf"<{name}[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{name}>",
                          block, re.S)
            return unesc(m.group(1)) if m else ""
        title = tag("title")
        link = tag("link")
        pub = tag("pubDate")
        source = tag("source")
        # 「タイトル - メディア名」形式ならメディア名を分離
        if not source and " - " in title:
            title, source = title.rsplit(" - ", 1)
        try:
            dt = parsedate_to_datetime(pub).astimezone(
                datetime.timezone(datetime.timedelta(hours=9)))
            date = dt.strftime("%m/%d %H:%M")
            sort = dt.isoformat()
        except Exception:
            date, sort = "", ""
        if any(ng in title for ng in NG_WORDS):
            continue
        out.append({"title": title, "url": link, "source": source,
                    "date": date, "sort": sort})
    return out

def main():
    seen, items = set(), []
    for q in QUERIES:
        print(f"📥 ニュース取得: {q}")
        try:
            for it in parse_items(fetch_rss(q)):
                key = it["title"][:30]
                if key in seen:
                    continue
                seen.add(key)
                items.append(it)
        except Exception as e:
            print(f"   ⚠ 取得失敗: {e}")
    items.sort(key=lambda x: x["sort"], reverse=True)
    items = items[:MAX_ITEMS]
    for it in items:
        it.pop("sort", None)
    if not items:
        print("❌ 0件。news.jsは更新しません。")
        return
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    js = f"// W杯関連ニュース（{today} 自動更新 / update_news.py）\n"
    js += "const NEWS = " + json.dumps(items, ensure_ascii=False) + ";\n"
    js += f'const NEWS_UPDATED = "{today}";\n'
    open(OUT, "w").write(js)
    print(f"✅ {OUT} を更新（{len(items)}件）")
    for it in items[:5]:
        print(f"   ・{it['date']} {it['title'][:40]}")

if __name__ == "__main__":
    main()
