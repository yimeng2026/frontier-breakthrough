"""Assemble verified research notes from garden drafts and live figures."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "garden" / "drafts"
OUT = ROOT / "papers"


def replace_once(text, old, new):
    assert text.count(old) == 1, f"Expected exactly one occurrence: {old[:100]}"
    return text.replace(old, new, 1)


def insert_before(text, anchor, addition):
    return replace_once(text, anchor, addition + "\n\n" + anchor)


def body(path):
    raw = json.loads(path.read_text(encoding="utf-8"))["content"]
    return raw[raw.index("## 摘要"):]


def fig(name, caption, analysis):
    return f"![{caption}]({name})\n\n*图注：{caption}。*\n\n{analysis}"


def collapse_abstract(text, keywords=None):
    match = re.search(r"## 摘要\n\n(.*?)(\n\n---)", text, flags=re.S)
    assert match, "Abstract block not found"
    source = match.group(1)
    existing = re.search(r"\*\*关键词\*\*：(.+)$", source, flags=re.S)
    keyword_text = keywords or (existing.group(1).strip() if existing else None)
    source = re.sub(r"\n?\s*\*\*关键词\*\*：.+$", "", source, flags=re.S)
    abstract = " ".join(source.split())
    addition = ("\n\n**关键词**：" + keyword_text) if keyword_text else ""
    return text[:match.start()] + "## 摘要\n\n" + abstract + addition + match.group(2) + text[match.end():]


def header(title, english, category):
    return (f"# {title}\n**{english}**\n---\n"
            "> **作者** | 千界花园学术系统\n"
            "> **单位** | 千界花园学术系统 · 前沿共生计划\n"
            "> **日期** | 2026年10月\n"
            f"> **分类** | {category} · 研究简报／预印本草案（未同行评议）\n"
            "> **文档血缘** | 千界花园流水线初稿，经数值、来源与边界核验修订\n---\n\n")


# Paper 01 -------------------------------------------------------------------
p1 = body(DRAFTS / "01-evidence-chain.json")
p1 = p1.replace("### 1.4 证据链声明（本简报核心命题）", "### 1.4 本文的研究动机与内容安排")
p1 = p1.replace("ChEMBL 20", "ChEMBL")
p1 = p1.replace("唯一被检出的 Ki 测定", "选定的 Ki 测定")
p1 = p1.replace("唯一检出的活性记录", "选定的活性记录")
p1 = p1.replace("活性层仅检出**一条** Ki 记录", "活性层选取**一条** Ki 记录")
p1 = replace_once(p1,
    "本文采取\"数据核型\"（data karyotyping）方法：不生成新实验数据，而是对既有开放数据进行逐层身份核验（identity verification）、结构证据确认（structural corroboration）与活性边界划定（activity boundary demarcation）。本文明确**不是**实验复现（experimental replication）；文中所有数值均可溯源至指定的数据库条目与本地计算。",
    "本文将“数据核型”作为内部工作术语，指对既有开放数据进行逐层身份核验、结构证据确认与活性边界划定；它不表示一个既有独立学科分类。本文不生成新实验数据，也明确**不是**实验复现；所有数值均可溯源至指定数据库条目与本地计算。")
p1 = re.sub(r"### 1\.3 相关工作与已知结果\n\n.*?(?=### 1\.4)",
    "### 1.3 相关工作与已知结果\n\n3HS4 的原始论文报告了人 CA II 与乙酰唑胺的高分辨率复合物；ChEMBL 则提供化合物、靶点、策划机制和具体活性测量。本文只使用这些可回查记录，不以“教科书共识”代替数据审计，也不把选定 assay 的数值当成全部文献的唯一值。\n\n", p1, flags=re.S)
p1 = re.sub(r"\$\$\\mathrm\{pChEMBL\} = .*?\$\$",
    lambda _: "$$\\mathrm{pChEMBL}=-\\log_{10}\\!\\left(K_i[\\mathrm{mol\\,L^{-1}}]\\right).$$", p1, count=1, flags=re.S)
p1 = re.sub(r"\$\$-\\log_\{10\}\(1\.2\\times 10\^\{-8\}\).*?\$\$",
    lambda _: "$$-\\log_{10}(12\\times10^{-9})=7.920818753952375\\ldots$$", p1, count=1, flags=re.S)
p1 = p1.replace("其他记录**可能**源自同一实验的多次上报", "其他记录**可能**存在重复；具体原因需由原始实验和数据库血缘进一步判断")
p1 = p1.replace("其一，警告的语义是\"可能重复\"而非\"已证伪\"，按无罪推定原则不应删除有效数据", "其一，警告的语义是\"可能重复\"而非\"已证伪\"，不能在缺乏依据时删除待审计记录")
p1 = insert_before(p1, "### 3.2 逐层核验状态", fig("fig01a_sequence_identity.png", "CA II 的 260 个残基逐字符一致", "图中每位置均为 1，表示 P00918 与 3HS4 entity 1 在全部 260 个位置一致。这是序列身份核验，不是酶功能验证。"))
p1 = insert_before(p1, "### 3.3 结构性发现", fig("fig01b_activity_pchembl.png", "选定 assay 的 Ki 与 pChEMBL 重算", "左图只表示 CHEMBL657848 的 12 nM；右图外部记录为 7.92，本地重算为 7.920818753952375。二者精度不同，不应被解释为实验误差。"))
p1 = insert_before(p1, "---\n\n## 四、讨论",
    fig("fig01c_evidence_chain.png", "药物—靶点—序列—实验结构的分层证据链", "四层节点分别回答“是谁、作用于谁、序列是否对应、是否存在实验复合物”。底部活性节点单独标明 assay 与重复警告，避免把不同证据类型压成一个成功标签。") + "\n\n" +
    fig("fig01d_descriptor_audit.png", "TPSA 与 LogP 的算法口径对照", "TPSA 在计入 S/P 后为 151.66 Å²，与 PubChem 整数显示 152 同口径；MolLogP 与 XLogP 则属于不同算法，数值差异不能直接判作数据造假。"))
p1 = insert_before(p1, "---\n\n## 五、结论", """### 4.5 不同构建的结构对照与“独立重复”的边界

