# 上游成果与本地验证接口

本文件定义“借用—复核—回馈”的实际接口，而不是合作方名单。只有真实运行的检查才进入证据包。

## 统一数据契约

- Schema：`contracts/frontier-evidence.schema.json`。
- 生成器：`scripts/export_evidence_packet.py`。
- 输出：`exports/frontier-evidence.json`。
- 校验：`python scripts/export_evidence_packet.py --check`。

每一项包含：领域、状态、证据类别、原始来源、指标、科学主张、限制、可回馈贡献和快照文件。`verified` 只对应文字明确描述的本机或跨库检查，不表示新发现、外部认证或湿实验。

## 已接通的上游链路

| 上游成果 | 本地/独立检查 | 输出 | 可提供的互补贡献 |
|---|---|---|---|
| PySINDy | 固定线性库，从合成轨迹恢复已知系数并保留数值误差 | `validation/pysindy.json` | 可重放基线与误差边界 |
| Z3 | 两个实数不可满足约束 | `validation/z3.json` | 形式化前的反例搜索样例 |
| PubChem + RDKit | 规范结构、分子式、精确质量、TPSA 与 LogP 算法口径 | `validation/rdkit.json` | 跨数据库化学数据质量检查 |
| Materials Project + PyMatGen | 从 Si 公开结构本地重算密度和空间群 | `validation/pymatgen.json` | 结构派生量与规范 ID 的轻量复核 |
| RCSB PDB + UniProt | 基因/物种检索后，对 HBB 序列做逐字符比对和 MD5 重算 | `validation/pdb-uniprot.json` | 实验结构到 reviewed 序列的可追溯桥接 |
| ChEMBL + PubChem + RCSB PDB + UniProt | 乙酰唑胺 InChIKey、CA II 靶点、P00918 与 3HS4 entity 1 的 260 aa 精确序列、单一 Ki assay、AZM 配体与 pChEMBL 重算；同酯酶方法 CA I/II 表观比值，CA IX 方法不同不合并 | `validation/drug-target-structure.json`、`validation/ca-selectivity.json`、`validation/ca-document-stability.json`、`validation/structural-control.json` | 药物—靶点—蛋白序列—实验结构的来源审计；保留重复标记、assay 可比性、跨文档不稳定性、不同构建和长度元数据不一致，不冒充独立野生型重复 |
| NIST Chwirut2 | 47 个训练观测、7 个高距离留出观测，双起点模型与两项基线；54 点独立复算 | `validation/chwirut-holdout.json`、`validation/chwirut-holdout-verification.json` | 首个公开真实数据留出包；只支持该切片，不宣称普适规律 |
| Z3 扩展反例 | 分母正性定义域、零分母反例、x=0 参数非识别性 | `validation/z3-identifiability.json` | 把实验设计和模型定义域转成可执行证明义务与反例 |
| PubChem + ChEMBL + RDKit | 阿司匹林结构、InChIKey、分子式、精确质量、TPSA、LogP、氢键和可旋转键多口径审计 | `validation/pubchem-aspirin.json`、`validation/chembl-aspirin.json`、`validation/aspirin-crosscheck.json` | 身份一致与算法差异并列保留，不把差异称为造假 |
| Materials Project + OQMD + PyMatGen | Si、GaAs、SiO2 的结构、带隙、密度、稳定性对照；原生 entry_id 与 OPTIMADE 结构 ID 分开核验 | `validation/material-crosscheck.json`、`validation/oqmd-structure-*.json` | 结构身份和 DFT 差异分开；提供可复核的结构映射与本地派生量 |
| NIST Eckerle4 | 27 个中央训练观测、低尾 3 点和高尾 5 点；35 点独立复算 | `validation/eckerle4-two-tail.json`、`validation/eckerle4-two-tail-verification.json` | 第二个独立真实数据双尾外推包；只支持该双尾协议 |
| cvc5 + Z3 | 三类定义域与可识别性检查结果一致；精确有理数模型 | `validation/cvc5-crosscheck.json`、`validation/cvc5-*.smt2`、`validation/cvc5-*.log` | 双求解器 SMT-LIB 与日志，降低单求解器依赖 |
| NIST Hahn1 + Z3 + cvc5 | 219 个训练观测与 17 个高温留出观测；三次多项式基线；分母区间内无零根、域外正根 | `validation/hahn1-high-temperature.json`、`validation/z3-hahn1-denominator.json`、`validation/cvc5-hahn1-denominator.json` | 有理模型外推与分母边界同时交付，不把拟合成功写成全域数学安全 |
| NIST Chwirut2 + Eckerle4 + Hahn1 | 三个数据集共 15 折连续区间留出，相同 x 不跨训练与测试；Hahn1 第 1 折失效 | `validation/grouped-stress-protocol.json`、`validation/grouped-stress.json` | 提供跨数据集压力诊断和完整失败区间，不把分母非零等同于预测稳健 |
| Hahn1 五折冻结参数事后诊断 | 解析雅可比、列归一化条件数、参数相关和局部预测敏感度；第 1 折两个低温数值单极点 | `validation/hahn1-fold1-identifiability.json`、`validation/hahn1-frozen-denominator-roots.json` | 提供逐折极点排除与可识别性验收义务；不把事后机制解释当作独立验证 |
| NIST Thurber 数据集前瞻验收 | 37 个观测、五折连续留出、预测区极点与最低数值可识别性门；四折通过、一折失败 | `validation/thurber-prospective-gate-protocol.json`、`validation/thurber-prospective-gate.json` | 在新数据集上检验 Hahn1 衍生验收规则，保留整体未通过结论 |
| NIST Kirby2 跨次数前瞻验收 | 151 个观测、五参数二次有理模型；五折均通过预测区、局部数值与二次基线验收 | `validation/kirby2-prospective-gate-protocol.json`、`validation/kirby2-prospective-gate.json` | 提供阳性对照，同时保留外推衰减、条件数和区间检查边界 |
| 有理模型统一内核与跨数据集综合 | 统一雅可比、根定位、预测区和局部数值诊断；15 折中 13 折符合验收，区分事后重建与前瞻标签 | `scripts/rational_gate.py`、`exports/rational-cross-dataset.json` | 为后续有理模型提供可复用接口，不把折叠计数当作普适检出率 |
| 精确 Sturm 根隔离 + Z3 + cvc5 | 对十五折有理系数快照精确计数；13 折 unsat、2 折 sat，数值与精确计数全一致 | `scripts/exact_roots.py`、`validation/rational-exact-interval-roots.json`、`validation/exact-interval-smt/` | 提供闭区间根证明与日志，不把 sat 模型或系数快照当作精确物理常数 |
| 连续参数盒稳定性证明 | 13 折获得正的区域安全半径，11 折达到上限 4，2 折为有限半径括号；跨零区间分段证明 | `scripts/box_stability.py`、`validation/rational-parameter-box-stability.json` | 提供整个系数盒的无根充分证明，不把半径当作置信区或必要最大值 |
| 参数盒内逐点预测界 | 13 折共 369 个留出点获得精确预测平移与残差上界；两个有根折不生成同类界 | `scripts/prediction_box_bounds.py`、`validation/rational-prediction-box-bounds.json` | 把无根与预测信息质量分开，巨大有限上界不包装成高精度或概率区间 |
| 协方差椭球与独立盒比较 | 同一半径下 369 个适用点的椭球上界全部更紧，中位比值 0.604836 | `scripts/ellipsoid_bounds.py`、`validation/rational-ellipsoid-box-comparison.json` | 提供相关方向的确定性上界，不把区域替换或样本结果称为永远更紧或置信区 |
| 协方差椭球连续区间证明 | 13 折平方支撑多项式在整个留出闭区间均为正，0 折未认证，2 折有根 | `scripts/ellipsoid_interval.py`、`validation/rational-ellipsoid-interval-safety.json` | 用精确 Sturm 覆盖观测点之间，不把逐点检查冒充连续证明 |
| NIST Filip 外部候选压力测试 | 五折候选 RMSE 均优于三次基线；82／82 点椭球界覆盖实际残差，独立盒连续安全为 0 | `validation/filip-ellipsoid-coverage-protocol.json`、`validation/filip-ellipsoid-coverage.json` | 提供外部候选压力测试，不声称原生 11 参数模型、概率覆盖或物理内生 |
| 通用外部覆盖协议 + NIST MGH17 | 通用驱动保持 Filip 回归；MGH17 33／33 点覆盖，32 点椭球更紧，独立盒 5 折安全 | `scripts/external_coverage.py`、`validation/mgh17-ellipsoid-coverage.json`、`exports/external-coverage-comparison.json` | 提供可复用外部验收接口，不把 115 点汇总称为概率覆盖或普适成功率 |
| Gauss1 外部反例与三数据对照 | 250 点中 190 点可给界、60 点不可用，连续安全 3／5 折；三数据共 365 点，305 点适用 | `validation/gauss1-ellipsoid-coverage.json`、`exports/external-coverage-gauss1-comparison.json` | 保留预测失败和无可用界反例，不把代码复用或适用点零违规称为外部有效性保证 |
| Gauss1 界失效机制与同点分解 | 190 点数值全部一致；第 2 折最大界处平移占 97.561%，第 1、3、4 折主要由实际残差贡献 | `scripts/analyze_gauss1_bound_mechanism.py`、`validation/gauss1-bound-mechanism.json` | 区分候选误差、近零分母放大和极端协方差支撑，不把事后占比称为概率贡献或物理机制 |
| 三数据界组成与机制异质性 | 305 点算术恒等式全部一致；Filip 与 MGH17 几乎全由平移主导，Gauss1 多数由实际残差主导 | `scripts/build_external_bound_decomposition.py`、`exports/external-bound-decomposition.json` | 同时保留全点分布和最大界位置，不把算术占比称为概率贡献或普适排名 |
| 内外部六组界组成对照 | 674 点中 482 点平移主导、192 点实际残差主导；内部有根折与外部不可用点分开 | `scripts/build_internal_external_bound_comparison.py`、`exports/internal-external-bound-comparison.json` | 支持内外部可比较但不可混同的证据检索，不计算合并成功率或普适排名 |
| Misra1a 预测—证明解离 | 14 点中仅 4 点可给界，连续安全 1／5 折；小 RMSE 与宽上界和平移主导并存 | `validation/misra1a-ellipsoid-coverage-protocol.json`、`validation/misra1a-ellipsoid-coverage-scope-v2.json` | 提供预注册小样本反例，不把拟合接近或 4 点零越界称为连续证明、概率覆盖或高信息量 |
| 四外部与七组新版范围对照 | 外部 379 点中 309 可用、70 不可用；七组 678 点中 486 平移主导、192 实际残差主导 | `exports/external-bound-decomposition-v2.json`、`exports/internal-external-bound-comparison-v2.json` | 新旧文件并存并标明 Misra1a 增量，不覆盖历史或计算合并成功率 |
| Chwirut1 同族外部审计 | 214 点中 83 点可给界、131 点不可用；第 4 折最低 RMSE 但零可用界；与 Chwirut2 同研究同模型族 | `validation/chwirut1-ellipsoid-coverage-protocol.json`、`validation/chwirut1-ellipsoid-coverage.json` | 区分未触碰数据与独立模型族验证，分开记录预测和证明 |
| 五外部与八组新版范围对照 | 外部 593 点中 392 可用、201 不可用；八组 761 点中 561 平移主导、200 实际残差主导 | `exports/external-bound-decomposition-v3.json`、`exports/internal-external-bound-comparison-v3.json` | 标明 Chwirut1 增量与同族边界，不覆盖历史或计算合并成功率 |
| 外部模型族限制文本修订 | MGH17、Gauss1、Misra1a 各生成一份修订副本；除首条限制文本和溯源字段外原字段全部保持 | `validation/external-scope-limitations-amendment-01.json`、`validation/external-scope-limitations-amendment-01-audit.json` | 保留原始文件、冻结协议和全部数值，阻止错误文本继续传播 |
| 范围感知外部分析适配层 | 校验驱动与适配器哈希，生成或采用数据专属限制文本，保留调用方与同族数据边界 | `scripts/external_coverage_scoped.py` | 新协议可复用正确范围说明，旧驱动与旧包装器不变 |
| ENSO 周期数据范围适配与预测—证明解离 | 168 点中 135 点可给界、33 点不可用；131 对比较收紧；第 5 折优于基线但零可用界 | `validation/enso-ellipsoid-coverage-protocol.json`、`validation/enso-ellipsoid-coverage.json` | 三类实现哈希完整留痕，不把相对预测改善或有利子集写成证明保证 |
| 六外部与九组新版范围及最大界对照 | 外部 761 点中 527 可用、234 不可用；九组 896 点中 594 平移主导、302 实际残差主导；ENSO 最大界由实际残差主导 | `exports/external-bound-decomposition-v4.json`、`exports/internal-external-bound-comparison-v4.json` | 标明 ENSO 增量和最大界反例，不覆盖历史、同族边界或周期候选限制 |
| 最大界点与全点组成审计 | 8／9 组最大点类别与多数一致，6 组低于中位占比；Gauss1 最大界宽为中位界宽 82.994 倍，ENSO 最大点占比位于描述性第 13.33% | `validation/maximum-full-composition-protocol.json`、`exports/maximum-full-composition-audit.json` | 分开类别、占比、描述性百分位和界宽比，不把最大点当作典型点或概率 |
| 极值报告三级写作契约 | L0 极值描述、L1 全点分布、L2 限定机制解释；九组审计通过 L2，错误百分位、类别、界宽比和最大点典型性被拒绝 | `contracts/extreme-reporting.rules.json`、`validation/extreme-reporting-check.json` | 机器验证字段义务、数值关系和反例，不把结构通过当作物理真实性证明 |
| 既有报告极值表述全集分级 | 16 份文档全部覆盖：10 份联读、4 份仅描述、2 份完整；10 份联读原文哈希全部不变 | `validation/extreme-corpus-audit.json`、`validation/extreme-corpus-check.json` | 约束旧报告的阅读等级，不批量改写历史文件，不用单个极值替代整体机制 |
| Roszman1 小样本预测—证明解离 | 25 点中仅第 2 折 5 点可给界、20 点不可用；第 1、4 折优于基线但零可用界，第 5 折预测失败；4 对比较收紧 | `validation/roszman1-ellipsoid-coverage-protocol.json`、`validation/roszman1-ellipsoid-coverage.json`、`docs/ROSZMAN1_COVERAGE_2026-11-09.md` | 冻结三类实现哈希并保留逐折反例，不把平移主导的小样本可用子集写成概率覆盖、连续 x 误差界或原生反正切模型验证 |
| 七外部与十组新版范围对照 | 外部 786 点中 532 可用、254 不可用；十组 901 点中 599 平移主导、302 实际残差主导；Roszman1 可用点仅位于第 2 折 | `exports/external-bound-decomposition-v5.json`、`exports/internal-external-bound-comparison-v5.json`、`docs/BOUND_COMPARISON_V5_2026-11-09.md` | 保留六外部与九组历史版本，标明 Roszman1 增量和原生模型边界，不计算合并成功率 |
| 十组最大界与全点组成新版审计 | 9／10 组最大点类别与多数一致，6 组低于中位占比；Roszman1 在 5 个第 2 折可用点中的描述性百分位为 100%，另有 20 点不可用 | `validation/maximum-full-composition-v2-protocol.json`、`exports/maximum-full-composition-audit-v2.json`、`validation/extreme-reporting-v2-check.json` | 保留九组审计和收据，分开类别、百分位与界宽比，不把局部百分位写成概率覆盖或总体代表性 |
| Roszman1 原生反正切同折对照 | 原生在第 3、4、5 折 RMSE 更低，第 1、2 折有理候选更低；五折全部成功，25 点 RMSE 分别为 0.007568255 和 0.219326962 | `validation/roszman1-native-holdout-protocol.json`、`validation/roszman1-native-holdout.json`、`docs/ROSZMAN1_NATIVE_HOLDOUT_2026-11-09.md` | 分开全数据已知答案与留出证据，保留逐折胜负，不移植有理证明区域或宣称绝对模型排名 |
| Roszman1 原生参数局部可识别性 | 五折数值秩均为 4，最大条件数 90.743359、最大相关绝对值 0.987535；b2、b4 逐折范围分别为 0.000010411859、112.236141 | `validation/roszman1-native-identifiability-protocol.json`、`validation/roszman1-native-identifiability.json`、`docs/ROSZMAN1_NATIVE_IDENTIFIABILITY_2026-11-09.md` | 使用解析雅可比且不重拟合，不把局部满秩、预测稳定或 Delta-method 敏感度写成全局可识别性、参数唯一性或概率区间 |
| ENSO 原生 Fourier 同折对照 | 原生在第 2—5 折 RMSE 更低，第 1 折有理候选更低；默认 LM 未达原容差而认证前向通过；b4、b7 范围为 3.126309、1.946067 个月 | `validation/enso-native-holdout-protocol.json`、`validation/enso-native-holdout-protocol-amendment-01.json`、`validation/enso-native-holdout.json`、`docs/ENSO_NATIVE_HOLDOUT_2026-11-09.md` | 分开优化器复现与认证前向，保留逐折胜负和周期变化，不移植有理证明区域或宣称全域模型排名 |
| Chwirut1 原生指数同折对照 | 原生在第 1、3、4、5 折 RMSE 更低，第 2 折有理候选更低；214 点汇总 RMSE 为 7.778996 对 9.456158；22 个距离分组与同族边界完整保留 | `validation/chwirut1-native-holdout-protocol.json`、`validation/chwirut1-native-holdout-protocol-amendment-01.json`、`validation/chwirut1-native-holdout.json`、`docs/CHWIRUT1_NATIVE_HOLDOUT_2026-11-09.md` | 保留重复观测、计数修订和参数变化，不把预测优势写成独立模型族复现、原生误差界或概率校准 |
| 极值相关报告全集分级第二版 | 23 份文档：12 份联读、7 份描述、4 份完整；22 份非接口文档哈希匹配，旧 10 份联读原文未变 | `validation/extreme-corpus-v2-audit.json`、`validation/extreme-corpus-v2-check.json`、`docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md` | 约束第三十五阶段文档阅读等级，保留旧清单、旧验证器、原文和收据，不把 complete 等同于物理真实性 |
| 全仓库一致性审计 | 检查 README 本地链接、报告图片、Word 清单、证据快照、图谱、全集计数和 10 份近期协议，错误数为 0；显式刷新保留旧收据 | `validation/repository-integrity-rules.json`、`validation/repository-integrity-report.json`、`docs/REPOSITORY_INTEGRITY_2026-11-09.md` | 提供动态 JSON/README 计数核对与负例门禁，不把结构一致误称为科学真实性或视觉验收 |
| 三数据原生模型同折综合 | 15 折、407 个配对留出点；原生 11 折 RMSE 低于有理、10 折为三者最低；保留 Roszman1 逐点 12 比 13 与第 4 折 RMSE／MAE 反向 | `validation/native-cross-dataset-synthesis-protocol.json`、`exports/native-cross-dataset-synthesis.json`、`docs/NATIVE_CROSS_DATASET_SYNTHESIS_2026-11-09.md` | 区分折级 RMSE、逐点多票数与不同误差指标，不跨量纲合并误差，不建立概率排名或移植有理证书 |
| Roszman1 第 4 折误差贡献分解 | D1 为 +0.000461975122、D2 为 -1.317350031e-5；五点逐点方向全部一致；移除第 4 或第 5 点反转 MAE，五次移除均不反转 RMSE | `validation/roszman1-native-fold4-error-decomposition-protocol.json`、`validation/roszman1-native-fold4-error-decomposition.json`、`docs/ROSZMAN1_NATIVE_FOLD4_ERROR_DECOMPOSITION_2026-11-09.md` | 用残差权重恒等式定位汇总反向，不把五点算术、单点贡献移除当作显著性、因果机制或重新拟合 |
| Chwirut1 原生参数可识别性与分母诊断 | 五折局部秩均为 3，最大条件数 28.674083，第 1 折 b2 相对标准误 1.710628、最大敏感度 14.836682；五折极点均在观测范围外 | `validation/chwirut1-native-identifiability-protocol.json`、`validation/chwirut1-native-identifiability.json`、`docs/CHWIRUT1_NATIVE_IDENTIFIABILITY_2026-11-09.md` | 使用逐折自由度、解析雅可比和原生分母诊断，不把满秩、局部协方差或观测点极点写成全局识别、概率区间或独立复现 |
| ENSO 原生周期参数可识别性与谐波补偿 | 五折局部秩均为 9，最大相关 0.918709 来自周期与自身振幅；第 4 折 RMSE 较低但 b4、b7 相对标准误均最高，周期范围为 3.126309、1.946067 个月 | `validation/enso-native-identifiability-protocol.json`、`validation/enso-native-identifiability.json`、`docs/ENSO_NATIVE_IDENTIFIABILITY_2026-11-09.md` | 分离周期间、周期与自身振幅、跨谐波块相关，不把低 RMSE 或局部相关写成周期唯一、物理耦合、新周期或概率区间 |
| 三模型局部可识别性受限综合 | 15 折、407 点全部局部满秩；三个折的敏感度高于 RMSE，最大比值 2.697264；ENSO 比值均小于 1 仍不证明周期安全 | `validation/native-identifiability-cross-model-protocol.json`、`exports/native-identifiability-cross-model-synthesis.json`、`docs/NATIVE_IDENTIFIABILITY_CROSS_MODEL_2026-11-09.md` | 提供共同审计接口与逐折比值，保留原生单位、专有病征与已知答案分层，不合成误差池、概率覆盖率或稳定性评分 |
| 三模型局部敏感度固定阈值覆盖审计 | 407 点、1221 次判定；1、2、4 倍分别覆盖 85、181、283 点；最大逐点比值 25.724483，Roszman1 第 5 折折级比值 2.697264 但 1 倍已全覆盖 | `validation/native-sensitivity-threshold-coverage-protocol.json`、`exports/native-sensitivity-threshold-coverage.json`、`docs/NATIVE_SENSITIVITY_THRESHOLD_COVERAGE_2026-11-09.md` | 提供逐点违规 ID 和两类聚合反例，不把固定计数称为概率覆盖，也不把局部标准差当作确定性残差界 |
| Chwirut1 原生椭球连续分母与保守预测界 | 五折连续分母均为正并生成 22 个原生包络；最大宽度 170.146309，中位宽度 19.222110；214 点中心一致性通过但不是概率覆盖 | `validation/chwirut1-native-ellipsoid-continuous-protocol.json`、`validation/chwirut1-native-ellipsoid-continuous-bounds.json`、`docs/CHWIRUT1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md` | 提供端点凹凸性和原始非线性包络接口，区分区域证书、信息宽度、中心一致性与外部有效性 |
| Chwirut1 原生椭球半径敏感性与临界半径 | 五折临界半径为 7.415974 至 16.542845；第 1 折半径 8 不可用，其余 24 案例通过并生成 105 个包络；第二份修订恢复 1070 计数 | `validation/chwirut1-native-ellipsoid-radius-sensitivity-protocol.json`、`validation/chwirut1-native-ellipsoid-radius-sensitivity-protocol-amendment-02.json`、`validation/chwirut1-native-ellipsoid-radius-sensitivity.json` | 区分几何临界值、网格最大值与信息宽度，保留不可用案例和计数修订链，不选择最优半径或宣称概率覆盖 |
| Roszman1 原生反正切椭球奇异证书与预测界 | 前四折负号通过并生成 20 个包络，第 5 折临界半径 2.828351 且跨零，5 点不可用；最大宽度 0.867292 | `validation/roszman1-native-ellipsoid-continuous-protocol.json`、`validation/roszman1-native-ellipsoid-continuous-bounds.json`、`docs/ROSZMAN1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md` | 区分 arctan 有界性、分母存在性、奇异临界半径和中心一致性，不用低 RMSE 绕过奇异检查或宣称概率覆盖 |
| ENSO 原生 Fourier 椭球正周期与连续预测包络 | 五折两个周期下界均为正并生成 168 个包络；最小临界半径 26.766839，最大宽度 17.641929，中位宽度 13.164436；中心一致性不是外部验证 | `validation/enso-native-ellipsoid-continuous-protocol.json`、`validation/enso-native-ellipsoid-continuous-bounds.json`、`docs/ENSO_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md` | 提供正周期支撑证书、原始 Fourier 包络和宽度审计；不宣称物理周期、概率覆盖、联合最优界或精确有理证明 |
| 主张—证据—反例—实验图谱 | 255 个节点、672 条边，所有节点链接实际证据文件 | `exports/frontier-knowledge-graph.json`、`contracts/frontier-knowledge-graph.schema.json` | 为上游和组件提供同时包含支持、反例与限制的可追溯接口 |

