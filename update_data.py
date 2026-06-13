#!/usr/bin/env python3
"""
W杯2026サイトのデータ更新スクリプト（無料・依存ライブラリなし）

worldcup2026-japan.com から最新の試合日程・結果・順位表を取得して
data.js を再生成する。

使い方:
  python3 update_data.py        # data.js を更新
  python3 update_data.py --dry  # 取得結果を表示するだけ（書き込みなし）
"""
import re, json, sys, urllib.request, datetime, os

BASE = "https://worldcup2026-japan.com"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")

GROUP_ORDER = {
    "A": ["メキシコ", "南アフリカ", "韓国", "チェコ"],
    "B": ["カナダ", "ボスニア・ヘルツェゴビナ", "スイス", "カタール"],
    "C": ["ブラジル", "モロッコ", "ハイチ", "スコットランド"],
    "D": ["アメリカ", "パラグアイ", "オーストラリア", "トルコ"],
    "E": ["ドイツ", "キュラソー", "コートジボワール", "エクアドル"],
    "F": ["オランダ", "日本", "スウェーデン", "チュニジア"],
    "G": ["ベルギー", "エジプト", "イラン", "ニュージーランド"],
    "H": ["スペイン", "カーボベルデ", "サウジアラビア", "ウルグアイ"],
    "I": ["フランス", "セネガル", "イラク", "ノルウェー"],
    "J": ["アルゼンチン", "アルジェリア", "オーストリア", "ヨルダン"],
    "K": ["ポルトガル", "DRコンゴ", "ウズベキスタン", "コロンビア"],
    "L": ["イングランド", "クロアチア", "ガーナ", "パナマ"],
}
STAGE_BADGE = {
    "6-29": "決勝T 1回戦", "6-30": "決勝T 1回戦", "7-1": "決勝T 1回戦",
    "7-2": "決勝T 1回戦", "7-3": "決勝T 1回戦", "7-4": "決勝T 1回戦",
    "7-5": "決勝T 2回戦", "7-6": "決勝T 2回戦", "7-7": "決勝T 2回戦", "7-8": "決勝T 2回戦",
    "7-10": "準々決勝", "7-11": "準々決勝", "7-12": "準々決勝",
    "7-15": "準決勝", "7-16": "準決勝", "7-19": "3位決定戦", "7-20": "決勝",
}

def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

def clean(t):
    return re.sub(r"<!-- -->", "", t)

def parse_schedule(html):
    date_iter = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(
        r'font-size:34px;font-weight:900[^>]*>(\d+)<!-- -->\.<!-- -->(\d+)</div>', html)]
    starts = [m.start() for m in re.finditer(r'<a class="match-card"', html)]
    out = []
    for i, s in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else len(html)
        c = html[s:nxt]
        idm = re.search(r'href="/match/(m[\w]+)"', c[:400])
        if not idm:
            continue  # PR広告カードはスキップ
        mid = idm.group(1)
        time = re.search(r'font-size:20px;font-weight:900[^>]*>([\d:]+)<', c)
        late = re.search(r'font-size:12px;font-weight:900;color:var\(--accent\)[^>]*>([\d:]+)<', c)
        lateday = re.search(r'font-size:8\.5px[^>]*>((?:[^<]|<!-- -->)+)<', c)
        names = re.findall(r'font-size:14px;font-weight:700;color:var\(--ink-1\)[^>]*>((?:[^<]|<!-- -->)+)<', c)
        flags = re.findall(r'flagcdn\.com/([a-z\-]+)\.svg', c)
        ranks = re.findall(r'font-size:10px;font-weight:800;color:var\(--ink-3\);flex-shrink:0">(\d+)<', c)
        # スコア表記（終了試合）: "2 - 1" のような形式があれば拾う
        score = re.search(r'>(\d+)\s*-\s*(\d+)<', c)
        grpcity = re.search(r'font-size:9px;font-weight:800;color:var\(--ink-3\);letter-spacing:\.04em[^>]*>((?:[^<]|<!-- -->)+)<', c)
        bar = re.search(r'width:3px;background:(#[0-9a-fA-F]+|var\(--accent\))', c)
        bcs = re.findall(r'(DAZN無料|DAZN|NHK BS|NHK|日テレ|フジ|BSP4K|BS4K)', c)
        tv = []
        [tv.append(b) for b in bcs if b not in tv]
        d = [dd for dd in date_iter if dd[0] < s]
        mo, day = int(d[-1][1]), int(d[-1][2])
        if not time or len(names) < 2:
            print(f"  ⚠ {mid}: データ不完全のためスキップ", file=sys.stderr)
            continue
        out.append({
            "id": mid,
            "kick": f"2026-{mo:02d}-{day:02d}T{time.group(1)}:00+09:00",
            "late": late.group(1) if late else None,
            "lateday": clean(lateday.group(1)) if lateday else None,
            "t": [{"n": clean(n),
                   "f": (flags[j] if j < len(flags) else None),
                   "r": (ranks[j] if j < len(ranks) else None)}
                  for j, n in enumerate(names[:2])],
            "score": [int(score.group(1)), int(score.group(2))] if score else None,
            "info": clean(grpcity.group(1)) if grpcity else "",
            "bar": bar.group(1) if bar else "#8a8c95",
            "tv": tv,
            "jp": mid.startswith("m_jp"),
        })
    return out