为检查结构证据能否跨实验成立，本文进一步比较 1997 年的 2H4N 与 2009 年的 3HS4。二者均为 X 射线衍射的人 CA II—乙酰唑胺实验结构，配体均为 AZM，分辨率分别为 1.9 Å 与 1.1 Å。它们提供的是不同时间、不同构建的结构对照，而不是同一野生型复合物的独立重复。

全局序列对齐显示三类差异：起始 M 缺失、H94N 替换和中段 P 插入。2H4N 返回序列字符串为 260 aa，而对应元数据 `rcsb_sample_sequence_length=259`，这一长度不一致必须保留并回查原始 mmCIF。本文没有把 2H4N 简化为“仅一个点突变”，也没有比较两者的结合几何或 Ki，因此不将其写成活性重复。

候选排除同样重要：1CA2 虽为 CA II 但不含 AZM；3UCJ 来自绿藻；2XTK 来自真菌几丁质酶。只有先通过物种、蛋白身份、构建和配体检查，才能进入结构对照集合。

""" + fig("fig01e_structural_control.png", "2H4N 与 3HS4 的不同构建结构对照", "左图比较 3HS4 的 1.1 Å 与 2H4N 的 1.9 Å 分辨率；右图列出三类序列差异及 260/259 的长度元数据不一致。该对照丰富实验背景，但不满足同一野生型复合物的独立重复定义。") + "\n\n")
p1_refs = """## 参考文献

