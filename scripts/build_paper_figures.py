"""Generate paper figures exclusively from saved evidence JSON files."""
from pathlib import Path
import json
import math
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "papers"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.figsize": (7.2, 4.2),
    "font.size": 10,
})
BLUE, GRAY, ORANGE, GREEN, RED = "#2f6b9a", "#8a9299", "#b8752a", "#3b7d5c", "#a64b4b"


def load(name):
    return json.loads((ROOT / "validation" / name).read_text(encoding="utf-8"))


def save(fig, folder, name):
    target = OUT / folder
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"{path.relative_to(ROOT)}\t{path.stat().st_size}")


drug = load("drug-target-structure.json")
rdkit = load("rdkit.json")
stability = load("ca-document-stability.json")
selectivity = load("ca-selectivity.json")
sindy = load("pysindy.json")
material = load("pymatgen.json")
hbb = load("pdb-uniprot.json")
ca2 = load("ca2-sequence.json")
structural_control = load("structural-control.json")
p1 = "01_乙酰唑胺跨库证据链"
p2 = "02_CA表观比值不稳定性"
p3 = "03_轻量可复现科研引擎"

# 01a：全长序列逐字符一致，不用相似度百分比代替。
fig, ax = plt.subplots()
x = np.arange(1, ca2["sequence_length"] + 1)
ax.fill_between(x, 0, 1, color=GREEN, alpha=0.75, step="mid")
ax.set(xlabel="CA II 残基位置", ylabel="逐字符一致（1=一致）", title="P00918 与 3HS4 entity 1：260/260 一致", ylim=(-0.05, 1.15), xlim=(1, 260))
ax.set_yticks([0, 1])
ax.grid(axis="x", alpha=0.2)
save(fig, p1, "fig01a_sequence_identity.png")

# 01b：选定 assay 与 pChEMBL 重算，两个量分轴呈现。
fig, axes = plt.subplots(1, 2)
axes[0].bar(["CHEMBL657848"], [drug["ki_nM"]], color=BLUE)
axes[0].set(title="选定活性记录", ylabel="Ki（nM）", ylim=(0, 14))
axes[0].text(0, drug["ki_nM"] + 0.4, "12", ha="center")
axes[1].bar(["ChEMBL 记录", "本地重算"], [drug["pchembl_external"], drug["pchembl_recomputed"]], color=[GRAY, BLUE])
axes[1].set(title="pChEMBL 对照", ylim=(7.85, 7.97))
for i, value in enumerate([drug["pchembl_external"], drug["pchembl_recomputed"]]):
    axes[1].text(i, value + 0.003, f"{value:.6f}", ha="center", fontsize=9)
save(fig, p1, "fig01b_activity_pchembl.png")

# 01c：证据链节点与边界。
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.axis("off")
nodes = [
    (0.12, 0.68, "化合物\nCHEMBL20\nPubChem 1986"),
    (0.38, 0.68, "靶点\nCHEMBL205\nUniProt P00918"),
    (0.64, 0.68, "蛋白序列\n3HS4 entity 1\n260 aa 完全一致"),
    (0.88, 0.68, "实验复合物\n3HS4 / AZM entity 4\nX 射线 1.1 Å"),
]
for x0, y0, text in nodes:
    ax.text(x0, y0, text, ha="center", va="center", bbox=dict(boxstyle="round,pad=0.55", fc="#f4f6f8", ec=BLUE, lw=1.2), fontsize=10)
