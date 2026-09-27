# token
token

## 網站

- **Token 圖解**(LLM token 教學):https://panpanhuang332.github.io/token/
- **國貿大會考 14 天衝刺**:https://panpanhuang332.github.io/token/trade/

`trade/` 為國貿大會考衝刺站:`index.html`(程式)+ `bank.js`(講義、仿真題庫、單字、14 天計畫、速記表)。題目為依官方 12 大命題方向自行編寫的練習題,非主辦單位原題;歷屆試題請至官方網站下載後由「考古題」頁匯入。

### 歷屆考古題套件(`data/itce-pack/`)

放入 `question_bank.json`、`curriculum.json`、`assets/` 後執行:

```
python3 tools/build_past.py data/itce-pack
```

腳本會依 CODEX_HANDOFF.md 的驗收基準檢查(500 題、每題 4 選項與原卷答案與解析、12 教材、15 張附件、drills 對應),通過才輸出 `trade/past_data.js` 與 `trade/assets/`;網站偵測到 `past_data.js` 即自動開啟「歷屆考古題」模式。原題與附件權利屬台北市進出口商業同業公會,僅供教學練習,解析為本站編寫、非官方解析。
