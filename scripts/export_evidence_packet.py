#!/usr/bin/env python3
"""Build a stable cross-domain evidence packet for downstream tools and widgets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"
OUTPUT = ROOT / "exports" / "frontier-evidence.json"


def read(name: str) -> dict:
    return json.loads((VALIDATION / name).read_text(encoding="utf-8"))


def build() -> dict:
    sindy = read("pysindy.json")
    z3 = read("z3.json")
    rdkit = read("rdkit.json")
    pymatgen = read("pymatgen.json")
    pdb = read("pdb-uniprot.json")
    drug = read("drug-target-structure.json")
    selectivity = read("ca-selectivity.json")
    stability = read("ca-document-stability.json")
    structuralControl = read("structural-control.json")
    chwirut = read("chwirut-holdout.json")
    z3identifiability = read("z3-identifiability.json")
    aspirin = read("aspirin-crosscheck.json")
    material = read("material-crosscheck.json")
    eckerle = read("eckerle4-two-tail.json")
    cvc5 = read("cvc5-crosscheck.json")
    hahn1 = read("hahn1-high-temperature.json")
    z3Hahn1 = read("z3-hahn1-denominator.json")
    cvc5Hahn1 = read("cvc5-hahn1-denominator.json")
    groupedStress = read("grouped-stress.json")
    identifiability = read("hahn1-fold1-identifiability.json")
    denominatorRoots = read("hahn1-frozen-denominator-roots.json")
    thurber = read("thurber-prospective-gate.json")
    kirby = read("kirby2-prospective-gate.json")
    crossDataset = json.loads((ROOT / "exports/rational-cross-dataset.json").read_text(encoding="utf-8"))
    exactRoots = read("rational-exact-interval-roots.json")
    parameterBox = read("rational-parameter-box-stability.json")
    predictionBounds = read("rational-prediction-box-bounds.json")
    ellipsoidComparison = read("rational-ellipsoid-box-comparison.json")
    ellipsoidInterval = read("rational-ellipsoid-interval-safety.json")
    filipCoverage = read("filip-ellipsoid-coverage.json")
    mgh17Coverage = read("mgh17-ellipsoid-coverage-scope-v2.json")
    externalComparison = json.loads((ROOT / "exports/external-coverage-comparison.json").read_text(encoding="utf-8"))
    gauss1Coverage = read("gauss1-ellipsoid-coverage-scope-v2.json")
    gauss1Comparison = json.loads((ROOT / "exports/external-coverage-gauss1-comparison.json").read_text(encoding="utf-8"))
    gauss1Mechanism = read("gauss1-bound-mechanism.json")
    externalDecomposition = json.loads((ROOT / "exports/external-bound-decomposition.json").read_text(encoding="utf-8"))
    internalExternalDecomposition = json.loads((ROOT / "exports/internal-external-bound-comparison.json").read_text(encoding="utf-8"))
    misra1aCoverage = read("misra1a-ellipsoid-coverage-scope-v2.json")
    chwirut1Coverage = read("chwirut1-ellipsoid-coverage.json")
    chwirut1Protocol = read("chwirut1-ellipsoid-coverage-protocol.json")
    externalV2Decomposition = json.loads((ROOT / "exports/external-bound-decomposition-v2.json").read_text(encoding="utf-8"))
    combinedV2Decomposition = json.loads((ROOT / "exports/internal-external-bound-comparison-v2.json").read_text(encoding="utf-8"))
    externalV3Decomposition = json.loads((ROOT / "exports/external-bound-decomposition-v3.json").read_text(encoding="utf-8"))
    combinedV3Decomposition = json.loads((ROOT / "exports/internal-external-bound-comparison-v3.json").read_text(encoding="utf-8"))
    externalV4Decomposition = json.loads((ROOT / "exports/external-bound-decomposition-v4.json").read_text(encoding="utf-8"))
    combinedV4Decomposition = json.loads((ROOT / "exports/internal-external-bound-comparison-v4.json").read_text(encoding="utf-8"))
    externalV5Decomposition = json.loads((ROOT / "exports/external-bound-decomposition-v5.json").read_text(encoding="utf-8"))
    combinedV5Decomposition = json.loads((ROOT / "exports/internal-external-bound-comparison-v5.json").read_text(encoding="utf-8"))
    maximumAudit = json.loads((ROOT / "exports/maximum-full-composition-audit.json").read_text(encoding="utf-8"))
    maximumV2Audit = json.loads((ROOT / "exports/maximum-full-composition-audit-v2.json").read_text(encoding="utf-8"))
    extremeV2Check = read("extreme-reporting-v2-check.json")
    extremeCheck = read("extreme-reporting-check.json")
    corpusCheck = read("extreme-corpus-check.json")
    roszman1Coverage = read("roszman1-ellipsoid-coverage.json")
    roszman1Protocol = read("roszman1-ellipsoid-coverage-protocol.json")
    externalScopeAmendment = read("external-scope-limitations-amendment-01-audit.json")
    ensoCoverage = read("enso-ellipsoid-coverage.json")
    ensoProtocol = read("enso-ellipsoid-coverage-protocol.json")
    items = [
        {
            "id": "pysindy-linear-system", "domain": "math", "title": "稀疏动力学已知答案复核",
            "status": sindy["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/dynamicslab/pysindy"],
            "metrics": {"version": sindy["version"], "maxAbsError": sindy["max_abs_error"], "coefficients": sindy["coefficients"]},
            "scientificClaim": "本机 PySINDy 能从合成轨迹近似恢复预设线性系数。",
            "limitations": sindy["scope"], "upstreamContribution": "提供固定特征库和显式误差边界的可重放基线。",
            "snapshotFiles": ["validation/pysindy.json"],
        },
        {
            "id": "z3-real-constraints", "domain": "math", "title": "实数约束已知答案复核",
            "status": z3["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/Z3Prover/z3"],
            "metrics": {"version": z3["version"], "checks": z3["checks"]},
            "scientificClaim": "两个预设实数约束均被 Z3 判定为不可满足。",
            "limitations": z3["scope"], "upstreamContribution": "为形式化前的反例搜索提供最小可执行样例。",
            "snapshotFiles": ["validation/z3.json"],
        },
        {
            "id": "acetazolamide-pubchem-rdkit", "domain": "chemistry", "title": "乙酰唑胺跨库属性审计",
            "status": rdkit["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://pubchem.ncbi.nlm.nih.gov/rest/pug", "https://github.com/rdkit/rdkit"],
            "metrics": {"pubchemCid": rdkit["pubchem_cid"], "formula": rdkit["formula"], "tpsaDefault": rdkit["tpsa_default_NO_A2"], "tpsaIncludeSP": rdkit["tpsa_include_S_P_A2"], "pubchemTpsa": rdkit["pubchem_tpsa_A2"], "rdkitMolLogP": rdkit["rdkit_crippen_mollogp"], "pubchemXLogP": rdkit["pubchem_xlogp"]},
            "scientificClaim": "规范结构、分子式和精确质量一致；描述符差异必须连算法口径一起解释。",
            "limitations": rdkit["scope"], "upstreamContribution": "提供结构归一、S/P 口径、算法差异和精度的公开对照样例。",
            "snapshotFiles": ["validation/rdkit.json", "validation/pubchem-acetazolamide.json"],
        },
        {
            "id": "silicon-materials-project-pymatgen", "domain": "physics", "title": "硅结构派生量独立重算",
            "status": pymatgen["status"], "evidenceClass": "local_recomputation",
            "sources": ["https://api.materialsproject.org", "https://github.com/materialsproject/pymatgen"],
            "metrics": {"materialId": pymatgen["material_id"], "densityLocal": pymatgen["density_local_g_cm3"], "densityExternal": pymatgen["density_external_g_cm3"], "spaceGroup": pymatgen["space_group_local"], "spaceGroupNumber": pymatgen["space_group_number_local"], "externalBandGapEv": pymatgen["external_band_gap_eV"]},
            "scientificClaim": "从同一公开晶体结构本地重算的密度和空间群与 Materials Project 快照一致。",
            "limitations": pymatgen["scope"], "upstreamContribution": "提供规范 ID 迁移、结构快照与本地派生量核对的轻量复现包。",
            "snapshotFiles": ["validation/pymatgen.json", "validation/materials-project-si.json"],
        },
        {
            "id": "4hhb-hbb-uniprot", "domain": "biology", "title": "血红蛋白结构—序列跨库桥接",
            "status": pdb["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://data.rcsb.org/rest/v1/core", "https://rest.uniprot.org"],
            "metrics": {"pdbId": pdb["pdb_id"], "pdbEntity": pdb["pdb_entity"], "chains": pdb["pdb_chains"], "resolutionA": pdb["resolution_A"], "uniprotAccession": pdb["uniprot_accession"], "uniprotLength": pdb["uniprot_length"], "pdbLength": pdb["pdb_length"], "sequenceMd5": pdb["sequence_md5_recomputed"]},
            "scientificClaim": "P68871 去除起始甲硫氨酸后与 4HHB entity 2 的 146 aa 序列逐字符一致。",
            "limitations": pdb["scope"], "upstreamContribution": "提供不依赖截断字段、由基因/物种检索到精确序列验证的跨库桥接。",
            "snapshotFiles": ["validation/pdb-uniprot.json", "validation/pdb-4hhb.json", "validation/uniprot-hbb.json"],
        },
        {
            "id": "acetazolamide-chembl-pubchem-pdb", "domain": "chemistry", "title": "乙酰唑胺—CA II—实验结构链",
            "status": drug["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://www.ebi.ac.uk/chembl/api/data", "https://pubchem.ncbi.nlm.nih.gov/rest/pug", "https://data.rcsb.org/rest/v1/core"],
            "metrics": {"chemblMolecule": drug["chembl_molecule"], "pubchemCid": drug["pubchem_cid"], "targetChemblId": drug["target_chembl_id"], "targetUniprot": drug["target_uniprot"], "targetPdbEntity": drug["target_pdb_entity"], "targetPdbChain": drug["target_pdb_chain"], "targetSequenceExactMatch": drug["target_sequence_exact_match"], "targetSequenceLength": drug["target_sequence_length"], "targetSequenceMd5": drug["target_sequence_md5"], "activityId": drug["activity_id"], "assayChemblId": drug["assay_chembl_id"], "kiNm": drug["ki_nM"], "pchemblExternal": drug["pchembl_external"], "pchemblRecomputed": drug["pchembl_recomputed"], "potentialDuplicate": drug["potential_duplicate"], "pdbId": drug["pdb_id"], "ligandCompId": drug["pdb_ligand_comp_id"], "resolutionA": drug["resolution_A"], "caIKiNm": selectivity["ca_i"]["ki_nM"], "caIiKiNm": selectivity["ca_ii"]["ki_nM"], "caIxKiNm": selectivity["ca_ix"]["ki_nM"], "caIiKiRatio": selectivity["ca_i_ii_ki_ratio"], "caIiPchemblDelta": selectivity["ca_ii_minus_ca_i_pchembl_delta"], "caIxRatioComputed": selectivity["ca_ix_ratio_computed"], "selectivityIndependence": selectivity["independence"], "ratioMin": stability["ratio_min"], "ratioMax": stability["ratio_max"], "maxMinFold": stability["max_min_fold"], "methodMatchedCount": stability["strict_method_matched_count"], "methodIncompleteCount": stability["method_incomplete_count"], "documentCount": stability["document_count"], "stabilityConclusion": stability["stability_conclusion"], "structuralControlPdbId": structuralControl["control"]["pdb_id"], "structuralControlExactWildtypeReplication": structuralControl["exact_wildtype_replication"], "structuralControlDifferenceEvents": structuralControl["alignment_difference_event_count"], "structuralControlLengthDiscrepancy": structuralControl["length_metadata_discrepancy"]},
            "scientificClaim": "乙酰唑胺的化合物标识、CA II 策划机制、P00918/3HS4 的 260 aa 精确序列、单一 Ki 测定和实验复合物可以逐层追溯；同方法 CA I/II 表观比值单独分析，跨文档固定常数不成立；2H4N 只作不同构建的结构对照。",
            "limitations": drug["scope"] + " " + selectivity["scope"] + " " + stability["scope"] + " " + structuralControl["scope"], "upstreamContribution": "提供 InChIKey、靶点全长序列、assay、配体实体、重复标记、方法一致定量对照、跨文档负结果和不同构建结构对照完整保留的药物—靶点—结构审计链。",
            "snapshotFiles": ["validation/drug-target-structure.json", "validation/structural-control.json", "validation/pdb-2h4n.json", "validation/ca-selectivity.json", "validation/chembl-ca-selectivity-panel.json", "validation/ca-document-stability.json", "validation/chembl-ca-document-pairs.json", "validation/ca2-sequence.json", "validation/chembl-acetazolamide.json", "validation/pdb-3hs4.json", "validation/pdb-3hs4-ca2.json", "validation/uniprot-ca2.json", "validation/pubchem-acetazolamide.json"],
        },
        {
            "id": "chwirut-high-distance-holdout", "domain": "physics", "title": "Chwirut 高距离真实数据留出",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/chwirut2.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Chwirut2.dat"],
            "metrics": {"trainCount": chwirut["split"]["train_count"], "holdoutCount": chwirut["split"]["holdout_count"], "trainRmse": chwirut["train_fit"]["metrics"]["train_rmse"], "holdoutRmse": chwirut["train_fit"]["metrics"]["holdout_rmse"], "linearHoldoutRmse": chwirut["baselines"]["linear"]["holdout_rmse"], "meanHoldoutRmse": chwirut["baselines"]["training_mean"]["holdout_rmse"], "limitedSupport": chwirut["decision"]["limited_support"], "nistReproduction": chwirut["full_fit_certification"]["matches_nist_within_frozen_tolerances"]},
            "scientificClaim": "三参数模型在预注册高距离切片获得有限支持；NIST 全数据认证复现与留出预测证据严格分开。",
            "limitations": " ".join(chwirut["limitations"]), "upstreamContribution": "提供原始数据哈希、冻结留出协议、双起点拟合、两项基线和54点独立复算。",
            "snapshotFiles": ["validation/chwirut-holdout-protocol.json", "validation/chwirut-holdout.json", "validation/chwirut-holdout-verification.json"],
        },
        {
            "id": "z3-identifiability-counterexamples", "domain": "math", "title": "Z3 定义域与参数可识别性反例",
            "status": z3identifiability["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/Z3Prover/z3"],
            "metrics": {"version": z3identifiability["version"], "checks": z3identifiability["checks"]},
            "scientificClaim": "显式正性域内分母恒正；无分母约束存在反例，x=0 单点不能唯一识别全部参数。",
            "limitations": " ".join(z3identifiability["limitations"]), "upstreamContribution": "提供可重放的有限域证明义务、显式反例和实验设计可识别性边界。",
            "snapshotFiles": ["validation/z3-identifiability.json"],
        },
        {
            "id": "aspirin-pubchem-chembl-rdkit", "domain": "chemistry", "title": "阿司匹林跨库身份与描述符口径审计",
            "status": aspirin["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://pubchem.ncbi.nlm.nih.gov/rest/pug", "https://www.ebi.ac.uk/chembl/api/data", "https://github.com/rdkit/rdkit"],
            "metrics": {"pubchemCid": aspirin["pubchem_cid"], "chemblId": aspirin["chembl_id"], "canonicalStructureIdentical": aspirin["canonical_structure_identical"], "inchikeyIdentical": aspirin["inchikey_identical"], "formula": aspirin["rdkit"]["formula"], "exactMass": aspirin["rdkit"]["exact_mass"], "tpsa": aspirin["rdkit"]["tpsa"], "rdkitMolLogP": aspirin["rdkit"]["mol_logp"], "pubchemXLogP": aspirin["pubchem"]["XLogP"], "chemblALogP": aspirin["chembl_properties"]["alogp"], "rdkitHba": aspirin["rdkit"]["hba"], "chemblHba": aspirin["chembl_properties"]["hba"], "pubchemRotatable": aspirin["pubchem"]["RotatableBondCount"], "chemblRotatable": aspirin["chembl_properties"]["rtb"]},
            "scientificClaim": "阿司匹林在 PubChem、ChEMBL 与 RDKit 间结构身份一致；LogP、氢键和可旋转键定义差异不构成造假证据。",
            "limitations": " ".join(aspirin["limitations"]), "upstreamContribution": "提供 CID/CHEMBL/InChIKey 对照、结构归一、精确质量和多口径描述符审计。",
            "snapshotFiles": ["validation/pubchem-aspirin.json", "validation/chembl-aspirin.json", "validation/aspirin-crosscheck.json"],
        },
        {
            "id": "mp-oqmd-structure-crosscheck", "domain": "physics", "title": "MP／OQMD／PyMatGen 三组材料结构复核",
            "status": material["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://api.materialsproject.org", "https://oqmd.org/", "https://github.com/materialsproject/pymatgen"],
            "metrics": {"structureIdentityConfirmed": material["structure_identity_confirmed"], "items": [{"formula": item["formula"], "mpId": item["mp"]["material_id"], "oqmdEntryId": item["oqmd"]["entry_id"], "optimadeId": item["oqmd_structure_id"], "bandGapMpEv": item["band_gap_mp_eV"], "bandGapOqmdEv": item["band_gap_oqmd_eV"], "densityLocal": item["local"]["density_g_cm3"], "densityMp": item["density_mp_g_cm3"], "spaceGroupLocal": item["local"]["space_group_symbol"]} for item in material["materials"]]},
            "scientificClaim": "Si、GaAs、SiO2 的跨库结构身份分别成立，但 DFT 带隙、密度和稳定性不因此被强制相等。",
            "limitations": " ".join(material["limitations"]), "upstreamContribution": "提供原生 entry_id 与 OPTIMADE ID 的显式映射、完整结构快照和独立密度/空间群重算。",
            "snapshotFiles": ["validation/material-crosscheck-protocol.json", "validation/material-crosscheck-protocol-amendment-01.json", "validation/material-crosscheck.json", "validation/materials-project-si-dft.json", "validation/materials-project-gaas-dft.json", "validation/materials-project-sio2-dft.json", "validation/oqmd-structure-si.json", "validation/oqmd-structure-gaas.json", "validation/oqmd-structure-sio2.json"],
        },
        {
            "id": "eckerle4-two-tail-extrapolation", "domain": "physics", "title": "Eckerle4 双尾真实数据外推",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/eckerle4.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Eckerle4.dat"],
            "metrics": {"middleCount": eckerle["split"]["middle_count"], "lowCount": eckerle["split"]["low_count"], "highCount": eckerle["split"]["high_count"], "middleRmse": eckerle["middle_fit"]["metrics"]["middle_rmse"], "lowRmse": eckerle["middle_fit"]["metrics"]["low_rmse"], "highRmse": eckerle["middle_fit"]["metrics"]["high_rmse"], "holdoutRmse": eckerle["middle_fit"]["metrics"]["holdout_rmse"], "linearHoldoutRmse": eckerle["baselines"]["linear"]["holdout_rmse"], "meanHoldoutRmse": eckerle["baselines"]["training_mean"]["holdout_rmse"], "limitedSupport": eckerle["decision"]["limited_support"], "nistReproduction": eckerle["full_fit_certification"]["matches_nist_within_frozen_tolerances"]},
            "scientificClaim": "三参数高斯在独立 Eckerle4 的预注册双尾任务获得有限支持；全数据认证复现与双尾外推严格分开。",
            "limitations": " ".join(eckerle["limitations"]), "upstreamContribution": "提供第二独立数据集、双尾协议、中央拟合、两项基线和35点独立复算。",
            "snapshotFiles": ["validation/eckerle4-two-tail-protocol.json", "validation/eckerle4-two-tail.json", "validation/eckerle4-two-tail-verification.json"],
        },
        {
            "id": "cvc5-z3-cross-solver", "domain": "math", "title": "cvc5／Z3 交叉求解器复核",
            "status": cvc5["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2", "https://github.com/Z3Prover/z3"],
            "metrics": {"version": cvc5["solver_version"], "allResultsMatchZ3": cvc5["all_results_match_z3"], "checks": [{"id": item["id"], "cvc5": item["cvc5"], "z3": item["z3"]} for item in cvc5["checks"]]},
            "scientificClaim": "cvc5 与 Z3 对分母正性、零分母反例和 x=0 参数非识别性给出相同结果，并生成精确有理数反例模型。",
            "limitations": " ".join(cvc5["limitations"]), "upstreamContribution": "提供双求解器 SMT-LIB、原始日志、官方二进制哈希和精确模型，降低单求解器依赖。",
            "snapshotFiles": ["validation/cvc5-crosscheck.json", "validation/cvc5-positive-denominator.smt2", "validation/cvc5-zero-denominator.smt2", "validation/cvc5-xzero-identifiability.smt2"],
        },
        {
            "id": "hahn1-rational-high-temperature", "domain": "physics", "title": "Hahn1 有理模型高温外推与分母边界",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Hahn1.dat", "https://github.com/Z3Prover/z3", "https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2"],
            "metrics": {"trainCount": hahn1["split"]["train_count"], "holdoutCount": hahn1["split"]["holdout_count"], "trainRmse": hahn1["train_fit"]["metrics"]["train_rmse"], "holdoutRmse": hahn1["train_fit"]["metrics"]["holdout_rmse"], "cubicHoldoutRmse": hahn1["baselines"]["cubic_polynomial"]["holdout_rmse"], "linearHoldoutRmse": hahn1["baselines"]["linear"]["holdout_rmse"], "limitedSupport": hahn1["decision"]["limited_support"], "nistReproduction": hahn1["full_fit_certification"]["matches_nist_within_frozen_tolerances"], "denominatorDomain": cvc5Hahn1["domain"], "cvc5Result": cvc5Hahn1["result"], "z3Result": z3Hahn1["result"], "unboundedRootExists": z3Hahn1["unbounded_root_exists"], "unboundedModelX": z3Hahn1["unbounded_model_x"]},
            "scientificClaim": "七参数有理模型在预注册高温切片获得有限支持并优于三次多项式基线；分母在实验区间内无零根，但存在域外正根。",
            "limitations": " ".join(hahn1["limitations"]) + " " + z3Hahn1["limitations"], "upstreamContribution": "提供有理模型、强基线、236点预测复算和双求解器分母边界审计。",
            "snapshotFiles": ["validation/hahn1-high-temperature-protocol.json", "validation/hahn1-high-temperature.json", "validation/hahn1-high-temperature-verification.json", "validation/z3-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.smt2"],
        },
        {
            "id": "grouped-contiguous-stress-diagnostics", "domain": "physics", "title": "跨数据集连续区间压力测试与失效定位",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/chwirut2.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/eckerle4.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml"],
            "metrics": {"overallRobustLimitedSupport": groupedStress["overall_robust_limited_support"], "datasets": [{"id": item["id"], "robustLimitedSupport": item["decision"]["robust_limited_support"], "medianRmse": item["median_model_rmse"], "worstFold": item["worst_fold"]} for item in groupedStress["datasets"]]},
            "scientificClaim": "Chwirut 和 Eckerle4 五折均不劣于基线；Hahn1 第 1 折显著失效，因此整体不能称为稳健支持。",
            "limitations": " ".join(groupedStress["limitations"]), "upstreamContribution": "提供15折连续区间压力诊断、全部失败区间、基线对照和防泄漏协议。",
            "snapshotFiles": ["validation/grouped-stress-protocol.json", "validation/grouped-stress.json"],
        },
        {
            "id": "hahn1-fold1-identifiability-and-poles", "domain": "physics", "title": "Hahn1 第 1 折局部可识别性与双极点诊断",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Hahn1.dat"],
            "metrics": {"fold1TrainingRmse": identifiability["folds"][0]["training_metrics"]["rmse"], "fold1TestRmse": identifiability["folds"][0]["test_metrics"]["rmse"], "fold1ScaledConditionNumber": identifiability["folds"][0]["training_jacobian"]["scaled_condition_number"], "allFoldNumericalRanks": [fold["training_jacobian"]["numerical_rank"] for fold in identifiability["folds"]], "fold1MaxParameterCorrelation": identifiability["folds"][0]["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"], "fold1MaxLocalPredictionSd": identifiability["folds"][0]["held_out_prediction_sensitivity"]["max_local_standard_deviation"], "fold1MinAbsDenominatorHeldOut": identifiability["folds"][0]["denominator"]["min_absolute_on_held_out_points"], "fold1HeldOutPoles": [{"rootX": root["root_x"], "numeratorAtRoot": root["numerator_at_root"], "denominatorDerivativeAtRoot": root["denominator_derivative_at_root"]} for root in denominatorRoots["folds"][0]["real_roots"] if root["within_held_out_closed_interval"]], "fold1FailureReversed": identifiability["decision"]["fold_1_failure_reversed"]},
            "scientificClaim": "五折均为数值满秩；第 1 折在约 45.526978 K 和 72.131671 K 有两个留出区数值单极点，近根位置出现巨大预测与残差，支持局部失效机制解释。",
            "limitations": " ".join(identifiability["limitations"] + denominatorRoots["limitations"]), "upstreamContribution": "提供逐折解析雅可比、局部敏感度、数值根及根处分子和导数，形成预测区极点排除与可识别性验收义务。",
            "snapshotFiles": ["validation/hahn1-fold1-identifiability-protocol.json", "validation/hahn1-fold1-identifiability.json", "validation/hahn1-frozen-denominator-roots-protocol.json", "validation/hahn1-frozen-denominator-roots.json"],
        },
        {
            "id": "thurber-dataset-prospective-gate", "domain": "physics", "title": "Thurber 预测区与可识别性数据集前瞻验收",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Thurber.dat", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/v-thurber.shtml"],
            "metrics": {"nistReproduction": thurber["full_fit_certification"]["matches_nist_within_frozen_tolerances"], "overallAllFoldsGatedSupport": thurber["decision"]["overall_all_folds_gated_support"], "folds": [{"fold": fold["fold"], "testRmse": fold["test_metrics"]["rmse"], "baselineRmse": fold["baseline_test_metrics"]["rmse"], "rootsInHeldOutInterval": fold["domain_audit"].get("real_roots_in_closed_interval"), "numericalRank": fold["identifiability"].get("numerical_rank"), "scaledConditionNumber": fold["identifiability"].get("scaled_condition_number"), "gatedLimitedSupport": fold["decision"]["gated_limited_support"]} for fold in thurber["folds"]]},
            "scientificClaim": "Thurber 全数据拟合通过 NIST 已知答案复核；第 2—5 折通过冻结验收，第 1 折在约 -3.019661 的留出区实根处失效，因此整体五折支持不成立。",
            "limitations": " ".join(thurber["limitations"]), "upstreamContribution": "提供新数据集冻结协议、全部五折预测区根检查、局部秩与协方差检查、三次基线和失败记录。",
            "snapshotFiles": ["validation/thurber-prospective-gate-protocol.json", "validation/thurber-prospective-gate.json"],
        },
        {
            "id": "kirby2-cross-degree-prospective-gate", "domain": "physics", "title": "Kirby2 二次有理模型跨次数前瞻验收",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Kirby2.dat", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/v-kirby2.shtml"],
            "metrics": {"nistReproduction": kirby["full_fit_certification"]["matches_nist_within_frozen_tolerances"], "overallAllFoldsGatedSupport": kirby["decision"]["overall_all_folds_gated_support"], "fold1TrainingRmse": kirby["folds"][0]["identifiability"]["training_metrics"]["rmse"], "fold1TestRmse": kirby["folds"][0]["test_metrics"]["rmse"], "fold1BaselineRmse": kirby["folds"][0]["baseline_test_metrics"]["rmse"], "folds": [{"fold": fold["fold"], "testRmse": fold["test_metrics"]["rmse"], "baselineRmse": fold["baseline_test_metrics"]["rmse"], "rootsInHeldOutInterval": fold["domain_audit"].get("real_roots_in_closed_interval"), "numericalRank": fold["identifiability"].get("numerical_rank"), "scaledConditionNumber": fold["identifiability"].get("scaled_condition_number"), "gatedLimitedSupport": fold["decision"]["gated_limited_support"]} for fold in kirby["folds"]]},
            "scientificClaim": "Kirby2 五折均无留出区实根、数值秩均为 5 且均优于二次基线，因此获得本协议下整体有限支持；第 1 折外推衰减和高条件数仍保留。",
            "limitations": " ".join(kirby["limitations"]), "upstreamContribution": "提供不同次数有理模型的阳性对照、全部五折根检查、局部数值诊断、二次基线和训练—留出衰减对照。",
            "snapshotFiles": ["validation/kirby2-prospective-gate-protocol.json", "validation/kirby2-prospective-gate.json"],
        },
        {
            "id": "rational-cross-dataset-synthesis", "domain": "math", "title": "有理模型统一内核与跨数据集综合",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml"],
            "metrics": crossDataset["totals"],
            "scientificClaim": "统一内核下 15 折中 13 折符合验收；Hahn1 和 Thurber 各有一个预测区失败折，Kirby2 五折均通过。计数不表示普适检出率。",
            "limitations": " ".join(crossDataset["limitations"]), "upstreamContribution": "提供统一雅可比、数值根、预测区和局部数值诊断接口，并区分事后重建与数据集前瞻证据。",
            "snapshotFiles": ["validation/rational-cross-dataset-protocol.json", "validation/hahn1-fold1-identifiability.json", "validation/hahn1-frozen-denominator-roots.json", "validation/thurber-prospective-gate.json", "validation/kirby2-prospective-gate.json"],
        },
        {
            "id": "rational-exact-interval-sturm-solvers", "domain": "math", "title": "精确 Sturm 区间根隔离与双求解器复核",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://github.com/Z3Prover/z3", "https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2"],
            "metrics": exactRoots["totals"],
            "scientificClaim": "对十五折有理系数快照，13 个闭区间精确无根，Hahn1 第 1 折精确有 2 根，Thurber 第 1 折精确有 1 根；双求解器逐折一致。",
            "limitations": " ".join(exactRoots["limitations"]), "upstreamContribution": "提供精确 Sturm 隔离、十五份 SMT-LIB、三十份求解器日志及完整哈希，区分快照证明与物理参数精确性。",
            "snapshotFiles": ["validation/rational-exact-interval-protocol.json", "validation/rational-exact-interval-roots.json", "validation/exact-interval-smt/hahn1-fold-1.smt2", "validation/exact-interval-smt/thurber-fold-1.smt2", "validation/exact-interval-logs/hahn1-fold-1-z3.log", "validation/exact-interval-logs/thurber-fold-1-cvc5.log"],
        },
        {
            "id": "rational-parameter-box-stability", "domain": "math", "title": "连续参数盒无根稳定性证明",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml"],
            "metrics": {"totals": parameterBox["totals"], "finiteRadiusBrackets": [{"dataset": case["dataset"], "fold": case["fold"], "lower": case["certified_radius_lower_bound_float"], "upper": case["uncertified_radius_upper_bound_float"]} for case in parameterBox["cases"] if not case["cap_hit"] and case["snapshot_safe"]]},
            "scientificClaim": "13 个无根快照均获得正的连续参数盒无根半径；11 折达到上限 4，Hahn1 第 5 折和 Thurber 第 2 折为有限半径括号。",
            "limitations": " ".join(parameterBox["limitations"]), "upstreamContribution": "提供连续参数区域的精确充分性证明和跨零分段协议，不把下界当作置信区或必要最大半径。",
            "snapshotFiles": ["validation/rational-parameter-box-protocol.json", "validation/rational-parameter-box-protocol-amendment-01.json", "validation/rational-parameter-box-stability.json"],
        },
        {
            "id": "rational-prediction-box-bounds", "domain": "math", "title": "认证参数盒内逐点预测与残差上界",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml"],
            "metrics": predictionBounds["totals"],
            "scientificClaim": "13 折共 369 个留出观测获得确定性预测平移与残差上界；无根盒并不保证有用的预测精度，极大有限上界明确保留。",
            "limitations": " ".join(predictionBounds["limitations"]), "upstreamContribution": "提供逐点精确有理上界和分母下界，区分定义域安全、预测界宽度和实际预测信息。",
            "snapshotFiles": ["validation/rational-prediction-box-protocol.json", "validation/rational-prediction-box-bounds.json"],
        },
        {
            "id": "rational-ellipsoid-box-comparison", "domain": "math", "title": "协方差椭球与独立参数盒逐点比较",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml"],
            "metrics": {"totals": ellipsoidComparison["totals"], "specialCases": [{"dataset": case["dataset"], "fold": case["fold"], "boxMaxShift": case["max_box_prediction_shift_upper_bound_float"], "ellipsoidMaxShift": case["max_ellipsoid_prediction_shift_upper_bound_float"]} for case in ellipsoidComparison["cases"] if (case["dataset"] == "hahn1" and case["fold"] == 5) or (case["dataset"] == "thurber" and case["fold"] == 2)]},
            "scientificClaim": "同一半径下 369 个适用点的协方差椭球上界全部小于独立盒；中位比值 0.604836，最大 0.999351，两个有根折不适用。",
            "limitations": " ".join(ellipsoidComparison["limitations"]), "upstreamContribution": "提供完整协方差方向、精确支撑上界和逐点比值，明确盒与椭球是不同区域，不把样本收紧称为永远更紧。",
            "snapshotFiles": ["validation/rational-ellipsoid-box-protocol.json", "validation/rational-ellipsoid-box-comparison.json"],
        },
        {
            "id": "rational-ellipsoid-continuous-interval", "domain": "math", "title": "协方差椭球连续区间平方支撑证明",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml"],
            "metrics": ellipsoidInterval["totals"],
            "scientificClaim": "13 个无根快照的 D²-rho²z^TΣz 在整个留出闭区间均为正，未认证折为 0，有根快照折为 2。",
            "limitations": " ".join(ellipsoidInterval["limitations"]), "upstreamContribution": "提供精确平方支撑连续证明，覆盖观测点之间，不把逐点正分母当作连续安全。",
            "snapshotFiles": ["validation/rational-ellipsoid-interval-protocol.json", "validation/rational-ellipsoid-interval-safety.json"],
        },
        {
            "id": "filip-external-ellipsoid-coverage", "domain": "physics", "title": "Filip 外部候选模型椭球覆盖压力测试",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/LINKS/DATA/Filip.dat"],
            "metrics": filipCoverage["totals"],
            "scientificClaim": "候选 cubic/cubic 在 Filip 五折均优于三次基线且连续椭球安全；82／82 点未发生实际残差越界，独立盒连续安全为 0。",
            "limitations": " ".join(filipCoverage["limitations"]), "upstreamContribution": "提供外部候选压力测试和逐点覆盖，区分候选近似、概率覆盖、界宽度及独立盒不可用。",
            "snapshotFiles": ["validation/filip-ellipsoid-coverage-protocol.json", "validation/filip-ellipsoid-coverage.json"],
        },
        {
            "id": "external-coverage-framework-mgh17", "domain": "physics", "title": "通用外部覆盖协议与 MGH17 对照",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/MGH17.dat", "https://www.itl.nist.gov/div898/strd/lls/data/LINKS/DATA/Filip.dat"],
            "metrics": {"comparisonTotals": externalComparison["totals"], "mgh17": mgh17Coverage["totals"], "driverSha256": externalComparison["analysis_scope"]["driver_sha256"]},
            "scientificClaim": "通用驱动保持 Filip 的 82 点覆盖与连续安全；MGH17 33／33 点覆盖且连续安全，32 点椭球更紧，独立盒五折安全。",
            "limitations": " ".join(externalComparison["limitations"]), "upstreamContribution": "提供可复用外部覆盖驱动和跨数据对照，不把 115 点汇总称为概率覆盖或普适成功率。",
            "snapshotFiles": ["validation/mgh17-ellipsoid-coverage-protocol.json", "validation/mgh17-ellipsoid-coverage.json", "validation/mgh17-ellipsoid-coverage-scope-v2.json", "validation/external-coverage-framework-protocol.json"],
        },
        {
            "id": "gauss1-external-coverage-counterexample", "domain": "physics", "title": "Gauss1 外部覆盖反例与三数据证据轴对照",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Gauss1.dat"],
            "metrics": {"comparisonTotals": gauss1Comparison["totals"], "gauss1": gauss1Coverage["totals"], "driverSha256": gauss1Comparison["analysis_scope"]["driver_sha256"], "protocolFrozenBeforeCandidateAnalysis": True},
            "scientificClaim": "Gauss1 的 250 点中仅 190 点可给出椭球界，连续安全为 3／5 折；第 2 折预测显著失败，第 5 折无可用界。三数据共 365 点，其中 305 点适用、60 点不可用。",
            "limitations": "Gauss1 是生成数据，候选不是原生八参数模型。305 个适用点零违规不是概率覆盖率或普适外部成功率；60 个不可用点不能解释为覆盖或安全。" + " ".join(gauss1Comparison["limitations"]),
            "upstreamContribution": "提供先推送冻结协议再执行的外部检验、完整失败记录和三数据证据轴对照，否定代码复用自动保证外部有效性的强解释。",
            "snapshotFiles": ["validation/gauss1-ellipsoid-coverage-protocol.json", "validation/gauss1-ellipsoid-coverage.json", "validation/gauss1-ellipsoid-coverage-scope-v2.json", "validation/external-coverage-gauss1-comparison-protocol.json"],
        },
        {
            "id": "gauss1-bound-mechanism-decomposition", "domain": "math", "title": "Gauss1 分母下界与同点残差界分解",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Gauss1.dat"],
            "metrics": {"totals": gauss1Mechanism["totals"], "analysisScope": gauss1Mechanism["analysis_scope"], "samePointMaxima": [case["maximum_residual_upper_bound"] for case in gauss1Mechanism["folds"] if case["maximum_residual_upper_bound"] is not None], "foldDiagnostics": [{"fold": case["fold"], "minimumDenominatorLower": case["minimum_denominator_lower"], "maximumCovarianceSupport": case["maximum_covariance_support"], "available": case["ellipsoid_available_point_count"]} for case in gauss1Mechanism["folds"]]},
            "scientificClaim": "190 个已有界点的三项数值与冻结结果全部一致。第 1、3、4 折最大残差界位置主要由实际残差贡献，第 2 折预测平移占 97.561%，第 5 折 50 点全部不可用；宽界不是单一机制。",
            "limitations": "这是只读事后诊断，不是重新拟合或前瞻检验；同点占比不是概率贡献，连续未认证不等于已证明不安全。" + " ".join(gauss1Mechanism["limitations"]),
            "upstreamContribution": "提供全 250 点分母下界、60 点不可用原因、190 点数值一致性及同点误差—平移分解，支持按机制而非仅按数据集检索。",
            "snapshotFiles": ["validation/gauss1-bound-mechanism.json", "validation/gauss1-ellipsoid-coverage.json", "validation/gauss1-ellipsoid-coverage-scope-v2.json", "validation/frontier-gauss1-bound-mechanism-word.json"],
        },
        {
            "id": "external-bound-composition-heterogeneity", "domain": "math", "title": "三数据同点界组成与机制异质性",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml"],
            "metrics": {"totals": externalDecomposition["totals"], "datasets": [{"id": item["id"], "ellipsoid_available_point_count": item["ellipsoid_available_point_count"], "prediction_shift_dominant_point_count": item["prediction_shift_dominant_point_count"], "snapshot_residual_dominant_point_count": item["snapshot_residual_dominant_point_count"], "median_shift_share": item["median_shift_share"], "maximum_residual_upper_bound": item["maximum_residual_upper_bound"]} for item in externalDecomposition["datasets"]], "gauss1Regression": externalDecomposition["gauss1_regression"], "analysisScope": externalDecomposition["analysis_scope"]},
            "scientificClaim": "305 个可用点的算术恒等式全部一致。Filip 82／82 点、MGH17 32／33 点由预测平移主导，Gauss1 则 166／190 点由快照实际残差主导；三数据最大界虽均由平移主导，全点分布并不相同。",
            "limitations": "这是只读事后算术分解，不是概率、方差或物理因果贡献；60 个不可用点没有虚构占比，三数据不形成普适排名。" + " ".join(externalDecomposition["limitations"]),
            "upstreamContribution": "提供全点分布与最大界位置的双层对照，防止用单一数据集或单一最大值概括所有残差上界。",
            "snapshotFiles": ["validation/external-bound-decomposition-protocol.json", "validation/frontier-external-bound-decomposition-word.json", "validation/gauss1-bound-mechanism.json"],
        },
        {
            "id": "internal-external-bound-scope-comparison", "domain": "math", "title": "内外部六组界组成与范围边界对照",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml"],
            "metrics": {"totals": internalExternalDecomposition["totals"], "datasets": [{"id": item["id"], "scope": item["scope"], "ellipsoid_available_point_count": item["ellipsoid_available_point_count"], "prediction_shift_dominant_point_count": item["prediction_shift_dominant_point_count"], "snapshot_residual_dominant_point_count": item["snapshot_residual_dominant_point_count"], "median_shift_share": item["median_shift_share"], "maximum_residual_upper_bound": item["maximum_residual_upper_bound"]} for item in internalExternalDecomposition["datasets"]], "analysisScope": internalExternalDecomposition["analysis_scope"], "decision": internalExternalDecomposition["decision"]},
            "scientificClaim": "六组共 674 个可用点，482 点由平移主导、192 点由实际残差主导；内部两个有根折与外部 60 个不可用点分别保留。六组最大界虽均由平移主导，全点分布并不相同。",
            "limitations": "674 点仅是描述性可用样本，不是总体成功率；内部有根折与外部不可用点不可混同，算术占比不是概率贡献或物理因果。" + " ".join(internalExternalDecomposition["limitations"]),
            "upstreamContribution": "提供六组分布、最大界位置和两类不适用边界的联合接口，支持内外部可比较但不可混同的证据检索。",
            "snapshotFiles": ["validation/internal-external-bound-comparison-protocol.json", "validation/frontier-internal-external-bound-word.json", "validation/internal-bound-decomposition-protocol.json"],
        },
        {
            "id": "misra1a-prediction-proof-dissociation", "domain": "physics", "title": "Misra1a 预测—证明解离与小样本界审计",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Misra1a.dat"],
            "metrics": {"totals": misra1aCoverage["totals"], "availablePoints": [{"x": point["x"], "actual_absolute_residual": point["actual_absolute_residual"], "prediction_shift": point["ellipsoid_prediction_shift_upper_bound_float"], "residual_upper_bound": point["ellipsoid_absolute_residual_upper_bound_float"], "shift_share": point["ellipsoid_prediction_shift_upper_bound_float"] / point["ellipsoid_absolute_residual_upper_bound_float"], "denominator_lower_bound": point["ellipsoid_denominator_lower_bound_float"]} for case in misra1aCoverage["folds"] for point in case["point_results"] if point.get("ellipsoid_available", False)], "folds": [{"fold": case["fold"], "modelRmse": case["test_metrics"]["rmse"], "baselineRmse": case["baseline_test_metrics"]["rmse"], "continuousSafe": case["continuous_ellipsoid_safe"], "available": sum(point.get("ellipsoid_available", False) for point in case["point_results"])} for case in misra1aCoverage["folds"]], "decision": {**misra1aCoverage["decision"], "independent_physical_experiment_claimed": False}},
            "scientificClaim": "Misra1a 的 14 点中仅 4 点可给界，连续安全仅 1／5 折；候选 RMSE 较小但只有两折优于基线。4 个可用点平移占比均超过 99.9%，最大上界为 414.13，形成预测—证明解离。",
            "limitations": "小样本候选不是原生两参数模型，重分析不是新完成的独立物理实验；4 个适用点零越界不是概率覆盖或高信息量证明。" + " ".join(misra1aCoverage["limitations"]),
            "upstreamContribution": "提供预注册小样本实测数据案例，分开记录 RMSE、连续安全、逐点可用性、界宽度和同点组成，避免拟合接近被误写为有用证明。",
            "snapshotFiles": ["validation/misra1a-ellipsoid-coverage-protocol.json", "validation/misra1a-ellipsoid-coverage.json", "validation/misra1a-ellipsoid-coverage-scope-v2.json", "validation/frontier-misra1a-coverage-word.json"],
        },
        {
            "id": "chwirut1-prediction-proof-dissociation", "domain": "physics", "title": "Chwirut1 同族外部审计与最低 RMSE 折零可用界",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/chwirut1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Chwirut1.dat"],
            "metrics": {
                "totals": chwirut1Coverage["totals"],
                "folds": [{"fold": case["fold"], "pointCount": len(case["point_results"]), "modelRmse": case["test_metrics"]["rmse"], "baselineRmse": case["baseline_test_metrics"]["rmse"], "continuousSafe": case["continuous_ellipsoid_safe"], "available": sum(point.get("ellipsoid_available", False) for point in case["point_results"]), "boxAvailable": sum(point.get("box_available", False) for point in case["point_results"])} for case in chwirut1Coverage["folds"]],
                "bestPredictionWithoutBounds": {"fold": chwirut1Coverage["folds"][3]["fold"], "modelRmse": chwirut1Coverage["folds"][3]["test_metrics"]["rmse"], "baselineRmse": chwirut1Coverage["folds"][3]["baseline_test_metrics"]["rmse"], "availablePointCount": sum(point.get("ellipsoid_available", False) for point in chwirut1Coverage["folds"][3]["point_results"]), "continuousSafe": chwirut1Coverage["folds"][3]["continuous_ellipsoid_safe"]},
                "boxComparison": {"availablePairCount": chwirut1Coverage["totals"]["tighter_point_count"] + chwirut1Coverage["totals"]["looser_point_count"], "tighterPointCount": chwirut1Coverage["totals"]["tighter_point_count"], "medianShiftRatio": chwirut1Coverage["totals"]["median_shift_ratio"], "minShiftRatio": chwirut1Coverage["totals"]["min_shift_ratio"], "maxShiftRatio": chwirut1Coverage["totals"]["max_shift_ratio"]},
                "relatedDataset": chwirut1Protocol["dataset_scope"]["related_prior_dataset"],
                "protocolCommits": {"frozenBeforeResults": "e07df7a", "results": "c339a0b"},
                "decision": {**chwirut1Coverage["decision"], "independent_physical_experiment_claimed": False, "independent_model_family_claimed": False},
            },
            "scientificClaim": "Chwirut1 的 214 点中 83 点可给界、131 点不可用，连续椭球安全为 2／5 折；第 2、4、5 折优于三次基线。第 4 折 RMSE 最低且优于基线，但 23 点全部无可给界，形成新的预测—证明解离。",
            "limitations": "Chwirut1 与 Chwirut2 同族，未触碰不是独立模型族或实验室复现；83 个适用点零越界不是 214 点概率覆盖，未认证不等于已证明不安全。" + " ".join(chwirut1Coverage["limitations"]),
            "upstreamContribution": "提供同族但未触碰数据的预注册压力测试，将预测排序、连续安全、逐点可用性、界宽度、盒／椭球可比较范围与数据亲缘关系分层记录。",
            "snapshotFiles": ["validation/chwirut1-ellipsoid-coverage-protocol.json", "validation/chwirut1-ellipsoid-coverage.json", "validation/frontier-chwirut1-coverage-word.json"],
        },
        {
            "id": "bound-comparison-v2-scope-expansion", "domain": "math", "title": "四外部与七组界组成新版范围对照",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml"],
            "metrics": {"externalV2Totals": externalV2Decomposition["totals"], "combinedV2Totals": combinedV2Decomposition["totals"], "datasets": [{"id": item["id"], "scope": item["scope"], "ellipsoid_available_point_count": item["ellipsoid_available_point_count"], "prediction_shift_dominant_point_count": item["prediction_shift_dominant_point_count"], "snapshot_residual_dominant_point_count": item["snapshot_residual_dominant_point_count"], "median_shift_share": item["median_shift_share"]} for item in combinedV2Decomposition["datasets"]], "decision": combinedV2Decomposition["decision"], "historicalPreservation": {"previousFilesPreserved": True, "threeExternal": "exports/external-bound-decomposition.json", "sixDatasets": "exports/internal-external-bound-comparison.json", "misra1aIncrement": {"pointCount": 14, "available": 4, "unavailable": 10, "predictionShiftDominant": 4, "snapshotResidualDominant": 0}}},
            "scientificClaim": "四外部共 379 点，其中 309 点可用、70 点不可用；142 点平移主导、167 点实际残差主导。七组共 678 个可用点，486 点平移主导、192 点实际残差主导。Misra1a 带来 +14 总点、+4 可用点、+10 不可用点和 +4 平移主导点，历史文件未改写。",
            "limitations": "这是新增数据后的事后范围汇总，不是合并成功率或证明能力改善；内部有根折与外部不可用点仍不可混同。" + " ".join(combinedV2Decomposition["limitations"]),
            "upstreamContribution": "提供新旧版本并存的范围扩展接口，明确 Misra1a 增量来源、七组分布和两类不适用边界，防止旧对照被静默覆盖。",
            "snapshotFiles": ["validation/external-bound-decomposition-v2-protocol.json", "validation/internal-external-bound-comparison-v2-protocol.json", "validation/internal-external-bound-comparison-v2-protocol-amendment-01.json", "validation/frontier-bound-comparison-v2-word.json"],
        },
        {
            "id": "bound-comparison-v3-scope-expansion", "domain": "math", "title": "五外部与八组界组成新版范围及同族数据对照",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/chwirut1.shtml"],
            "metrics": {
                "externalV3Totals": externalV3Decomposition["totals"],
                "combinedV3Totals": combinedV3Decomposition["totals"],
                "datasets": [{"id": item["id"], "scope": item["scope"], "ellipsoid_available_point_count": item["ellipsoid_available_point_count"], "prediction_shift_dominant_point_count": item["prediction_shift_dominant_point_count"], "snapshot_residual_dominant_point_count": item["snapshot_residual_dominant_point_count"], "median_shift_share": item["median_shift_share"]} for item in combinedV3Decomposition["datasets"]],
                "chwirut1Increment": {"pointCount": 214, "available": 83, "unavailable": 131, "predictionShiftDominant": 75, "snapshotResidualDominant": 8},
                "relatedDataset": chwirut1Protocol["dataset_scope"]["related_prior_dataset"],
                "decision": {**combinedV3Decomposition["decision"], "independent_model_family_claimed": False},
                "historicalPreservation": {"previousFilesPreserved": True, "fourExternal": "exports/external-bound-decomposition-v2.json", "sevenDatasets": "exports/internal-external-bound-comparison-v2.json"},
            },
            "scientificClaim": "五外部共 593 点，其中 392 点可用、201 点不可用；217 点平移主导、175 点实际残差主导。八组共 761 个可用点，561 点平移主导、200 点实际残差主导。Chwirut1 带来 +214 总点、+83 可用点、+131 不可用点、+75 平移主导点和 +8 实际残差主导点，历史版本未改写。",
            "limitations": "这是新增同族数据后的事后范围汇总，不是合并成功率、证明能力改善或独立模型族验证；Chwirut1 与 Chwirut2 的亲缘关系必须保留。" + " ".join(combinedV3Decomposition["limitations"]),
            "upstreamContribution": "提供五外部与八组并存的新版范围接口，将 Chwirut1 增量、数据亲缘、八组分布和两类不适用边界显式连接，防止总对照覆盖历史或夸大独立性。",
            "snapshotFiles": ["validation/external-bound-decomposition-v3-protocol.json", "validation/internal-external-bound-comparison-v3-protocol.json", "validation/chwirut1-ellipsoid-coverage-protocol.json", "validation/frontier-bound-comparison-v3-word.json"],
        },
        {
            "id": "external-scope-limitations-amendment", "domain": "math", "title": "三组外部结果的模型族限制文本可审计修订",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml"],
            "metrics": {
                "correctionCount": externalScopeAmendment["correction_count"],
                "datasetIds": externalScopeAmendment["dataset_ids"],
                "changedJsonPointer": externalScopeAmendment["changed_json_pointer"],
                "numericResultsModified": externalScopeAmendment["numeric_results_modified"],
                "originalFilesPreserved": externalScopeAmendment["original_files_preserved"],
                "corrections": externalScopeAmendment["corrections"],
                "amendmentRunnerSha256": externalScopeAmendment["amendment_runner_sha256"],
            },
            "scientificClaim": "MGH17、Gauss1、Misra1a 的三份修订副本分别使用各自原生模型族的限制文本；除 /limitations/0 和新增 scope_correction 溯源字段外，原文件所有字段保持不变。",
            "limitations": "这是文档适用范围修订，不是重新拟合、数值结果升级或原冻结文件消失；原始文件及其历史错误文本保留用于审计，新证据叙述使用修订副本。",
            "upstreamContribution": "提供原文件、原协议、修订副本、修订脚本和输出哈希的完整链条，阻止通用 Filip 文案继续传播，同时不重写科学结果。",
            "snapshotFiles": ["validation/external-scope-limitations-amendment-01.json", "validation/external-scope-limitations-amendment-01-audit.json", "validation/mgh17-ellipsoid-coverage-scope-v2.json", "validation/gauss1-ellipsoid-coverage-scope-v2.json", "validation/misra1a-ellipsoid-coverage-scope-v2.json"],
        },
        {
            "id": "enso-prediction-proof-dissociation", "domain": "physics", "title": "ENSO 周期数据预测—证明解离与范围适配审计",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/enso.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/ENSO.dat"],
            "metrics": {
                "totals": ensoCoverage["totals"],
                "folds": [{"fold": case["fold"], "pointCount": len(case["point_results"]), "modelRmse": case["test_metrics"]["rmse"], "baselineRmse": case["baseline_test_metrics"]["rmse"], "continuousSafe": case["continuous_ellipsoid_safe"], "boxContinuousSafe": case["independent_box_continuous_safe"], "available": sum(point.get("ellipsoid_available", False) for point in case["point_results"]), "boxAvailable": sum(point.get("box_available", False) for point in case["point_results"])} for case in ensoCoverage["folds"]],
                "fold5PredictionWithoutBounds": {"fold": ensoCoverage["folds"][4]["fold"], "modelRmse": ensoCoverage["folds"][4]["test_metrics"]["rmse"], "baselineRmse": ensoCoverage["folds"][4]["baseline_test_metrics"]["rmse"], "availablePointCount": sum(point.get("ellipsoid_available", False) for point in ensoCoverage["folds"][4]["point_results"]), "continuousSafe": ensoCoverage["folds"][4]["continuous_ellipsoid_safe"]},
                "boxComparison": {"availablePairCount": ensoCoverage["totals"]["tighter_point_count"] + ensoCoverage["totals"]["looser_point_count"], "tighterPointCount": ensoCoverage["totals"]["tighter_point_count"], "ellipsoidOnlyPointCount": sum(point.get("ellipsoid_available", False) and not point.get("box_available", False) for case in ensoCoverage["folds"] for point in case["point_results"]), "medianShiftRatio": ensoCoverage["totals"]["median_shift_ratio"], "minShiftRatio": ensoCoverage["totals"]["min_shift_ratio"], "maxShiftRatio": ensoCoverage["totals"]["max_shift_ratio"]},
                "implementation": {"driver": ensoProtocol["implementation_rule"]["driver"], "driverSha256": ensoProtocol["implementation_rule"]["driver_sha256"], "scopeAdapter": ensoProtocol["implementation_rule"]["scope_adapter"], "scopeAdapterSha256": ensoCoverage["analysis_scope"]["scope_adapter_sha256"], "wrapper": ensoProtocol["implementation_rule"]["wrapper"], "wrapperSha256": ensoProtocol["implementation_rule"]["wrapper_sha256"]},
                "protocolCommits": {"frozenBeforeResults": "f4bcf28", "results": "53bf6cf"},
                "decision": {**ensoCoverage["decision"], "independent_physical_experiment_claimed": False, "independent_model_family_claimed": False},
            },
            "scientificClaim": "ENSO 的 168 点中 135 点可给界、33 点不可用，连续椭球安全为 4／5 折，独立盒为 3／5 折；131 个可比较点中椭球均更紧。第 5 折 RMSE 明显优于基线，但 33 点全部无可给界，形成新的预测—证明解离。",
            "limitations": "候选不是 ENSO 原生九参数周期模型，适用范围文本正确不等于物理机制或结果正确；131 对收紧比较不覆盖另外 4 个椭球独有界或 33 个无界点。" + " ".join(ensoCoverage["limitations"]),
            "upstreamContribution": "提供范围适配层首次用于新数据前瞻协议的完整案例，分开记录周期预测、连续安全、逐点可用性、界组成、同点比较和三类实现哈希。",
            "snapshotFiles": ["validation/enso-ellipsoid-coverage-protocol.json", "validation/enso-ellipsoid-coverage.json", "validation/frontier-enso-coverage-word.json"],
        },
        {
            "id": "bound-comparison-v4-scope-expansion", "domain": "math", "title": "六外部与九组界组成及 ENSO 最大界反例对照",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/chwirut1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/enso.shtml"],
            "metrics": {
                "externalV4Totals": externalV4Decomposition["totals"],
                "combinedV4Totals": combinedV4Decomposition["totals"],
                "datasets": [{"id": item["id"], "scope": item["scope"], "ellipsoid_available_point_count": item["ellipsoid_available_point_count"], "prediction_shift_dominant_point_count": item["prediction_shift_dominant_point_count"], "snapshot_residual_dominant_point_count": item["snapshot_residual_dominant_point_count"], "median_shift_share": item["median_shift_share"], "maximumBoundDominant": item["maximum_residual_upper_bound"]["dominant"]} for item in combinedV4Decomposition["datasets"]],
                "ensoIncrement": {"pointCount": 168, "available": 135, "unavailable": 33, "predictionShiftDominant": 33, "snapshotResidualDominant": 102},
                "ensoMaximumBound": externalV4Decomposition["datasets"][-1]["maximum_residual_upper_bound"],
                "relatedDataset": chwirut1Protocol["dataset_scope"]["related_prior_dataset"],
                "periodicCandidateScope": externalV4Decomposition["analysis_scope"]["periodic_candidate_scope"],
                "decision": {**combinedV4Decomposition["decision"], "independent_model_family_claimed": False, "native_periodic_model_claimed": False},
                "historicalPreservation": {"previousFilesPreserved": True, "fiveExternal": "exports/external-bound-decomposition-v3.json", "eightDatasets": "exports/internal-external-bound-comparison-v3.json"},
            },
            "scientificClaim": "六外部共 761 点，其中 527 点可用、234 点不可用；250 点平移主导、277 点实际残差主导。九组共 896 个可用点，594 点平移主导、302 点实际残差主导。ENSO 增加 102 个实际残差主导点，其最大界平移占比仅 0.108143，九组最大界不再全部由平移主导。",
            "limitations": "这是新增周期数据后的事后范围汇总，不是合并成功率、证明能力改善或原生周期模型验证；Chwirut1 的同族边界与 ENSO 的子集比较范围必须保留。" + " ".join(combinedV4Decomposition["limitations"]),
            "upstreamContribution": "提供六外部与九组并存的新版范围接口，同时连接 ENSO 增量、最大界实际残差主导反例、数据亲缘和两类不可用边界，防止旧机制概括覆盖新证据。",
            "snapshotFiles": ["validation/external-bound-decomposition-v4-protocol.json", "validation/internal-external-bound-comparison-v4-protocol.json", "validation/enso-ellipsoid-coverage-protocol.json", "validation/frontier-bound-comparison-v4-word.json"],
        },
        {
            "id": "maximum-full-composition-audit", "domain": "math", "title": "九组最大界点与全点组成的极值代表性审计",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/chwirut1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/enso.shtml"],
            "metrics": {"totals": maximumAudit["totals"], "datasets": maximumAudit["datasets"], "analysisScope": maximumAudit["analysis_scope"], "decision": maximumAudit["decision"]},
            "scientificClaim": "九组中 8 组最大界点与多数主导项一致，Gauss1 唯一不一致；6 组最大点占比低于中位数。Gauss1 最大界宽为中位界宽的 82.994 倍，ENSO 最大点占比仅处于描述性第 13.33% 位置，类别一致不代表典型幅度。",
            "limitations": "这是只读事后分布审计，最大点不是典型点；描述性百分位、占比和界宽比不是概率、方差分解或物理因果贡献。" + " ".join(maximumAudit["limitations"]),
            "upstreamContribution": "提供最大点类别、全点中位占比、描述性百分位和最大／中位界宽比的联合验收接口，防止单个极值替代整体机制。",
            "snapshotFiles": ["validation/maximum-full-composition-protocol.json", "validation/frontier-maximum-full-composition-word.json"],
        },
        {
            "id": "extreme-reporting-contract", "domain": "math", "title": "极值报告三级写作契约与机器验收",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/enso.shtml"],
            "metrics": {"claimLevel": extremeCheck["claim_level"], "levelNames": extremeCheck["level_names"], "datasetCount": extremeCheck["dataset_count"], "errorCount": extremeCheck["error_count"], "decision": extremeCheck["decision"], "reportSha256": extremeCheck["report_sha256"], "rulesSha256": extremeCheck["rules_sha256"], "validatorSha256": extremeCheck["validator_sha256"]},
            "scientificClaim": "L0 极值描述、L1 全点分布和 L2 限定机制解释已形成可执行契约；九组审计通过 L2 验收，错误百分位、类别、界宽比和最大点典型性主张会被拒绝。",
            "limitations": "契约只验证报告结构、字段和数值关系，不证明物理机制为真，也不替代原始数据、独立实验或人工科学审查。",
            "upstreamContribution": "提供报告等级、字段义务、数值重算、反例保留和哈希验收记录，防止单个极值在写作中被升级为整体机制。",
            "snapshotFiles": ["validation/extreme-reporting-check.json", "validation/frontier-extreme-reporting-word.json"],
        },
        {
            "id": "extreme-corpus-classification", "domain": "math", "title": "既有报告极值表述的全集分级与原文保持审计",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/enso.shtml"],
            "metrics": {"documentCount": corpusCheck["document_count"], "companionRequiredCount": corpusCheck["companion_required_count"], "completeCount": corpusCheck["complete_count"], "descriptiveOnlyCount": corpusCheck["descriptive_only_count"], "unchangedOriginalCount": corpusCheck["unchanged_original_count"], "errorCount": corpusCheck["error_count"], "corpusDocumentSha256": corpusCheck["corpus_document_sha256"], "specSha256": corpusCheck["spec_sha256"], "validatorSha256": corpusCheck["validator_sha256"]},
            "scientificClaim": "16 份极值相关文档已完成分级：10 份需与全点分布审计联读，4 份仅作极值事实或索引，2 份已满足契约；10 份需联读原文的哈希全部保持不变。",
            "limitations": "全集分级只约束极值表述的阅读方式，不替代原始证据，不批量修改历史 Markdown 或 Word，也不把补充说明当作新的物理结论。",
            "upstreamContribution": "提供全文件覆盖、主张等级、联读义务和原文哈希保持的审计接口，防止旧报告中的单个极值脱离后续反例被过度推广。",
            "snapshotFiles": ["validation/extreme-corpus-audit.json", "validation/extreme-corpus-check.json", "validation/frontier-extreme-corpus-word.json"],
        },
        {
            "id": "roszman1-prediction-proof-dissociation",
            "domain": "physics",
            "title": "Roszman1 小样本预测—证明解离与平移主导界审计",
            "status": "verified",
            "evidenceClass": "local_recomputation",
            "sources": [
                "https://www.itl.nist.gov/div898/strd/nls/data/roszman1.shtml",
                "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Roszman1.dat",
            ],
            "metrics": {
                "totals": roszman1Coverage["totals"],
                "folds": [
                    {
                        "fold": case["fold"],
                        "testPointCount": len(case["point_results"]),
                        "modelRmse": case["test_metrics"]["rmse"],
                        "baselineRmse": case["baseline_test_metrics"]["rmse"],
                        "continuousEllipsoidSafe": case["continuous_ellipsoid_safe"],
                        "independentBoxContinuousSafe": case["independent_box_continuous_safe"],
                        "availablePointCount": sum(point.get("ellipsoid_available", False) for point in case["point_results"]),
                        "boxAvailablePointCount": sum(point.get("box_available", False) for point in case["point_results"]),
                    }
                    for case in roszman1Coverage["folds"]
                ],
                "betterBaselineWithoutBounds": [
                    {
                        "fold": case["fold"],
                        "modelRmse": case["test_metrics"]["rmse"],
                        "baselineRmse": case["baseline_test_metrics"]["rmse"],
                        "availablePointCount": sum(point.get("ellipsoid_available", False) for point in case["point_results"]),
                    }
                    for case in [roszman1Coverage["folds"][0], roszman1Coverage["folds"][3]]
                ],
                "fold5Failure": {
                    "fold": 5,
                    "modelRmse": roszman1Coverage["folds"][4]["test_metrics"]["rmse"],
                    "baselineRmse": roszman1Coverage["folds"][4]["baseline_test_metrics"]["rmse"],
                    "availablePointCount": sum(point.get("ellipsoid_available", False) for point in roszman1Coverage["folds"][4]["point_results"]),
                },
                "boxComparison": {
                    "availablePairCount": sum(
                        point.get("ellipsoid_available", False) and point.get("box_available", False)
                        for case in roszman1Coverage["folds"] for point in case["point_results"]
                    ),
                    "tighterPointCount": roszman1Coverage["totals"]["tighter_point_count"],
                    "ellipsoidOnlyPointCount": sum(
                        point.get("ellipsoid_available", False) and not point.get("box_available", False)
                        for case in roszman1Coverage["folds"] for point in case["point_results"]
                    ),
                    "medianShiftRatio": roszman1Coverage["totals"]["median_shift_ratio"],
                    "minShiftRatio": roszman1Coverage["totals"]["min_shift_ratio"],
                    "maxShiftRatio": roszman1Coverage["totals"]["max_shift_ratio"],
                },
                "minimumAvailableShiftShare": min(
                    point["ellipsoid_prediction_shift_upper_bound_float"] / point["ellipsoid_absolute_residual_upper_bound_float"]
                    for case in roszman1Coverage["folds"]
                    for point in case["point_results"] if point.get("ellipsoid_available")
                ),
                "implementation": {
                    "driver": roszman1Protocol["implementation_rule"]["driver"],
                    "driverSha256": roszman1Protocol["implementation_rule"]["driver_sha256"],
                    "scopeAdapter": roszman1Protocol["implementation_rule"]["scope_adapter"],
                    "scopeAdapterSha256": roszman1Coverage["analysis_scope"]["scope_adapter_sha256"],
                    "wrapper": roszman1Protocol["implementation_rule"]["wrapper"],
                    "wrapperSha256": roszman1Protocol["implementation_rule"]["wrapper_sha256"],
                },
                "protocolCommits": {"frozenBeforeResults": "0ad8c06", "results": "a25641a"},
                "decision": {
                    **roszman1Coverage["decision"],
                    "independent_physical_experiment_claimed": False,
                    "independent_model_family_claimed": False,
                },
            },
            "scientificClaim": "25 点中仅第 2 折的 5 点可给界，20 点不可用；第 1、4 折优于基线但零可用界，第 5 折明显预测失败。4 对比较中椭球更紧，另 1 点只有椭球界，平移占比均超过 98.3%。",
            "limitations": "小样本和平移主导界只覆盖第 2 折，不是 25 点概率覆盖、连续 x 误差界或原生反正切模型验证。",
            "upstreamContribution": "分开记录预测、连续安全、逐点可用性、界宽度、平移组成、同点比较范围和三类实现哈希。",
            "snapshotFiles": [
                "validation/roszman1-ellipsoid-coverage-protocol.json",
                "validation/roszman1-ellipsoid-coverage.json",
                "validation/frontier-roszman1-coverage-word.json",
            ],
        },
        {
            "id": "bound-comparison-v5-scope-expansion", "domain": "math", "title": "七外部与十组界组成及 Roszman1 小样本边界对照",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/chwirut1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/enso.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/roszman1.shtml"],
            "metrics": {
                "externalV5Totals": externalV5Decomposition["totals"],
                "combinedV5Totals": combinedV5Decomposition["totals"],
                "datasets": [{"id": item["id"], "scope": item["scope"], "ellipsoid_available_point_count": item["ellipsoid_available_point_count"], "prediction_shift_dominant_point_count": item["prediction_shift_dominant_point_count"], "snapshot_residual_dominant_point_count": item["snapshot_residual_dominant_point_count"], "median_shift_share": item["median_shift_share"], "maximumBoundDominant": item["maximum_residual_upper_bound"]["dominant"]} for item in combinedV5Decomposition["datasets"]],
                "datasetCount": len(combinedV5Decomposition["datasets"]),
                "roszman1Increment": {"pointCount": 25, "available": 5, "unavailable": 20, "predictionShiftDominant": 5, "snapshotResidualDominant": 0},
                "roszman1AvailableFolds": [case["fold"] for case in externalV5Decomposition["datasets"][-1]["folds"] if case["available_point_count"]],
                "roszman1MaximumBound": externalV5Decomposition["datasets"][-1]["maximum_residual_upper_bound"],
                "relatedDataset": chwirut1Protocol["dataset_scope"]["related_prior_dataset"],
                "periodicCandidateScope": externalV5Decomposition["analysis_scope"]["periodic_candidate_scope"],
                "roszman1CandidateScope": externalV5Decomposition["analysis_scope"]["roszman1_candidate_scope"],
                "decision": {**combinedV5Decomposition["decision"], "independent_model_family_claimed": False, "native_periodic_model_claimed": False, "native_arctangent_model_claimed": False, "independent_physical_experiment_claimed": False},
                "historicalPreservation": {"previousFilesPreserved": True, "sixExternal": "exports/external-bound-decomposition-v4.json", "nineDatasets": "exports/internal-external-bound-comparison-v4.json"},
                "protocolCommits": {"externalProtocol": "ae89706", "externalResultsAndCombinedProtocol": "862379e", "combinedResults": "851a842"},
            },
            "scientificClaim": "七外部共 786 点，其中 532 点可用、254 点不可用；255 点平移主导、277 点实际残差主导。十组共 901 个可用点，599 点平移主导、302 点实际残差主导。Roszman1 增加 25 总点、5 个第 2 折可用点和 20 个不可用点；十组最大界中九组由平移主导，ENSO 仍由实际残差主导。",
            "limitations": "这是新增小样本量子缺陷数据后的事后范围汇总，不是合并成功率、证明能力改善、原生反正切模型验证或独立物理实验；Chwirut1 同族边界、ENSO 周期候选边界和 Roszman1 第 2 折局部可用范围必须保留。" + " ".join(combinedV5Decomposition["limitations"]),
            "upstreamContribution": "提供七外部与十组并存的新版范围接口，同时连接 Roszman1 增量、逐折小样本限制、历史版本、数据亲缘和两类不可用边界，防止新增计数被写成统一成功率。",
            "snapshotFiles": ["validation/external-bound-decomposition-v5-protocol.json", "validation/internal-external-bound-comparison-v5-protocol.json", "validation/frontier-bound-comparison-v5-word.json"],
        },
        {
            "id": "maximum-full-composition-v2-audit", "domain": "math", "title": "十组最大界点、全点组成与小样本描述性百分位审计",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/lls/data/filip.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/mgh17.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/gauss1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/misra1a.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/chwirut1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/enso.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/roszman1.shtml"],
            "metrics": {
                "totals": maximumV2Audit["totals"],
                "datasets": maximumV2Audit["datasets"],
                "roszman1": maximumV2Audit["datasets"][-1],
                "roszman1AvailableFolds": [case["fold"] for case in externalV5Decomposition["datasets"][-1]["folds"] if case["available_point_count"]],
                "excludedRoszman1PointCount": externalV5Decomposition["datasets"][-1]["ellipsoid_unavailable_point_count"],
                "analysisScope": maximumV2Audit["analysis_scope"],
                "decision": {**maximumV2Audit["decision"], "native_arctangent_model_claimed": False, "independent_physical_experiment_claimed": False},
                "reportingReceipt": {"claimLevel": extremeV2Check["claim_level"], "errorCount": extremeV2Check["error_count"], "datasetCount": extremeV2Check["dataset_count"], "reportSha256": extremeV2Check["report_sha256"], "rulesSha256": extremeV2Check["rules_sha256"], "validatorSha256": extremeV2Check["validator_sha256"], "baseValidatorSha256": extremeV2Check["base_validator_sha256"]},
                "historicalPreservation": {"nineDatasetAudit": "exports/maximum-full-composition-audit.json", "nineDatasetReceipt": "validation/extreme-reporting-check.json", "previousFilesPreserved": True},
                "protocolCommits": {"protocol": "b9b65e4", "results": "767e26a", "reportingReceipt": "280b7f5"},
            },
            "scientificClaim": "十组中 9 组最大点类别与多数一致，Gauss1 仍是唯一类别反例，ENSO 仍是唯一最大点实际残差主导组，6 组最大点占比低于中位数。Roszman1 最大点占比在 5 个第 2 折可用点中处描述性第 100% 位置，界宽比为 1.220322；该百分位不覆盖另外 20 个不可用点。",
            "limitations": "描述性百分位只适用于各组已定义占比的可用点，不是概率、总体代表性或物理因果；Roszman1 的 100% 仅指 5 个第 2 折可用点，不是 25 点概率覆盖或原生模型验证。" + " ".join(maximumV2Audit["limitations"]),
            "upstreamContribution": "在保留九组审计和旧收据的同时，提供十组动态图题、独立 L2 收据和小样本百分位反例，阻止把局部排序升级为概率覆盖。",
            "snapshotFiles": ["validation/maximum-full-composition-v2-protocol.json", "validation/extreme-reporting-v2-check.json", "validation/frontier-maximum-full-composition-v2-word.json"],
        },
    ]
    packet = {
        "schemaVersion": 1,
        "asOf": "2026-11-09",
        "project": "frontier-breakthrough",
        "scope": "跨项目本地复核与数据库对照；verified 仅指所述检查，不是新发现、独立实验或外部认证。",
        "items": items,
    }
    validate(packet)
    return packet


def validate(packet: dict) -> None:
    assert packet["schemaVersion"] == 1 and packet["project"] == "frontier-breakthrough"
    ids = [item["id"] for item in packet["items"]]
    assert len(ids) == len(set(ids))
    required = {"id", "domain", "title", "status", "evidenceClass", "sources", "metrics", "scientificClaim", "limitations", "upstreamContribution", "snapshotFiles"}
    for item in packet["items"]:
        assert required <= item.keys()
        assert item["status"] == "verified"
        assert item["sources"] and all(url.startswith("https://") for url in item["sources"])
        assert item["limitations"] and item["upstreamContribution"]
        for name in item["snapshotFiles"]:
            assert name.startswith("validation/") and (ROOT / name).is_file(), name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == text, "证据包不是最新"
        print("OK: evidence packet is current")
    else:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
