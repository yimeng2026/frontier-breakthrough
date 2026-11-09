# 前沿共生第三十六阶段：极值相关报告全集分级（第二版）

**日期**：2026-11-09  
**文档性质**：将极值相关文档分级扩展到第三十五阶段；不是重新拟合、数值修订、物理真实性认证或对历史结论的静默覆盖。

## 1. 全集范围与历史保留

本次共审阅 **23 份**涉及最大界、最大残差、极值、参数极值或相关索引的文档，其中 **12 份**需要联读，**7 份**仅作极值描述，**4 份**已具备其主张所需的完整证据。旧清单包含 16 份文档，本次新增 7 份，不用“全集”一词掩盖新增缺口。

**原始 Markdown 与旧 Word 均不改写。** 旧 `validation/extreme-corpus-audit.json`、`validation/extreme-corpus-check.json` 和 `scripts/validate_extreme_corpus.py` 保持原样，旧 10 份联读原文的 SHA-256 仍与历史清单一致。新版只约束如何理解这些表述，禁止用新证据覆盖历史数值。

| 分级结果 | 数量 | 阅读方式 | 是否修改原文 |
|---|---:|---|---|
| `companion_required` | 12 | 必须与全点分布审计及三级契约联读，按 `distribution_summary` 或受限 `mechanism_interpretation` 使用 | 否，以本补充说明约束解释 |
| `descriptive_only` | 7 | 只涉及极值事实、比值、预测汇总或索引，按 `maximum_only` 使用 | 否 |
| `complete` | 4 | 已包含相应分布、反例和限制，可按其主张等级使用 | 否 |
| 合计 | 23 | 文档证据等级不同，不统一升格为 L2 | 否 |

## 2. 分级所依据的数值关系

最大点占比与中位占比之差：

\[
\Delta_{\max}=q_{\max}-\operatorname{median}(q)。
\]

最大界宽与中位界宽之比：

\[
R_B=\frac{B_{\max}}{\operatorname{median}(B)}。
\]

需要联读的文档并非数值错误，而是原文没有同时提供全部所需证据。若只作极值描述，可按较低等级阅读；若用于机制解释，则必须结合 `docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md`、`docs/EXTREME_REPORTING_PROTOCOL.md` 和 `docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md`，并保留后续原生模型的边界。

## 3. 需要联读的十二份文档

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
| `docs/ROSZMAN1_COVERAGE_2026-11-09.md` | `distribution_summary` | `companion_required` | 5 个第 2 折可用点的最大界、中位界和平移主导不能替代 25 点概率覆盖或完整分布 |
| `docs/BOUND_COMPARISON_V5_2026-11-09.md` | `distribution_summary` | `companion_required` | 十组最大界类别已给出，但仍需结合十组百分位、界宽比和小样本边界 |

这 12 份文档必须与其联读文件共同使用。Roszman1 的小样本最大界和十组新增计数都不能脱离后续十组极值审计独立升级为机制。

## 4. 仅作极值事实、预测汇总或索引的文档

| 文档 | 分级状态 | 原因 |
|---|---|---|
| `docs/ELLIPSOID_BOUNDS_2026-11-09.md` | `descriptive_only` | 最大上界比值是区域比较指标，不是用最大点解释整体机制 |
| `docs/FILIP_COVERAGE_2026-11-09.md` | `descriptive_only` | 只列最大残差上界并要求单独审阅，没有升级成典型机制 |
| `docs/PREDICTION_BOUNDS_2026-11-09.md` | `descriptive_only` | 用具体点说明近零分母放大，已有明确位置和局部机制边界 |
| `docs/UPSTREAM_INTERFACES.md` | `descriptive_only` | 属于证据索引，分级说明应由对应原始报告承担；入口持续更新，故不冻结其哈希 |
| `docs/ROSZMAN1_NATIVE_HOLDOUT_2026-11-09.md` | `descriptive_only` | 主要是逐折预测、汇总 RMSE 和模型族对照，最大残差不用于证明整体机制 |
| `docs/ENSO_NATIVE_HOLDOUT_2026-11-09.md` | `descriptive_only` | 主要是周期预测与参数变化，极值只作结果描述，不用于证明新周期机制 |
| `docs/CHWIRUT1_NATIVE_HOLDOUT_2026-11-09.md` | `descriptive_only` | 主要是重复距离预测和同族边界，最大残差不用于独立复现或原生证明 |

这 7 份文档不需要补写机制解释，但也不能借“仅描述”省略其适用范围。特别是原生模型预测对照不能被反向移植成有理模型的证明区域。

## 5. 已具备相应完整证据的文档与分级图

| 文档 | 分级状态 | 已具备的证据 |
|---|---|---|
| `docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md` | `complete` | 九组多数类别、中位数、最大点差值、描述性百分位、界宽比和反例 |
| `docs/EXTREME_REPORTING_PROTOCOL.md` | `complete` | L0／L1／L2 义务、数值关系、禁止主张、机器验收与哈希记录 |
| `docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md` | `complete` | 十组分布、Roszman1 小样本百分位边界、独立 L2 收据和历史保留 |
| `docs/ROSZMAN1_NATIVE_IDENTIFIABILITY_2026-11-09.md` | `complete` | 五折解析雅可比、局部秩、条件数、相关矩阵、参数范围、敏感度和非概率限制 |

`complete` 只表示文档包含其当前主张所需证据，不表示物理理论为真。全局可识别性、物理内生性、概率覆盖和独立实验仍需另行证据。

图：`papers/43_极值全集分级V2/fig43_extreme_corpus_v2.png`。

左图比较旧 16 份与新版 23 份的三类数量，右图单独显示新增 7 份的分类。图题和计数必须对应 `12 companion / 7 descriptive / 4 complete`，不得继续把旧 16 份计数当作当前全集。

## 6. 机器验收与后续义务

新版 `validation/extreme-corpus-v2-check.json` 应记录：23 份文档、12 份联读、7 份描述、4 份完整、22 份非接口文档哈希匹配、旧 10 份联读原文未变、错误数 0，以及历史协议和收据哈希。验证器拒绝漏文档、哈希篡改、缺少联读文件和陈旧收据。

后续新增极值相关报告应先加入新版本清单，再判断是否需要全点分布和机制解释。不得静默修改本版清单或原文；若文档内容改变，应另立版本并保留本版历史。引用本仓库极值结论时，应同时引用原始报告与相应分级说明，不能只保留更强势的句子。

## 可复核文件

- 新版分级清单：`validation/extreme-corpus-v2-audit.json`
- 新版验证器：`scripts/validate_extreme_corpus_v2.py`
- 新版验收记录：`validation/extreme-corpus-v2-check.json`
- 旧版分级说明：`docs/EXTREME_REPORTING_CORPUS_AUDIT.md`
- 九组全点组成审计：`docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md`
- 三级写作契约：`docs/EXTREME_REPORTING_PROTOCOL.md`
- 十组全点组成审计：`docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md`
- 分级图：`papers/43_极值全集分级V2/fig43_extreme_corpus_v2.png`