[1] EMBL-EBI. ChEMBL molecule CHEMBL20（ACETAZOLAMIDE）及 molecule_structures。https://www.ebi.ac.uk/chembl/api/data
[2] EMBL-EBI. ChEMBL target CHEMBL205（Carbonic anhydrase 2，Homo sapiens，component P00918）。同上。
[3] EMBL-EBI. Activity 47560；assay CHEMBL657848；document CHEMBL1146805。Ki=12 nM，pChEMBL=7.92，potential_duplicate=1。同上。
[4] NCBI. PubChem CID 1986（Acetazolamide），MolecularFormula、ConnectivitySMILES、InChIKey、TPSA 与 XLogP。https://pubchem.ncbi.nlm.nih.gov/rest/pug
[5] UniProt Consortium. UniProtKB reviewed P00918（CAH2_HUMAN），260 aa reviewed 序列。https://rest.uniprot.org
[6] RCSB PDB. 3HS4：Human carbonic anhydrase II complexed with acetazolamide；entity 1 与 AZM entity 4。https://data.rcsb.org/rest/v1/core
[7] Sippel KH, Robbins AH, Domsic J, Genis C, Agbandje-McKenna M, McKenna R. High-resolution structure of human carbonic anhydrase II complexed with acetazolamide reveals insights into inhibitor drug design. Acta Crystallographica Section F, 2009, 65:992–995. DOI: 10.1107/S1744309109036665（元数据由 PDB 3HS4 回读）。
[8] RDKit contributors. RDKit 2026.9.1：规范结构、TPSA、Crippen MolLogP 与 ExactMolWt 的本地计算。https://github.com/rdkit/rdkit
[9] 本研究快照：`validation/chembl-acetazolamide.json`、`validation/pdb-3hs4.json`、`validation/pdb-3hs4-ca2.json`、`validation/uniprot-ca2.json`、`validation/pubchem-acetazolamide.json`。
[10] RCSB PDB. 2H4N：H94N carbonic anhydrase II complexed with acetazolamide；entity 1 与 AZM entity 3。https://data.rcsb.org/rest/v1/core
[11] Lesburg CA, Huang C, Christianson DW, Fierke CA. Histidine --> carboxamide ligand substitutions in the zinc binding site of carbonic anhydrase II alter metal coordination geometry but retain catalytic activity. Biochemistry, 1997, 36:15780–15791. DOI: 10.1021/bi971296x（元数据由 PDB 2H4N 回读）。
[12] 本研究结构对照：`validation/pdb-2h4n.json` 与 `validation/structural-control.json`，由 `scripts/analyze_structural_control.py` 全局对齐生成。

## 附录 A：复现路径

1. 依次运行 `python scripts/verify_rdkit.py`（使用 D 盘 RDKit 环境）、`python scripts/verify_ca2_sequence.py` 和 `python scripts/verify_drug_target_structure.py`。
2. 检查 CHEMBL20 与 PubChem CID 1986 的 InChIKey 均为 `BZKPWHYZMXOIDC-UHFFFAOYSA-N`，规范结构一致。
3. 检查 P00918 与 3HS4 entity 1 的 260 aa 逐字符一致，MD5 为 `94EB709966E01FBC15DC1C46A0D03AC5`。
4. 检查 3HS4 的实验方法为 X-RAY DIFFRACTION、分辨率 1.1 Å、AZM 位于 entity 4。
5. 检查 Ki=12 nM 仅属于 CHEMBL657848；重算 `−log10(12×10⁻⁹)=7.920818753952375`，并保留 `potential_duplicate=1`。
6. 全部结论只覆盖数据库与本地计算，不包含湿实验或独立实验复现。
7. 运行 `python scripts/analyze_structural_control.py`，复核 2H4N 的不同构建、三类序列差异及 260/259 长度元数据不一致；不得将其写为独立野生型重复。
"""
p1 = p1[:p1.index("## 参考文献")] + p1_refs
p1 = collapse_abstract(p1)
p1 = header("乙酰唑胺—碳酸酐酶 II 的跨库证据链", "An Auditable Cross-Database Evidence Chain from Acetazolamide to Human Carbonic anhydrase II", "化学信息学 · 结构生物学 · 跨库复核") + p1


# Paper 02 -------------------------------------------------------------------
p2 = body(DRAFTS / "02-selectivity-stability.json")
p2 = p2.replace("### 1.4 为什么该问题在当前数据中具有方法学尖锐性", "### 1.4 本文的研究动机与内容安排")
p2 = p2.replace("### 3.2 不执行跨文献合并的理由", "### 3.3 不执行跨文献合并的理由")
p2 = p2.replace("20.8333333333333332", "20.833333333333332")
p2 = p2.replace("\\gamma(II)", "\\gamma_m(II)")
p2 = p2.replace("非同方法充分可比条件下的合并固定比值不可识别", "在所述异质性条件下，固定比值的合并估计缺乏可识别性")
pair_rows = """### 3.2 六组文档配对明细

