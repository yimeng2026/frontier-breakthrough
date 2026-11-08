"""Presentation-only legend adjustment; material evidence is read-only."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / "validation/material-crosscheck.json").read_text(encoding="utf-8"))
materials = summary["materials"]
labels = [item["formula"] for item in materials]
x = np.arange(len(labels))
width = 0.35
fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.6), constrained_layout=True)
ax = axes[0]
ax.bar(x - width / 2, [item["band_gap_mp_eV"] for item in materials], width, label="Materials Project", color="#316c9b")
ax.bar(x + width / 2, [item["band_gap_oqmd_eV"] for item in materials], width, label="OQMD", color="#b47a3c")
ax.set_xticks(x, labels)
ax.set_ylabel("DFT band gap (eV)")
ax.set_title("Same structure identity, different DFT band gaps")
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.2)
for index, item in enumerate(materials):
    ax.text(index, max(item["band_gap_mp_eV"], item["band_gap_oqmd_eV"]) + 0.12, f"Δ={item['band_gap_difference_oqmd_minus_mp']:+.3f}", ha="center", fontsize=9)
ax = axes[1]
ax.bar(x - width / 2, [item["density_mp_g_cm3"] for item in materials], width, label="MP density", color="#487a52")
ax.bar(x + width / 2, [item["local"]["density_g_cm3"] for item in materials], width, label="PyMatGen on OQMD structure", color="#6c5b8e")
ax.set_xticks(x, labels)
ax.set_ylabel("Density (g cm$^{-3}$)")
ax.set_title("Independent density recomputation from lattice/sites")
ax.legend(frameon=False, loc="upper left")
ax.grid(axis="y", alpha=0.2)
for index, item in enumerate(materials):
    ax.text(index, max(item["density_mp_g_cm3"], item["local"]["density_g_cm3"]) + 0.08, f"{item['density_relative_difference_abs'] * 100:.2f}%", ha="center", fontsize=9)
fig.suptitle("Cross-database checks quantify differences without calling them fraud", fontsize=13)
figure = ROOT / "papers/05_材料跨库复核/fig05_material_crosscheck.png"
fig.savefig(figure, dpi=180)
print(figure)
