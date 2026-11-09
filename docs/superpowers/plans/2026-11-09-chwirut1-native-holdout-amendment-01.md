# Chwirut1 Native Holdout Metadata Amendment 01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 保留原协议与全部科学选择，仅将五折观测数元数据纠正为冻结候选结果中的 `[57,54,51,23,29]`，并让分析和测试显式引用该修订。

**Architecture:** 原协议文件保持不变，以独立修订文件记录原协议 SHA-256、错误数组、纠正数组和来源。分析加载修订后验证计数，距离分组、起点、模型、优化器和容差均不改变。

**Tech Stack:** JSON、Python、unittest、Git。

## Global Constraints

- 在当前 `main` 内联执行，不创建工作树或子代理。
- 不修改原协议文件，不改变 22 个距离分组、214 个观测、重复观测或任何模型选择。

---

### Task 1: 冻结并验证计数修订

**Files:**
- Create: `validation/chwirut1-native-holdout-protocol-amendment-01.json`
- Create: `docs/superpowers/plans/2026-11-09-chwirut1-native-holdout-amendment-01.md`
- Modify: `tests/test_chwirut1_native_holdout_protocol.py`

**Interfaces:**
- Consumes: 原协议 SHA-256 `735228da3c0eb4729b922d8e312b59844030a63ba360d502068bca28da695237`；冻结候选五折 `point_results`。
- Produces: `correction.corrected_observation_counts=[57,54,51,23,29]`、`fold_assignments_changed=false`。

- [ ] **Step 1: 让协议测试引用修订**

```python
amendment = json.loads((root / "validation/chwirut1-native-holdout-protocol-amendment-01.json").read_text(encoding="utf-8"))
assert amendment["original_protocol"]["sha256"] == "735228da3c0eb4729b922d8e312b59844030a63ba360d502068bca28da695237"
assert amendment["correction"]["corrected_observation_counts"] == [57, 54, 51, 23, 29]
assert amendment["decision"]["fold_assignments_changed"] is False
```

- [ ] **Step 2: 确认测试因修订文件缺失而失败**

Run: `python -m unittest tests.test_chwirut1_native_holdout_protocol -v`

Expected: FAIL，`FileNotFoundError`。

- [ ] **Step 3: 写入修订并验证推送**

Run: `python -m unittest tests.test_chwirut1_native_holdout_protocol tests.test_chwirut1_external_protocol -v`

Expected: 全部 PASS，原协议和旧候选哈希不变。

```bash
git add validation/chwirut1-native-holdout-protocol-amendment-01.json docs/superpowers/plans/2026-11-09-chwirut1-native-holdout-amendment-01.md tests/test_chwirut1_native_holdout_protocol.py
git commit -m "research: correct Chwirut1 fold-count metadata"
git push origin main
```

### Task 2: 让原生分析引用纠正计数

**Files:**
- Modify: `scripts/analyze_chwirut1_native_holdout.py`
- Modify: `tests/test_chwirut1_native_holdout.py`
- Create: `validation/chwirut1-native-holdout.json`
- Create: `papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png`

**Interfaces:**
- Consumes: Task 1 修订文件。
- Produces: `metadata_amendment_sha256` 和正确的五折计数 `[57,54,51,23,29]`。

- [ ] **Step 1: 更新五折测试并确认实现尚未引用修订**

```python
self.assertEqual([len(fold["point_results"]) for fold in summary["folds"]], [57, 54, 51, 23, 29])
self.assertEqual(summary["metadata_amendment_sha256"], hashlib.sha256((ROOT / "validation/chwirut1-native-holdout-protocol-amendment-01.json").read_bytes()).hexdigest())
```

- [ ] **Step 2: 实现修订加载与验证**

```python
amendment_path = ROOT / "validation/chwirut1-native-holdout-protocol-amendment-01.json"
amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
if amendment["original_protocol"]["sha256"] != sha256(protocol_path):
    raise ValueError("Chwirut1 metadata amendment does not match original protocol")
expected_counts = amendment["correction"]["corrected_observation_counts"]
```

验证器使用 `expected_counts`，输出写入 `metadata_amendment_sha256=sha256(amendment_path)`，原协议和原候选结果不改。

- [ ] **Step 3: 生成结果并全量复验**

Run: `python scripts/analyze_chwirut1_native_holdout.py`

Run: `python -m unittest discover -s tests`

Expected: 全部 PASS，五折计数正确且原文件不变。

```bash
git add scripts/analyze_chwirut1_native_holdout.py tests/test_chwirut1_native_holdout.py validation/chwirut1-native-holdout.json papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png
git commit -m "research: compare native Chwirut1 with corrected fold metadata"
git push origin main
```
