"""Build a validated claim-evidence-counterexample-experiment graph from real outputs."""

import json
from pathlib import Path


def node(identifier, kind, title, status, sources):
    return {"id": identifier, "kind": kind, "title": title, "status": status, "sourceFiles": sources}


def edge(source, target, relation):
    return {"from": source, "to": target, "relation": relation}


def build_graph(root):
    root = Path(root)
    chwirut = json.loads((root / "validation/chwirut-holdout.json").read_text(encoding="utf-8"))
    z3 = json.loads((root / "validation/z3-identifiability.json").read_text(encoding="utf-8"))
    aspirin = json.loads((root / "validation/aspirin-crosscheck.json").read_text(encoding="utf-8"))
    material = json.loads((root / "validation/material-crosscheck.json").read_text(encoding="utf-8"))
    eckerle = json.loads((root / "validation/eckerle4-two-tail.json").read_text(encoding="utf-8"))
    cvc5 = json.loads((root / "validation/cvc5-crosscheck.json").read_text(encoding="utf-8"))
    hahn1 = json.loads((root / "validation/hahn1-high-temperature.json").read_text(encoding="utf-8"))
    z3Hahn1 = json.loads((root / "validation/z3-hahn1-denominator.json").read_text(encoding="utf-8"))
    cvc5Hahn1 = json.loads((root / "validation/cvc5-hahn1-denominator.json").read_text(encoding="utf-8"))
    groupedStress = json.loads((root / "validation/grouped-stress.json").read_text(encoding="utf-8"))
    identifiability = json.loads((root / "validation/hahn1-fold1-identifiability.json").read_text(encoding="utf-8"))
    denominatorRoots = json.loads((root / "validation/hahn1-frozen-denominator-roots.json").read_text(encoding="utf-8"))
    thurber = json.loads((root / "validation/thurber-prospective-gate.json").read_text(encoding="utf-8"))
    kirby = json.loads((root / "validation/kirby2-prospective-gate.json").read_text(encoding="utf-8"))
    crossDataset = json.loads((root / "exports/rational-cross-dataset.json").read_text(encoding="utf-8"))
    exactRoots = json.loads((root / "validation/rational-exact-interval-roots.json").read_text(encoding="utf-8"))
    parameterBox = json.loads((root / "validation/rational-parameter-box-stability.json").read_text(encoding="utf-8"))
    predictionBounds = json.loads((root / "validation/rational-prediction-box-bounds.json").read_text(encoding="utf-8"))
    ellipsoidComparison = json.loads((root / "validation/rational-ellipsoid-box-comparison.json").read_text(encoding="utf-8"))
    ellipsoidInterval = json.loads((root / "validation/rational-ellipsoid-interval-safety.json").read_text(encoding="utf-8"))
    filipCoverage = json.loads((root / "validation/filip-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    mgh17Coverage = json.loads((root / "validation/mgh17-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    externalComparison = json.loads((root / "exports/external-coverage-comparison.json").read_text(encoding="utf-8"))
    gauss1Coverage = json.loads((root / "validation/gauss1-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    gauss1Comparison = json.loads((root / "exports/external-coverage-gauss1-comparison.json").read_text(encoding="utf-8"))
    gauss1Mechanism = json.loads((root / "validation/gauss1-bound-mechanism.json").read_text(encoding="utf-8"))
    externalDecomposition = json.loads((root / "exports/external-bound-decomposition.json").read_text(encoding="utf-8"))
    internalExternalDecomposition = json.loads((root / "exports/internal-external-bound-comparison.json").read_text(encoding="utf-8"))
    misra1aCoverage = json.loads((root / "validation/misra1a-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    chwirut1Coverage = json.loads((root / "validation/chwirut1-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    chwirut1Protocol = json.loads((root / "validation/chwirut1-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
    externalV2Decomposition = json.loads((root / "exports/external-bound-decomposition-v2.json").read_text(encoding="utf-8"))
    combinedV2Decomposition = json.loads((root / "exports/internal-external-bound-comparison-v2.json").read_text(encoding="utf-8"))
    externalV3Decomposition = json.loads((root / "exports/external-bound-decomposition-v3.json").read_text(encoding="utf-8"))
    combinedV3Decomposition = json.loads((root / "exports/internal-external-bound-comparison-v3.json").read_text(encoding="utf-8"))
    externalV4Decomposition = json.loads((root / "exports/external-bound-decomposition-v4.json").read_text(encoding="utf-8"))
    combinedV4Decomposition = json.loads((root / "exports/internal-external-bound-comparison-v4.json").read_text(encoding="utf-8"))
    externalV5Decomposition = json.loads((root / "exports/external-bound-decomposition-v5.json").read_text(encoding="utf-8"))
    combinedV5Decomposition = json.loads((root / "exports/internal-external-bound-comparison-v5.json").read_text(encoding="utf-8"))
    if externalV5Decomposition["totals"]["point_count"] != 786 or externalV5Decomposition["totals"]["ellipsoid_available_point_count"] != 532 or externalV5Decomposition["totals"]["ellipsoid_unavailable_point_count"] != 254 or externalV5Decomposition["totals"]["prediction_shift_dominant_point_count"] != 255 or externalV5Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 277 or len(externalV5Decomposition["datasets"]) != 7 or externalV5Decomposition["datasets"][-1]["id"] != "roszman1" or [case["available_point_count"] for case in externalV5Decomposition["datasets"][-1]["folds"]] != [0, 5, 0, 0, 0] or combinedV5Decomposition["totals"]["ellipsoid_available_point_count"] != 901 or combinedV5Decomposition["totals"]["prediction_shift_dominant_point_count"] != 599 or combinedV5Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 302 or len(combinedV5Decomposition["datasets"]) != 10 or combinedV5Decomposition["analysis_scope"]["roszman1_native_arctangent_model_claimed"] or combinedV5Decomposition["analysis_scope"]["roszman1_independent_physical_experiment"]:
        raise ValueError("Expected v5 scope expansion and Roszman1 small-sample boundaries are not present")
    maximumAudit = json.loads((root / "exports/maximum-full-composition-audit.json").read_text(encoding="utf-8"))
    maximumV2Audit = json.loads((root / "exports/maximum-full-composition-audit-v2.json").read_text(encoding="utf-8"))
    extremeV2Check = json.loads((root / "validation/extreme-reporting-v2-check.json").read_text(encoding="utf-8"))
    if maximumV2Audit["totals"]["dataset_count"] != 10 or maximumV2Audit["totals"]["maximum_matches_majority_count"] != 9 or maximumV2Audit["totals"]["maximum_majority_mismatch_dataset_ids"] != ["gauss1"] or maximumV2Audit["totals"]["maximum_snapshot_residual_dominant_dataset_ids"] != ["enso"] or maximumV2Audit["totals"]["maximum_share_below_median_count"] != 6 or maximumV2Audit["totals"]["maximum_share_above_median_dataset_ids"] != ["filip", "mgh17", "gauss1", "roszman1"] or maximumV2Audit["datasets"][-1]["id"] != "roszman1" or maximumV2Audit["datasets"][-1]["available_point_count"] != 5 or maximumV2Audit["datasets"][-1]["maximum_share_descriptive_percentile"] != 1.0 or maximumV2Audit["analysis_scope"]["roszman1_native_arctangent_model_claimed"] or maximumV2Audit["analysis_scope"]["roszman1_independent_physical_experiment"] or extremeV2Check["status"] != "passed" or extremeV2Check["dataset_count"] != 10 or extremeV2Check["error_count"] != 0 or extremeV2Check["claim_level"] != "mechanism_interpretation":
        raise ValueError("Expected ten-dataset extreme audit and small-sample percentile boundaries are not present")
    extremeCheck = json.loads((root / "validation/extreme-reporting-check.json").read_text(encoding="utf-8"))
    corpusCheck = json.loads((root / "validation/extreme-corpus-check.json").read_text(encoding="utf-8"))
    corpusV2Spec = json.loads((root / "validation/extreme-corpus-v2-audit.json").read_text(encoding="utf-8"))
    corpusV2Check = json.loads((root / "validation/extreme-corpus-v2-check.json").read_text(encoding="utf-8"))
    if corpusV2Check["status"] != "passed" or corpusV2Check["document_count"] != 23 or corpusV2Check["companion_required_count"] != 12 or corpusV2Check["complete_count"] != 4 or corpusV2Check["descriptive_only_count"] != 7 or corpusV2Check["hash_matched_document_count"] != 22 or corpusV2Check["unchanged_original_count"] != 10 or corpusV2Check["error_count"] != 0 or not corpusV2Check["previous_files_preserved"] or [item["review_status"] for item in corpusV2Spec["documents"][-7:]] != ["companion_required", "companion_required", "complete", "descriptive_only", "complete", "descriptive_only", "descriptive_only"]:
        raise ValueError("Expected expanded extreme corpus and historical preservation are not present")
    repositoryAudit = json.loads((root / "validation/repository-integrity-report.json").read_text(encoding="utf-8"))
    if repositoryAudit["status"] != "passed" or repositoryAudit["error_count"] != 0 or repositoryAudit["groups"]["readme_local_links"]["count"] < 84 or repositoryAudit["groups"]["document_figure_links"]["count"] < 44 or repositoryAudit["groups"]["word_manifests"]["count"] < 36 or repositoryAudit["groups"]["protocol_inputs"]["count"] < 10 or repositoryAudit["groups"]["corpus_v2"]["documents"] != 23 or not repositoryAudit["groups"]["dynamic_counts"]["readme_consistent"] or repositoryAudit["decision"]["visual_qa_claimed"] or repositoryAudit["decision"]["scientific_truth_claimed"]:
        raise ValueError("Expected repository integrity audit and dynamic counts are not present")
    nativeCross = json.loads((root / "exports/native-cross-dataset-synthesis.json").read_text(encoding="utf-8"))
    if nativeCross["totals"]["dataset_count"] != 3 or nativeCross["totals"]["fold_count"] != 15 or nativeCross["totals"]["point_count"] != 407 or nativeCross["totals"]["native_better_than_rational_fold_count"] != 11 or nativeCross["totals"]["rational_better_than_native_fold_count"] != 4 or nativeCross["totals"]["overall_best_model_fold_counts"] != {"native": 10, "rational": 3, "cubic": 2, "tie": 0} or nativeCross["totals"]["point_outcomes"] != {"native": 256, "rational": 151, "tie": 0} or nativeCross["totals"]["metric_direction_disagreement_fold_ids"] != ["roszman1:4"] or nativeCross["totals"]["point_fold_disagreement_fold_ids"] or nativeCross["cross_dataset_pooled_error_metrics"] is not None or nativeCross["decision"]["universal_model_ranking_claimed"] or nativeCross["decision"]["rational_bounds_transferred_to_native"]:
        raise ValueError("Expected native cross-dataset fold, point and metric-direction boundaries are not present")
    fold4Decomposition = json.loads((root / "validation/roszman1-native-fold4-error-decomposition.json").read_text(encoding="utf-8"))
    if fold4Decomposition["totals"]["point_count"] != 5 or fold4Decomposition["totals"]["native_absolute_winner_count"] != 3 or fold4Decomposition["totals"]["rational_absolute_winner_count"] != 2 or fold4Decomposition["totals"]["leave_one_out_reverses_rational_mae_count"] != 2 or fold4Decomposition["totals"]["leave_one_out_reverses_native_rmse_count"] != 0 or fold4Decomposition["totals"]["per_point_absolute_squared_direction_disagreement_count"] != 0 or fold4Decomposition["aggregate"]["absolute_delta_sum"] <= 0 or fold4Decomposition["aggregate"]["squared_delta_sum"] >= 0 or fold4Decomposition["aggregate"]["weight_identity_mismatch_count"] or fold4Decomposition["aggregate"]["frozen_metric_mismatch_count"] or fold4Decomposition["decision"]["leave_one_out_refitting_performed"] or fold4Decomposition["decision"]["statistical_significance_claimed"]:
        raise ValueError("Expected Roszman1 fold-4 weighted reversal and leave-one-out boundaries are not present")
    chwirut1NativeIdentifiability = json.loads((root / "validation/chwirut1-native-identifiability.json").read_text(encoding="utf-8"))
    if chwirut1NativeIdentifiability["totals"]["fold_count"] != 5 or chwirut1NativeIdentifiability["totals"]["held_out_point_count"] != 214 or chwirut1NativeIdentifiability["totals"]["full_numerical_rank_fold_count"] != 5 or chwirut1NativeIdentifiability["totals"]["local_diagnostic_failure_count"] != 0 or chwirut1NativeIdentifiability["totals"]["max_scaled_condition_number"] != 28.674083116404475 or chwirut1NativeIdentifiability["totals"]["max_absolute_off_diagonal_parameter_correlation"] != 0.9794131139106378 or chwirut1NativeIdentifiability["totals"]["max_local_prediction_standard_deviation"] != 14.836682306268235 or chwirut1NativeIdentifiability["totals"]["minimum_absolute_denominator"] != 0.009384279096904605 or chwirut1NativeIdentifiability["totals"]["pole_inside_observed_range_fold_count"] != 0 or chwirut1NativeIdentifiability["folds"][0]["training_jacobian"]["parameters"][1]["absolute_relative_standard_error"] != 1.7106283204180401 or chwirut1NativeIdentifiability["analysis_scope"]["refit"] or chwirut1NativeIdentifiability["decision"]["global_structural_identifiability_proved"] or chwirut1NativeIdentifiability["decision"]["independent_model_family_claimed"]:
        raise ValueError("Expected Chwirut1 native local-identifiability, denominator and related-study boundaries are not present")
    roszman1Coverage = json.loads((root / "validation/roszman1-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    roszman1Protocol = json.loads((root / "validation/roszman1-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
    nativeHoldout = json.loads((root / "validation/roszman1-native-holdout.json").read_text(encoding="utf-8"))
    nativeProtocol = json.loads((root / "validation/roszman1-native-holdout-protocol.json").read_text(encoding="utf-8"))
    nativeIdentifiability = json.loads((root / "validation/roszman1-native-identifiability.json").read_text(encoding="utf-8"))
    nativeIdentifiabilityProtocol = json.loads((root / "validation/roszman1-native-identifiability-protocol.json").read_text(encoding="utf-8"))
    if nativeIdentifiability["totals"]["fold_count"] != 5 or nativeIdentifiability["totals"]["full_numerical_rank_fold_count"] != 5 or nativeIdentifiability["totals"]["local_diagnostic_failure_count"] != 0 or nativeIdentifiability["totals"]["max_scaled_condition_number"] != 90.74335888809009 or nativeIdentifiability["totals"]["max_absolute_off_diagonal_parameter_correlation"] != 0.9875352588520016 or nativeIdentifiability["parameter_stability"]["b2"]["range"] <= 1.0e-5 or nativeIdentifiability["parameter_stability"]["b4"]["range"] <= 112 or nativeIdentifiability["analysis_scope"]["refit"] or nativeIdentifiability["analysis_scope"]["global_identifiability"] or nativeIdentifiability["decision"]["prediction_stability_equals_parameter_uniqueness"] or nativeIdentifiability["decision"]["calibrated_prediction_intervals_produced"]:
        raise ValueError("Expected native local-identifiability and parameter-stability boundaries are not present")
    if len(nativeHoldout["folds"]) != 5 or nativeHoldout["totals"]["point_count"] != 25 or nativeHoldout["totals"]["native_optimizer_failure_count"] != 0 or nativeHoldout["totals"]["native_better_than_rational_fold_count"] != 3 or nativeHoldout["totals"]["rational_better_than_native_fold_count"] != 2 or not nativeHoldout["known_answer"]["within_certified_tolerances"] or not nativeHoldout["analysis_scope"]["same_holdout_points"] or nativeHoldout["decision"]["rational_bounds_transferred_to_native"] or nativeHoldout["decision"]["certified_full_fit_used_as_holdout"] or nativeHoldout["folds"][0]["native_test_metrics"]["rmse"] <= nativeHoldout["folds"][0]["rational_candidate_test_metrics"]["rmse"] or nativeHoldout["folds"][4]["native_test_metrics"]["rmse"] >= nativeHoldout["folds"][4]["rational_candidate_test_metrics"]["rmse"] or nativeHoldout["pooled"]["native"]["rmse"] >= nativeHoldout["pooled"]["rational_candidate"]["rmse"]:
        raise ValueError("Expected native Roszman1 fold-specific comparison and proof separation are not present")
    if roszman1Coverage["totals"]["point_count"] != 25 or roszman1Coverage["totals"]["ellipsoid_available_point_count"] != 5 or roszman1Coverage["totals"]["continuous_safe_fold_count"] != 1 or roszman1Coverage["totals"]["independent_box_continuous_safe_fold_count"] != 0 or roszman1Coverage["totals"]["tighter_point_count"] != 4 or roszman1Coverage["totals"]["looser_point_count"] != 0 or any(point.get("ellipsoid_available", False) for point in roszman1Coverage["folds"][0]["point_results"]) or any(point.get("ellipsoid_available", False) for point in roszman1Coverage["folds"][3]["point_results"]) or any(point.get("ellipsoid_available", False) for point in roszman1Coverage["folds"][4]["point_results"]) or roszman1Coverage["folds"][0]["test_metrics"]["rmse"] >= roszman1Coverage["folds"][0]["baseline_test_metrics"]["rmse"] or roszman1Coverage["folds"][3]["test_metrics"]["rmse"] >= roszman1Coverage["folds"][3]["baseline_test_metrics"]["rmse"] or roszman1Coverage["folds"][4]["test_metrics"]["rmse"] <= roszman1Coverage["folds"][4]["baseline_test_metrics"]["rmse"] or roszman1Coverage["analysis_scope"]["scope_adapter_sha256"] != roszman1Protocol["implementation_rule"]["scope_adapter_sha256"]:
        raise ValueError("Expected Roszman1 fold-specific dissociation and scoped provenance are not present")
    if corpusCheck["status"] != "passed" or corpusCheck["document_count"] != 16 or corpusCheck["companion_required_count"] != 10 or corpusCheck["unchanged_original_count"] != 10 or corpusCheck["error_count"] != 0:
        raise ValueError("Expected extreme corpus classification and original preservation are not present")
    if extremeCheck["status"] != "passed" or extremeCheck["error_count"] != 0 or extremeCheck["claim_level"] != "mechanism_interpretation" or extremeCheck["dataset_count"] != 9 or extremeCheck["decision"]["maximum_point_used_as_typical_claimed"]:
        raise ValueError("Expected executable extreme reporting contract is not present")
    if maximumAudit["totals"]["dataset_count"] != 9 or maximumAudit["totals"]["maximum_matches_majority_count"] != 8 or maximumAudit["totals"]["maximum_majority_mismatch_dataset_ids"] != ["gauss1"] or maximumAudit["totals"]["maximum_share_below_median_count"] != 6 or maximumAudit["totals"]["largest_bound_to_median_ratio_dataset_id"] != "gauss1" or maximumAudit["decision"]["maximum_point_used_as_typical_claimed"] or maximumAudit["decision"]["probability_representativeness_claimed"]:
        raise ValueError("Expected maximum/full composition audit states are not present")
    if externalV4Decomposition["totals"]["point_count"] != 761 or externalV4Decomposition["totals"]["ellipsoid_available_point_count"] != 527 or externalV4Decomposition["totals"]["ellipsoid_unavailable_point_count"] != 234 or externalV4Decomposition["totals"]["prediction_shift_dominant_point_count"] != 250 or externalV4Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 277 or len(externalV4Decomposition["datasets"]) != 6 or externalV4Decomposition["datasets"][-1]["id"] != "enso" or externalV4Decomposition["datasets"][-1]["prediction_shift_dominant_point_count"] != 33 or externalV4Decomposition["datasets"][-1]["snapshot_residual_dominant_point_count"] != 102 or externalV4Decomposition["datasets"][-1]["maximum_residual_upper_bound"]["dominant"] != "snapshot_residual_dominant" or externalV4Decomposition["datasets"][-1]["maximum_residual_upper_bound"]["shift_share"] >= 0.5 or combinedV4Decomposition["totals"]["ellipsoid_available_point_count"] != 896 or combinedV4Decomposition["totals"]["prediction_shift_dominant_point_count"] != 594 or combinedV4Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 302 or len(combinedV4Decomposition["datasets"]) != 9 or combinedV4Decomposition["analysis_scope"]["chwirut1_independent_model_family_test"] or combinedV4Decomposition["analysis_scope"]["enso_native_periodic_model_claimed"]:
        raise ValueError("Expected v4 scope expansion and ENSO maximum-bound counterexample are not present")
    externalScopeAmendment = json.loads((root / "validation/external-scope-limitations-amendment-01-audit.json").read_text(encoding="utf-8"))
    ensoCoverage = json.loads((root / "validation/enso-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    ensoProtocol = json.loads((root / "validation/enso-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
    ensoNativeHoldout = json.loads((root / "validation/enso-native-holdout.json").read_text(encoding="utf-8"))
    ensoNativeProtocol = json.loads((root / "validation/enso-native-holdout-protocol.json").read_text(encoding="utf-8"))
    ensoNativeAmendment = json.loads((root / "validation/enso-native-holdout-protocol-amendment-01.json").read_text(encoding="utf-8"))
    chwirut1NativeHoldout = json.loads((root / "validation/chwirut1-native-holdout.json").read_text(encoding="utf-8"))
    chwirut1NativeProtocol = json.loads((root / "validation/chwirut1-native-holdout-protocol.json").read_text(encoding="utf-8"))
    chwirut1NativeAmendment = json.loads((root / "validation/chwirut1-native-holdout-protocol-amendment-01.json").read_text(encoding="utf-8"))
    if chwirut1NativeHoldout["totals"]["point_count"] != 214 or chwirut1NativeHoldout["totals"]["unique_distance_count"] != 22 or [len(case["point_results"]) for case in chwirut1NativeHoldout["folds"]] != chwirut1NativeAmendment["correction"]["corrected_observation_counts"] or chwirut1NativeHoldout["totals"]["native_optimizer_failure_count"] != 0 or chwirut1NativeHoldout["totals"]["native_better_than_rational_fold_count"] != 4 or chwirut1NativeHoldout["totals"]["rational_better_than_native_fold_count"] != 1 or not chwirut1NativeHoldout["known_answer"]["within_certified_tolerances"] or not chwirut1NativeHoldout["analysis_scope"]["repeated_x_never_crosses_fitting_and_test"] or not chwirut1NativeHoldout["analysis_scope"]["related_prior_dataset"]["same_native_model_family"] or chwirut1NativeHoldout["folds"][1]["native_test_metrics"]["rmse"] <= chwirut1NativeHoldout["folds"][1]["rational_candidate_test_metrics"]["rmse"] or chwirut1NativeHoldout["folds"][0]["native_test_metrics"]["rmse"] <= 14 or chwirut1NativeHoldout["decision"]["independent_model_family_claimed"] or chwirut1NativeHoldout["decision"]["rational_bounds_transferred_to_native"]:
        raise ValueError("Expected Chwirut1 native fold results, metadata correction and related-study scope are not present")
    if ensoNativeHoldout["totals"]["point_count"] != 168 or ensoNativeHoldout["totals"]["native_optimizer_failure_count"] != 0 or ensoNativeHoldout["totals"]["native_better_than_rational_fold_count"] != 4 or ensoNativeHoldout["totals"]["rational_better_than_native_fold_count"] != 1 or ensoNativeHoldout["known_answer"]["within_certified_tolerances"] or not ensoNativeHoldout["known_answer"]["certified_forward_rss_check_passed"] or ensoNativeHoldout["known_answer"]["original_tolerances_relaxed"] or ensoNativeHoldout["known_answer"]["optimizer_mismatch_hidden"] or ensoNativeHoldout["folds"][0]["native_test_metrics"]["rmse"] <= ensoNativeHoldout["folds"][0]["rational_candidate_test_metrics"]["rmse"] or ensoNativeHoldout["folds"][4]["native_test_metrics"]["rmse"] >= ensoNativeHoldout["folds"][4]["rational_candidate_test_metrics"]["rmse"] or ensoNativeHoldout["decision"]["rational_bounds_transferred_to_native"]:
        raise ValueError("Expected ENSO native fold comparison and optimizer/forward evidence separation are not present")
    if ensoCoverage["totals"]["point_count"] != 168 or ensoCoverage["totals"]["ellipsoid_available_point_count"] != 135 or ensoCoverage["totals"]["coverage_violation_count"] != 0 or ensoCoverage["totals"]["continuous_safe_fold_count"] != 4 or ensoCoverage["totals"]["independent_box_continuous_safe_fold_count"] != 3 or ensoCoverage["totals"]["tighter_point_count"] != 131 or ensoCoverage["totals"]["looser_point_count"] != 0 or ensoCoverage["folds"][4]["test_metrics"]["rmse"] >= ensoCoverage["folds"][4]["baseline_test_metrics"]["rmse"] or any(point.get("ellipsoid_available", False) for point in ensoCoverage["folds"][4]["point_results"]) or not ensoCoverage["analysis_scope"]["dataset_specific_scope_text"] or ensoCoverage["analysis_scope"]["scope_adapter_sha256"] != ensoProtocol["implementation_rule"]["scope_adapter_sha256"]:
        raise ValueError("Expected ENSO prediction-proof dissociation and scoped adapter provenance are not present")
    if externalScopeAmendment["correction_count"] != 3 or externalScopeAmendment["numeric_results_modified"] or not externalScopeAmendment["original_files_preserved"] or externalScopeAmendment["dataset_ids"] != ["mgh17", "gauss1", "misra1a"]:
        raise ValueError("Expected external scope amendment is not present")
    if externalV3Decomposition["totals"]["point_count"] != 593 or externalV3Decomposition["totals"]["ellipsoid_available_point_count"] != 392 or externalV3Decomposition["totals"]["ellipsoid_unavailable_point_count"] != 201 or externalV3Decomposition["totals"]["prediction_shift_dominant_point_count"] != 217 or externalV3Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 175 or len(externalV3Decomposition["datasets"]) != 5 or externalV3Decomposition["datasets"][-1]["id"] != "chwirut1" or externalV3Decomposition["datasets"][-1]["prediction_shift_dominant_point_count"] != 75 or externalV3Decomposition["datasets"][-1]["snapshot_residual_dominant_point_count"] != 8 or combinedV3Decomposition["totals"]["ellipsoid_available_point_count"] != 761 or combinedV3Decomposition["totals"]["prediction_shift_dominant_point_count"] != 561 or combinedV3Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 200 or len(combinedV3Decomposition["datasets"]) != 8 or combinedV3Decomposition["analysis_scope"]["chwirut1_independent_model_family_test"]:
        raise ValueError("Expected v3 scope expansion and related-data scope are not present")
    if chwirut1Coverage["totals"]["point_count"] != 214 or chwirut1Coverage["totals"]["ellipsoid_available_point_count"] != 83 or chwirut1Coverage["totals"]["coverage_violation_count"] != 0 or chwirut1Coverage["totals"]["continuous_safe_fold_count"] != 2 or chwirut1Coverage["folds"][3]["test_metrics"]["rmse"] != min(case["test_metrics"]["rmse"] for case in chwirut1Coverage["folds"]) or chwirut1Coverage["folds"][3]["test_metrics"]["rmse"] >= chwirut1Coverage["folds"][3]["baseline_test_metrics"]["rmse"] or any(point.get("ellipsoid_available", False) for point in chwirut1Coverage["folds"][3]["point_results"]) or chwirut1Coverage["analysis_scope"]["independent_model_family_test"] or not chwirut1Protocol["dataset_scope"]["related_prior_dataset"]["same_study"] or not chwirut1Protocol["dataset_scope"]["related_prior_dataset"]["same_native_model_family"]:
        raise ValueError("Expected Chwirut1 prediction-proof dissociation and related-data scope are not present")
    if not chwirut["decision"]["limited_support"] or not aspirin["canonical_structure_identical"] or not material["structure_identity_confirmed"] or not eckerle["decision"]["limited_support"] or not cvc5["all_results_match_z3"] or not hahn1["decision"]["limited_support"] or cvc5Hahn1["result"] != "unsat" or z3Hahn1["result"] != "unsat" or groupedStress["overall_robust_limited_support"] or identifiability["decision"]["fold_1_failure_reversed"] or denominatorRoots["decision"]["fold_1_failure_reversed"] or denominatorRoots["folds"][0]["real_root_count_in_held_out_closed_interval"] != 2 or thurber["decision"]["overall_all_folds_gated_support"] or not thurber["full_fit_certification"]["matches_nist_within_frozen_tolerances"] or not kirby["decision"]["overall_all_folds_gated_support"] or not kirby["full_fit_certification"]["matches_nist_within_frozen_tolerances"] or crossDataset["totals"]["gate_consistent_fold_count"] != 13 or crossDataset["totals"]["domain_failed_fold_count"] != 2 or exactRoots["totals"]["exact_root_count_total"] != 3 or exactRoots["totals"]["dual_solver_agreement_count"] != 15 or exactRoots["decision"]["unresolved_or_disagreement_present"] or parameterBox["totals"]["certified_region_safe_fold_count"] != 13 or parameterBox["totals"]["cap_hit_fold_count"] != 11 or predictionBounds["totals"]["bounded_fold_count"] != 13 or predictionBounds["totals"]["bounded_point_count"] != 369 or ellipsoidComparison["totals"]["comparison_point_count"] != 369 or ellipsoidComparison["totals"]["tighter_point_count"] != 369 or ellipsoidComparison["totals"]["unavailable_rooted_fold_count"] != 2 or ellipsoidInterval["totals"]["continuous_safe_fold_count"] != 13 or ellipsoidInterval["totals"]["not_certified_fold_count"] != 0 or ellipsoidInterval["totals"]["rooted_snapshot_fold_count"] != 2 or filipCoverage["totals"]["ellipsoid_available_point_count"] != 82 or filipCoverage["totals"]["covered_point_count"] != 82 or filipCoverage["totals"]["continuous_safe_fold_count"] != 5 or mgh17Coverage["totals"]["ellipsoid_available_point_count"] != 33 or mgh17Coverage["totals"]["covered_point_count"] != 33 or mgh17Coverage["totals"]["continuous_safe_fold_count"] != 5 or mgh17Coverage["totals"]["independent_box_continuous_safe_fold_count"] != 5 or mgh17Coverage["totals"]["tighter_point_count"] != 32 or externalComparison["totals"]["point_count"] != 115 or externalComparison["totals"]["covered_point_count"] != 115:
        raise ValueError("Expected evidence states are not present")
    if gauss1Coverage["totals"]["point_count"] != 250 or gauss1Coverage["totals"]["ellipsoid_available_point_count"] != 190 or gauss1Coverage["totals"]["continuous_safe_fold_count"] != 3 or gauss1Coverage["folds"][1]["test_metrics"]["rmse"] <= gauss1Coverage["folds"][1]["baseline_test_metrics"]["rmse"] or any(point.get("ellipsoid_available", False) for point in gauss1Coverage["folds"][4]["point_results"]) or gauss1Comparison["totals"]["point_count"] != 365 or gauss1Comparison["totals"]["ellipsoid_available_point_count"] != 305 or gauss1Comparison["totals"]["ellipsoid_unavailable_point_count"] != 60 or gauss1Comparison["totals"]["continuous_safe_fold_count"] != 13:
        raise ValueError("Expected Gauss1 counterexample states are not present")
    if gauss1Mechanism["analysis_scope"]["refit"] or gauss1Mechanism["analysis_scope"]["retuned"] or gauss1Mechanism["totals"]["stored_bound_agreement_count"] != 190 or gauss1Mechanism["totals"]["stored_bound_mismatch_count"] != 0 or gauss1Mechanism["folds"][0]["maximum_residual_upper_bound"]["shift_share"] >= 0.05 or gauss1Mechanism["folds"][1]["maximum_residual_upper_bound"]["shift_share"] <= 0.95 or gauss1Mechanism["folds"][4]["ellipsoid_available_point_count"] != 0:
        raise ValueError("Expected Gauss1 bound-mechanism states are not present")
    if externalDecomposition["totals"]["bound_identity_mismatch_count"] != 0 or externalDecomposition["totals"]["prediction_shift_dominant_point_count"] != 138 or externalDecomposition["totals"]["snapshot_residual_dominant_point_count"] != 167 or externalDecomposition["datasets"][0]["prediction_shift_dominant_point_count"] != 82 or externalDecomposition["datasets"][0]["median_shift_share"] <= 0.99 or externalDecomposition["datasets"][2]["snapshot_residual_dominant_point_count"] != 166 or externalDecomposition["datasets"][2]["median_shift_share"] >= 0.2 or externalDecomposition["gauss1_regression"]["mismatch_count"] != 0:
        raise ValueError("Expected external bound-composition heterogeneity is not present")
    if internalExternalDecomposition["totals"]["ellipsoid_available_point_count"] != 674 or internalExternalDecomposition["totals"]["prediction_shift_dominant_point_count"] != 482 or internalExternalDecomposition["totals"]["snapshot_residual_dominant_point_count"] != 192 or internalExternalDecomposition["totals"]["external_unavailable_point_count"] != 60 or internalExternalDecomposition["totals"]["internal_unavailable_rooted_fold_count"] != 2 or internalExternalDecomposition["totals"]["bound_identity_mismatch_count"] != 0 or len(internalExternalDecomposition["datasets"]) != 6 or internalExternalDecomposition["datasets"][0]["prediction_shift_dominant_point_count"] != 189 or internalExternalDecomposition["datasets"][-1]["snapshot_residual_dominant_point_count"] != 166:
        raise ValueError("Expected internal/external bound-comparison states are not present")
    if misra1aCoverage["totals"]["point_count"] != 14 or misra1aCoverage["totals"]["ellipsoid_available_point_count"] != 4 or misra1aCoverage["totals"]["continuous_safe_fold_count"] != 1 or misra1aCoverage["totals"]["independent_box_continuous_safe_fold_count"] != 0 or misra1aCoverage["totals"]["max_ellipsoid_absolute_residual_upper_bound_float"] <= 400 or misra1aCoverage["folds"][4]["test_metrics"]["rmse"] <= misra1aCoverage["folds"][4]["baseline_test_metrics"]["rmse"] or not all(point["ellipsoid_prediction_shift_upper_bound_float"] / point["ellipsoid_absolute_residual_upper_bound_float"] > 0.999 for case in misra1aCoverage["folds"] for point in case["point_results"] if point.get("ellipsoid_available", False)):
        raise ValueError("Expected Misra1a prediction-proof dissociation is not present")
    if externalV2Decomposition["totals"]["point_count"] != 379 or externalV2Decomposition["totals"]["ellipsoid_available_point_count"] != 309 or externalV2Decomposition["totals"]["ellipsoid_unavailable_point_count"] != 70 or externalV2Decomposition["totals"]["prediction_shift_dominant_point_count"] != 142 or externalV2Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 167 or combinedV2Decomposition["totals"]["ellipsoid_available_point_count"] != 678 or combinedV2Decomposition["totals"]["prediction_shift_dominant_point_count"] != 486 or combinedV2Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 192 or len(combinedV2Decomposition["datasets"]) != 7 or combinedV2Decomposition["datasets"][-1]["ellipsoid_available_point_count"] != 4:
        raise ValueError("Expected v2 scope-expansion states are not present")

    nodes = [
        node("track-holdout", "project", "真实数据留出与外推边界", "active", ["validation/chwirut-holdout-protocol.json"]),
        node("track-formal", "project", "形式化定义域与可识别性反例", "active", ["validation/z3-identifiability.json"]),
        node("track-chemistry", "project", "化学与生物数据质量", "active", ["validation/aspirin-crosscheck.json"]),
        node("track-materials", "project", "物理与材料跨库复核", "active", ["validation/material-crosscheck.json"]),
        node("track-knowledge", "project", "主张—证据—反例—实验知识连接", "active", ["contracts/frontier-knowledge-graph.schema.json"]),
        node("claim-chwirut-extrapolation", "claim", "Chwirut 三参数模型只在本预注册高距离切片获得有限支持", "limited_support", ["validation/chwirut-holdout.json"]),
        node("claim-nist-reproduction", "claim", "全数据拟合复现 NIST 认证值只属于已知答案复核", "supported", ["validation/chwirut-holdout.json", "validation/chwirut-holdout-verification.json"]),
        node("claim-universal-identifiability", "claim", "任意少量点都能唯一识别全部模型参数", "falsified", ["validation/z3-identifiability.json"]),
        node("claim-positive-denominator", "claim", "显式正性定义域内 Chwirut 分母为正", "supported", ["validation/z3-identifiability.json"]),
        node("claim-aspirin-identity", "claim", "阿司匹林在 PubChem、ChEMBL 与 RDKit 间具有同一结构身份", "supported", ["validation/aspirin-crosscheck.json"]),
        node("claim-descriptor-fraud", "claim", "描述符或计数差异本身就是数据造假证据", "falsified", ["validation/aspirin-crosscheck.json"]),
        node("claim-material-identity", "claim", "Si、GaAs、SiO2 的三组跨库结构身份分别成立", "supported", ["validation/material-crosscheck.json"]),
        node("claim-universal-bandgap", "claim", "同一结构在不同 DFT 数据库中必须给出相同带隙", "falsified", ["validation/material-crosscheck.json"]),
        node("claim-knowledge-graph", "claim", "知识连接必须同时保留支持、反例、实验与限制", "supported", ["contracts/frontier-knowledge-graph.schema.json"]),
        node("evidence-chwirut", "evidence", "54 个 NIST 观测的逐点预测与独立指标复算", "supported", ["validation/chwirut-holdout.json", "validation/chwirut-holdout-verification.json"]),
        node("evidence-z3", "evidence", "Z3 定义域不可满足性与可识别性反例", "supported", ["validation/z3-identifiability.json"]),
        node("evidence-aspirin", "evidence", "阿司匹林身份与描述符口径快照", "supported", ["validation/pubchem-aspirin.json", "validation/chembl-aspirin.json", "validation/aspirin-crosscheck.json"]),
        node("evidence-material", "evidence", "三组材料的跨库 DFT 与本地结构重算", "supported", ["validation/material-crosscheck.json"]),
        node("counterexample-xzero", "counterexample", "x=0 时两个不同参数三元组产生相同响应", "supported", ["validation/z3-identifiability.json"]),
        node("counterexample-descriptor", "counterexample", "LogP、氢键和可旋转键的定义差异无需被解释为造假", "supported", ["validation/aspirin-crosscheck.json"]),
        node("counterexample-bandgap", "counterexample", "同结构的 MP 与 OQMD 带隙仍可不同", "supported", ["validation/material-crosscheck.json"]),
        node("experiment-chwirut-protocol", "experiment", "47 个训练观测与 7 个高距离留出观测", "supported", ["validation/chwirut-holdout-protocol.json"]),
        node("experiment-material-protocol", "experiment", "三组 MP／OQMD／PyMatGen 结构复核协议", "supported", ["validation/material-crosscheck-protocol.json", "validation/material-crosscheck-protocol-amendment-01.json"]),
        node("limitation-single-split", "limitation", "单次单数据集留出不能证明普适规律或参数完全内生", "active", ["validation/chwirut-holdout.json"]),
        node("limitation-public-records", "limitation", "公开记录与本地重算不等于独立湿实验或临床结论", "active", ["validation/aspirin-crosscheck.json"]),
        node("limitation-small-material-sample", "limitation", "三种材料不是全球 DFT 基准，也不证明某个实现普遍更准确", "active", ["validation/material-crosscheck.json"]),
        node("claim-eckerle4-two-tail", "claim", "Eckerle4 高斯模型只在预注册双尾切片获得有限支持", "limited_support", ["validation/eckerle4-two-tail.json"]),
        node("evidence-eckerle4", "evidence", "35 个 Eckerle4 观测的逐点预测与独立指标复算", "supported", ["validation/eckerle4-two-tail.json", "validation/eckerle4-two-tail-verification.json"]),
        node("experiment-eckerle4-protocol", "experiment", "27 个中央训练观测、低尾 3 点和高尾 5 点", "supported", ["validation/eckerle4-two-tail-protocol.json"]),
        node("claim-solver-agreement", "claim", "cvc5 与 Z3 对三项定义域和可识别性检查给出一致结果", "supported", ["validation/cvc5-crosscheck.json"]),
        node("evidence-cvc5", "evidence", "cvc5 1.4.2 的 SMT-LIB 日志与精确有理数反例模型", "supported", ["validation/cvc5-crosscheck.json"]),
        node("limitation-two-datasets", "limitation", "两个 NIST 数据集的有限支持仍不是跨领域普适规律", "active", ["validation/chwirut-holdout.json", "validation/eckerle4-two-tail.json"]),
        node("claim-hahn1-high-temperature", "claim", "Hahn1 七参数有理模型只在预注册高温切片获得有限支持", "limited_support", ["validation/hahn1-high-temperature.json"]),
        node("evidence-hahn1", "evidence", "236 个 Hahn1 观测的逐点预测与独立指标复算", "supported", ["validation/hahn1-high-temperature.json", "validation/hahn1-high-temperature-verification.json"]),
        node("experiment-hahn1-protocol", "experiment", "219 个训练观测与 17 个高温留出观测", "supported", ["validation/hahn1-high-temperature-protocol.json"]),
        node("limitation-three-datasets", "limitation", "三个 NIST 数据集的有限支持仍不是跨模型类别普适规律", "active", ["validation/chwirut-holdout.json", "validation/eckerle4-two-tail.json", "validation/hahn1-high-temperature.json"]),
        node("claim-hahn1-denominator", "claim", "认证 Hahn1 分母在 0<=x<=900 内无零根", "supported", ["validation/z3-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.json"]),
        node("evidence-hahn1-denominator", "evidence", "Z3 与 cvc5 对 Hahn1 分母实验区间给出 unsat", "supported", ["validation/z3-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.smt2"]),
        node("claim-unbounded-denominator-safety", "claim", "Hahn1 分母在所有非负温度都没有零根", "falsified", ["validation/z3-hahn1-denominator.json"]),
        node("counterexample-hahn1-outdomain-root", "counterexample", "Hahn1 分母在约 1931 K 的域外正根", "supported", ["validation/z3-hahn1-denominator.json"]),
        node("claim-universal-robustness", "claim", "三个模型在五组连续区间留出中均稳健且不劣于基线", "falsified", ["validation/grouped-stress.json"]),
        node("evidence-grouped-stress", "evidence", "三个数据集的 15 折连续区间留出结果与失败审计", "supported", ["validation/grouped-stress.json"]),
        node("experiment-grouped-stress-protocol", "experiment", "相同 x 不跨训练与测试的五组连续区间留出协议", "supported", ["validation/grouped-stress-protocol.json"]),
        node("limitation-grouped-stress", "limitation", "分母非零、参数可识别和跨区间预测稳健是不同问题", "active", ["validation/grouped-stress.json"]),
        node("claim-fold1-heldout-pole-free", "claim", "Hahn1 第 1 折冻结模型在低温留出闭区间内无实极点", "falsified", ["validation/hahn1-frozen-denominator-roots.json"]),
        node("evidence-hahn1-fold1-identifiability", "evidence", "五折局部雅可比、参数相关和留出预测敏感度诊断", "supported", ["validation/hahn1-fold1-identifiability.json"]),
        node("evidence-hahn1-frozen-denominator-roots", "evidence", "第 1 折约 45.526978 K 与 72.131671 K 的两个数值单极点", "supported", ["validation/hahn1-frozen-denominator-roots.json"]),
        node("limitation-post-hoc-mechanism", "limitation", "事后机制诊断与数值根定位不是预注册检验或精确代数证书", "active", ["validation/hahn1-fold1-identifiability.json", "validation/hahn1-frozen-denominator-roots.json"]),
        node("claim-thurber-all-folds-gated", "claim", "Thurber 五个连续区间折全部通过预测区、可识别性与基线验收", "falsified", ["validation/thurber-prospective-gate.json"]),
        node("evidence-thurber-prospective-gate", "evidence", "Thurber 四折通过、一折预测区实根与预测失败的全部记录", "supported", ["validation/thurber-prospective-gate.json"]),
        node("experiment-thurber-prospective-protocol", "experiment", "在任何 Thurber 拟合前冻结的五折验收协议", "supported", ["validation/thurber-prospective-gate-protocol.json"]),
        node("limitation-thurber-prospective", "limitation", "单个新数据集的数值前瞻检验不是独立物理实验或普适检出率证明", "active", ["validation/thurber-prospective-gate.json"]),
        node("claim-kirby2-all-folds-gated", "claim", "Kirby2 五个连续区间折全部通过预测区、可识别性与二次基线验收", "supported", ["validation/kirby2-prospective-gate.json"]),
        node("evidence-kirby2-prospective-gate", "evidence", "Kirby2 五折有限支持及第 1 折外推衰减、高条件数记录", "supported", ["validation/kirby2-prospective-gate.json"]),
        node("experiment-kirby2-prospective-protocol", "experiment", "在任何 Kirby2 拟合前冻结的五折跨次数验收协议", "supported", ["validation/kirby2-prospective-gate-protocol.json"]),
        node("limitation-kirby2-prospective", "limitation", "Kirby2 的整体有限支持不是全域无根、绝对精度或其他模型的保证", "active", ["validation/kirby2-prospective-gate.json"]),
        node("claim-rational-gate-always-passes", "claim", "统一有理验收在所有数据集和所有折上都通过", "falsified", ["exports/rational-cross-dataset.json"]),
        node("evidence-rational-cross-dataset", "evidence", "统一内核下 13／15 折符合验收及两种证据等级", "supported", ["exports/rational-cross-dataset.json"]),
        node("experiment-rational-cross-dataset-protocol", "experiment", "跨数据集冻结输入哈希与标准化综合协议", "supported", ["validation/rational-cross-dataset-protocol.json"]),
        node("limitation-rational-cross-dataset", "limitation", "三个数据集十五折且含事后重建，不能估计普适检出率", "active", ["exports/rational-cross-dataset.json"]),
        node("claim-exact-snapshot-all-folds-root-free", "claim", "全部十五折有理系数快照在各自留出闭区间内均无实根", "falsified", ["validation/rational-exact-interval-roots.json"]),
        node("evidence-exact-sturm-intervals", "evidence", "精确 Sturm 隔离的 13 折无根、Hahn1 两根与 Thurber 一根", "supported", ["validation/rational-exact-interval-roots.json"]),
        node("experiment-exact-interval-protocol", "experiment", "十五折精确有理计数与双求解器复核协议", "supported", ["validation/rational-exact-interval-protocol.json"]),
        node("limitation-exact-snapshot-scope", "limitation", "精确结论只覆盖有理系数快照和指定闭区间，不是物理常数或全域证明", "active", ["validation/rational-exact-interval-roots.json"]),
        node("claim-no-positive-rootfree-box", "claim", "无根快照不存在正的连续无根参数盒", "falsified", ["validation/rational-parameter-box-stability.json"]),
        node("evidence-parameter-box-stability", "evidence", "13 折正区域半径、11 折封顶与 2 折有限半径括号", "supported", ["validation/rational-parameter-box-stability.json"]),
        node("experiment-parameter-box-protocol", "experiment", "连续参数盒精确充分性证明与跨零分段协议", "supported", ["validation/rational-parameter-box-protocol.json", "validation/rational-parameter-box-protocol-amendment-01.json"]),
        node("limitation-parameter-box-scope", "limitation", "参数盒半径是充分下界，不是置信区、必要最大值或预测精度保证", "active", ["validation/rational-parameter-box-stability.json"]),
        node("claim-rootfree-box-useful-prediction-bound", "claim", "无根参数盒自动提供有实际用途的预测误差界", "falsified", ["validation/rational-prediction-box-bounds.json"]),
        node("evidence-prediction-box-bounds", "evidence", "13 折 369 点精确保守上界与两处巨大分母下界驱动界", "supported", ["validation/rational-prediction-box-bounds.json"]),
        node("experiment-prediction-box-protocol", "experiment", "固定分子、认证半径和逐点精确预测界协议", "supported", ["validation/rational-prediction-box-protocol.json"]),
        node("limitation-prediction-box-bounds", "limitation", "巨大有限上界数学有效但可能无实际信息，且不覆盖分子、连续 x 或统计误差", "active", ["validation/rational-prediction-box-bounds.json"]),
        node("claim-ellipsoid-all-369-tighter", "claim", "同一半径下当前 369 个适用点的椭球上界全部小于独立盒", "supported", ["validation/rational-ellipsoid-box-comparison.json"]),
        node("evidence-ellipsoid-box-comparison", "evidence", "369 点全部收紧、中位比值 0.604836 与两个有根折不适用", "supported", ["validation/rational-ellipsoid-box-comparison.json"]),
        node("experiment-ellipsoid-box-protocol", "experiment", "完整协方差、同半径和精确支撑上界比较协议", "supported", ["validation/rational-ellipsoid-box-protocol.json"]),
        node("limitation-ellipsoid-box-scope", "limitation", "样本内全部收紧不等于永远更紧；盒与椭球是不同区域且不是置信区", "active", ["validation/rational-ellipsoid-box-comparison.json"]),
        node("claim-ellipsoid-continuous-gap", "claim", "指定椭球的连续留出区间存在未认证的支撑安全缺口", "falsified", ["validation/rational-ellipsoid-interval-safety.json"]),
        node("evidence-ellipsoid-continuous-interval", "evidence", "13 折连续平方支撑均为正、0 折未认证、2 折有根", "supported", ["validation/rational-ellipsoid-interval-safety.json"]),
        node("experiment-ellipsoid-interval-protocol", "experiment", "连续闭区间平方支撑精确证明协议", "supported", ["validation/rational-ellipsoid-interval-protocol.json"]),
        node("limitation-ellipsoid-continuous-scope", "limitation", "连续证明只覆盖指定椭球、半径和区间，不覆盖分子或其他区域", "active", ["validation/rational-ellipsoid-interval-safety.json"]),
        node("claim-filip-ellipsoid-covered", "claim", "Filip 候选模型的 82 个适用点均由椭球上界覆盖实际残差", "supported", ["validation/filip-ellipsoid-coverage.json"]),
        node("evidence-filip-ellipsoid-coverage", "evidence", "Filip 五折连续安全、82 点无越界与独立盒连续安全为 0", "supported", ["validation/filip-ellipsoid-coverage.json"]),
        node("experiment-filip-coverage-protocol", "experiment", "未参与区域设计的 Filip 固定半径五折压力测试协议", "supported", ["validation/filip-ellipsoid-coverage-protocol.json"]),
        node("limitation-filip-candidate-scope", "limitation", "Filip 候选不是原生 11 参数模型，覆盖检查不是概率校准或物理内生证明", "active", ["validation/filip-ellipsoid-coverage.json"]),
        node("claim-external-coverage-framework", "claim", "通用驱动可复现 Filip 并支持 MGH17 的逐点覆盖与连续安全", "supported", ["exports/external-coverage-comparison.json"]),
        node("evidence-external-coverage-framework", "evidence", "两个数据集 115 点无越界、10 折连续安全及 MGH17 32 点更紧", "supported", ["exports/external-coverage-comparison.json"]),
        node("experiment-external-coverage-framework", "experiment", "通用驱动回归与 MGH17 独立冻结协议", "supported", ["validation/mgh17-ellipsoid-coverage-protocol.json", "validation/external-coverage-framework-protocol.json"]),
        node("limitation-external-coverage-framework", "limitation", "通用驱动减少实现漂移但不增加科学独立性，115 点不是概率覆盖或普适成功率", "active", ["exports/external-coverage-comparison.json"]),
        node("claim-reusable-driver-guarantees-coverage", "claim", "复用同一外部覆盖驱动即可保证所有外部点可给界且所有折连续安全", "falsified", ["exports/external-coverage-gauss1-comparison.json"]),
        node("evidence-gauss1-external-coverage", "evidence", "Gauss1 共 250 点，190 点可给界、60 点不可用，连续椭球安全为 3／5 折", "supported", ["validation/gauss1-ellipsoid-coverage.json", "exports/external-coverage-gauss1-comparison.json"]),
        node("counterexample-gauss1-fold2-fold5", "counterexample", "Gauss1 第 2 折候选预测显著差于基线，第 5 折没有任何可用椭球界", "supported", ["validation/gauss1-ellipsoid-coverage.json"]),
        node("experiment-gauss1-coverage-protocol", "experiment", "先于任何 Gauss1 候选分析冻结并推送的五折固定半径协议", "supported", ["validation/gauss1-ellipsoid-coverage-protocol.json", "validation/external-coverage-gauss1-comparison-protocol.json"]),
        node("limitation-gauss1-generated-candidate-scope", "limitation", "Gauss1 是生成数据，候选不是原生八参数模型；适用点检查不是概率覆盖或独立物理实验", "active", ["validation/gauss1-ellipsoid-coverage.json", "exports/external-coverage-gauss1-comparison.json"]),
        node("claim-wide-bounds-parameter-uncertainty", "claim", "所有宽残差界都主要由参数扰动造成", "falsified", ["validation/gauss1-bound-mechanism.json"]),
        node("evidence-gauss1-bound-decomposition", "evidence", "190 点数值一致及最大残差界位置的实际残差—预测平移同点分解", "supported", ["validation/gauss1-bound-mechanism.json"]),
        node("counterexample-gauss1-fold1-wide-bound", "counterexample", "第 1 折 x=1 的残差上界为 330.728324，其中预测平移仅占 0.688%", "supported", ["validation/gauss1-bound-mechanism.json"]),
        node("experiment-gauss1-bound-mechanism", "experiment", "不重拟合、不调参的全 250 点只读事后分母与界组成诊断", "supported", ["validation/gauss1-bound-mechanism.json", "docs/superpowers/plans/2026-11-09-gauss1-bound-mechanism.md"]),
        node("limitation-gauss1-bound-mechanism-posthoc", "limitation", "同点事后分解不是前瞻检验、概率贡献或物理机制识别，连续未认证不等于不安全", "active", ["validation/gauss1-bound-mechanism.json"]),
        node("claim-uniform-external-bound-mechanism", "claim", "所有外部残差上界都由同一种项主导", "falsified", ["exports/external-bound-decomposition.json"]),
        node("evidence-external-bound-decomposition", "evidence", "305 点算术一致性及 Filip、MGH17、Gauss1 的全点主导项分布对照", "supported", ["exports/external-bound-decomposition.json"]),
        node("counterexample-filip-gauss1-composition", "counterexample", "Filip 82／82 点由平移主导，而 Gauss1 有 166／190 点由实际残差主导", "supported", ["exports/external-bound-decomposition.json"]),
        node("experiment-external-bound-decomposition-protocol", "experiment", "冻结输入、0.5 阈值、零界规则与四点 Gauss1 回归的只读分解协议", "supported", ["validation/external-bound-decomposition-protocol.json", "docs/superpowers/plans/2026-11-09-external-bound-decomposition.md"]),
        node("limitation-external-bound-decomposition-posthoc", "limitation", "事后算术占比不是概率、方差或物理因果贡献，三数据不形成普适排名", "active", ["exports/external-bound-decomposition.json"]),
        node("claim-combined-internal-external-success-rate", "claim", "内部与外部证据可直接合并为统一成功率", "falsified", ["exports/internal-external-bound-comparison.json"]),
        node("evidence-internal-external-bound-comparison", "evidence", "六组 674 点中 482 点平移主导、192 点实际残差主导及两类不适用边界", "supported", ["exports/internal-external-bound-comparison.json"]),
        node("counterexample-six-dataset-bound-composition", "counterexample", "六组最大界均由平移主导，但 Gauss1 与其他五组的全点分布显著不同", "supported", ["exports/internal-external-bound-comparison.json"]),
        node("experiment-internal-external-bound-protocol", "experiment", "冻结双输入、范围分离和六组分布的只读内外部对照协议", "supported", ["validation/internal-external-bound-comparison-protocol.json", "validation/internal-bound-decomposition-protocol.json"]),
        node("limitation-internal-external-scope", "limitation", "内部两个有根折与外部 60 个不可用点不可混同，674 点不是总体成功率", "active", ["exports/internal-external-bound-comparison.json"]),
        node("claim-small-rmse-useful-proof", "claim", "较小 RMSE 自动意味着连续证明和有用逐点界", "falsified", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("evidence-misra1a-prediction-proof-dissociation", "evidence", "Misra1a 小 RMSE 与仅 4／14 点可给界、1／5 折连续安全和宽上界并存", "supported", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("counterexample-misra1a-four-of-fourteen", "counterexample", "Misra1a 候选 RMSE 约 0.04—0.22，但仅 4 点可给界且平移占比均超过 99.9%", "supported", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("experiment-misra1a-prospective-protocol", "experiment", "在任何 Misra1a 候选分析前冻结并推送的小样本五折协议", "supported", ["validation/misra1a-ellipsoid-coverage-protocol.json"]),
        node("limitation-misra1a-small-sample-scope", "limitation", "小样本候选不是原生两参数模型，4 点零越界不是概率覆盖或高信息量证明", "active", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("claim-new-data-overwrite-history", "claim", "新增数据可以覆盖旧对照并合并历史范围", "falsified", ["exports/internal-external-bound-comparison-v2.json"]),
        node("evidence-bound-comparison-v2", "evidence", "四外部 379／309／70 与七组 678 点的新版本对照及 Misra1a 增量", "supported", ["exports/external-bound-decomposition-v2.json", "exports/internal-external-bound-comparison-v2.json"]),
        node("counterexample-misra1a-v2-increment", "counterexample", "Misra1a 增加 14 总点、4 可用点、10 不可用点和 4 平移主导点，实际残差主导数不变", "supported", ["validation/misra1a-ellipsoid-coverage.json", "exports/internal-external-bound-comparison-v2.json"]),
        node("experiment-bound-comparison-v2-protocol", "experiment", "保留历史文件并冻结四外部与七组输入哈希和范围差异的新版协议", "supported", ["validation/external-bound-decomposition-v2-protocol.json", "validation/internal-external-bound-comparison-v2-protocol.json"]),
        node("limitation-bound-comparison-v2-scope", "limitation", "新版范围合计不是成功率或证明能力改善，内部有根折与外部不可用点不可混同", "active", ["exports/internal-external-bound-comparison-v2.json"]),
    ]
    edges = []
    for track, claims in {
        "track-holdout": ["claim-chwirut-extrapolation", "claim-nist-reproduction", "evidence-chwirut", "experiment-chwirut-protocol", "limitation-single-split", "claim-eckerle4-two-tail", "evidence-eckerle4", "experiment-eckerle4-protocol", "limitation-two-datasets", "claim-hahn1-high-temperature", "evidence-hahn1", "experiment-hahn1-protocol", "limitation-three-datasets", "claim-universal-robustness", "evidence-grouped-stress", "experiment-grouped-stress-protocol", "limitation-grouped-stress", "claim-fold1-heldout-pole-free", "evidence-hahn1-fold1-identifiability", "evidence-hahn1-frozen-denominator-roots", "limitation-post-hoc-mechanism", "claim-thurber-all-folds-gated", "evidence-thurber-prospective-gate", "experiment-thurber-prospective-protocol", "limitation-thurber-prospective", "claim-kirby2-all-folds-gated", "evidence-kirby2-prospective-gate", "experiment-kirby2-prospective-protocol", "limitation-kirby2-prospective", "claim-rational-gate-always-passes", "evidence-rational-cross-dataset", "experiment-rational-cross-dataset-protocol", "limitation-rational-cross-dataset", "claim-filip-ellipsoid-covered", "evidence-filip-ellipsoid-coverage", "experiment-filip-coverage-protocol", "limitation-filip-candidate-scope", "claim-external-coverage-framework", "evidence-external-coverage-framework", "experiment-external-coverage-framework", "limitation-external-coverage-framework", "claim-reusable-driver-guarantees-coverage", "evidence-gauss1-external-coverage", "counterexample-gauss1-fold2-fold5", "experiment-gauss1-coverage-protocol", "limitation-gauss1-generated-candidate-scope", "claim-wide-bounds-parameter-uncertainty", "evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold1-wide-bound", "experiment-gauss1-bound-mechanism", "limitation-gauss1-bound-mechanism-posthoc", "claim-uniform-external-bound-mechanism", "evidence-external-bound-decomposition", "counterexample-filip-gauss1-composition", "experiment-external-bound-decomposition-protocol", "limitation-external-bound-decomposition-posthoc", "claim-combined-internal-external-success-rate", "evidence-internal-external-bound-comparison", "counterexample-six-dataset-bound-composition", "experiment-internal-external-bound-protocol", "limitation-internal-external-scope", "claim-small-rmse-useful-proof", "evidence-misra1a-prediction-proof-dissociation", "counterexample-misra1a-four-of-fourteen", "experiment-misra1a-prospective-protocol", "limitation-misra1a-small-sample-scope", "claim-new-data-overwrite-history", "evidence-bound-comparison-v2", "counterexample-misra1a-v2-increment", "experiment-bound-comparison-v2-protocol", "limitation-bound-comparison-v2-scope"],
        "track-formal": ["claim-universal-identifiability", "claim-positive-denominator", "evidence-z3", "counterexample-xzero", "claim-solver-agreement", "evidence-cvc5", "claim-hahn1-denominator", "evidence-hahn1-denominator", "claim-unbounded-denominator-safety", "counterexample-hahn1-outdomain-root", "claim-exact-snapshot-all-folds-root-free", "evidence-exact-sturm-intervals", "experiment-exact-interval-protocol", "limitation-exact-snapshot-scope", "claim-no-positive-rootfree-box", "evidence-parameter-box-stability", "experiment-parameter-box-protocol", "limitation-parameter-box-scope", "claim-rootfree-box-useful-prediction-bound", "evidence-prediction-box-bounds", "experiment-prediction-box-protocol", "limitation-prediction-box-bounds", "claim-ellipsoid-all-369-tighter", "evidence-ellipsoid-box-comparison", "experiment-ellipsoid-box-protocol", "limitation-ellipsoid-box-scope", "claim-ellipsoid-continuous-gap", "evidence-ellipsoid-continuous-interval", "experiment-ellipsoid-interval-protocol", "limitation-ellipsoid-continuous-scope"],
        "track-chemistry": ["claim-aspirin-identity", "claim-descriptor-fraud", "evidence-aspirin", "counterexample-descriptor", "limitation-public-records"],
        "track-materials": ["claim-material-identity", "claim-universal-bandgap", "evidence-material", "counterexample-bandgap", "experiment-material-protocol", "limitation-small-material-sample"],
        "track-knowledge": ["claim-knowledge-graph"],
    }.items():
        edges.extend(edge(track, target, "contains") for target in claims)
    edges += [
        edge("evidence-chwirut", "claim-chwirut-extrapolation", "supports"),
        edge("evidence-chwirut", "claim-nist-reproduction", "supports"),
        edge("experiment-chwirut-protocol", "claim-chwirut-extrapolation", "tests"),
        edge("limitation-single-split", "claim-chwirut-extrapolation", "limits"),
        edge("evidence-z3", "claim-positive-denominator", "supports"),
        edge("counterexample-xzero", "claim-universal-identifiability", "contradicts"),
        edge("evidence-aspirin", "claim-aspirin-identity", "supports"),
        edge("counterexample-descriptor", "claim-descriptor-fraud", "contradicts"),
        edge("limitation-public-records", "claim-aspirin-identity", "limits"),
        edge("evidence-material", "claim-material-identity", "supports"),
        edge("counterexample-bandgap", "claim-universal-bandgap", "contradicts"),
        edge("experiment-material-protocol", "claim-material-identity", "tests"),
        edge("limitation-small-material-sample", "claim-material-identity", "limits"),
        edge("evidence-eckerle4", "claim-eckerle4-two-tail", "supports"),
        edge("experiment-eckerle4-protocol", "claim-eckerle4-two-tail", "tests"),
        edge("limitation-two-datasets", "claim-eckerle4-two-tail", "limits"),
        edge("evidence-cvc5", "claim-solver-agreement", "supports"),
        edge("evidence-cvc5", "counterexample-xzero", "supports"),
        edge("evidence-hahn1", "claim-hahn1-high-temperature", "supports"),
        edge("experiment-hahn1-protocol", "claim-hahn1-high-temperature", "tests"),
        edge("limitation-three-datasets", "claim-hahn1-high-temperature", "limits"),
        edge("evidence-hahn1-denominator", "claim-hahn1-denominator", "supports"),
        edge("evidence-hahn1-denominator", "counterexample-hahn1-outdomain-root", "supports"),
        edge("counterexample-hahn1-outdomain-root", "claim-unbounded-denominator-safety", "contradicts"),
        edge("experiment-grouped-stress-protocol", "claim-universal-robustness", "tests"),
        edge("evidence-grouped-stress", "claim-universal-robustness", "contradicts"),
        edge("limitation-grouped-stress", "claim-universal-robustness", "limits"),
        edge("evidence-hahn1-frozen-denominator-roots", "claim-fold1-heldout-pole-free", "contradicts"),
        edge("evidence-hahn1-fold1-identifiability", "claim-universal-robustness", "contradicts"),
        edge("limitation-post-hoc-mechanism", "evidence-hahn1-fold1-identifiability", "limits"),
        edge("limitation-post-hoc-mechanism", "evidence-hahn1-frozen-denominator-roots", "limits"),
        edge("experiment-thurber-prospective-protocol", "claim-thurber-all-folds-gated", "tests"),
        edge("evidence-thurber-prospective-gate", "claim-thurber-all-folds-gated", "contradicts"),
        edge("limitation-thurber-prospective", "claim-thurber-all-folds-gated", "limits"),
        edge("experiment-kirby2-prospective-protocol", "claim-kirby2-all-folds-gated", "tests"),
        edge("evidence-kirby2-prospective-gate", "claim-kirby2-all-folds-gated", "supports"),
        edge("limitation-kirby2-prospective", "claim-kirby2-all-folds-gated", "limits"),
        edge("experiment-rational-cross-dataset-protocol", "claim-rational-gate-always-passes", "tests"),
        edge("evidence-rational-cross-dataset", "claim-rational-gate-always-passes", "contradicts"),
        edge("limitation-rational-cross-dataset", "claim-rational-gate-always-passes", "limits"),
        edge("experiment-exact-interval-protocol", "claim-exact-snapshot-all-folds-root-free", "tests"),
        edge("evidence-exact-sturm-intervals", "claim-exact-snapshot-all-folds-root-free", "contradicts"),
        edge("limitation-exact-snapshot-scope", "claim-exact-snapshot-all-folds-root-free", "limits"),
        edge("experiment-parameter-box-protocol", "claim-no-positive-rootfree-box", "tests"),
        edge("evidence-parameter-box-stability", "claim-no-positive-rootfree-box", "contradicts"),
        edge("limitation-parameter-box-scope", "claim-no-positive-rootfree-box", "limits"),
        edge("experiment-prediction-box-protocol", "claim-rootfree-box-useful-prediction-bound", "tests"),
        edge("evidence-prediction-box-bounds", "claim-rootfree-box-useful-prediction-bound", "contradicts"),
        edge("limitation-prediction-box-bounds", "claim-rootfree-box-useful-prediction-bound", "limits"),
        edge("experiment-ellipsoid-box-protocol", "claim-ellipsoid-all-369-tighter", "tests"),
        edge("evidence-ellipsoid-box-comparison", "claim-ellipsoid-all-369-tighter", "supports"),
        edge("limitation-ellipsoid-box-scope", "claim-ellipsoid-all-369-tighter", "limits"),
        edge("experiment-ellipsoid-interval-protocol", "claim-ellipsoid-continuous-gap", "tests"),
        edge("evidence-ellipsoid-continuous-interval", "claim-ellipsoid-continuous-gap", "contradicts"),
        edge("limitation-ellipsoid-continuous-scope", "claim-ellipsoid-continuous-gap", "limits"),
        edge("experiment-filip-coverage-protocol", "claim-filip-ellipsoid-covered", "tests"),
        edge("evidence-filip-ellipsoid-coverage", "claim-filip-ellipsoid-covered", "supports"),
        edge("limitation-filip-candidate-scope", "claim-filip-ellipsoid-covered", "limits"),
        edge("experiment-external-coverage-framework", "claim-external-coverage-framework", "tests"),
        edge("evidence-external-coverage-framework", "claim-external-coverage-framework", "supports"),
        edge("limitation-external-coverage-framework", "claim-external-coverage-framework", "limits"),
        edge("experiment-gauss1-coverage-protocol", "claim-reusable-driver-guarantees-coverage", "tests"),
        edge("evidence-gauss1-external-coverage", "claim-reusable-driver-guarantees-coverage", "contradicts"),
        edge("counterexample-gauss1-fold2-fold5", "claim-reusable-driver-guarantees-coverage", "contradicts"),
        edge("evidence-gauss1-external-coverage", "counterexample-gauss1-fold2-fold5", "supports"),
        edge("limitation-gauss1-generated-candidate-scope", "claim-reusable-driver-guarantees-coverage", "limits"),
        edge("experiment-gauss1-bound-mechanism", "claim-wide-bounds-parameter-uncertainty", "tests"),
        edge("evidence-gauss1-bound-decomposition", "claim-wide-bounds-parameter-uncertainty", "contradicts"),
        edge("counterexample-gauss1-fold1-wide-bound", "claim-wide-bounds-parameter-uncertainty", "contradicts"),
        edge("evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold1-wide-bound", "supports"),
        edge("evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold2-fold5", "supports"),
        edge("limitation-gauss1-bound-mechanism-posthoc", "claim-wide-bounds-parameter-uncertainty", "limits"),
        edge("experiment-external-bound-decomposition-protocol", "claim-uniform-external-bound-mechanism", "tests"),
        edge("evidence-external-bound-decomposition", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("counterexample-filip-gauss1-composition", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("evidence-external-bound-decomposition", "counterexample-filip-gauss1-composition", "supports"),
        edge("evidence-external-bound-decomposition", "claim-wide-bounds-parameter-uncertainty", "contradicts"),
        edge("limitation-external-bound-decomposition-posthoc", "claim-uniform-external-bound-mechanism", "limits"),
        edge("experiment-internal-external-bound-protocol", "claim-combined-internal-external-success-rate", "tests"),
        edge("evidence-internal-external-bound-comparison", "claim-combined-internal-external-success-rate", "contradicts"),
        edge("counterexample-six-dataset-bound-composition", "claim-combined-internal-external-success-rate", "contradicts"),
        edge("evidence-internal-external-bound-comparison", "counterexample-six-dataset-bound-composition", "supports"),
        edge("counterexample-six-dataset-bound-composition", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("evidence-internal-external-bound-comparison", "counterexample-filip-gauss1-composition", "supports"),
        edge("limitation-internal-external-scope", "claim-combined-internal-external-success-rate", "limits"),
        edge("experiment-misra1a-prospective-protocol", "claim-small-rmse-useful-proof", "tests"),
        edge("evidence-misra1a-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"),
        edge("counterexample-misra1a-four-of-fourteen", "claim-small-rmse-useful-proof", "contradicts"),
        edge("evidence-misra1a-prediction-proof-dissociation", "counterexample-misra1a-four-of-fourteen", "supports"),
        edge("evidence-misra1a-prediction-proof-dissociation", "claim-wide-bounds-parameter-uncertainty", "supports"),
        edge("limitation-misra1a-small-sample-scope", "claim-small-rmse-useful-proof", "limits"),
        edge("experiment-bound-comparison-v2-protocol", "claim-new-data-overwrite-history", "tests"),
        edge("evidence-bound-comparison-v2", "claim-new-data-overwrite-history", "contradicts"),
        edge("counterexample-misra1a-v2-increment", "claim-new-data-overwrite-history", "contradicts"),
        edge("evidence-bound-comparison-v2", "counterexample-misra1a-v2-increment", "supports"),
        edge("evidence-bound-comparison-v2", "evidence-misra1a-prediction-proof-dissociation", "supports"),
        edge("limitation-bound-comparison-v2-scope", "claim-new-data-overwrite-history", "limits"),
        edge("claim-knowledge-graph", "track-holdout", "recommends"),
        edge("claim-knowledge-graph", "track-formal", "recommends"),
        edge("claim-knowledge-graph", "track-chemistry", "recommends"),
        edge("claim-knowledge-graph", "track-materials", "recommends"),
    ]
    nodes.append(node("experiment-bound-comparison-v2-protocol-amendment", "experiment", "修订七组协议的外部诊断哈希并保留原协议与全部数值范围", "supported", ["validation/internal-external-bound-comparison-v2-protocol-amendment-01.json"]))
    edges.extend([
        edge("track-holdout", "experiment-bound-comparison-v2-protocol-amendment", "contains"),
        edge("experiment-bound-comparison-v2-protocol-amendment", "claim-new-data-overwrite-history", "tests"),
    ])
    nodes.extend([
        node("claim-untouched-data-independent-model-family", "claim", "未触碰数据自动构成独立模型族或独立实验室复现", "falsified", ["validation/chwirut1-ellipsoid-coverage-protocol.json", "validation/chwirut1-ellipsoid-coverage.json"]),
        node("evidence-chwirut1-prediction-proof-dissociation", "evidence", "Chwirut1 共 214 点，83 点可给界、131 点不可用，2／5 折连续安全且三折优于基线", "supported", ["validation/chwirut1-ellipsoid-coverage.json"]),
        node("counterexample-chwirut1-fold4-no-bounds", "counterexample", "Chwirut1 第 4 折 RMSE 最低且优于基线，但 23 个留出点有 0 个可用界", "supported", ["validation/chwirut1-ellipsoid-coverage.json"]),
        node("experiment-chwirut1-prospective-protocol", "experiment", "在任何 Chwirut1 候选分析前冻结并推送的同族数据五折协议", "supported", ["validation/chwirut1-ellipsoid-coverage-protocol.json"]),
        node("limitation-chwirut1-related-dataset-scope", "limitation", "Chwirut1 未触碰但与 Chwirut2 同研究同模型族，适用点零越界不是概率覆盖或独立模型族验证", "active", ["validation/chwirut1-ellipsoid-coverage-protocol.json", "validation/chwirut1-ellipsoid-coverage.json"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-untouched-data-independent-model-family", "contains"),
        edge("track-holdout", "evidence-chwirut1-prediction-proof-dissociation", "contains"),
        edge("track-holdout", "counterexample-chwirut1-fold4-no-bounds", "contains"),
        edge("track-holdout", "experiment-chwirut1-prospective-protocol", "contains"),
        edge("track-holdout", "limitation-chwirut1-related-dataset-scope", "contains"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"),
        edge("counterexample-chwirut1-fold4-no-bounds", "claim-small-rmse-useful-proof", "contradicts"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "counterexample-chwirut1-fold4-no-bounds", "supports"),
        edge("experiment-chwirut1-prospective-protocol", "claim-small-rmse-useful-proof", "tests"),
        edge("limitation-chwirut1-related-dataset-scope", "evidence-chwirut1-prediction-proof-dissociation", "limits"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "claim-untouched-data-independent-model-family", "contradicts"),
        edge("limitation-chwirut1-related-dataset-scope", "claim-untouched-data-independent-model-family", "limits"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "claim-reusable-driver-guarantees-coverage", "contradicts"),
    ])
    nodes.extend([
        node("evidence-bound-comparison-v3", "evidence", "五外部 593／392／201 与八组 761 点的新版本对照及 Chwirut1 增量", "supported", ["exports/external-bound-decomposition-v3.json", "exports/internal-external-bound-comparison-v3.json"]),
        node("counterexample-chwirut1-v3-increment", "counterexample", "Chwirut1 增加 214 总点、83 可用点、131 不可用点、75 平移主导点和 8 实际残差主导点，不能覆盖历史范围", "supported", ["validation/chwirut1-ellipsoid-coverage.json", "exports/internal-external-bound-comparison-v3.json"]),
        node("experiment-bound-comparison-v3-protocol", "experiment", "保留历史版本并冻结五外部与八组输入哈希、同族范围的新版协议", "supported", ["validation/external-bound-decomposition-v3-protocol.json", "validation/internal-external-bound-comparison-v3-protocol.json"]),
        node("limitation-bound-comparison-v3-scope", "limitation", "八组范围合计不是成功率或独立模型族验证，内部有根折、外部不可用点和同族边界均不可抹去", "active", ["exports/internal-external-bound-comparison-v3.json", "validation/chwirut1-ellipsoid-coverage-protocol.json"]),
    ])
    edges.extend([
        edge("track-holdout", "evidence-bound-comparison-v3", "contains"),
        edge("track-holdout", "counterexample-chwirut1-v3-increment", "contains"),
        edge("track-holdout", "experiment-bound-comparison-v3-protocol", "contains"),
        edge("track-holdout", "limitation-bound-comparison-v3-scope", "contains"),
        edge("evidence-bound-comparison-v3", "claim-new-data-overwrite-history", "contradicts"),
        edge("counterexample-chwirut1-v3-increment", "claim-new-data-overwrite-history", "contradicts"),
        edge("evidence-bound-comparison-v3", "counterexample-chwirut1-v3-increment", "supports"),
        edge("experiment-bound-comparison-v3-protocol", "claim-new-data-overwrite-history", "tests"),
        edge("limitation-bound-comparison-v3-scope", "claim-new-data-overwrite-history", "limits"),
        edge("evidence-bound-comparison-v3", "evidence-chwirut1-prediction-proof-dissociation", "supports"),
        edge("limitation-bound-comparison-v3-scope", "claim-untouched-data-independent-model-family", "limits"),
    ])
    nodes.append(node("experiment-external-scope-limitations-amendment", "experiment", "保留原冻结文件并修订 MGH17、Gauss1、Misra1a 的模型族限制文本及来源哈希", "supported", ["validation/external-scope-limitations-amendment-01.json", "validation/external-scope-limitations-amendment-01-audit.json"]))
    edges.extend([
        edge("track-knowledge", "experiment-external-scope-limitations-amendment", "contains"),
        edge("experiment-external-scope-limitations-amendment", "claim-knowledge-graph", "tests"),
    ])
    nodes.extend([
        node("evidence-enso-prediction-proof-dissociation", "evidence", "ENSO 共 168 点，135 点可给界、33 点不可用，4／5 折连续安全且 131 对比较收紧", "supported", ["validation/enso-ellipsoid-coverage.json"]),
        node("counterexample-enso-fold5-no-bounds", "counterexample", "ENSO 第 5 折 RMSE 明显优于基线，但 33 个留出点有 0 个可用界", "supported", ["validation/enso-ellipsoid-coverage.json"]),
        node("experiment-enso-scoped-prospective-protocol", "experiment", "在任何 ENSO 候选分析前冻结并推送的范围感知五折协议及三类实现哈希", "supported", ["validation/enso-ellipsoid-coverage-protocol.json", "scripts/external_coverage_scoped.py", "scripts/analyze_enso_ellipsoid_coverage.py"]),
        node("limitation-enso-periodic-candidate-scope", "limitation", "候选不是 ENSO 原生九参数周期模型，适用点检查与 131 对收紧均不是概率覆盖或物理机制验证", "active", ["validation/enso-ellipsoid-coverage-protocol.json", "validation/enso-ellipsoid-coverage.json"]),
    ])
    edges.extend([
        edge("track-holdout", "evidence-enso-prediction-proof-dissociation", "contains"),
        edge("track-holdout", "counterexample-enso-fold5-no-bounds", "contains"),
        edge("track-holdout", "experiment-enso-scoped-prospective-protocol", "contains"),
        edge("track-holdout", "limitation-enso-periodic-candidate-scope", "contains"),
        edge("evidence-enso-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"),
        edge("counterexample-enso-fold5-no-bounds", "claim-small-rmse-useful-proof", "contradicts"),
        edge("evidence-enso-prediction-proof-dissociation", "counterexample-enso-fold5-no-bounds", "supports"),
        edge("experiment-enso-scoped-prospective-protocol", "claim-small-rmse-useful-proof", "tests"),
        edge("limitation-enso-periodic-candidate-scope", "evidence-enso-prediction-proof-dissociation", "limits"),
        edge("evidence-enso-prediction-proof-dissociation", "claim-reusable-driver-guarantees-coverage", "contradicts"),
    ])
    nodes.extend([
        node("evidence-bound-comparison-v4", "evidence", "六外部 761／527／234 与九组 896 点的新版本对照及 ENSO 增量", "supported", ["exports/external-bound-decomposition-v4.json", "exports/internal-external-bound-comparison-v4.json"]),
        node("counterexample-enso-v4-increment", "counterexample", "ENSO 增加 168 总点、135 可用点、33 不可用点、33 平移主导点和 102 实际残差主导点，不能覆盖历史范围", "supported", ["validation/enso-ellipsoid-coverage.json", "exports/internal-external-bound-comparison-v4.json"]),
        node("counterexample-enso-v4-maximum-composition", "counterexample", "ENSO 最大界为 11.509464，平移占比仅 0.108143，由实际残差主导，九组最大界不再全部由平移主导", "supported", ["exports/external-bound-decomposition-v4.json", "validation/enso-ellipsoid-coverage.json"]),
        node("experiment-bound-comparison-v4-protocol", "experiment", "保留历史版本并冻结六外部与九组输入哈希、同族和周期候选范围的新版协议", "supported", ["validation/external-bound-decomposition-v4-protocol.json", "validation/internal-external-bound-comparison-v4-protocol.json"]),
        node("limitation-bound-comparison-v4-scope", "limitation", "九组范围合计不是成功率或原生周期模型验证，内部有根折、外部不可用点、同族边界和最大界反例均不可抹去", "active", ["exports/internal-external-bound-comparison-v4.json", "validation/chwirut1-ellipsoid-coverage-protocol.json", "validation/enso-ellipsoid-coverage-protocol.json"]),
    ])
    edges.extend([
        edge("track-holdout", "evidence-bound-comparison-v4", "contains"),
        edge("track-holdout", "counterexample-enso-v4-increment", "contains"),
        edge("track-holdout", "counterexample-enso-v4-maximum-composition", "contains"),
        edge("track-holdout", "experiment-bound-comparison-v4-protocol", "contains"),
        edge("track-holdout", "limitation-bound-comparison-v4-scope", "contains"),
        edge("evidence-bound-comparison-v4", "claim-new-data-overwrite-history", "contradicts"),
        edge("counterexample-enso-v4-increment", "claim-new-data-overwrite-history", "contradicts"),
        edge("evidence-bound-comparison-v4", "counterexample-enso-v4-increment", "supports"),
        edge("experiment-bound-comparison-v4-protocol", "claim-new-data-overwrite-history", "tests"),
        edge("limitation-bound-comparison-v4-scope", "claim-new-data-overwrite-history", "limits"),
        edge("evidence-bound-comparison-v4", "evidence-enso-prediction-proof-dissociation", "supports"),
        edge("limitation-bound-comparison-v4-scope", "claim-untouched-data-independent-model-family", "limits"),
        edge("counterexample-enso-v4-maximum-composition", "claim-wide-bounds-parameter-uncertainty", "contradicts"),
        edge("evidence-bound-comparison-v4", "counterexample-enso-v4-maximum-composition", "supports"),
    ])
    nodes.extend([
        node("evidence-maximum-full-composition-audit", "evidence", "九组中 8 组最大点类别与多数一致、6 组低于中位占比及最大界宽比审计", "supported", ["exports/maximum-full-composition-audit.json"]),
        node("counterexample-gauss1-maximum-majority-mismatch", "counterexample", "Gauss1 多数点由实际残差主导，但最大界点由平移主导且最大界宽为中位界宽的 82.994 倍", "supported", ["exports/maximum-full-composition-audit.json"]),
        node("counterexample-enso-maximum-low-share-percentile", "counterexample", "ENSO 最大点与多数一样由实际残差主导，但其平移占比只处于描述性第 13.33% 位置", "supported", ["exports/maximum-full-composition-audit.json"]),
        node("experiment-maximum-full-composition-protocol", "experiment", "冻结九组输入并分别计算类别、占比差、描述性百分位和界宽比的只读审计协议", "supported", ["validation/maximum-full-composition-protocol.json"]),
        node("limitation-maximum-not-typical", "limitation", "最大界点是极值而非典型点，描述性百分位和界宽比不是概率或物理因果", "active", ["exports/maximum-full-composition-audit.json"]),
    ])
    edges.extend([
        edge("track-holdout", "evidence-maximum-full-composition-audit", "contains"),
        edge("track-holdout", "counterexample-gauss1-maximum-majority-mismatch", "contains"),
        edge("track-holdout", "counterexample-enso-maximum-low-share-percentile", "contains"),
        edge("track-holdout", "experiment-maximum-full-composition-protocol", "contains"),
        edge("track-holdout", "limitation-maximum-not-typical", "contains"),
        edge("evidence-maximum-full-composition-audit", "counterexample-gauss1-maximum-majority-mismatch", "supports"),
        edge("evidence-maximum-full-composition-audit", "counterexample-enso-maximum-low-share-percentile", "supports"),
        edge("counterexample-gauss1-maximum-majority-mismatch", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("counterexample-enso-maximum-low-share-percentile", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("experiment-maximum-full-composition-protocol", "claim-uniform-external-bound-mechanism", "tests"),
        edge("limitation-maximum-not-typical", "evidence-maximum-full-composition-audit", "limits"),
        edge("evidence-maximum-full-composition-audit", "evidence-bound-comparison-v4", "supports"),
    ])
    nodes.append(node("experiment-extreme-reporting-contract", "experiment", "以 L0、L1、L2 三级契约和数值重算验收极值报告，九组审计通过且错误主张被拒绝", "supported", ["contracts/extreme-reporting.rules.json", "validation/extreme-reporting-check.json"]))
    edges.extend([
        edge("track-knowledge", "experiment-extreme-reporting-contract", "contains"),
        edge("experiment-extreme-reporting-contract", "claim-knowledge-graph", "tests"),
        edge("experiment-maximum-full-composition-protocol", "experiment-extreme-reporting-contract", "supports"),
    ])
    nodes.append(node("experiment-extreme-corpus-classification", "experiment", "对 16 份极值相关文档全集分级，10 份联读原文哈希保持不变", "supported", ["validation/extreme-corpus-audit.json", "validation/extreme-corpus-check.json"]))
    edges.extend([
        edge("track-knowledge", "experiment-extreme-corpus-classification", "contains"),
        edge("experiment-extreme-corpus-classification", "claim-knowledge-graph", "tests"),
        edge("experiment-extreme-reporting-contract", "experiment-extreme-corpus-classification", "supports"),
    ])
    nodes.extend([
        node("evidence-roszman1-prediction-proof-dissociation", "evidence", "Roszman1 共 25 点，5 点可给界、20 点不可用，1／5 折连续安全且 4 对比较收紧", "supported", ["validation/roszman1-ellipsoid-coverage.json"]),
        node("counterexample-roszman1-fold1-fold4-no-bounds", "counterexample", "Roszman1 第 1、4 折优于基线但均零可用界，第 5 折预测显著失败", "supported", ["validation/roszman1-ellipsoid-coverage.json"]),
        node("experiment-roszman1-scoped-prospective-protocol", "experiment", "在任何 Roszman1 候选分析前冻结并推送的范围感知五折协议", "supported", ["validation/roszman1-ellipsoid-coverage-protocol.json", "scripts/external_coverage_scoped.py", "scripts/analyze_roszman1_ellipsoid_coverage.py"]),
        node("limitation-roszman1-small-sample-shift-scope", "limitation", "Roszman1 的 5 个平移主导可用点只位于第 2 折，不能写成 25 点概率覆盖或原生模型验证", "active", ["validation/roszman1-ellipsoid-coverage.json"]),
    ])
    edges.extend([
        edge("track-holdout", "evidence-roszman1-prediction-proof-dissociation", "contains"),
        edge("track-holdout", "counterexample-roszman1-fold1-fold4-no-bounds", "contains"),
        edge("track-holdout", "experiment-roszman1-scoped-prospective-protocol", "contains"),
        edge("track-holdout", "limitation-roszman1-small-sample-shift-scope", "contains"),
        edge("evidence-roszman1-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"),
        edge("counterexample-roszman1-fold1-fold4-no-bounds", "claim-small-rmse-useful-proof", "contradicts"),
        edge("evidence-roszman1-prediction-proof-dissociation", "counterexample-roszman1-fold1-fold4-no-bounds", "supports"),
        edge("experiment-roszman1-scoped-prospective-protocol", "claim-small-rmse-useful-proof", "tests"),
        edge("limitation-roszman1-small-sample-shift-scope", "evidence-roszman1-prediction-proof-dissociation", "limits"),
        edge("evidence-roszman1-prediction-proof-dissociation", "claim-reusable-driver-guarantees-coverage", "contradicts"),
    ])
    nodes.extend([
        node("evidence-bound-comparison-v5", "evidence", "七外部 786／532／254 与十组 901 点的新版本对照及 Roszman1 增量", "supported", ["exports/external-bound-decomposition-v5.json", "exports/internal-external-bound-comparison-v5.json"]),
        node("counterexample-roszman1-v5-increment", "counterexample", "Roszman1 增加 25 总点、5 可用点、20 不可用点和 5 平移主导点，实际残差主导数不变", "supported", ["validation/roszman1-ellipsoid-coverage.json", "exports/internal-external-bound-comparison-v5.json"]),
        node("counterexample-roszman1-v5-small-sample-scope", "counterexample", "Roszman1 的 5 个可用点只在第 2 折，第 1、4 折优于基线却零可用界且第 5 折预测失败", "supported", ["exports/external-bound-decomposition-v5.json", "validation/roszman1-ellipsoid-coverage.json"]),
        node("experiment-bound-comparison-v5-protocol", "experiment", "保留历史版本并冻结七外部与十组输入哈希、同族、周期和原生反正切候选范围的新版协议", "supported", ["validation/external-bound-decomposition-v5-protocol.json", "validation/internal-external-bound-comparison-v5-protocol.json"]),
        node("limitation-bound-comparison-v5-scope", "limitation", "十组范围合计不是成功率或原生模型验证，内部有根折、外部不可用点、同族边界和第 2 折局部可用范围均不可抹去", "active", ["exports/internal-external-bound-comparison-v5.json", "validation/roszman1-ellipsoid-coverage-protocol.json"]),
    ])
    edges.extend([
        edge("track-holdout", "evidence-bound-comparison-v5", "contains"),
        edge("track-holdout", "counterexample-roszman1-v5-increment", "contains"),
        edge("track-holdout", "counterexample-roszman1-v5-small-sample-scope", "contains"),
        edge("track-holdout", "experiment-bound-comparison-v5-protocol", "contains"),
        edge("track-holdout", "limitation-bound-comparison-v5-scope", "contains"),
        edge("evidence-bound-comparison-v5", "claim-new-data-overwrite-history", "contradicts"),
        edge("counterexample-roszman1-v5-increment", "claim-new-data-overwrite-history", "contradicts"),
        edge("evidence-bound-comparison-v5", "counterexample-roszman1-v5-increment", "supports"),
        edge("experiment-bound-comparison-v5-protocol", "claim-new-data-overwrite-history", "tests"),
        edge("limitation-bound-comparison-v5-scope", "claim-new-data-overwrite-history", "limits"),
        edge("evidence-bound-comparison-v5", "evidence-roszman1-prediction-proof-dissociation", "supports"),
        edge("limitation-bound-comparison-v5-scope", "claim-untouched-data-independent-model-family", "limits"),
        edge("counterexample-roszman1-v5-small-sample-scope", "claim-small-rmse-useful-proof", "contradicts"),
        edge("evidence-bound-comparison-v5", "counterexample-roszman1-v5-small-sample-scope", "supports"),
        edge("limitation-bound-comparison-v5-scope", "evidence-bound-comparison-v5", "limits"),
        edge("counterexample-roszman1-v5-small-sample-scope", "claim-reusable-driver-guarantees-coverage", "contradicts"),
        edge("evidence-bound-comparison-v5", "evidence-bound-comparison-v4", "supports"),
    ])
    nodes.extend([
        node("claim-descriptive-percentile-probability-coverage", "claim", "描述性百分位等于概率覆盖率或总体代表性", "falsified", ["exports/maximum-full-composition-audit-v2.json"]),
        node("evidence-maximum-full-composition-v2", "evidence", "十组中 9 组最大点类别与多数一致、6 组低于中位占比及十组界宽比审计", "supported", ["exports/maximum-full-composition-audit-v2.json", "validation/extreme-reporting-v2-check.json"]),
        node("counterexample-roszman1-v2-percentile-not-coverage", "counterexample", "Roszman1 最大点占比在 5 个第 2 折可用点中为描述性第 100%，但另有 20 点不可用，不能称为 25 点概率覆盖", "supported", ["exports/maximum-full-composition-audit-v2.json", "validation/roszman1-ellipsoid-coverage.json"]),
        node("experiment-maximum-full-composition-v2-protocol", "experiment", "冻结十组输入并分别计算类别、占比差、描述性百分位和界宽比的只读审计协议及独立 L2 收据", "supported", ["validation/maximum-full-composition-v2-protocol.json", "validation/extreme-reporting-v2-check.json"]),
        node("limitation-maximum-v2-small-sample-not-probability", "limitation", "最大界点是极值而非典型点，小样本描述性百分位不是概率、总体代表性或物理因果", "active", ["exports/maximum-full-composition-audit-v2.json"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-descriptive-percentile-probability-coverage", "contains"),
        edge("track-holdout", "evidence-maximum-full-composition-v2", "contains"),
        edge("track-holdout", "counterexample-roszman1-v2-percentile-not-coverage", "contains"),
        edge("track-holdout", "experiment-maximum-full-composition-v2-protocol", "contains"),
        edge("track-holdout", "limitation-maximum-v2-small-sample-not-probability", "contains"),
        edge("evidence-maximum-full-composition-v2", "claim-descriptive-percentile-probability-coverage", "contradicts"),
        edge("counterexample-roszman1-v2-percentile-not-coverage", "claim-descriptive-percentile-probability-coverage", "contradicts"),
        edge("evidence-maximum-full-composition-v2", "counterexample-roszman1-v2-percentile-not-coverage", "supports"),
        edge("experiment-maximum-full-composition-v2-protocol", "claim-descriptive-percentile-probability-coverage", "tests"),
        edge("limitation-maximum-v2-small-sample-not-probability", "evidence-maximum-full-composition-v2", "limits"),
        edge("evidence-maximum-full-composition-v2", "evidence-bound-comparison-v5", "supports"),
        edge("evidence-maximum-full-composition-v2", "evidence-maximum-full-composition-audit", "supports"),
        edge("experiment-maximum-full-composition-v2-protocol", "experiment-extreme-reporting-contract", "supports"),
        edge("evidence-maximum-full-composition-v2", "counterexample-gauss1-maximum-majority-mismatch", "supports"),
        edge("evidence-maximum-full-composition-v2", "counterexample-enso-maximum-low-share-percentile", "supports"),
        edge("limitation-maximum-v2-small-sample-not-probability", "claim-descriptive-percentile-probability-coverage", "limits"),
    ])
    nodes.extend([
        node("claim-model-family-fold-independent-winner", "claim", "同一模型族在所有留出折都优于其他模型族", "falsified", ["validation/roszman1-native-holdout.json"]),
        node("claim-rational-bounds-transfer-native", "claim", "有理分母、椭球和参数盒证明区域可直接移植到原生反正切模型", "falsified", ["validation/roszman1-native-holdout.json"]),
        node("evidence-roszman1-native-holdout", "evidence", "原生模型在第 3、4、5 折 RMSE 更低，第 1、2 折有理候选更低，五折全部成功且已知答案复核通过", "supported", ["validation/roszman1-native-holdout.json"]),
        node("counterexample-roszman1-native-fold-dependent-ranking", "counterexample", "原生与有理候选各在三折和两折取得更低 RMSE，三次基线又在第 2、3 折最低，不存在固定赢家", "supported", ["validation/roszman1-native-holdout.json"]),
        node("experiment-roszman1-native-holdout-protocol", "experiment", "在任何原生拟合前冻结 NIST 起点、相同五折、奇异性和失败规则的同折对照协议", "supported", ["validation/roszman1-native-holdout-protocol.json", "scripts/analyze_roszman1_native_holdout.py"]),
        node("limitation-roszman1-native-no-bounds", "limitation", "原生预测对照没有建立原生确定性界或概率校准，也不继承有理模型的证明区域", "active", ["validation/roszman1-native-holdout.json"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-model-family-fold-independent-winner", "contains"),
        edge("track-holdout", "claim-rational-bounds-transfer-native", "contains"),
        edge("track-holdout", "evidence-roszman1-native-holdout", "contains"),
        edge("track-holdout", "counterexample-roszman1-native-fold-dependent-ranking", "contains"),
        edge("track-holdout", "experiment-roszman1-native-holdout-protocol", "contains"),
        edge("track-holdout", "limitation-roszman1-native-no-bounds", "contains"),
        edge("evidence-roszman1-native-holdout", "claim-model-family-fold-independent-winner", "contradicts"),
        edge("counterexample-roszman1-native-fold-dependent-ranking", "claim-model-family-fold-independent-winner", "contradicts"),
        edge("evidence-roszman1-native-holdout", "counterexample-roszman1-native-fold-dependent-ranking", "supports"),
        edge("experiment-roszman1-native-holdout-protocol", "claim-model-family-fold-independent-winner", "tests"),
        edge("evidence-roszman1-native-holdout", "claim-rational-bounds-transfer-native", "contradicts"),
        edge("limitation-roszman1-native-no-bounds", "claim-rational-bounds-transfer-native", "limits"),
        edge("limitation-roszman1-native-no-bounds", "evidence-roszman1-native-holdout", "limits"),
        edge("evidence-roszman1-native-holdout", "evidence-roszman1-prediction-proof-dissociation", "supports"),
        edge("experiment-roszman1-native-holdout-protocol", "experiment-roszman1-scoped-prospective-protocol", "supports"),
        edge("evidence-roszman1-native-holdout", "claim-nist-reproduction", "supports"),
        edge("experiment-roszman1-native-holdout-protocol", "claim-nist-reproduction", "tests"),
    ])
    nodes.extend([
        node("claim-local-rank-global-identifiability", "claim", "五折局部数值满秩即可证明全局结构可识别性", "falsified", ["validation/roszman1-native-identifiability.json"]),
        node("claim-prediction-stability-parameter-uniqueness", "claim", "留出预测稳定即可证明参数唯一、恒定或物理内生", "falsified", ["validation/roszman1-native-identifiability.json"]),
        node("evidence-roszman1-native-identifiability", "evidence", "五折局部数值秩均为 4，最大条件数 90.743359、最大相关绝对值 0.987535，参数逐折变化明显", "supported", ["validation/roszman1-native-identifiability.json"]),
        node("counterexample-roszman1-native-parameter-variation", "counterexample", "原生 RMSE 约为 0.006—0.010，但 b2 范围为 0.000010411859、b4 范围为 112.236141", "supported", ["validation/roszman1-native-identifiability.json"]),
        node("experiment-roszman1-native-identifiability-protocol", "experiment", "在计算前冻结解析雅可比、SVD、局部协方差和 Delta-method 规则的只读诊断协议", "supported", ["validation/roszman1-native-identifiability-protocol.json", "scripts/analyze_roszman1_native_identifiability.py"]),
        node("limitation-roszman1-native-local-linearization", "limitation", "局部秩、标准误和敏感度不是全局可识别性、概率区间、物理内生性或原生确定性界", "active", ["validation/roszman1-native-identifiability.json"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-local-rank-global-identifiability", "contains"),
        edge("track-holdout", "claim-prediction-stability-parameter-uniqueness", "contains"),
        edge("track-holdout", "evidence-roszman1-native-identifiability", "contains"),
        edge("track-holdout", "counterexample-roszman1-native-parameter-variation", "contains"),
        edge("track-holdout", "experiment-roszman1-native-identifiability-protocol", "contains"),
        edge("track-holdout", "limitation-roszman1-native-local-linearization", "contains"),
        edge("evidence-roszman1-native-identifiability", "claim-local-rank-global-identifiability", "contradicts"),
        edge("experiment-roszman1-native-identifiability-protocol", "claim-local-rank-global-identifiability", "tests"),
        edge("limitation-roszman1-native-local-linearization", "claim-local-rank-global-identifiability", "limits"),
        edge("evidence-roszman1-native-identifiability", "claim-prediction-stability-parameter-uniqueness", "contradicts"),
        edge("counterexample-roszman1-native-parameter-variation", "claim-prediction-stability-parameter-uniqueness", "contradicts"),
        edge("evidence-roszman1-native-identifiability", "counterexample-roszman1-native-parameter-variation", "supports"),
        edge("limitation-roszman1-native-local-linearization", "evidence-roszman1-native-identifiability", "limits"),
        edge("evidence-roszman1-native-identifiability", "evidence-roszman1-native-holdout", "supports"),
        edge("experiment-roszman1-native-identifiability-protocol", "experiment-roszman1-native-holdout-protocol", "supports"),
        edge("evidence-roszman1-native-identifiability", "limitation-roszman1-native-no-bounds", "supports"),
        edge("evidence-roszman1-native-identifiability", "claim-rational-bounds-transfer-native", "contradicts"),
        edge("experiment-roszman1-native-identifiability-protocol", "claim-prediction-stability-parameter-uniqueness", "tests"),
    ])
    nodes.extend([
        node("claim-certified-forward-equals-optimizer-reproduction", "claim", "认证参数直接代入通过即可证明优化器已在同一容差内复现认证参数", "falsified", ["validation/enso-native-holdout.json", "validation/enso-native-holdout-protocol-amendment-01.json"]),
        node("evidence-enso-native-holdout", "evidence", "ENSO 原生在第 2—5 折 RMSE 更低，第 1 折有理更低；默认 LM 未达原容差而认证前向通过", "supported", ["validation/enso-native-holdout.json"]),
        node("counterexample-enso-native-fold1-rational-better", "counterexample", "ENSO 第 1 折原生 RMSE 为 3.448449，高于有理候选的 2.723813，不能写成所有折原生更优", "supported", ["validation/enso-native-holdout.json"]),
        node("counterexample-enso-optimizer-mismatch", "counterexample", "默认 LM 的 b8 相对偏差约 0.000634 且 RSS 超出原容差，但认证参数直接代入通过", "supported", ["validation/enso-native-holdout.json", "validation/enso-native-holdout-protocol-amendment-01.json"]),
        node("experiment-enso-native-holdout-protocol", "experiment", "冻结九参数起点、五段月份和失败规则，并保留优化器未达标后冻结的认证前向修订", "supported", ["validation/enso-native-holdout-protocol.json", "validation/enso-native-holdout-protocol-amendment-01.json", "scripts/analyze_enso_native_holdout.py"]),
        node("limitation-enso-native-period-and-bounds", "limitation", "多数折预测更低不等于全域排名或原生误差界，周期参数随折变化也不证明新周期机制", "active", ["validation/enso-native-holdout.json"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-certified-forward-equals-optimizer-reproduction", "contains"),
        edge("track-holdout", "evidence-enso-native-holdout", "contains"),
        edge("track-holdout", "counterexample-enso-native-fold1-rational-better", "contains"),
        edge("track-holdout", "counterexample-enso-optimizer-mismatch", "contains"),
        edge("track-holdout", "experiment-enso-native-holdout-protocol", "contains"),
        edge("track-holdout", "limitation-enso-native-period-and-bounds", "contains"),
        edge("evidence-enso-native-holdout", "claim-model-family-fold-independent-winner", "contradicts"),
        edge("counterexample-enso-native-fold1-rational-better", "claim-model-family-fold-independent-winner", "contradicts"),
        edge("evidence-enso-native-holdout", "counterexample-enso-native-fold1-rational-better", "supports"),
        edge("experiment-enso-native-holdout-protocol", "claim-model-family-fold-independent-winner", "tests"),
        edge("evidence-enso-native-holdout", "claim-certified-forward-equals-optimizer-reproduction", "contradicts"),
        edge("counterexample-enso-optimizer-mismatch", "claim-certified-forward-equals-optimizer-reproduction", "contradicts"),
        edge("evidence-enso-native-holdout", "counterexample-enso-optimizer-mismatch", "supports"),
        edge("experiment-enso-native-holdout-protocol", "claim-certified-forward-equals-optimizer-reproduction", "tests"),
        edge("limitation-enso-native-period-and-bounds", "evidence-enso-native-holdout", "limits"),
        edge("evidence-enso-native-holdout", "evidence-enso-prediction-proof-dissociation", "supports"),
        edge("experiment-enso-native-holdout-protocol", "experiment-enso-scoped-prospective-protocol", "supports"),
        edge("evidence-enso-native-holdout", "claim-nist-reproduction", "supports"),
        edge("experiment-enso-native-holdout-protocol", "claim-nist-reproduction", "tests"),
        edge("evidence-enso-native-holdout", "evidence-roszman1-native-holdout", "supports"),
        edge("limitation-enso-native-period-and-bounds", "evidence-enso-prediction-proof-dissociation", "limits"),
    ])
    nodes.extend([
        node("claim-low-rmse-independent-replication", "claim", "较低留出 RMSE 即可构成独立模型族或独立实验室复现", "falsified", ["validation/chwirut1-native-holdout.json"]),
        node("evidence-chwirut1-native-holdout", "evidence", "Chwirut1 原生在第 1、3、4、5 折 RMSE 更低，第 2 折有理更低；214 点汇总 RMSE 为 7.778996 对 9.456158", "supported", ["validation/chwirut1-native-holdout.json"]),
        node("counterexample-chwirut1-native-fold2-rational-better", "counterexample", "Chwirut1 第 2 折原生 RMSE 为 2.622278，高于有理候选的 2.449395，不能写成所有折原生更优", "supported", ["validation/chwirut1-native-holdout.json"]),
        node("counterexample-chwirut1-native-fold1-error-and-parameters", "counterexample", "Chwirut1 第 1 折原生 RMSE 仍有 14.465527，b2 逐折范围为 0.005195445，低相对误差和参数稳定都不能过度解释", "supported", ["validation/chwirut1-native-holdout.json"]),
        node("experiment-chwirut1-native-holdout-protocol", "experiment", "冻结三参数起点、22 个距离分组和重复观测规则，并以独立修订纠正折级计数", "supported", ["validation/chwirut1-native-holdout-protocol.json", "validation/chwirut1-native-holdout-protocol-amendment-01.json", "scripts/analyze_chwirut1_native_holdout.py"]),
        node("limitation-chwirut1-native-related-study-and-bounds", "limitation", "Chwirut1 与 Chwirut2 同研究同模型族，预测优势不构成独立复现、原生误差界或概率校准", "active", ["validation/chwirut1-native-holdout.json", "validation/chwirut1-ellipsoid-coverage-protocol.json"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-low-rmse-independent-replication", "contains"),
        edge("track-holdout", "evidence-chwirut1-native-holdout", "contains"),
        edge("track-holdout", "counterexample-chwirut1-native-fold2-rational-better", "contains"),
        edge("track-holdout", "counterexample-chwirut1-native-fold1-error-and-parameters", "contains"),
        edge("track-holdout", "experiment-chwirut1-native-holdout-protocol", "contains"),
        edge("track-holdout", "limitation-chwirut1-native-related-study-and-bounds", "contains"),
        edge("evidence-chwirut1-native-holdout", "claim-model-family-fold-independent-winner", "contradicts"),
        edge("counterexample-chwirut1-native-fold2-rational-better", "claim-model-family-fold-independent-winner", "contradicts"),
        edge("evidence-chwirut1-native-holdout", "counterexample-chwirut1-native-fold2-rational-better", "supports"),
        edge("experiment-chwirut1-native-holdout-protocol", "claim-model-family-fold-independent-winner", "tests"),
        edge("evidence-chwirut1-native-holdout", "claim-low-rmse-independent-replication", "contradicts"),
        edge("counterexample-chwirut1-native-fold1-error-and-parameters", "claim-low-rmse-independent-replication", "contradicts"),
        edge("evidence-chwirut1-native-holdout", "counterexample-chwirut1-native-fold1-error-and-parameters", "supports"),
        edge("experiment-chwirut1-native-holdout-protocol", "claim-low-rmse-independent-replication", "tests"),
        edge("limitation-chwirut1-native-related-study-and-bounds", "evidence-chwirut1-native-holdout", "limits"),
        edge("evidence-chwirut1-native-holdout", "evidence-chwirut1-prediction-proof-dissociation", "supports"),
        edge("evidence-chwirut1-native-holdout", "claim-nist-reproduction", "supports"),
        edge("experiment-chwirut1-native-holdout-protocol", "claim-nist-reproduction", "tests"),
        edge("evidence-chwirut1-native-holdout", "evidence-roszman1-native-holdout", "supports"),
        edge("evidence-chwirut1-native-holdout", "evidence-enso-native-holdout", "supports"),
        edge("limitation-chwirut1-native-related-study-and-bounds", "claim-untouched-data-independent-model-family", "limits"),
    ])
    nodes.append(node("experiment-extreme-corpus-v2-classification", "experiment", "对 23 份极值相关文档全集分级，22 份非接口文档哈希匹配，旧 10 份联读原文未变", "supported", ["validation/extreme-corpus-v2-audit.json", "validation/extreme-corpus-v2-check.json", "scripts/validate_extreme_corpus_v2.py"]))
    edges.extend([
        edge("track-knowledge", "experiment-extreme-corpus-v2-classification", "contains"),
        edge("experiment-extreme-corpus-v2-classification", "claim-knowledge-graph", "tests"),
        edge("experiment-extreme-corpus-classification", "experiment-extreme-corpus-v2-classification", "supports"),
    ])
    nodes.append(node("experiment-repository-integrity-audit", "experiment", "检查 README 链接、图片、Word 哈希、证据快照、图谱、全集计数和 10 份近期协议，错误数为 0", "supported", ["validation/repository-integrity-rules.json", "validation/repository-integrity-report.json", "scripts/audit_repository_integrity.py"]))
    edges.extend([
        edge("track-knowledge", "experiment-repository-integrity-audit", "contains"),
        edge("experiment-repository-integrity-audit", "claim-knowledge-graph", "tests"),
        edge("experiment-extreme-corpus-v2-classification", "experiment-repository-integrity-audit", "supports"),
    ])
    nodes.extend([
        node("claim-single-error-metric-sufficient", "claim", "单一误差指标或逐点多票数足以决定模型优劣", "falsified", ["exports/native-cross-dataset-synthesis.json"]),
        node("evidence-native-cross-dataset-synthesis", "evidence", "三数据 15 折中原生 11 折 RMSE 低于有理、10 折为三者最低；407 点逐点结果与指标反例完整保留", "supported", ["exports/native-cross-dataset-synthesis.json", "validation/native-cross-dataset-synthesis-check.json"]),
        node("counterexample-roszman1-native-fold4-metric-direction", "counterexample", "Roszman1 第 4 折原生 RMSE 更低但有理 MAE 更低，单一指标不能隐藏方向分歧", "supported", ["exports/native-cross-dataset-synthesis.json"]),
        node("counterexample-roszman1-native-point-majority-rmse", "counterexample", "Roszman1 逐点计数为原生 12、有理 13，但原生 25 点 RMSE 更低，逐点多票数不等同于平方误差", "supported", ["exports/native-cross-dataset-synthesis.json"]),
        node("experiment-native-cross-dataset-synthesis-protocol", "experiment", "冻结三项输入哈希、15 折、407 点、RMSE 主指标和逐点规则的只读综合协议", "supported", ["validation/native-cross-dataset-synthesis-protocol.json", "scripts/analyze_native_cross_dataset_synthesis.py"]),
        node("limitation-native-cross-dataset-scope", "limitation", "三数据事后综合不跨量纲合并误差，不是概率排名、独立实验、原生误差界或普适规律", "active", ["exports/native-cross-dataset-synthesis.json", "docs/NATIVE_CROSS_DATASET_SYNTHESIS_2026-11-09.md"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-single-error-metric-sufficient", "contains"),
        edge("track-holdout", "evidence-native-cross-dataset-synthesis", "contains"),
        edge("track-holdout", "counterexample-roszman1-native-fold4-metric-direction", "contains"),
        edge("track-holdout", "counterexample-roszman1-native-point-majority-rmse", "contains"),
        edge("track-holdout", "experiment-native-cross-dataset-synthesis-protocol", "contains"),
        edge("track-holdout", "limitation-native-cross-dataset-scope", "contains"),
        edge("evidence-native-cross-dataset-synthesis", "claim-model-family-fold-independent-winner", "contradicts"),
        edge("experiment-native-cross-dataset-synthesis-protocol", "claim-model-family-fold-independent-winner", "tests"),
        edge("evidence-native-cross-dataset-synthesis", "claim-single-error-metric-sufficient", "contradicts"),
        edge("counterexample-roszman1-native-fold4-metric-direction", "claim-single-error-metric-sufficient", "contradicts"),
        edge("counterexample-roszman1-native-point-majority-rmse", "claim-single-error-metric-sufficient", "contradicts"),
        edge("experiment-native-cross-dataset-synthesis-protocol", "claim-single-error-metric-sufficient", "tests"),
        edge("evidence-native-cross-dataset-synthesis", "counterexample-roszman1-native-fold4-metric-direction", "supports"),
        edge("evidence-native-cross-dataset-synthesis", "counterexample-roszman1-native-point-majority-rmse", "supports"),
        edge("limitation-native-cross-dataset-scope", "evidence-native-cross-dataset-synthesis", "limits"),
        edge("limitation-native-cross-dataset-scope", "claim-single-error-metric-sufficient", "limits"),
        edge("evidence-native-cross-dataset-synthesis", "evidence-roszman1-native-holdout", "supports"),
        edge("evidence-native-cross-dataset-synthesis", "evidence-enso-native-holdout", "supports"),
        edge("evidence-native-cross-dataset-synthesis", "evidence-chwirut1-native-holdout", "supports"),
        edge("experiment-native-cross-dataset-synthesis-protocol", "experiment-roszman1-native-holdout-protocol", "supports"),
        edge("experiment-native-cross-dataset-synthesis-protocol", "experiment-enso-native-holdout-protocol", "supports"),
        edge("experiment-native-cross-dataset-synthesis-protocol", "experiment-chwirut1-native-holdout-protocol", "supports"),
    ])
    nodes.extend([
        node("claim-aggregate-loss-direction-implies-per-point", "claim", "汇总 RMSE 与 MAE 反向意味着单点绝对与平方残差方向也相反", "falsified", ["validation/roszman1-native-fold4-error-decomposition.json"]),
        node("evidence-roszman1-fold4-error-decomposition", "evidence", "第 4 折 D1 为正、D2 为负；五点逐点方向一致，权重恒等式和冻结指标全部通过", "supported", ["validation/roszman1-native-fold4-error-decomposition.json", "validation/roszman1-native-fold4-error-decomposition-check.json"]),
        node("counterexample-roszman1-fold4-weighted-reversal", "counterexample", "原生优势点平均权重 0.018460300，有理优势点平均权重 0.004268459，汇总反向来自残差尺度加权", "supported", ["validation/roszman1-native-fold4-error-decomposition.json"]),
        node("counterexample-roszman1-fold4-leave-one-out-asymmetry", "counterexample", "移除第 4 或第 5 点均反转 MAE 方向，五次移除均不反转 RMSE 方向，两种指标具有不同单点依赖", "supported", ["validation/roszman1-native-fold4-error-decomposition.json"]),
        node("experiment-roszman1-fold4-error-decomposition-protocol", "experiment", "冻结五点预测、绝对与平方差值、残差权重恒等式及不重拟合的单点贡献移除规则", "supported", ["validation/roszman1-native-fold4-error-decomposition-protocol.json", "scripts/analyze_roszman1_native_fold4_error_decomposition.py"]),
        node("limitation-roszman1-fold4-five-point-arithmetic", "limitation", "五点贡献分解和单点移除只是算术诊断，不是显著性、因果机制、重新拟合或普适模型选择规则", "active", ["validation/roszman1-native-fold4-error-decomposition.json", "docs/ROSZMAN1_NATIVE_FOLD4_ERROR_DECOMPOSITION_2026-11-09.md"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-aggregate-loss-direction-implies-per-point", "contains"),
        edge("track-holdout", "evidence-roszman1-fold4-error-decomposition", "contains"),
        edge("track-holdout", "counterexample-roszman1-fold4-weighted-reversal", "contains"),
        edge("track-holdout", "counterexample-roszman1-fold4-leave-one-out-asymmetry", "contains"),
        edge("track-holdout", "experiment-roszman1-fold4-error-decomposition-protocol", "contains"),
        edge("track-holdout", "limitation-roszman1-fold4-five-point-arithmetic", "contains"),
        edge("evidence-roszman1-fold4-error-decomposition", "claim-single-error-metric-sufficient", "contradicts"),
        edge("experiment-roszman1-fold4-error-decomposition-protocol", "claim-single-error-metric-sufficient", "tests"),
        edge("evidence-roszman1-fold4-error-decomposition", "claim-aggregate-loss-direction-implies-per-point", "contradicts"),
        edge("counterexample-roszman1-fold4-weighted-reversal", "claim-single-error-metric-sufficient", "contradicts"),
        edge("counterexample-roszman1-fold4-weighted-reversal", "claim-aggregate-loss-direction-implies-per-point", "contradicts"),
        edge("experiment-roszman1-fold4-error-decomposition-protocol", "claim-aggregate-loss-direction-implies-per-point", "tests"),
        edge("evidence-roszman1-fold4-error-decomposition", "counterexample-roszman1-fold4-weighted-reversal", "supports"),
        edge("evidence-roszman1-fold4-error-decomposition", "counterexample-roszman1-fold4-leave-one-out-asymmetry", "supports"),
        edge("counterexample-roszman1-fold4-leave-one-out-asymmetry", "claim-single-error-metric-sufficient", "contradicts"),
        edge("limitation-roszman1-fold4-five-point-arithmetic", "evidence-roszman1-fold4-error-decomposition", "limits"),
        edge("limitation-roszman1-fold4-five-point-arithmetic", "claim-aggregate-loss-direction-implies-per-point", "limits"),
        edge("evidence-roszman1-fold4-error-decomposition", "evidence-native-cross-dataset-synthesis", "supports"),
        edge("experiment-roszman1-fold4-error-decomposition-protocol", "experiment-native-cross-dataset-synthesis-protocol", "supports"),
        edge("limitation-roszman1-fold4-five-point-arithmetic", "counterexample-roszman1-fold4-leave-one-out-asymmetry", "limits"),
    ])
    nodes.extend([
        node("claim-native-pole-free-observations-global-safety", "claim", "观测点分母非零且极点在观测范围外即可证明全域原生安全", "falsified", ["validation/chwirut1-native-identifiability.json"]),
        node("evidence-chwirut1-native-identifiability", "evidence", "五折局部秩均为 3，最大条件数 28.674083，最大相关 0.979413，第 1 折最大敏感度 14.836682，五折极点均在观测范围外", "supported", ["validation/chwirut1-native-identifiability.json", "validation/chwirut1-native-identifiability-check.json"]),
        node("counterexample-chwirut1-native-fold1-local-instability", "counterexample", "第 1 折虽然局部满秩，但 b2 相对标准误 1.710628、最大敏感度 14.836682 且 RMSE 为 14.465527", "supported", ["validation/chwirut1-native-identifiability.json"]),
        node("counterexample-chwirut1-native-low-rmse-parameter-uniqueness", "counterexample", "第 4 折原生 RMSE 最低为 1.368210，但三个参数仍随折变化，低误差不能证明参数唯一或内生", "supported", ["validation/chwirut1-native-identifiability.json"]),
        node("experiment-chwirut1-native-identifiability-protocol", "experiment", "冻结五折参数、逐折自由度、解析雅可比、Delta-method 与原生分母极点诊断规则", "supported", ["validation/chwirut1-native-identifiability-protocol.json", "scripts/analyze_chwirut1_native_identifiability.py"]),
        node("limitation-chwirut1-native-local-and-related-scope", "limitation", "局部秩、协方差和观测点极点不是全局识别、概率区间或全域证书；Chwirut1 与 Chwirut2 同研究同模型族", "active", ["validation/chwirut1-native-identifiability.json", "docs/CHWIRUT1_NATIVE_IDENTIFIABILITY_2026-11-09.md"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-native-pole-free-observations-global-safety", "contains"),
        edge("track-holdout", "evidence-chwirut1-native-identifiability", "contains"),
        edge("track-holdout", "counterexample-chwirut1-native-fold1-local-instability", "contains"),
        edge("track-holdout", "counterexample-chwirut1-native-low-rmse-parameter-uniqueness", "contains"),
        edge("track-holdout", "experiment-chwirut1-native-identifiability-protocol", "contains"),
        edge("track-holdout", "limitation-chwirut1-native-local-and-related-scope", "contains"),
        edge("evidence-chwirut1-native-identifiability", "claim-local-rank-global-identifiability", "contradicts"),
        edge("experiment-chwirut1-native-identifiability-protocol", "claim-local-rank-global-identifiability", "tests"),
        edge("evidence-chwirut1-native-identifiability", "claim-native-pole-free-observations-global-safety", "contradicts"),
        edge("experiment-chwirut1-native-identifiability-protocol", "claim-native-pole-free-observations-global-safety", "tests"),
        edge("counterexample-chwirut1-native-fold1-local-instability", "claim-local-rank-global-identifiability", "contradicts"),
        edge("counterexample-chwirut1-native-low-rmse-parameter-uniqueness", "claim-prediction-stability-parameter-uniqueness", "contradicts"),
        edge("evidence-chwirut1-native-identifiability", "counterexample-chwirut1-native-fold1-local-instability", "supports"),
        edge("evidence-chwirut1-native-identifiability", "counterexample-chwirut1-native-low-rmse-parameter-uniqueness", "supports"),
        edge("limitation-chwirut1-native-local-and-related-scope", "evidence-chwirut1-native-identifiability", "limits"),
        edge("limitation-chwirut1-native-local-and-related-scope", "claim-native-pole-free-observations-global-safety", "limits"),
        edge("limitation-chwirut1-native-local-and-related-scope", "claim-untouched-data-independent-model-family", "limits"),
        edge("evidence-chwirut1-native-identifiability", "evidence-chwirut1-native-holdout", "supports"),
        edge("experiment-chwirut1-native-identifiability-protocol", "experiment-chwirut1-native-holdout-protocol", "supports"),
        edge("evidence-chwirut1-native-identifiability", "evidence-roszman1-native-identifiability", "supports"),
        edge("experiment-chwirut1-native-identifiability-protocol", "experiment-roszman1-native-identifiability-protocol", "supports"),
        edge("counterexample-chwirut1-native-low-rmse-parameter-uniqueness", "claim-low-rmse-independent-replication", "contradicts"),
    ])
    return {"schemaVersion": 1, "asOf": "2026-11-09", "project": "frontier-breakthrough", "nodes": nodes, "edges": edges}


def validate_graph(graph, root):
    errors = []
    allowed_kinds = {"project", "claim", "evidence", "counterexample", "experiment", "limitation"}
    allowed_status = {"active", "supported", "limited_support", "falsified", "unresolved"}
    allowed_relations = {"contains", "supports", "contradicts", "tests", "limits", "recommends"}
    if graph.get("schemaVersion") != 1 or graph.get("project") != "frontier-breakthrough":
        errors.append("Invalid graph header")
    identifiers = set()
    for node in graph.get("nodes", []):
        identifier = node.get("id")
        if identifier in identifiers:
            errors.append(f"Duplicate node id: {identifier}")
        identifiers.add(identifier)
        if node.get("kind") not in allowed_kinds or node.get("status") not in allowed_status:
            errors.append(f"Invalid node kind/status: {identifier}")
        for source in node.get("sourceFiles", []):
            if not (Path(root) / source).is_file():
                errors.append(f"Missing source file: {identifier}: {source}")
    for edge in graph.get("edges", []):
        if edge["from"] not in identifiers or edge["to"] not in identifiers:
            errors.append(f"Dangling edge: {edge}")
        if edge["relation"] not in allowed_relations:
            errors.append(f"Invalid relation: {edge}")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "exports/frontier-knowledge-graph.json"
    graph = build_graph(root)
    errors = validate_graph(graph, root)
    if errors:
        raise ValueError(errors)
    import sys
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if previous != graph:
            if "--extend" not in sys.argv:
                raise ValueError("Refusing to overwrite a different knowledge graph; use --extend only for append-only additions")
            previous_nodes = {node["id"]: node for node in previous["nodes"]}
            current_nodes = {node["id"]: node for node in graph["nodes"]}
            if any(current_nodes.get(identifier) != node for identifier, node in previous_nodes.items()):
                raise ValueError("Existing nodes may not be modified or deleted")
            previous_edges = {(edge["from"], edge["to"], edge["relation"]) for edge in previous["edges"]}
            current_edges = {(edge["from"], edge["to"], edge["relation"]) for edge in graph["edges"]}
            if not previous_edges.issubset(current_edges):
                raise ValueError("Existing edges may not be modified or deleted")
            output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
