"""Compare MP/OQMD DFT records with independent PyMatGen structure calculations."""

import hashlib
import json
from pathlib import Path

from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/material-crosscheck.json"
FIGURE = ROOT / "papers/05_材料跨库复核/fig05_material_crosscheck.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_symbol(symbol):
    return symbol.replace(" ", "").replace("_", "")


def main():
    protocol = json.loads((ROOT / "validation/material-crosscheck-protocol.json").read_text(encoding="utf-8"))
    amendment = json.loads((ROOT / "validation/material-crosscheck-protocol-amendment-01.json").read_text(encoding="utf-8"))
    materials = []
    for key, pair in protocol["pairs"].items():
        mp = json.loads((ROOT / f"validation/materials-project-{key}-dft.json").read_text(encoding="utf-8"))
        oqmd = json.loads((ROOT / f"validation/oqmd-{key}.json").read_text(encoding="utf-8"))
        structure_record = json.loads((ROOT / f"validation/oqmd-structure-{key}.json").read_text(encoding="utf-8"))
        corrected = amendment["corrected_pairs"][key]
        if structure_record["id"] != corrected["optimade_structure_id"] or oqmd["entry_id"] != corrected["native_entry_id"]:
            raise ValueError(f"Corrected ID mismatch for {key}")
        attributes = structure_record["attributes"]
        structure = Structure(
            attributes["lattice_vectors"], attributes["species_at_sites"],
            attributes["cartesian_site_positions"], coords_are_cartesian=True,
        )
        if len(structure) != attributes["nsites"] or len(structure) != mp["nsites"]:
            raise ValueError(f"Site-count mismatch for {key}")
        analyzer = SpacegroupAnalyzer(structure, symprec=0.1)
        local_symbol = analyzer.get_space_group_symbol()
        local_number = analyzer.get_space_group_number()
        local_density = float(structure.density)
        symbols = {
            normalize_symbol(local_symbol),
            normalize_symbol(mp["symmetry"]["symbol"]),
            normalize_symbol(oqmd["spacegroup"]),
        }
        if len(symbols) != 1:
            raise ValueError(f"Space-group mismatch for {key}: {symbols}")
        band_gap_difference = float(oqmd["band_gap"] - mp["band_gap"])
        density_relative_difference = abs(local_density - mp["density"]) / mp["density"]
        materials.append({
            "key": key,
            "formula": pair["formula"],
            "mp": mp,
            "oqmd": oqmd,
            "oqmd_structure_id": structure_record["id"],
            "local": {
                "density_g_cm3": local_density,
                "space_group_symbol": local_symbol,
                "space_group_number": local_number,
                "nsites": len(structure),
                "volume_A3": float(structure.volume),
                "method": "PyMatGen Structure.density and SpacegroupAnalyzer(symprec=0.1) on OQMD OPTIMADE lattice/sites",
            },
            "band_gap_mp_eV": mp["band_gap"],
            "band_gap_oqmd_eV": oqmd["band_gap"],
            "band_gap_difference_oqmd_minus_mp": band_gap_difference,
            "density_mp_g_cm3": mp["density"],
            "density_relative_difference_abs": density_relative_difference,
            "stability_mp_energy_above_hull": mp["energy_above_hull"],
            "stability_oqmd": oqmd["stability"],
            "structure_identity_match": True,
        })
    report = {
        "status": "verified",
        "structure_identity_confirmed": all(item["structure_identity_match"] for item in materials),
        "differences_not_called_fraud": True,
        "global_dft_benchmark_claimed": False,
        "independent_experiment": False,
        "id_spaces_separate": True,
        "materials": materials,
        "protocol_sha256": sha256(ROOT / "validation/material-crosscheck-protocol.json"),
        "protocol_amendment_sha256": sha256(ROOT / "validation/material-crosscheck-protocol-amendment-01.json"),
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
        "limitations": [
            "Three paired structures are a methods demonstration, not a global DFT accuracy benchmark or new material discovery",
            "Band gaps and stability fields come from different DFT workflows and convex-hull references; they are not forced equal",
            "Local density is recomputed from OQMD structures; MP density may correspond to another structure snapshot or setting",
            "No independent experiment, experimental band gap or universal ranking of DFT implementations is claimed",
        ],
    }
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous != report:
            raise ValueError("Refusing to overwrite a different material crosscheck")
    else:
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

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
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    for index, item in enumerate(materials):
        ax.text(index, max(item["density_mp_g_cm3"], item["local"]["density_g_cm3"]) + 0.08, f"{item['density_relative_difference_abs'] * 100:.2f}%", ha="center", fontsize=9)
    fig.suptitle("Cross-database checks quantify differences without calling them fraud", fontsize=13)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "materials": [{"key": item["key"], "band_gap_delta": item["band_gap_difference_oqmd_minus_mp"], "density_local": item["local"]["density_g_cm3"], "space_group": item["local"]["space_group_symbol"]} for item in materials]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
