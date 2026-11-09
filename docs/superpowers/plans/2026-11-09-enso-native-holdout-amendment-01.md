# ENSO Native Holdout Diagnostic Amendment 01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不放宽原协议容差、不改变优化器或五折结果的前提下，保留 ENSO 全数据 LM 已知答案未达标，并新增直接代入 NIST 认证参数的公式复核。

**Architecture:** 原协议保持不变，以独立修订文件冻结触发值、原协议哈希和直接代入规则。分析结果分别记录优化器复现与认证参数前向计算，禁止把前向结果写成优化器复现或留出证据。

**Tech Stack:** JSON、Python、NumPy、unittest、Git。

## Global Constraints

- 在当前 `main` 内联执行，不创建工作树或子代理。
- 不放宽 `parameter_relative_tolerance=0.00001`、`parameter_absolute_tolerance=0.00000001`、`rss_absolute_tolerance=0.000001`。
- 不新增起点、周期约束、缩放、优化器选项或折分，不隐藏默认 LM 未达标。

---

### Task 1: 冻结诊断修订

**Files:**
- Create: `validation/enso-native-holdout-protocol-amendment-01.json`
- Create: `docs/superpowers/plans/2026-11-09-enso-native-holdout-amendment-01.md`
- Create: `tests/test_enso_native_holdout_amendment.py`

**Interfaces:**
- Consumes: 原协议 SHA-256 `94d91a09b48ecc2c8904ce51e0507a4ad0d85e4f330d5b78374734c3b4eb8cc4`。
- Produces: `certified_forward_rule`、`optimizer_mismatch_hidden=false`、`original_tolerances_relaxed=false`。

- [ ] **Step 1: 写修订结构测试**

```python
def test_amendment_preserves_original_optimizer_mismatch():
    amendment = json.loads(Path("validation/enso-native-holdout-protocol-amendment-01.json").read_text(encoding="utf-8"))
    assert amendment["original_protocol"]["sha256"] == "94d91a09b48ecc2c8904ce51e0507a4ad0d85e4f330d5b78374734c3b4eb8cc4"
    assert amendment["trigger"]["original_tolerances_relaxed"] is False
    assert amendment["decision"]["optimizer_mismatch_hidden"] is False
    assert amendment["certified_forward_rule"]["evidence_class"] == "known_answer_forward_evaluation_not_optimizer_or_holdout"
```

- [ ] **Step 2: 验证并推送修订**

Run: `python -m unittest tests.test_enso_native_holdout_amendment tests.test_enso_native_holdout_protocol -v`

Expected: 全部 PASS，原协议文件哈希不变。

```bash
git add validation/enso-native-holdout-protocol-amendment-01.json docs/superpowers/plans/2026-11-09-enso-native-holdout-amendment-01.md tests/test_enso_native_holdout_amendment.py
git commit -m "research: preserve ENSO optimizer mismatch and freeze forward check"
git push origin main
```

### Task 2: 分别记录优化器与认证前向结果

**Files:**
- Modify: `scripts/analyze_enso_native_holdout.py`
- Modify: `tests/test_enso_native_holdout.py`

**Interfaces:**
- Consumes: Task 1 修订文件。
- Produces: `known_answer.certified_forward_rss`、`known_answer.certified_forward_rss_check_passed`、`known_answer.amendment_sha256`，原 `within_certified_tolerances` 保持实际 false。

- [ ] **Step 1: 修改测试以要求两类证据分开**

```python
known = module.analyze()["known_answer"]
self.assertTrue(known["optimizer_success"])
self.assertFalse(known["within_certified_tolerances"])
self.assertTrue(known["certified_forward_rss_check_passed"])
self.assertEqual(known["certified_forward_evidence_class"], "known_answer_forward_evaluation_not_optimizer_or_holdout")
self.assertFalse(known["original_tolerances_relaxed"])
self.assertFalse(known["optimizer_mismatch_hidden"])
```

- [ ] **Step 2: 运行测试确认新增字段缺失**

Run: `python -m unittest tests.test_enso_native_holdout -v`

Expected: FAIL，缺少认证前向字段；不得把原 `within_certified_tolerances` 改成 true。

- [ ] **Step 3: 实现直接认证参数计算**

```python
certified = known_rule["certified_parameters"]
values = [certified[name] for name in PARAMETER_NAMES]
prediction = native_model(x, *values)
forward_rss = float(np.sum((y - prediction) ** 2))
forward_match = math.isclose(forward_rss, known_rule["certified_rss"], rel_tol=0, abs_tol=known_rule["rss_absolute_tolerance"])
known_answer["certified_forward_rss"] = forward_rss
known_answer["certified_forward_rss_check_passed"] = forward_match
known_answer["certified_forward_evidence_class"] = amendment["certified_forward_rule"]["evidence_class"]
known_answer["original_tolerances_relaxed"] = False
known_answer["optimizer_mismatch_hidden"] = False
known_answer["amendment_sha256"] = sha256(AMENDMENT)
```

验证器要求直接代入 RSS 检查通过，同时保留优化器实际 `within_certified_tolerances=false`，不得只保留成功面。

- [ ] **Step 4: 生成结果并全量复验**

Run: `python scripts/analyze_enso_native_holdout.py`

Run: `python -m unittest discover -s tests`

Expected: 全部 PASS；结果同时包含优化器未达标与认证前向通过，旧协议和旧有理结果不变。

```bash
git add scripts/analyze_enso_native_holdout.py tests/test_enso_native_holdout.py validation/enso-native-holdout.json papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png
git commit -m "research: compare native ENSO while preserving optimizer mismatch"
git push origin main
```