## 范围感知外部分析适配层

新外部分析包装器使用 `scripts/external_coverage_scoped.py`，不在旧冻结驱动上改文案或重跑旧结果。调用形式：

```python
from external_coverage_scoped import run_scoped_external_analysis

summary = run_scoped_external_analysis(PROTOCOL, Path(__file__).resolve())
```

第二个参数是调用方文件，原有 `analysis_runner_sha256` 继续标识实际包装器；适配器另写入 `analysis_scope.scope_adapter_sha256`。当前适配器哈希为 `a6f53ffea1e743fdae839677b45938274652af0ac8bd70bd503e11afe74fb548`。

新协议应在 `implementation_rule` 中同时冻结 `driver`、`driver_sha256` 和 `scope_adapter_sha256`，并在 `candidate_rule.scope_limitation` 中写明数据专属候选边界。未提供专属文本时，适配器只从 `dataset_scope.native_model` 的首段生成说明；存在 `related_prior_dataset` 时，强制保留 `independent_model_family_test=false` 和关联数据名称。驱动或适配器哈希不符会在调用拟合前停止。

该适配层只修正文档范围和实现追溯，不改变模型、折分、优化器、半径、协方差、数值界或失败判定。旧协议和旧包装器不回改；下一组新数据必须在自己的前瞻协议中冻结上述字段。

