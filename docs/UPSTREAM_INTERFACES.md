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
| 主张—证据—反例—实验图谱 | 98 个节点、169 条边，所有节点链接实际证据文件 | `exports/frontier-knowledge-graph.json`、`contracts/frontier-knowledge-graph.schema.json` | 为上游和组件提供同时包含支持、反例与限制的可追溯接口 |

## 与自动科学发现项目的配合

- **Co-Scientist**：把“生成—批评—改进”产生的假设转成本证据包的验证义务；没有原始证据的假设不进入 `verified`。
- **Robin**：复用专业代理分工和公开轨迹，把湿实验、计算与文献主张分别标记；不把自动化程度当准确性。
- **Kosmos**：借鉴结构化世界模型和代码/原始文献双引用，同时保留准确率分层与独立人工复核。

## 与千界花园和组件的边界

证据包是稳定的 JSON 数据产品，可供独立组件读取。组件仍放 `garden-widgets` 或新的专用组件仓库，不写入 `bloombloomgarden` 主仓库。当前文件是通用接口，不声称已经完成花园原生 Binding；组件需要展示时，应以 `items[]` 为输入，并直接显示每条 `limitations`，不能只展示“成功”。

## 回馈规则

上游回馈必须来自实际运行结果，附输入、版本、命令和输出。数据库快照只用于指定日期的复核；数据更新后重新生成，不覆盖历史。任何 issue、PR 或对外发送都需另行明确授权。
