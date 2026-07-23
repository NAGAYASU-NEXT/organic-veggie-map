# 百年の春 有機野菜マップ

百年の春が使わせていただいている有機野菜の生産者さんと、お野菜の購入できるお店をまとめたA4印刷用ページ・スマホ用ページを生成するプロジェクトです。

これまでチャットで直接HTMLを編集していましたが、今後お店や生産者さんが増えていくことを見込み、
**データ（data.json）とデザイン（templates/）を分離** した構成に作り直しました。
今後は基本的に `data.json` を編集して `python3 build.py` を実行するだけで、
印刷用PDF・印刷用HTML・スマホ用HTMLの3つが自動で更新されます。

## できること

- `output/map.html` … A4印刷用ページ（このHTMLをブラウザで開いて印刷、またはPDFを直接使用）
- `output/map.pdf`  … 上記から生成したA4印刷用PDF
- `output/map_mobile.html` … スマホでそのまま開ける縦スクロールページ

3つとも同じ `data.json` から生成されるので、**店舗の並び順・地図のピン番号・生産者さんの取扱店番号が自動的に一致します**
（これまで手作業で数字がズレてしまっていた問題が起きなくなります）。

## セットアップ

```bash
pip install jinja2 weasyprint
```

## 使い方

### 1. お店や生産者さんを追加・修正する

`data.json` を編集します。主なセクションは次の通りです。

```jsonc
{
  "restaurant": { ... },      // 百年の春自体の情報・地図上のマーカー位置
  "header": { ... },          // ページ上部の見出し文言
  "areas": [ ... ],           // エリア（臼杵市・大分市・豊後大野市）の定義
  "stores": [                 // お店の一覧（★ここに追加するのが一番多い作業）
    {
      "number": 1,             // 表示番号（地図のピンと一覧の番号が連動します）
      "area": "usuki",         // "usuki" / "oita" / "bungo" のいずれか
      "name": "なずな",
      "address": "臼杵市野津町落谷2181-1",
      "map_url": "https://www.google.com/maps/search/?api=1&query=...",
      "hp_url": "https://...",           // なければ null
      "producers": [                     // このお店で買える生産者さん
        { "name": "なずな農園", "self": true }   // "self": このお店＝生産者直売のとき
      ],
      "pin": { "cx": 438, "cy": 368 },   // 地図上のピン座標（下記「地図の座標」参照）
      "highlight": true                 // 目立たせたい店舗（任意、なずなのみtrue）
    }
  ],
  "producers": [               // 生産者さん一覧（PDF右側・エクセルの記載順）
    { "name": "槌本農園", "url": "https://..." }
  ],
  "producers_pending": { ... },// まだ販売店が決まっていない生産者さん（西森ゆうじん農場）
  "markets": [ ... ],          // 定期マルシェ情報
  "bottom_note": "..."
}
```

**生産者さんの「取扱店」番号は `build.py` が `stores[].producers[].name` を見て自動計算します。**
`data.json` 側で手入力する必要はありません。

### 2. 生成する

```bash
python3 build.py
```

`output/` フォルダに3ファイルが書き出されます。

### 3. 地図の座標について

地図は実在の緯度経度からGoogleマップ上の相対位置を計算し、SVGの座標（`pin.cx` / `pin.cy`）に変換した
イラスト地図です（`templates/map_svg.j2` に大分市・臼杵市などの地形イラストが静的に描かれています）。

新しいお店を追加する場合は、次のいずれかの方法で座標を決めてください。

- **簡単な方法**：近くの既存店舗の `cx`/`cy` を参考に、数十px以内で近い位置に置く
- **正確な方法**：Google検索または地図検索でその住所の緯度経度を調べ、以下の計算式で
  変換する（Claude Codeに「◯◯の住所の緯度経度を調べて、この計算式でピン座標を出して」と
  頼むのが早いです）。

```python
import math
lat0, lon0 = 33.2332, 131.6064  # 大分駅を原点とする
X0, Y0, scale = 330, 108, 10.3   # 現在の地図のスケール設定

def to_pixel(lat, lon):
    x_km = (lon - lon0) * 111.32 * math.cos(math.radians(lat0))
    y_km = (lat - lat0) * 110.57
    return X0 + x_km * scale, Y0 - y_km * scale
```

同じ場所に何店舗も近接する場合（例：関青果とめぐみ工房）は、番号が重ならないよう
数十px手動でずらして構いません。実際の位置関係の目安を崩さない範囲で調整してください。

新しい店舗が地図の枠（viewBox: `0 0 700 460`）からはみ出す場合は、
`templates/map_svg.j2` の `viewBox` を調整するか、`data.json` の `map.viewBox` を変更してください。

### 4. デザインを調整する

- 印刷用のレイアウト・配色・フォントサイズ → `templates/print.html.j2`
- スマホ用のレイアウト → `templates/mobile.html.j2`
- 地図の地形イラスト（大分市・臼杵市などの塗り絵部分）→ `templates/map_svg.j2`

## ディレクトリ構成

```
.
├── data.json              # ★ 内容の編集はここだけでOK
├── build.py                # data.json + templates/ → output/ を生成
├── templates/
│   ├── print.html.j2       # A4印刷用ページのテンプレート
│   ├── mobile.html.j2      # スマホ用ページのテンプレート
│   └── map_svg.j2          # 地図SVG（両方のテンプレートから共通で読み込み）
├── output/                 # 生成結果（build.py実行のたびに上書きされます）
│   ├── map.html
│   ├── map.pdf
│   └── map_mobile.html
└── README.md                # このファイル
```

## Claude Codeでの引き継ぎ方

このフォルダをそのままClaude Codeのプロジェクトとして開き、
「なずな農園の隣に新しい店舗を追加して」「地図のscaleを見直して津久見市エリアも実在店舗を追加したい」
のように自然文で指示すれば、`data.json` の編集と `python3 build.py` の実行をまとめて行えます。
