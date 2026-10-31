"""Independently recompute structure-derived fields from a public MP snapshot."""
import importlib.metadata
import json
from pathlib import Path

from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

OUT = Path(__file__).resolve().parents[1] / "validation"
external = json.loads((OUT / "materials-project-si.json").read_text(encoding="utf-8"))
structure = Structure.from_dict(external["structure"])
density = float(structure.density)
analyzer = SpacegroupAnalyzer(
    structure,
    symprec=external["symmetry"]["symprec"],
    angle_tolerance=external["symmetry"]["angle_tolerance"],
)
symbol = analyzer.get_space_group_symbol()
number = analyzer.get_space_group_number()
assert len(structure) == external["nsites"] == 2
assert structure.composition.reduced_formula == external["formula_pretty"] == "Si"
assert abs(density - external["density"]) < 1e-6, density
assert symbol == external["symmetry"]["symbol"] == "Fd-3m", symbol
assert number == external["symmetry"]["number"] == 227, number
report = {
    "engine": "PyMatGen",
    "version": importlib.metadata.version("pymatgen"),
    "python": "D:/research-engines/pymatgen-env/Scripts/python.exe",
    "material_id": external["material_id"],
    "formula": structure.composition.reduced_formula,
    "nsites": len(structure),
    "density_local_g_cm3": density,
    "density_external_g_cm3": external["density"],
    "density_abs_error": abs(density - external["density"]),
    "space_group_local": symbol,
    "space_group_number_local": number,
    "external_band_gap_eV": external["band_gap"],
    "external_energy_above_hull_eV_atom": external["energy_above_hull"],
    "status": "verified",
    "scope": "本地从公开结构独立重算密度与空间群并核对；带隙和稳定性仅为外部 DFT 快照，未在本机重算。",
}
(OUT / "pymatgen.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
