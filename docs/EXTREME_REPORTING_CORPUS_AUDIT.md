# 前沿共生第二十八阶段：既有报告极值表述的分级复核

**日期**：2026-11-09  
**文档性质**：对既有 Markdown 的极值表述进行全集补充分级；不是重新拟合、数值修订或对历史结论的静默覆盖。

## 1. 复核范围与处理方式

本次共审阅 **16 份**涉及最大界、最大残差、极值或相关索引的文档。审阅采用“全集补充说明”而非批量改写：其中 **10 份**需要与全点分布审计联读，4 份只涉及极值事实或索引，2 份已满足三级契约。

**原始 Markdown 与旧 Word 均不改写。** 原文的数值、证据等级和历史语境保持原样；本文件只约束如何理解这些极值表述，防止把单个最大点直接升级为整体机制。

| 分级结果 | 数量 | 阅读方式 | 是否修改原文 |
|---|---:|---|---|
| `companion_required` | 10 | 必须与全点分布审计及三级契约联读，按 `distribution_summary` 或受限 `mechanism_interpretation` 使用 | 否，以本补充说明约束解释 |
| `descriptive_only` | 4 | 只涉及极值事实、比值或索引，按 `maximum_only` 使用 | 否 |
| `complete` | 2 | 已包含全点分布、百分位、界宽比、反例和限制，可按 L2 使用 | 否 |

## 2. 分级所依据的数值关系

最大点占比与中位占比之差：

\[
\Delta_{\max}=q_{\max}-\operatorname{median}(q)。
\]

最大界宽与中位界宽之比：

\[
R_B=\frac{B_{\max}}{\operatorname{median}(B)}。
\]

需要联读的文档并非数值错误，而是原文没有同时提供全部 L2 证据。若只用原文作极值描述，可按较低等级阅读；若用于机制解释，则必须结合 `docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md` 的多数类别、中位占比、描述性百分位和界宽比，并遵守 `docs/EXTREME_REPORTING_PROTOCOL.md` 的反例和限制要求。

## 3. 需要联读的十份文档

| 文档 | 主张等级 | 分级状态 | 补充理由 |
|---|---|---|---|
| `docs/BOUND_COMPARISON_V2_2026-11-09.md` | `distribution_summary` | `companion_required` | 有全点计数和中位数，但缺少当时的百分位和界宽比 |
| `docs/BOUND_COMPARISON_V3_2026-11-09.md` | `distribution_summary` | `companion_required` | 有新增分布，仍需补充极值位置和界宽证据 |
| `docs/BOUND_COMPARISON_V4_2026-11-09.md` | `distribution_summary` | `companion_required` | ENSO 最大界反例需与完整审计联读，不得只记类别 |
| `docs/CHWIRUT1_COVERAGE_2026-11-09.md` | `distribution_summary` | `companion_required` | 最大界及逐折分布需要结合描述性位置理解 |
| `docs/ENSO_COVERAGE_2026-11-09.md` | `distribution_summary` | `companion_required` | 最大点低占比与 131 对收紧比较属于不同证据轴 |
| `docs/EXTERNAL_BOUND_DECOMPOSITION_2026-11-09.md` | `distribution_summary` | `companion_required` | 三数据最大点与全点分布需要额外界宽比支持 |
| `docs/GAUSS1_BOUND_MECHANISM_2026-11-09.md` | `mechanism_interpretation` | `companion_required` | 机制解释必须同时保留全点分布、反例和非概率边界 |
| `docs/GAUSS1_EXTERNAL_COVERAGE_2026-11-09.md` | `distribution_summary` | `companion_required` | 极大上界、中位上界和预测失败不能相互替代 |
| `docs/INTERNAL_EXTERNAL_BOUND_COMPARISON_2026-11-09.md` | `distribution_summary` | `companion_required` | 最大点组成与六组分布需要后续百分位和界宽比补充 |
| `docs/MISRA1A_COVERAGE_2026-11-09.md` | `distribution_summary` | `companion_required` | 小 RMSE、宽上界和少量可用点必须联合解释 |

这 10 份文档的原始 SHA-256 已冻结在 `validation/extreme-corpus-audit.json`。验证器会拒绝任何借分级复核改变原文的行为，也会拒绝漏掉其中任一文档的补充说明。

## 4. 仅作极值事实或索引的文档

| 文档 | 分级状态 | 原因 |
|---|---|---|
| `docs/ELLIPSOID_BOUNDS_2026-11-09.md` | `descriptive_only` | “最大上界比值”是区域比较指标，不是用最大点解释整体机制 |
| `docs/FILIP_COVERAGE_2026-11-09.md` | `descriptive_only` | 只列最大残差上界并要求单独审阅，没有升级成典型机制 |
| `docs/PREDICTION_BOUNDS_2026-11-09.md` | `descriptive_only` | 用具体点说明近零分母放大，已有明确位置和局部机制边界 |
| `docs/UPSTREAM_INTERFACES.md` | `descriptive_only` | 属于证据索引，分级说明应由对应原始报告承担 |

这 4 份文档不需要补写机制解释，但也不能借“仅描述”省略其已经注明的适用范围。

## 5. 已满足契约的文档与三联图

| 文档 | 分级状态 | 已具备的证据 |
|---|---|---|
| `docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md` | `complete` | 多数类别、中位数、最大点差值、描述性百分位、界宽比和反例 |
| `docs/EXTREME_REPORTING_PROTOCOL.md` | `complete` | L0／L1／L2 义务、数值关系、禁止主张、机器验收与哈希记录 |

图：`papers/34_最大界与全点组成/fig34_maximum_full_composition.png`。

三联图继续作为联读证据，而不是为历史文档重新排名。它同时展示最大点类别与多数方向、最大点占比与中位数差异以及最大界宽比，使读者能够识别原文哪些说法需要降级或补充。

## 6. 后续写作与验收

既有报告不应因新数据出现而被静默改写，但也不能脱离后续反例独立使用。引用本仓库极值结论时，应同时引用原文和本分级说明；若原文缺少 L2 义务，就降低主张等级或补充最新证据，而不是只保留更强势的句子。

机器验收记录为 `validation/extreme-corpus-check.json`，包含文档数、联读数、原文未变数量、补充说明与规则哈希。后续新增文档应先加入分级清单，再决定是否需要全点分布和机制解释。

## 可复核文件

- 分级清单：`validation/extreme-corpus-audit.json`
- 验证器：`scripts/validate_extreme_corpus.py`
- 验收记录：`validation/extreme-corpus-check.json`
- 全点组成审计：`docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md`
- 三级写作契约：`docs/EXTREME_REPORTING_PROTOCOL.md`
- 三联图：`papers/34_最大界与全点组成/fig34_maximum_full_composition.png`
