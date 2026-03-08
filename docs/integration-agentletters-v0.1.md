# AgentLetters Integration v0.1

## 目標
把 `ldrit-memory-loop` 作為 AgentLetters 的摘要引擎。

## 使用方式
```powershell
python src/generate_consensus_note.py `
  --mode agentletters `
  --input "C:\path\YYYYMMDD__ALL__主題__discussion.md" `
  --output "C:\path\YYYYMMDD__ConsensusNote__主題__v1.md"
```

## AgentLetters 模式驗證條件
1. 輸入檔名必須符合：`YYYYMMDD__ALL__主題名稱__discussion.md`
2. 內容需含 `From:` 與 `時間：` 區塊
3. 至少兩位參與者發言
4. 內容至少包含一段 `我目前最擔心的風險`

若不符合，程式會回報錯誤並停止，避免產生偽摘要。

## 輸出章節
- 已收斂共識
- 保留分歧
- 待驗證命題
- 最小可執行實驗
- 目前最大風險
- 建議主控決策