| 编号 | ChEMBL 文档 | CA I / CA II Ki（nM） | 表观比值 | 方法状态 | 双方重复标记 |
|---|---|---:|---:|---|---|
"""
stability = json.loads((ROOT / "validation" / "ca-document-stability.json").read_text(encoding="utf-8"))
for i, pair in enumerate(stability["pairs"], 1):
    method = "明确同酯酶" if pair["method_status"] == "explicit_matched" else "信息不足"
    pair_rows += f"| D{i} | {pair['document_chembl_id']} | {pair['ca_i_ki_nM']:g} / {pair['ca_ii_ki_nM']:g} | {pair['ki_ratio']:.4f} | {method} | {pair['ca_i_duplicate']} / {pair['ca_ii_duplicate']} |\n"
pair_rows += "\nD1–D6 的“不同文档”不自动等于独立实验；相同数值与重复标记限制了独立性解释。\n"
p2 = insert_before(p2, "### 3.3 不执行跨文献合并的理由", pair_rows)
p2 = insert_before(p2, "### 3.2 六组文档配对明细",
    fig("fig02a_document_ratios.png", "六组文档的 CA I/II 表观 Ki 比", "六组比值依次为 20.8333、75、75、28.5714、20.8333、75。只有 D1 明确同酯酶方法，因此不能把这六个数当成同一总体的独立随机样本。") + "\n\n" +
    fig("fig02b_ki_pairs.png", "六组文档内 CA I 与 CA II 的 Ki 配对", "对数坐标显示 CA I 与 CA II 的绝对 Ki 水平及配对间距。D4 的比值为 200/7=28.5714，而其他多组为 250/12 或 900/12，说明端点并非全部数据。"))
p2 = insert_before(p2, "---\n\n## 四、讨论",
    fig("fig02c_method_completeness.png", "同方法信息完整性：仅 1/6 明确匹配", "绿色部分是允许计算同方法表观比值的 D1；灰色五组不进入同方法合并。这个 1/5 划分是限制，不是额外实验样本量。") + "\n\n" +
    fig("fig02d_assay_methods.png", "CA I、CA II、CA IX 的 assay 方法对照", "CA I 与 CA II 可计算同酯酶方法的表观比值 20.8333；CA IX 使用 CO2 水合酶方法，只列出 Ki=25 nM 和 pChEMBL=7.60，不计算跨方法选择性比。"))
p2 = p2.replace("### 3.3 负结果的呈现", "### 3.4 负结果的呈现")
p2_refs = """## 参考文献

[1] EMBL-EBI. ChEMBL activities 47559/47560/47561，document CHEMBL1146805，record_id=235477；CA I/II 为 esterase，CA IX 为 CO2 hydrase。https://www.ebi.ac.uk/chembl/api/data
[2] EMBL-EBI. Activities 49652/49653，document CHEMBL1133556，record_id=282506。Ki 900/12 nM，方法描述未给出酯酶细节。同上。
[3] EMBL-EBI. Activities 80687/80688，document CHEMBL1146697，record_id=136210。Ki 900/12 nM，方法信息不足。同上。
[4] EMBL-EBI. Activities 106505/106506，document CHEMBL1136178，record_id=180522。Ki 200/7 nM，双方 potential_duplicate=0。同上。
[5] EMBL-EBI. Activities 151872/151873，document CHEMBL1146695，record_id=126435。Ki 250/12 nM，方法信息不足。同上。
[6] EMBL-EBI. Activities 288595/288596，document CHEMBL1134204，record_id=302270。Ki 900/12 nM，方法信息不足。同上。
[7] EMBL-EBI. Assay CHEMBL873200、CHEMBL657848、CHEMBL657970：用于核对 esterase 与 CO2 hydrase 方法及 confidence_score=8。同上。
[8] 本研究原始面板与计算：`validation/chembl-ca-selectivity-panel.json`、`validation/ca-selectivity.json`、`validation/chembl-ca-document-pairs.json`、`validation/ca-document-stability.json`。

## 附录 A：复现路径