## 极值报告生成门禁

`build_frontier_word.main` 在创建 Word 前调用 `enforce_extreme_reporting_gate`。`maximum_full_composition` 和 `extreme_reporting` 必须先通过 L2 的字段与数值关系检查；`extreme_corpus` 必须先通过全集覆盖、分级和原文哈希保持检查。任何错误都会在 Pandoc、DOCX 写入和视觉处理之前终止，不允许先生成文件再补救。

非极值报告模式不经过这组专用门禁，原有生成流程保持不变。三份相关 Word 均已通过实际门禁重建；验收失败测试覆盖伪造的典型性主张和不完整全集，不需要修改历史原文即可拒绝生成。

## 与自动科学发现项目的配合

- **Co-Scientist**：把“生成—批评—改进”产生的假设转成本证据包的验证义务；没有原始证据的假设不进入 `verified`。
- **Robin**：复用专业代理分工和公开轨迹，把湿实验、计算与文献主张分别标记；不把自动化程度当准确性。
- **Kosmos**：借鉴结构化世界模型和代码/原始文献双引用，同时保留准确率分层与独立人工复核。

## 与千界花园和组件的边界

证据包是稳定的 JSON 数据产品，可供独立组件读取。组件仍放 `garden-widgets` 或新的专用组件仓库，不写入 `bloombloomgarden` 主仓库。当前文件是通用接口，不声称已经完成花园原生 Binding；组件需要展示时，应以 `items[]` 为输入，并直接显示每条 `limitations`，不能只展示“成功”。

## 回馈规则

上游回馈必须来自实际运行结果，附输入、版本、命令和输出。数据库快照只用于指定日期的复核；数据更新后重新生成，不覆盖历史。任何 issue、PR 或对外发送都需另行明确授权。
