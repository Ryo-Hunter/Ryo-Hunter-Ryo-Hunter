# ldrit-memory-loop

LDRIT 衍生的第一個開源專案（規劃版）。

## 專案目標
將多人討論檔（`discussion.md`）轉為可傳承、可審閱的標準化摘要資產，降低上下文遺失與重複推理成本。

## v0.1 範圍（MVP）
- 輸入：一份 `discussion.md`
- 輸出：一份 `consensus-note.md`
- 功能：抽取四類資訊
  - 收斂共識
  - 保留分歧
  - 待驗證命題
  - 下一步決策門檻

## 不在 v0.1 的範圍
- 不做 Web UI
- 不接資料庫
- 不做雲端部署
- 不做模型微調

## 專案結構
- `docs/spec-v0.1.md`：規格與驗收標準
- `docs/roadmap-v0.1.md`：實作里程碑
- `templates/consensus-note.template.md`：輸出模板
- `examples/discussion.sample.md`：輸入範例
- `tests/`：保留給後續測試

## 成功判準（v0.1）
1. 相同輸入重跑，輸出結構一致。
2. 三份示例檔可穩定產出可讀摘要。
3. 人工審閱可直接用於下一步決策。

## AgentLetters 模式
```powershell
python src/generate_consensus_note.py `
  --mode agentletters `
  --input "C:\path\YYYYMMDD__ALL__主題__discussion.md" `
  --output "C:\path\YYYYMMDD__ConsensusNote__主題__v1.md"
```
詳細規範見：`docs/integration-agentletters-v0.1.md`