1. 运行 `python scripts/analyze_ca_selectivity.py`，检查 CA I/II 的 250/12=20.833333333333332，ΔpChEMBL=1.3187587626244124。
2. 确认 CA IX 的 25 nM 属于 CO2 hydrase assay，脚本强制 `ca_ix_ratio_computed=false`。
3. 运行 `python scripts/analyze_ca_document_stability.py`，枚举六组文档，得到最小 20.8333、最大 75、极差倍数 3.6。
4. 检查 `strict_method_matched_count=1`、`method_incomplete_count=5`、`meta_analysis_performed=false`。
5. 探索性中位数仅保留在机器结果中并明确“不是选择性估计”；正文不以其替代固定常数。
"""
p2 = p2[:p2.index("## 参考文献")] + p2_refs
p2 = collapse_abstract(p2, "碳酸酐酶；表观 Ki；assay 可比性；跨文档敏感性；负结果")
p2 = header("CA I/II 表观活性比为什么不应当作固定常数", "Why the Apparent CA I/CA II Inhibition Ratio Should Not Be Treated as a Fixed Constant", "生物活性数据 · 方法学敏感性分析") + p2


# Paper 03 -------------------------------------------------------------------
p3 = body(DRAFTS / "03-reproducible-engines.json")
p3 = p3.replace("### 1.4 核心命题与贡献", "### 1.4 本文的研究动机与内容安排")
p3 = p3.replace("（按给定精度 0.00003136190275787598）", "")
p3 = p3.replace("0.00003190275787598", "0.00003136190275787598")
p3 = p3.replace("Z3 与 RDKit 在本简报中仅作为被钉住的本地引擎出现在清点中，其具体断言留待后续工作；此处不作运行结果陈述。",
    "Z3 的两个实数不可满足约束均返回 UNSAT；RDKit 与 PubChem 的规范结构、分子式和精确质量一致，TPSA 与 LogP 差异按算法口径保留。它们分别是已知约束验证和跨库算法审计。")
p3 = p3.replace("5. 对 Z3/RDKit：本阶段仅核对“可被钉住且可加载”的环境事实；其具体运行断言属后续工作，不在本 r‑bundle 中声明结论。",
    "5. 对 Z3：复核 `x>0 ∧ x+1≤0` 与 `x²<0` 均为 UNSAT。对 RDKit：复核规范结构、分子式与精确质量；TPSA 必须区分 N/O 与 S/P 口径，LogP 必须区分算法。")
p3 = p3.replace("仅当输出等于 0.00003136190275787598 时，记为验证通过", "仅当输出与保存结果一致且满足脚本阈值（最大系数误差 <1e-4）时，记为验证通过")
p3 = p3.replace("仅当输出等于 2.3128002565764314 g·cm⁻³ 时，记为快照复核通过", "仅当本地密度与快照密度之差 <1e-6 g·cm⁻³ 时，记为快照复核通过")
p3 = p3.replace("一致性判据的唯一性：步骤 2–3 的通过条件**严格等于**上述两个给定数值；不得用“容差内”“约等于”替代（浮点一致性的实现范围已在 \\(L\\) 中声明并钉住）。",
    "一致性判据使用脚本明示容差与记录精度，不要求跨硬件位级一致。PySINDy 的误差上限为 1e-4，密度差上限为 1e-6 g·cm⁻³；浮点与数值微分误差必须保留。")
p3 = insert_before(p3, "### 3.3 硅密度的快照复核（对 \\(S\\)）", fig("fig03a_sindy_coefficients.png", "PySINDy 对已知线性系统的系数恢复", "恢复系数约为 −2.00003136 与 1.00000404，最大误差 3.136×10⁻⁵。图证明的是指定实现的已知答案验证，不是从真实自然数据发现新规律。"))
p3 = insert_before(p3, "### 3.4 证据汇总（最小数值集）", fig("fig03b_material_recompute.png", "Materials Project 与本地 PyMatGen 的硅密度对照", "两者均为 2.3128002565764314 g/cm³，空间群重算为 Fd-3m (227)。带隙 0.6103 eV 仍标为外部 DFT 数据，未在本地重算。"))
p3 = insert_before(p3, "---\n\n## 四、讨论",
    fig("fig03c_sequence_bridges.png", "HBB 与 CA II 的结构—序列映射规则", "HBB 需要去掉 UniProt 起始 M 后与 4HHB 的 146 aa 对应；CA II 则是 260 aa 全长一致。不同对齐规则必须显式声明，不能只用“相似”概括。") + "\n\n" +
    fig("fig03d_evidence_boundaries.png", "四个轻量引擎的证据类型与限制", "PySINDy 和 Z3 是已知答案验证，RDKit 是跨库算法审计，PyMatGen 是公开快照复核。任何“发现”都需要额外数据、留出验证和独立实验。"))
p3_refs = """## 参考文献