for i in range(3):
    ax.annotate("", xy=(nodes[i+1][0]-0.09, 0.68), xytext=(nodes[i][0]+0.09, 0.68), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
ax.text(0.5, 0.20, "活性边界：CHEMBL657848 · Ki=12 nM · pChEMBL=7.92\n仅属于该 assay；potential_duplicate=1 保留，不作临床外推", ha="center", va="center", bbox=dict(boxstyle="round,pad=0.55", fc="#fff7e8", ec=ORANGE))
save(fig, p1, "fig01c_evidence_chain.png")

# 01d：描述符算法口径。
fig, axes = plt.subplots(1, 2)
labels = ["RDKit 默认", "RDKit 含 S/P", "PubChem"]
values = [rdkit["tpsa_default_NO_A2"], rdkit["tpsa_include_S_P_A2"], rdkit["pubchem_tpsa_A2"]]
axes[0].bar(labels, values, color=[GRAY, BLUE, ORANGE])
axes[0].set(title="TPSA：元素口径与取整", ylabel="Å²", ylim=(0, 170))
axes[0].tick_params(axis="x", rotation=15)
axes[1].bar(["RDKit MolLogP", "PubChem XLogP"], [rdkit["rdkit_crippen_mollogp"], rdkit["pubchem_xlogp"]], color=[BLUE, ORANGE])
axes[1].set(title="LogP：算法不同，保留差异", ylim=(-1.0, 0.1))
axes[1].axhline(0, color="black", lw=0.6)
save(fig, p1, "fig01d_descriptor_audit.png")

# 01e：不同构建的结构对照与序列/元数据异常。
fig, axes = plt.subplots(1, 2)
resolutions = [structural_control["reference"]["resolution_A"], structural_control["control"]["resolution_A"]]
axes[0].bar(["3HS4 野生型", "2H4N 对照构建"], resolutions, color=[GREEN, ORANGE])
axes[0].set(title="两套 X 射线实验结构", ylabel="分辨率（Å，越低越高）", ylim=(0, 2.3))
for i, value in enumerate(resolutions):
    axes[0].text(i, value + 0.06, f"{value:.1f}", ha="center")
axes[1].axis("off")
axes[1].set_title("结构对照的差异与边界")
axes[1].text(0.02, 0.82, "序列差异事件：3 类", fontsize=13, weight="bold")
axes[1].text(0.02, 0.62, "起始 M 缺失\nH94N 替换\n中段 P 插入", fontsize=11, linespacing=1.6)
axes[1].text(0.02, 0.26, "序列字符串 260 vs 元数据 259\n不是独立野生型重复，也不证明 Ki 重复", fontsize=11, color=ORANGE, linespacing=1.6)
save(fig, p1, "fig01e_structural_control.png")

# 02a：六组文档比值，方法状态显式区分。
pairs = stability["pairs"]
labels = [f"D{i+1}" for i in range(len(pairs))]
ratios = [p["ki_ratio"] for p in pairs]
colors = [GREEN if p["method_status"] == "explicit_matched" else GRAY for p in pairs]
fig, ax = plt.subplots()
ax.bar(labels, ratios, color=colors)
ax.set(xlabel="文档配对（D1–D6 按附表顺序）", ylabel="CA I Ki / CA II Ki", title="六组文档的表观比值：20.8333–75")
ax.axhline(ratios[0], color=GREEN, ls="--", lw=0.8)
for i, value in enumerate(ratios):
    ax.text(i, value + 1.2, f"{value:.2f}", ha="center", fontsize=9)
ax.text(0.01, 0.96, "绿色：明确同酯酶方法；灰色：方法信息不足", transform=ax.transAxes, va="top", fontsize=9)
save(fig, p2, "fig02a_document_ratios.png")

# 02b：对数坐标下每对 Ki，不能理解为独立重复。
fig, ax = plt.subplots()
x = np.arange(len(pairs))
ca_i = [p["ca_i_ki_nM"] for p in pairs]
ca_ii = [p["ca_ii_ki_nM"] for p in pairs]
for i in x:
    ax.plot([i, i], [ca_ii[i], ca_i[i]], color="#c9ced3", zorder=1)
ax.scatter(x, ca_i, label="CA I", color=ORANGE, zorder=3)
ax.scatter(x, ca_ii, label="CA II", color=BLUE, zorder=3)
ax.set_yscale("log")
ax.set_xticks(x, labels)
ax.set(xlabel="文档配对", ylabel="Ki（nM，对数坐标）", title="同一文档内的 CA I/II 配对值")
ax.legend()
ax.grid(axis="y", alpha=0.2)
save(fig, p2, "fig02b_ki_pairs.png")

# 02c：方法完整性决定能否合并。
fig, ax = plt.subplots()
ax.barh(["六组文档"], [1], color=GREEN, label="明确同酯酶方法：1")
ax.barh(["六组文档"], [5], left=[1], color=GRAY, label="方法信息不足：5")
ax.set(xlabel="文档配对数", title="只有 1/6 明确满足同方法比较", xlim=(0, 6))
ax.legend(loc="lower right")
save(fig, p2, "fig02c_method_completeness.png")

# 02d：CA IX 仅单列，不进入酯酶比值。
fig, ax = plt.subplots()
names = ["CA I\nesterase", "CA II\nesterase", "CA IX\nCO2 hydrase"]
vals = [selectivity["ca_i"]["pchembl"], selectivity["ca_ii"]["pchembl"], selectivity["ca_ix"]["pchembl"]]
ax.bar(names, vals, color=[ORANGE, BLUE, GRAY])
ax.set(ylabel="pChEMBL", title="同一文档的三条活性记录：方法不同不合并", ylim=(0, 9))
for i, value in enumerate(vals):
    ax.text(i, value + 0.15, f"{value:.2f}", ha="center")
ax.text(0.5, 0.05, "CA I/II 表观 Ki 比=20.8333；CA IX 不计算跨方法选择性比", transform=ax.transAxes, ha="center", fontsize=9)
save(fig, p2, "fig02d_assay_methods.png")

# 03a：PySINDy 真值与恢复值。
coeff = np.array(sindy["coefficients"])
fig, ax = plt.subplots()
x = np.arange(2)
width = 0.34
ax.bar(x-width/2, [-2, 1], width, label="解析真值", color=GRAY)
ax.bar(x+width/2, [coeff[0,0], coeff[1,1]], width, label="PySINDy 恢复", color=BLUE)
ax.set_xticks(x, ["x′ 的 x 系数", "y′ 的 y 系数"])
ax.set(ylabel="系数", title=f"已知线性系统恢复：最大误差 {sindy['max_abs_error']:.3e}")
ax.axhline(0, color="black", lw=0.6)
ax.legend()
save(fig, p3, "fig03a_sindy_coefficients.png")

# 03b：材料结构派生量复核；带隙标为外部数据。
fig, ax = plt.subplots()
vals = [material["density_external_g_cm3"], material["density_local_g_cm3"]]
ax.bar(["Materials Project", "本地 PyMatGen"], vals, color=[GRAY, BLUE])
ax.set(ylabel="密度（g/cm³）", title="同一 Si 结构的密度重算一致", ylim=(0, 2.8))
for i, value in enumerate(vals):
    ax.text(i, value + 0.06, f"{value:.10f}", ha="center", fontsize=8)
ax.text(0.5, 0.03, f"空间群：{material['space_group_local']} (227)；外部带隙 {material['external_band_gap_eV']:.4f} eV 未在本地重算", transform=ax.transAxes, ha="center", fontsize=9)
save(fig, p3, "fig03b_material_recompute.png")

# 03c：两种序列映射规则不能混写。
fig, ax = plt.subplots()
x = np.arange(2)
width = 0.34
ax.bar(x-width/2, [hbb["uniprot_length"], ca2["sequence_length"]], width, label="UniProt", color=GRAY)
ax.bar(x+width/2, [hbb["pdb_length"], ca2["sequence_length"]], width, label="PDB 实体", color=BLUE)
ax.set_xticks(x, ["HBB：去起始 M 后一致", "CA II：全长一致"])
ax.set(ylabel="序列长度（aa）", title="结构—序列映射：分别声明对齐规则")
ax.legend()
save(fig, p3, "fig03c_sequence_bridges.png")

# 03d：验证、复核与发现边界。
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.axis("off")
rows = [
    ("PySINDy", "已知答案验证", "约 −2、1；不是新规律"),
    ("Z3", "已知约束验证", "两个 UNSAT；不是通用定理证明"),
    ("RDKit", "跨库算法审计", "结构一致；描述符口径不同"),
    ("PyMatGen", "公开快照复核", "密度/空间群；DFT 未本地重算"),
]
ax.text(0.5, 0.93, "轻量引擎的认识论边界", ha="center", fontsize=15, weight="bold")
for i, (engine, kind, limit) in enumerate(rows):
    y = 0.76 - i * 0.18
    ax.text(0.08, y, engine, weight="bold", fontsize=11)
    ax.text(0.32, y, kind, color=BLUE, fontsize=11)
    ax.text(0.62, y, limit, fontsize=10)
    ax.plot([0.06, 0.94], [y-0.07, y-0.07], color="#e0e3e6", lw=0.8)
ax.text(0.5, 0.02, "发现主张需要额外数据、留出验证与独立实验，不能由运行成功自动晋升", ha="center", fontsize=9, color=ORANGE)
save(fig, p3, "fig03d_evidence_boundaries.png")
