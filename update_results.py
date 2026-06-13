#!/usr/bin/env python3
"""
試合結果・順位表をWikipedia（英語版）から取得して data.js に上書きするスクリプト。

参考サイト（worldcup2026-japan.com）は結果反映が遅いため、
試合結果と順位表はWikipediaを正とする。Wikipediaは試合後数分で更新される。

必ず update_data.py の後に実行すること（data.jsを上書き加工するため）。
  python3 update_data.py && python3 update_results.py
"""
import re, json, sys, time, urllib.request, datetime, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")
WIKI = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_"

EN2JA = {
    "Mexico": "メキシコ", "South Africa": "南アフリカ", "South Korea": "韓国",
    "Czech Republic": "チェコ", "Czechia": "チェコ",
    "Canada": "カナダ", "Bosnia and Herzegovina": "ボスニア・ヘルツェゴビナ",
    "Switzerland": "スイス", "Qatar": "カタール",
    "Brazil": "ブラジル", "Morocco": "モロッコ", "Haiti": "ハイチ", "Scotland": "スコットランド",
    "United States": "アメリカ", "Paraguay": "パラグアイ", "Australia": "オーストラリア",
    "Turkey": "トルコ", "Türkiye": "トルコ",
    "Germany": "ドイツ", "Curaçao": "キュラソー", "Ivory Coast": "コートジボワール", "Ecuador": "エクアドル",
    "Netherlands": "オランダ", "Japan": "日本", "Sweden": "スウェーデン", "Tunisia": "チュニジア",
    "Belgium": "ベルギー", "Egypt": "エジプト", "Iran": "イラン", "New Zealand": "ニュージーランド",
    "Spain": "スペイン", "Cape Verde": "カーボベルデ", "Saudi Arabia": "サウジアラビア", "Uruguay": "ウルグアイ",
    "France": "フランス", "Senegal": "セネガル", "Iraq": "イラク", "Norway": "ノルウェー",
    "Argentina": "アルゼンチン", "Algeria": "アルジェリア", "Austria": "オーストリア", "Jordan": "ヨルダン",
    "Portugal": "ポルトガル", "DR Congo": "DRコンゴ", "Uzbekistan": "ウズベキスタン", "Colombia": "コロンビア",
    "England": "イングランド", "Croatia": "クロアチア", "Ghana": "ガーナ", "Panama": "パナマ",
}

def fetch(url, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (watch-hai data bot)"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last

# 国によって "national football team" / "men's national soccer team" 等と表記が揺れる
# アポストロフィは &#39; にエンティティ化されている場合がある
TEAM_TITLE = r'title="([^"]+?)(?: men(?:&#39;|\x27)s| women(?:&#39;|\x27)s)? national (?:football|soccer) team"'

def parse_scores(html):
    """footballboxから終了/進行中試合のスコアを抽出 → [(homeJA, hs, as_, awayJA)]"""
    out = []
    for box in html.split('class="footballbox"')[1:]:
        box = box[:4000]  # 1ボックス分に制限（次のボックスを跨がない保険）
        home = re.search(r'class="fhome"[^>]*>.*?' + TEAM_TITLE, box, re.S)
        score = re.search(r'class="fscore"[^>]*>(?:<a[^>]*>)?\s*(\d+)\s*–\s*(\d+)', box)
        away = re.search(r'class="faway"[^>]*>.*?' + TEAM_TITLE, box, re.S)
        if not (home and score and away):
            continue  # 未開催（fscoreが "Match 25" 等）はスキップ
        h, a = EN2JA.get(home.group(1)), EN2JA.get(away.group(1))
        if h and a:
            out.append((h, int(score.group(1)), int(score.group(2)), a))
    return out

def parse_standings(html):
    """Pldを含む順位表テーブルから [(JA名, [試,勝,分,負,得失,勝点])] を順位順に"""
    i = html.find(">Pld<")
    if i < 0:
        return []
    # テーブル終端まで
    end = html.find("</table>", i)
    seg = html[i:end]
    out = []
    for tr in seg.split("<tr")[1:]:
        tm = re.search(TEAM_TITLE, tr)
        if not tm:
            continue
        ja = EN2JA.get(tm.group(1))
        if not ja:
            continue
        # マイナスは − や &#8722; &minus; にエンティティ化される場合がある
        nums = re.findall(r'<td[^>]*>\s*((?:&#8722;|&minus;|[+\-−])?\d+)\s*<', tr)
        if len(nums) < 8:
            continue
        # 行頭に順位番号のtdが入る場合があるため、末尾8個（Pld W D L GF GA GD Pts）を採用
        pld, w, d, l, gf, ga, gd, pts = nums[-8:]
        gd = int(gd.replace("&#8722;", "-").replace("&minus;", "-").replace("−", "-").replace("+", ""))
        out.append((ja, [int(pld), int(w), int(d), int(l), gd, int(pts)]))
    return out

def main():
    # data.js 読み込み
    src = open(OUT).read()
    matches = json.loads(re.search(r'const MATCHES = (\[.*?\]);\n', src, re.S).group(1))
    groups = json.loads(re.search(r'const GROUPS = (\{.*?\});\n', src, re.S).group(1))

    flagmap = {}
    for g, ts in groups.items():
        for t in ts:
            flagmap[t["n"]] = t["f"]

    score_count, stand_count = 0, 0
    for g in "ABCDEFGHIJKL":
        try:
            html = fetch(WIKI + g)
        except Exception as e:
            print(f"⚠ グループ{g} 取得失敗: {e}", file=sys.stderr)
            continue
        # スコア反映
        for h, hs, as_, a in parse_scores(html):
            for m in matches:
                if not m["info"].startswith("グループ" + g):
                    continue
                names = [t["n"] for t in m["t"]]
                if set(names) == {h, a}:
                    m["score"] = [hs, as_] if names[0] == h else [as_, hs]
                    score_count += 1
        # 順位表反映（Wikipediaの順位をそのまま採用）
        rows = parse_standings(html)
        if len(rows) == 4:
            groups[g] = [{"n": ja, "f": flagmap.get(ja), "s": s} for ja, s in rows]
            stand_count += 1
        else:
            print(f"  ⚠ グループ{g}: 順位表パース不可（{len(rows)}行）→ 既存データ維持", file=sys.stderr)
        time.sleep(0.3)

    today = datetime.date.today().isoformat()
    src = re.sub(r'const MATCHES = \[.*?\];\n',
                 "const MATCHES = " + json.dumps(matches, ensure_ascii=False) + ";\n", src, flags=re.S)
    src = re.sub(r'const GROUPS = \{.*?\};\n',
                 "const GROUPS = " + json.dumps(groups, ensure_ascii=False) + ";\n", src, flags=re.S)
    src = re.sub(r'const DATA_UPDATED = "[^"]*";',
                 f'const DATA_UPDATED = "{today}";', src)
    open(OUT, "w").write(src)
    print(f"✅ Wikipedia結果を反映: スコア{score_count}試合 / 順位表{stand_count}グループ")

if __name__ == "__main__":
    main()