def parse_standings(html, flagmap):
    """順位表ページから各グループの順位・成績を取得"""
    groups = {}
    # 「グループ<!-- -->A」見出しで分割
    secs = re.split(r'グループ<!-- -->([A-L])</div>', html)
    for i in range(1, len(secs) - 1, 2):
        g, body = secs[i], secs[i + 1]
        if g in groups:
            continue
        teams = []
        for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', body, re.S):
            name = re.search(r'class="team-name"[^>]*>([^<]+)<', tr)
            if not name:
                continue
            flag = re.search(r'flagcdn\.com/([a-z\-]+)\.svg', tr)
            nums = re.findall(r'<td[^>]*>\s*(-?\d+)\s*</td>', tr)
            stats = [int(x) for x in nums[-6:]] if len(nums) >= 6 else [0] * 6
            teams.append({"n": name.group(1),
                          "f": flag.group(1) if flag else flagmap.get(name.group(1)),
                          "s": stats})
            if len(teams) == 4:
                break
        if len(teams) == 4:
            groups[g] = teams
    return groups

def main():
    dry = "--dry" in sys.argv
    print("📥 全試合日程を取得中…")
    matches = parse_schedule(fetch("/schedule/"))
    print(f"   {len(matches)}試合 取得")
    if len(matches) < 100:
        print("❌ 試合数が少なすぎる（サイト構造が変わった可能性）。data.jsは更新しません。")
        sys.exit(1)

    flagmap = {}
    for m in matches:
        for t in m["t"]:
            if t["f"]:
                flagmap[t["n"]] = t["f"]

    print("📥 順位表を取得中…")
    try:
        groups = parse_standings(fetch("/standings/"), flagmap)
        print(f"   {len(groups)}グループ 取得")
    except Exception as e:
        print(f"   ⚠ 順位表の取得失敗（{e}）→ 既定の組み合わせで0埋め")
        groups = {}
    # 取れなかったグループは既定順・0埋め
    for g, names in GROUP_ORDER.items():
        if g not in groups or len(groups[g]) != 4:
            groups[g] = [{"n": n, "f": flagmap.get(n), "s": [0] * 6} for n in names]

    today = datetime.date.today().isoformat()
    js = f"// 全104試合データ（{today} 自動更新 / update_data.py）\n"
    js += "const MATCHES = " + json.dumps(matches, ensure_ascii=False) + ";\n"
    js += "const STAGE_BADGE = " + json.dumps(STAGE_BADGE, ensure_ascii=False) + ";\n"
    js += "const GROUPS = " + json.dumps(groups, ensure_ascii=False) + ";\n"
    js += f'const DATA_UPDATED = "{today}";\n'

    if dry:
        print(js[:800] + "\n…(dry run・書き込みなし)")
    else:
        open(OUT, "w").write(js)
        print(f"✅ {OUT} を更新（{len(matches)}試合・{today}）")

if __name__ == "__main__":
    main()