[1] de Silva BM, Champion K, Quade M, et al. PySINDy: a Python package for the sparse identification of nonlinear dynamics from data. arXiv:2004.08424（Scholar 检索返回）。
[2] Kaptanoglu AA, de Silva BM, Fasel U, et al. PySINDy: A comprehensive Python package for robust sparse system identification. arXiv:2111.08481（Scholar 检索返回）。
[3] PySINDy contributors. PySINDy 2.1.0：本地线性库与 STLSQ 验证。https://github.com/dynamicslab/pysindy
[4] Z3 contributors. Z3 5.3.3.0：实数约束求解与 UNSAT 结果。https://github.com/Z3Prover/z3
[5] RDKit contributors. RDKit 2026.9.1：规范结构与分子描述符。https://github.com/rdkit/rdkit
[6] Materials Project. PyMatGen 2026.10.24：结构、密度与空间群分析。https://github.com/materialsproject/pymatgen
[7] Jain A, Ong SP, Hautier G, Chen W, Richards WD, et al. Commentary: The Materials Project: A materials genome approach to accelerating materials innovation. APL Materials, 2013（Scholar 检索返回）。
[8] RCSB PDB 与 UniProt Consortium：4HHB/HBB_HUMAN、3HS4/CAH2_HUMAN 的结构与 reviewed 序列快照。https://data.rcsb.org/rest/v1/core；https://rest.uniprot.org
[9] 本研究全部机器可读结果：`validation/pysindy.json`、`validation/z3.json`、`validation/rdkit.json`、`validation/pymatgen.json`、`validation/pdb-uniprot.json`、`validation/ca2-sequence.json`。

## 附录 A：复现路径

1. 在 D 盘隔离环境分别运行 `verify_pysindy.py`、`verify_z3.py`、`verify_rdkit.py` 和 `verify_pymatgen.py`；依赖锁定见 `requirements/`。
2. 运行 `python scripts/verify_pdb_uniprot.py` 与 `python scripts/verify_ca2_sequence.py`，复核两类序列对齐规则。
3. 运行 `python scripts/export_evidence_packet.py --check`、`python scripts/build_catalog.py --check` 和 `python -m unittest discover -s tests -v`，确认统一证据包未漂移。
4. 图由 `python scripts/build_paper_figures.py` 从保存的 JSON 重新计算，不使用手工填写的 mock 数据。
5. 所有结果只限指定版本、样例和算法口径；真实数据发现需要另行设计留出验证与独立实验。
"""
p3 = p3[:p3.index("## 参考文献")] + p3_refs
p3 = collapse_abstract(p3)
p3 = header("轻量可复现科研引擎的协作方法", "A Collaboration Method for Lightweight Reproducible Scientific Engines", "AI for Science · 可复现基础设施") + p3


files = [
    ("01_乙酰唑胺跨库证据链", "01_乙酰唑胺跨库证据链.md", p1, "d504fd42-1eb2-4560-909f-b4243998a8c8"),
    ("02_CA表观比值不稳定性", "02_CA表观比值不稳定性.md", p2, "8ada04a1-2ee8-4603-a642-88902c439d96"),
    ("03_轻量可复现科研引擎", "03_轻量可复现科研引擎.md", p3, "c306e81f-bce6-4d5b-b482-7a26c94da774"),
]
manifest = []
for folder, filename, content, pipeline_id in files:
    target_dir = OUT / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    content = re.sub(r"[ \t]+\n", "\n", content)
    (target_dir / filename).write_text(content, encoding="utf-8")
    figures = sorted(target_dir.glob("fig*.png"))
    expected_figures = 5 if folder == "01_乙酰唑胺跨库证据链" else 4
    assert len(figures) == expected_figures, (folder, len(figures))
    assert "### 1.4" in content
    assert content.count("## 参考文献") == 1
    assert "mock" not in content.lower() or "不使用 mock 数据" in content or "不使用手工填写的 mock 数据" in content
    manifest.append({"folder": folder, "file": filename, "pipelineId": pipeline_id, "status": "研究简报／预印本草案，未同行评议", "characters": len(content), "figures": len(figures), "figureFiles": [f.name for f in figures]})

collection = "# 前沿共生研究简报合订本\n\n**文档性质**：三篇研究简报／预印本草案，未同行评议；由千界花园流水线生成初稿并经证据核验修订。\n\n## 目录\n\n"
for item in manifest:
    collection += f"- {item['file'].removesuffix('.md')}\n"
for item in manifest:
    text = (OUT / item["folder"] / item["file"]).read_text(encoding="utf-8")
    text = text.replace("](fig", f"]({item['folder']}/fig")
    collection += "\n\n＝＝＝＝＝＝＝\n\n" + text
(OUT / "前沿共生研究简报_合订本.md").write_text(collection, encoding="utf-8")
(OUT / "manifest.json").write_text(json.dumps({"schemaVersion": 1, "papers": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
