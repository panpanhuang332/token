# 國貿大會考題庫與教材參考套件

供 Codex 讀取與後續網站開發參考，UTF-8 編碼。

- 題庫：第17–21屆（2022–2026），每屆100題，共500題。
- 每題包含原題、四個選項、原卷答案、本站編寫的解析、題型、來源頁碼，以及適用的註記／運費表。
- 教材：12個題型，包含觀念對照、例題與對應練習題。
- 單證附件：五屆各3頁，共15頁，供第91–100題使用。
- 內容整理基準日：2026-09-24；套件匯出日：2026-09-27。匯出不代表再次更新政策或最終釋疑。

## 檔案入口

| 檔案／目錄 | 內容 |
| --- | --- |
| question_bank.json | 完整結構化題庫；優先以此匯入程式 |
| curriculum.json | 12個教材的結構化資料 |
| questions/ | 依屆次分開的Markdown全文，共5份 |
| lessons.md | 人工閱讀版教材 |
| assets/ | 信用狀、匯票／發票與提單原始附件JPEG |
| SOURCES.md | 原卷來源、版權與校核限制 |
| CODEX_HANDOFF.md | 給Codex的讀取及使用說明 |
| checksums.sha256 | 套件檔案校驗碼 |

## JSON欄位

`question_bank.json` 的根節點包含 `updated`、`editions`、`questions`。

| 欄位 | 意義 |
| --- | --- |
| id | 穩定題號，例如17-001；不可用字母答案當作題目ID |
| exam / year / number | 屆次／西元年／原卷題號 |
| question | 題幹 |
| options | 四個選項，依序對應A、B、C、D |
| answer | 原卷答案字母 |
| explanation | 本站學習解析，非官方解析 |
| topic | 對應curriculum.json的id |
| page | 原始PDF實體頁次，包含封面 |
| table | 運費等資料表；使用時必須呈現headers與rows |
| context | 作答前需要的題目補充 |
| note | 作答後的校核／歧義註記 |
| historical | true表示應依當屆歷史情境解題 |

`editions` 提供各屆 `pdf`、`sourcePage`、`sourceLabel` 和 `casePages`。`casePages` 是相對於本套件根目錄的影像路徑；移動資料時應保留或同步更新。

## 網站

https://itce-study-lab.e5060b85-02c2-4336-b68d-483091a94ab8.chatgpt.site

網站有存取權限；外部Codex工作階段未必能直接開啟。此套件包含參考所需的內容，不依賴網站登入，也不含登入憑證、私人作答紀錄或網站的管理權限。

## 校核重點

第21屆已對照官方釋疑，第98、100題維持原答案。第17–20屆採原卷所列答案，最終釋疑未完成核實。不要把500題解析稱為主辦單位官方解析；不要把時事題直接改寫為現行規則。詳細來源和限制請先讀SOURCES.md。
