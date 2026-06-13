// Watch杯— 共通レンダリング
const WEEKDAYS = ["日","月","火","水","木","金","土"];
const FLAG = c => `https://flagcdn.com/${c}.svg`;
// 開催都市 → スタジアム名（2026年大会の16会場）
const STADIUMS = {
  "メキシコシティ":"エスタディオ・アステカ","グアダラハラ":"エスタディオ・アクロン","モンテレイ":"エスタディオBBVA",
  "トロント":"BMOフィールド","バンクーバー":"BCプレイス",
  "シアトル":"ルーメン・フィールド","サンフランシスコ":"リーバイス・スタジアム","ロサンゼルス":"SoFiスタジアム",
  "ダラス":"AT&Tスタジアム","ヒューストン":"NRGスタジアム","アトランタ":"メルセデス・ベンツ・スタジアム",
  "カンザスシティ":"アローヘッド・スタジアム","ボストン":"ジレット・スタジアム",
  "フィラデルフィア":"リンカーン・フィナンシャル・フィールド","ニューヨーク":"メットライフ・スタジアム","マイアミ":"ハードロック・スタジアム"
};
const venueLabel = city => city ? `🏟 ${city}${STADIUMS[city]?` · ${STADIUMS[city]}`:""}` : "";
const PILL_CLS = {"DAZN":"dazn","DAZN無料":"daznfree","NHK":"nhk","NHK BS":"nhkbs","日テレ":"ntv","フジ":"fuji","BSP4K":"bsp4k","BS4K":"bsp4k"};
const PILL_ICON = {
  dazn:'<svg width="11" height="11" viewBox="0 0 12 12" fill="none"><path d="M2 4 Q6 1.5 10 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M3.5 6 Q6 4.2 8.5 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="6" cy="8.4" r="1.2" fill="currentColor"/></svg>',
  tv:'<svg width="11" height="11" viewBox="0 0 12 12" fill="none"><rect x="1.5" y="2.5" width="9" height="6.5" rx="1" stroke="currentColor" stroke-width="1.3"/><path d="M4 11h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>'
};
function pillHTML(tv){
  const cls = PILL_CLS[tv] || "nhk";
  const icon = (cls==="dazn"||cls==="daznfree") ? PILL_ICON.dazn : PILL_ICON.tv;
  return `<span class="pill ${cls}">${icon}${tv}</span>`;
}
function matchState(m){
  const t = new Date(m.kick).getTime(), now = Date.now();
  if(now >= t && now < t + 2.25*3600*1000) return "live";
  if(now >= t) return "past";
  return "future";
}
function teamRow(t, sc){
  const flag = t.f ? `<img src="${FLAG(t.f)}" alt="${t.n}" loading="lazy">` : `<span class="ph">?</span>`;
  const score = sc!=null ? `<span style="margin-left:auto;font-family:var(--font-num);font-size:15px;font-weight:900;${sc.lose?"color:var(--ink-3)":""}">${sc.v}</span>` : "";
  return `<div class="mc-team">${flag}<span class="n" ${sc&&sc.lose?'style="color:var(--ink-3)"':""}>${t.n}</span>${t.r?`<span class="r">${t.r}</span>`:""}${score}</div>`;
}
function gcalURL(m){
  const s = new Date(m.kick), e = new Date(s.getTime()+2*3600*1000);
  const pad = n => String(n).padStart(2,"0");
  const u = d => d.getUTCFullYear()+pad(d.getUTCMonth()+1)+pad(d.getUTCDate())+"T"+pad(d.getUTCHours())+pad(d.getUTCMinutes())+"00Z";
  const p = new URLSearchParams({action:"TEMPLATE",
    text:`【W杯】${m.t[0].n} vs ${m.t[1].n}`,
    dates:`${u(s)}/${u(e)}`,
    details:`放送: ${m.tv.join(" / ")}｜${m.info}`,
  });
  return "https://calendar.google.com/calendar/render?"+p.toString();
}
function matchCardHTML(m, opts={}){
  const st = matchState(m);
  const barColor = m.bar==="var(--accent)" ? "var(--accent)" : m.bar;
  const lateBox = m.late ? `<div class="mc-late"><span class="d">${m.lateday}</span><span class="t">${m.late}</span></div>` : "";
  const liveBadge = st==="live" ? `<div class="mc-live">● LIVE</div>` : "";
  const time = m.kick.slice(11,16);
  const calBtn = opts.noCal ? "" : `<button class="mc-cal" data-cal="${m.id}" title="カレンダーに登録">📅 登録</button>`;
  const sc = m.score;
  const home = sc ? {v:sc[0], lose:sc[0]<sc[1]} : null;
  const away = sc ? {v:sc[1], lose:sc[1]<sc[0]} : null;
  const endBadge = sc ? `<div style="margin-top:4px;font-size:9px;font-weight:900;color:var(--ink-3);background:var(--bg-2);border-radius:4px;padding:2px 4px">試合終了</div>` : "";
  return `<a class="match-card${m.jp?" jp":""}${st==="past"?" past":""}" data-mid="${m.id}" href="match.html?id=${m.id}">
    <div class="bar" style="background:${barColor}"></div>
    <div class="mc-grid">
      <div class="mc-time">
        <div class="lbl">日本時間</div>
        <div class="t">${time}</div>
        ${st==="live" ? liveBadge : (sc ? endBadge : lateBox)}
      </div>
      <div class="mc-teams">
        ${teamRow(m.t[0], home)}
        ${teamRow(m.t[1], away)}
        <div class="mc-info"><span class="sq" style="background:${barColor}"></span><span class="txt">${m.info}</span></div>
      </div>
      <div class="mc-right">
        ${m.tv.map(pillHTML).join("")}
        ${calBtn}
      </div>
    </div>
  </a>`;
}
function bindCalButtons(root){
  (root||document).querySelectorAll("[data-cal]").forEach(b=>{
    b.onclick = e=>{
      e.preventDefault();   // カード全体のリンク遷移を止める
      e.stopPropagation();
      const m = MATCHES.find(x=>x.id===b.dataset.cal);
      window.open(gcalURL(m), "_blank");
    };
  });
}
// 日付ごとにグループ化して描画
function renderSchedule(el, matches, opts={}){
  const byDate = {};
  matches.forEach(m=>{
    const key = m.kick.slice(0,10);
    (byDate[key]=byDate[key]||[]).push(m);
  });
  const todayKey = new Date(Date.now()+9*3600*1000).toISOString().slice(0,10); // JST
  let nextMarked = false;
  let html = "";
  Object.keys(byDate).sort().forEach(key=>{
    const d = new Date(key+"T00:00:00+09:00");
    const mo = d.getMonth()+1, day = d.getDate(), w = WEEKDAYS[d.getDay()];
    const stage = STAGE_BADGE[`${mo}-${day}`];
    let badge = "";
    if(stage) badge = `<span class="stage gray">${stage}</span>`;
    if(!nextMarked && key >= todayKey){ badge += `<span class="stage">NEXT</span>`; nextMarked = true; }
    html += `<section data-date="${key}">
      <div class="datehead">
        <div class="d">${mo}.${day}</div><div class="w">${w}曜</div>${badge}
        <div class="rule"></div><div class="cnt">${byDate[key].length}試合</div>
      </div>
      <div class="mlist">${byDate[key].map(m=>matchCardHTML(m,opts)).join("")}</div>
    </section>`;
  });
  el.innerHTML = html || `<p style="text-align:center;color:var(--ink-3);font-weight:700;padding:40px 0">該当する試合がありません</p>`;
  bindCalButtons(el);
}
// 順位表（s: [試,勝,分,負,得失,勝点] — update_data.pyが自動更新）
function groupTableHTML(g, teams, opts={}){
  const rows = teams.map((t,i)=>{
    const s = t.s || [0,0,0,0,0,0];
    return `
    <tr class="${t.n==="日本"?"jprow":""}${i===1&&opts.qline?" qline":""}">
      <td>${i+1}</td>
      <td class="team"><img src="${FLAG(t.f)}" alt="">${t.n}</td>
      ${s.map(v=>`<td>${v}</td>`).join("")}
    </tr>`;}).join("");
  return `<div class="gtable" id="group-${g}">
    <div class="ghead"><span class="chip${g==="F"?" jp":""}">${g}</span><span class="t">グループ ${g}</span></div>
    <table>
      <thead><tr><th>#</th><th>チーム</th><th>試</th><th>勝</th><th>分</th><th>負</th><th>得失</th><th>勝点</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`;
}
// 順位表のチーム名を各国ページへのリンクにする（teams.js読込時のみ）
function linkifyStandings(root){
  if(typeof TEAMS === "undefined") return;
  const byName = {};
  Object.values(TEAMS).forEach(t=>byName[t.name]=t.code);
  (root||document).querySelectorAll(".gtable td.team").forEach(td=>{
    const name = td.textContent.trim();
    const code = byName[name];
    if(!code) return;
    const img = td.querySelector("img");
    td.innerHTML = `<a href="team.html?c=${code}" style="color:inherit;text-decoration:none">${img?img.outerHTML:""}${name} <span style="color:var(--ink-3);font-size:10px">›</span></a>`;
  });
}
// PR枠（参考サイトと同形式・景表法対応のPR表記つき）
// kind: "dazn" | "dmm"（省略時はdazn）
function prCardHTML(kind="dazn"){
  if(typeof AFF === "undefined") return "";
  const p = kind==="dmm"
    ? {url:AFF.dmmUrl, title:AFF.dmmTitle, text:AFF.dmmText, cta:AFF.dmmCta}
    : {url:AFF.daznUrl, title:AFF.daznTitle, text:AFF.daznText, cta:AFF.daznCta};
  return `<a class="match-card" href="${p.url}" target="_blank" rel="noopener sponsored"
    style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin:8px 0">
    <div style="min-width:0">
      <div style="font-size:14px;font-weight:900">${p.title}</div>
      <div style="font-size:12px;color:var(--ink-2);margin-top:2px">${p.text}
        <span style="font-size:9px;font-weight:800;color:var(--ink-3);letter-spacing:.08em;margin-left:6px">PR</span>
      </div>
    </div>
    <span style="flex-shrink:0;background:var(--ink-1);color:#fff;font-size:12px;font-weight:900;border-radius:8px;padding:10px 14px;white-space:nowrap">${p.cta}</span>
  </a>`;
}
// 日付セクションのN番目ごとにPR枠を差し込む（DAZN/DMMを交互に）
function insertPRCards(root, every=3){
  const secs = [...(root||document).querySelectorAll("section[data-date]")];
  let n = 0;
  secs.forEach((s,i)=>{
    if((i+1)%every===0) s.insertAdjacentHTML("afterend", prCardHTML(n++%2===0?"dazn":"dmm"));
  });
}
// ===== ニュース（news.js / update_news.pyが自動更新）=====
function newsListHTML(limit=6){
  if(typeof NEWS === "undefined" || !NEWS.length) return "";
  const items = NEWS.slice(0,limit).map(n=>`
    <a href="${n.url}" target="_blank" rel="noopener"
       style="display:block;padding:11px 2px;border-bottom:1px solid var(--line);text-decoration:none;color:inherit">
      <div style="font-size:13px;font-weight:800;line-height:1.5">${n.title}</div>
      <div style="font-size:10px;font-weight:700;color:var(--ink-3);margin-top:3px">${n.source}${n.date?` ・ ${n.date}`:""} ↗</div>
    </a>`).join("");
  return `<div class="sec-label">NEWS</div>
    <h2 class="pagehead" style="margin-top:0;font-size:18px">W杯 直前情報・速報
      <span style="font-size:10px;color:var(--ink-3);font-weight:700">（${typeof NEWS_UPDATED!=="undefined"?NEWS_UPDATED:""} 更新）</span></h2>
    <div class="card" style="padding:4px 14px">${items}</div>`;
}
// ===== 突破条件の自動計算 =====
// 順位表の勝点＋未消化試合を全列挙して各チームの状態を判定（得失点差は未考慮）
function qualifyGroup(g){
  if(typeof GROUPS === "undefined" || !GROUPS[g]) return [];
  const teams = GROUPS[g];
  const pts = teams.map(t=>(t.s||[0,0,0,0,0,0])[5]);
  const played = teams.reduce((a,t)=>a+(t.s||[0])[0],0)/2;
  const gms = MATCHES
    .filter(m=>m.info.startsWith("グループ"+g))
    .sort((a,b)=>a.kick.localeCompare(b.kick));
  const remaining = gms.slice(played).map(m=>[
    teams.findIndex(t=>t.n===m.t[0].n),
    teams.findIndex(t=>t.n===m.t[1].n),
  ]).filter(p=>p[0]>=0&&p[1]>=0);
  const n = remaining.length;
  // 各チームの best/worst 順位と「全勝した場合のworst順位」を全列挙で求める
  const best = [4,4,4,4], worst = [1,1,1,1], winoutWorst = [4,4,4,4];
  const total = Math.pow(3,n);
  for(let mask=0; mask<total; mask++){
    const p = [...pts];
    let m = mask;
    const res = [];
    for(let i=0;i<n;i++){ res.push(m%3); m=Math.floor(m/3); }
    res.forEach((r,i)=>{
      const [h,a] = remaining[i];
      if(r===0) p[h]+=3; else if(r===1) p[a]+=3; else {p[h]++;p[a]++;}
    });
    for(let t=0;t<4;t++){
      const optimistic = 1 + p.filter((x,j)=>j!==t && x>p[t]).length;       // 同点は上扱い
      const pessimistic = 1 + p.filter((x,j)=>j!==t && x>=p[t]).length;     // 同点は下扱い
      if(optimistic < best[t]) best[t] = optimistic;
      if(pessimistic > worst[t]) worst[t] = pessimistic;
    }
  }
  // 「残り全勝した場合」の最悪順位（＝自力判定）
  for(let t=0;t<4;t++){
    let w = 1;
    for(let mask=0; mask<total; mask++){
      const p = [...pts];
      let m = mask; const res=[];
      for(let i=0;i<n;i++){ res.push(m%3); m=Math.floor(m/3); }
      let skip=false;
      res.forEach((r,i)=>{
        const [h,a]=remaining[i];
        if(h===t&&r!==0) skip=true;
        if(a===t&&r!==1) skip=true;
      });
      if(skip) continue;
      res.forEach((r,i)=>{
        const [h,a]=remaining[i];
        if(r===0) p[h]+=3; else if(r===1) p[a]+=3; else {p[h]++;p[a]++;}
      });
      const pess = 1 + p.filter((x,j)=>j!==t && x>=p[t]).length;
      if(pess>w) w=pess;
    }
    winoutWorst[t] = n===0 ? worst[t] : w;
  }
  return teams.map((t,i)=>{
    let label, cls;
    if(worst[i]<=2){ label="突破確定"; cls="go"; }
    else if(best[i]>3){ label="敗退確定"; cls="out"; }
    else if(best[i]===3){ label="3位進出に望み"; cls="hope"; }
    else if(winoutWorst[i]<=2){ label="自力突破圏"; cls="self"; }
    else { label="突破可能性あり（他力）"; cls="hope"; }
    return {n:t.n, f:t.f, label, cls, best:best[i], worst:worst[i]};
  });
}
function qualifyChipsHTML(g){
  const qs = qualifyGroup(g);
  if(!qs.length) return "";
  const color = {go:"#0e7a3d", self:"#1d4ed8", hope:"#b45309", out:"#8a8c95"};
  return `<div style="display:flex;flex-wrap:wrap;gap:6px;padding:10px 14px;border-top:1px solid var(--line)">
    ${qs.map(q=>`<span style="display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:800;border-radius:999px;padding:3px 9px;background:${color[q.cls]}14;color:${color[q.cls]};border:1px solid ${color[q.cls]}33">
      <img src="${FLAG(q.f)}" style="width:12px;height:12px;border-radius:50%" alt="">${q.n}: ${q.label}</span>`).join("")}
  </div>`;
}
// 共通フッタ＆ナビ
function renderChrome(active){
  document.querySelectorAll(".desktop-nav a, .bottom-nav a").forEach(a=>{
    a.classList.toggle("active", a.dataset.nav===active);
  });
}
const NAV_HTML = `
<header>
  <div class="wrap">
    <a class="logo" href="index.html">
      <span class="ball">⚽</span>
      <span><span class="t1">Watch<span>杯</span></span><br><span class="t2">W杯2026 観戦ガイド</span></span>
    </a>
    <nav class="desktop-nav">
      <a href="index.html" data-nav="top">トップ</a>
      <a href="schedule.html" data-nav="schedule">全試合日程</a>
      <a href="bracket.html" data-nav="bracket">優勝予想</a>
      <a href="japan.html" data-nav="japan">日本代表</a>
      <a href="standings.html" data-nav="standings">順位表</a>
      <a href="shindan.html" data-nav="shindan">視聴診断</a>
    </nav>
  </div>
</header>`;
const FOOT_HTML = `
<footer>
  <div class="links">
    <a href="legal.html#privacy">プライバシーポリシー</a><span>｜</span>
    <a href="legal.html#about">運営者情報</a><span>｜</span>
    <a href="legal.html#disclaimer">免責事項</a><span>｜</span>
    <a href="legal.html#contact">お問い合わせ</a><span>｜</span>
    <a href="legal.html#pwa" style="opacity:.6">アプリとして使う</a><span>｜</span>
    <a href="sns.html" style="opacity:.6">SNS素材</a>
  </div>
  <div class="copy">© 2026 Watch杯 · 非公式ファンサイトです。最新情報は各公式サイトをご確認ください。<br>
  <span style="opacity:.7">データ更新日: <span id="dataUpdated"></span> ｜ 当サイトはアフィリエイト広告（PR）を利用しています</span></div>
</footer>
<nav class="bottom-nav">
  <a href="index.html" data-nav="top"><svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 9v11h14V9"/></svg>トップ</a>
  <a href="schedule.html" data-nav="schedule"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>日程</a>
  <a href="bracket.html" data-nav="bracket"><svg viewBox="0 0 24 24"><path d="M6 3h12v4a6 6 0 01-12 0V3z"/><path d="M6 5H3v1a4 4 0 004 4M18 5h3v1a4 4 0 01-4 4"/><path d="M12 13v4M8 21h8M10 17h4v4h-4z"/></svg>予想</a>
  <a href="japan.html" data-nav="japan"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/></svg>日本代表</a>
  <a href="standings.html" data-nav="standings"><svg viewBox="0 0 24 24"><path d="M5 20V12M12 20V6M19 20v-9"/></svg>順位表</a>
  <a href="shindan.html" data-nav="shindan"><svg viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>視聴診断</a>
</nav>`;
function injectChrome(active){
  document.body.insertAdjacentHTML("afterbegin", NAV_HTML);
  document.body.insertAdjacentHTML("beforeend", FOOT_HTML);
  renderChrome(active);
  const du = document.getElementById("dataUpdated");
  if(du && typeof DATA_UPDATED !== "undefined") du.textContent = DATA_UPDATED;
  // PWA: サービスワーカー登録（https or localhostのみ動作）
  if("serviceWorker" in navigator){
    navigator.serviceWorker.register("sw.js").catch(()=>{});
  }
}
