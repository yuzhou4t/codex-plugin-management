# Agent 约定（插件仓）

- 默认简体中文；先结果后依据。
- 通用工作约定见 [`profiles/global-AGENTS.md`](profiles/global-AGENTS.md)。
- **AO / Matt 情境路由**：统一表在 [`skills/ask-matt/AO-SITUATION-TABLE.md`](skills/ask-matt/AO-SITUATION-TABLE.md)。编排交付走 [`skills/architect-led-agent-build/SKILL.md`](skills/architect-led-agent-build/SKILL.md)；迷路时用 `ask-matt`。AO 模式下派活只用 `ao spawn`，不要用 `implement` / `implement-spec` 另开一条派活轨。
- Matt 官方技能仍从 `mattpocock/skills` marketplace 安装；本仓的 `ask-matt` 是带 AO 分流的自维护路由层，不替代官方其余技能正文。
