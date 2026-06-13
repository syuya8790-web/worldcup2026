#!/usr/bin/env python3
"""
出場48カ国データ更新スクリプト（無料・依存ライブラリなし）

worldcup2026-japan.com の /teams と /team/<code> 全48ページから
国情報・代表メンバー（スカッド）を取得して teams.js を生成する。

スカッドはメンバー変更時のみ更新が必要なので、update_data.py（毎日）とは
別スクリプトにしてある。使い方:
  python3 update_teams.py
"""
import re, json, sys, time, urllib.request, datetime, os

BASE = "https://worldcup2026-japan.com"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teams.js")

def fetch(path, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))  # 2秒, 4秒…と待ってリトライ
    raise last

def clean(t):
    return re.sub(r"<!-- -->", "", t).replace("&quot;", '"').replace("&amp;", "&").strip()

def text_after(html, label, maxlen=200):
    """「<div>ラベル</div><div>値</div>」形式から値を取る"""
    m = re.search(re.escape(label) + r'</div><div[^>]*>((?:[^<]|<!-- -->)+)<', html)
    return clean(m.group(1)) if m else None

def parse_team(code, html):
    title = re.search(r'<title>([^｜<]+)｜グループ([A-L])', html)
    name = clean(title.group(1)) if title else code.upper()
    group = title.group(2) if title else None
    rank = re.search(r'FIFA RANK</div><div[^>]*>(\d+)', html) or \
           re.search(r'FIFA RANK.{0,200}?>(\d+)<', html, re.S)
    flag = re.search(r'flagcdn\.com/([a-z\-]+)\.svg', html)
    nickname = text_after(html, "愛称")
    caps = re.search(r'出場回数</div><div[^>]*><span[^>]*>(\d+)', html)
    desc = re.search(r'出場回数.*?<p[^>]*>((?:[^<]|<!-- -->)+)</p>', html, re.S)
    # スカッド: ポジション見出し(GK/DF/MF/FW)ごとに選手を割り当て
    squad = []
    sq = re.search(r'SQUAD(.*?)(?:DMM|HOW TO WATCH|</main|$)', html, re.S)
    body = sq.group(1) if sq else html
    pos_iter = [(m.start(), m.group(1)) for m in re.finditer(r'>(GK|DF|MF|FW)</div>', body)]
    for pm in re.finditer(
        r'class="squad-player-info">.*?squad-mark[^>]*>\s*([★◇]?)\s*</span>'
        r'<span class="squad-player-name"><span[^>]*>(\d+)</span>((?:[^<]|<!-- -->)+)</span>'
        r'<span class="squad-player-club">([^<]*)</span>', body, re.S):
        prior = [p for p in pos_iter if p[0] < pm.start()]
        squad.append({
            "pos": prior[-1][1] if prior else "?",
            "mark": pm.group(1) or "",
            "no": int(pm.group(2)),
            "name": clean(pm.group(3)),
            "club": clean(pm.group(4)),
        })
    return {
        "code": code, "name": name, "group": group,
        "rank": int(rank.group(1)) if rank else None,
        "flag": flag.group(1) if flag else None,
        "nickname": nickname,
        "caps": int(caps.group(1)) if caps else None,
        "desc": clean(desc.group(1)) if desc else "",
        "squad": squad,
    }

def main():
    print("📥 出場国一覧を取得中…")
    codes = []
    for c in re.findall(r'href="/team/([a-z]+)"', fetch("/teams")):
        if c not in codes:
            codes.append(c)
    print(f"   {len(codes)}カ国")
    teams = {}
    for i, code in enumerate(codes):
        try:
            t = parse_team(code, fetch(f"/team/{code}"))
            teams[code] = t
            print(f"   [{i+1}/{len(codes)}] {t['name']}: 選手{len(t['squad'])}名")
        except Exception as e:
            print(f"   ⚠ {code} 取得失敗: {e}", file=sys.stderr)
        time.sleep(0.4)  # 行儀よく
    if len(teams) < 40:
        print("❌ 取得数が少なすぎる。teams.jsは更新しません。")
        sys.exit(1)
    today = datetime.date.today().isoformat()
    js = f"// 出場48カ国データ（{today} 自動更新 / update_teams.py）\n"
    js += "const TEAMS = " + json.dumps(teams, ensure_ascii=False) + ";\n"
    open(OUT, "w").write(js)
    total = sum(len(t["squad"]) for t in teams.values())
    print(f"✅ {OUT} を更新（{len(teams)}カ国・選手{total}名）")

if __name__ == "__main__":
    main()
