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
| ChEMBL + PubChem + RCSB PDB | 乙酰唑胺 InChIKey、CA II 靶点、单一 Ki assay、3HS4/AZM 配体与 pChEMBL 重算 | `validation/drug-target-structure.json` | 药物—靶点—实验结构的来源审计；保留重复标记和 assay 边界 |

## 与自动科学发现项目的配合

- **Co-Scientist**：把“生成—批评—改进”产生的假设转成本证据包的验证义务；没有原始证据的假设不进入 `verified`。
- **Robin**：复用专业代理分工和公开轨迹，把湿实验、计算与文献主张分别标记；不把自动化程度当准确性。
- **Kosmos**：借鉴结构化世界模型和代码/原始文献双引用，同时保留准确率分层与独立人工复核。

## 与千界花园和组件的边界

证据包是稳定的 JSON 数据产品，可供独立组件读取。组件仍放 `garden-widgets` 或新的专用组件仓库，不写入 `bloombloomgarden` 主仓库。当前文件是通用接口，不声称已经完成花园原生 Binding；组件需要展示时，应以 `items[]` 为输入，并直接显示每条 `limitations`，不能只展示“成功”。

## 回馈规则

上游回馈必须来自实际运行结果，附输入、版本、命令和输出。数据库快照只用于指定日期的复核；数据更新后重新生成，不覆盖历史。任何 issue、PR 或对外发送都需另行明确授权。
