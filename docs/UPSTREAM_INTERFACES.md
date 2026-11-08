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
| 主张—证据—反例—实验图谱 | 32 个节点、49 条边，所有节点链接实际证据文件 | `exports/frontier-knowledge-graph.json`、`contracts/frontier-knowledge-graph.schema.json` | 为上游和组件提供同时包含支持、反例与限制的可追溯接口 |

## 与自动科学发现项目的配合

- **Co-Scientist**：把“生成—批评—改进”产生的假设转成本证据包的验证义务；没有原始证据的假设不进入 `verified`。
- **Robin**：复用专业代理分工和公开轨迹，把湿实验、计算与文献主张分别标记；不把自动化程度当准确性。
- **Kosmos**：借鉴结构化世界模型和代码/原始文献双引用，同时保留准确率分层与独立人工复核。

## 与千界花园和组件的边界

证据包是稳定的 JSON 数据产品，可供独立组件读取。组件仍放 `garden-widgets` 或新的专用组件仓库，不写入 `bloombloomgarden` 主仓库。当前文件是通用接口，不声称已经完成花园原生 Binding；组件需要展示时，应以 `items[]` 为输入，并直接显示每条 `limitations`，不能只展示“成功”。

## 回馈规则

上游回馈必须来自实际运行结果，附输入、版本、命令和输出。数据库快照只用于指定日期的复核；数据更新后重新生成，不覆盖历史。任何 issue、PR 或对外发送都需另行明确授权。
