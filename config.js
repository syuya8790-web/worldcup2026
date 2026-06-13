// ============================================
// マネタイズ設定（update_data.py等では上書きされない）
// ============================================
// ASP（A8.net / バリューコマース / felmat / DMMアフィリエイト等）で
// 提携承認が下りたら、各URLをアフィリエイトリンクに差し替える。
// 差し替えるのはこのファイルだけでOK。全ページに反映される。
// 機能フラグ
const FEATURES = {
  qualify: false,  // 突破条件の自動表示。グループ最終節が近づいたら(6/24頃) true にする
};

const AFF = {
  daznUrl: "https://www.dazn.com/ja-JP/welcome",  // ← DAZNアフィリンクに差し替え
  daznTitle: "DAZN公式サイト",
  daznText: "W杯2026 全104試合をライブ配信。日本戦は無料で見られる。",
  daznCta: "キャンペーンを確認",

  dmmUrl: "https://premium.dmm.com/dazn/",        // ← DMM×DAZNホーダイのアフィリンクに差し替え
  dmmTitle: "DMM×DAZNホーダイ",
  dmmText: "DAZNとDMMプレミアムのセットプラン。単体契約より月額がお得。",
  dmmCta: "公式サイトで確認",
};
