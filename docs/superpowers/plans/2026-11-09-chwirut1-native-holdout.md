# Chwirut1 Native Exponential Holdout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在完全相同的 214 个留出观测上比较 Chwirut1 原生三参数指数模型、已冻结三次／三次有理候选和三次多项式基线，并与 Roszman1、ENSO 形成有边界的跨原生模型证据。

**Architecture:** 新建独立协议、分析、结果和报告，复用不变的数据加载、原生公式与误差指标。按 22 个不同金属距离分组，重复观测全部留在同一侧；全数据认证拟合只验证实现，五折原生模型只用训练距离拟合，不修改旧覆盖或证明区域。

**Tech Stack:** Python 3.12、NumPy、SciPy `curve_fit`、Matplotlib、unittest、JSON、既有 Pandoc／python-docx／OOXML 流水线。

## Global Constraints

- 在当前 `main` 内联执行，用户已授权直接修改、提交和推送，不创建工作树或子代理。
- 协议先于任何原生拟合提交并推送；测试先失败，再实现，再全量复验。
- 冻结 NIST 两组起点、LM `maxfev=200000`、五组不同距离和失败规则；不因结果新增起点、参数界限、缩放或折分。
- Chwirut1 与 Chwirut2 同研究、同原生模型族；不得称为独立模型族或独立实验室复现。
- 全数据认证拟合不是留出证据；不移植有理分母、椭球、盒或连续安全证书，不宣称概率校准、物理内生或绝对模型排名。
- 所有 Bash 调用使用中文、通俗、约 8—10 字的 `description`。

---

### Task 1: 冻结 Chwirut1 原生同折协议

**Files:**
- Create: `validation/chwirut1-native-holdout-protocol.json`
- Create: `docs/superpowers/plans/2026-11-09-chwirut1-native-holdout.md`
- Create: `tests/test_chwirut1_native_holdout_protocol.py`

**Interfaces:**
- Consumes: `data/Chwirut1.dat` SHA-256 `d9a055dfe5af71a8754c00f073ef00f8fed2e3fd1c6fd20cea8fd62d7cc3ed84`；`validation/chwirut1-ellipsoid-coverage.json` SHA-256 `e6c6816d4c4616a1efbd739fcf92d4b782049e38201ebdd4db37479ca156ed33`。
- Produces: `frozen_before_chwirut1_native_holdout` 状态、三参数顺序、22 个距离分组、各折观测数、认证参数与 RSS、独立输出路径。

- [ ] **Step 1: 写协议失败测试**

```python
import json
from pathlib import Path


def test_chwirut1_protocol_freezes_unique_distance_groups():
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "validation/chwirut1-native-holdout-protocol.json").read_text(encoding="utf-8"))
    assert protocol["status"] == "frozen_before_chwirut1_native_holdout"
    assert protocol["fold_rule"]["unique_x"] == {
        "1": [0.5, 0.625, 0.75, 0.875, 1.0],
        "2": [1.25, 1.5, 1.75, 2.0, 2.25],
        "3": [2.5, 2.75, 3.0, 3.25],
        "4": [3.75, 4.0, 4.25, 4.75],
        "5": [5.0, 5.25, 5.75, 6.0],
    }
    assert protocol["fold_rule"]["observation_counts"] == [54, 54, 51, 23, 32]
    assert protocol["dataset_scope"]["related_prior_dataset"]["same_native_model_family"] is True
    assert protocol["decision"]["independent_model_family_claimed"] is False
```

- [ ] **Step 2: 确认测试因协议缺失而失败**

Run: `python -m unittest tests.test_chwirut1_native_holdout_protocol -v`

Expected: FAIL，`FileNotFoundError`。

- [ ] **Step 3: 写入原生公式、起点和已知答案**

```json
{
  "status": "frozen_before_chwirut1_native_holdout",
  "native_rule": {
    "parameters": ["b1", "b2", "b3"],
    "equation": "y=exp(-b1*x)/(b2+b3*x)+e",
    "starts": [
      {"b1": 0.1, "b2": 0.01, "b3": 0.02},
      {"b1": 0.15, "b2": 0.008, "b3": 0.01}
    ],
    "optimizer": "scipy.optimize.curve_fit method=lm,maxfev=200000,full_output=true; select lowest finite training RSS",
    "singular_rule": "Any evaluation point with b2+b3*x=0 returns non-finite prediction; do not replace it with a limit or certified fit"
  },
  "fold_rule": {
    "unique_x": {
      "1": [0.5, 0.625, 0.75, 0.875, 1.0],
      "2": [1.25, 1.5, 1.75, 2.0, 2.25],
      "3": [2.5, 2.75, 3.0, 3.25],
      "4": [3.75, 4.0, 4.25, 4.75],
      "5": [5.0, 5.25, 5.75, 6.0]
    },
    "observation_counts": [54, 54, 51, 23, 32],
    "construction": "All repeated observations of a frozen distance remain on the same side; no distance crosses fitting and test sets"
  },
  "known_answer_rule": {
    "certified_parameters": {"b1": 0.19027818370, "b2": 0.0061314004477, "b3": 0.010530908399},
    "certified_rss": 2384.4771393,
    "parameter_relative_tolerance": 0.00001,
    "parameter_absolute_tolerance": 0.00000001,
    "rss_absolute_tolerance": 0.000001,
    "evidence_class": "known_answer_reproduction_not_holdout"
  },
  "dataset_scope": {
    "related_prior_dataset": {"name": "Chwirut2", "same_study": true, "same_native_model_family": true}
  },
  "decision": {
    "independent_model_family_claimed": false,
    "independent_physical_experiment_claimed": false,
    "certified_full_fit_used_as_holdout": false,
    "rational_bounds_transferred_to_native": false,
    "native_deterministic_bounds_claimed": false,
    "native_probability_calibration_claimed": false,
    "failed_fits_hidden": false
  }
}
```

协议另冻结输入哈希、逐点 fold/index/x/y 连接、214 点原生与有理汇总、三次基线无逐点预测时不计算汇总、输出 `validation/chwirut1-native-holdout.json` 和 `papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png`，拒绝覆盖。

- [ ] **Step 4: 验证并推送协议**

Run: `python -m unittest tests.test_chwirut1_native_holdout_protocol tests.test_chwirut1_external_protocol -v`

Expected: 全部 PASS，且未运行原生拟合。

```bash
git add validation/chwirut1-native-holdout-protocol.json docs/superpowers/plans/2026-11-09-chwirut1-native-holdout.md tests/test_chwirut1_native_holdout_protocol.py
git commit -m "research: freeze Chwirut1 native exponential holdout comparison"
git push origin main
```

---

### Task 2: 实现三参数原生拟合与逐折对照

**Files:**
- Create: `scripts/analyze_chwirut1_native_holdout.py`
- Create: `tests/test_chwirut1_native_holdout.py`
- Create: `validation/chwirut1-native-holdout.json`
- Create: `papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png`

**Interfaces:**
- Consumes: Task 1 协议；`chwirut_model`、`load_observations`、`error_metrics`、`sha256`。
- Produces: `native_model(x,b1,b2,b3)`、`fit_native(x,y,starts)`、`analyze()`、`validate_summary(summary)`、`render_figure(summary)`。

- [ ] **Step 1: 写公式与分母奇异性失败测试**

```python
def test_native_exponential_formula_and_denominator_singularity(self):
    module = self.load_module()
    x = np.array([0.5, 1.0, 2.0])
    p = (0.15, 0.008, 0.01)
    np.testing.assert_allclose(module.native_model(x, *p), np.exp(-p[0]*x)/(p[1]+p[2]*x), rtol=0, atol=1e-14)
    self.assertTrue(np.isnan(module.native_model(np.array([1.0]), 0.1, -0.01, 0.01)[0]))
```

- [ ] **Step 2: 写已知答案、五折与最终输出失败测试**

测试断言：认证参数与 RSS 在容差内；五折观测数为 54、54、51、23、32，重复 x 不跨训练与测试；原生指标由逐点残差重算，既有有理指标和预测逐点一致；所有起点、训练 RSS、选中起点、参数范围和失败均保留；输出与重新分析一致且 PNG 真实。

Run: `python -m unittest tests.test_chwirut1_native_holdout -v`

Expected: FAIL，`Missing native Chwirut1 analysis`。

- [ ] **Step 3: 实现原生模型与冻结起点拟合**

```python
import numpy as np


def native_model(x, b1, b2, b3):
    x = np.asarray(x, dtype=float)
    denominator = b2 + b3 * x
    if np.any(denominator == 0):
        return np.full(x.shape, np.nan, dtype=float)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return np.exp(-b1 * x) / denominator
```

`fit_native` 逐个运行两个起点，保存参数、训练 RSS、优化器消息、警告和异常，以最低有限训练 RSS 选择。全数据认证参数不得替代任何折训练拟合。逐点连接按原冻结 `point_results` 的观测顺序，不能只按 x 去重后丢弃重复观测。

- [ ] **Step 4: 实现汇总、参数范围、动态图与验证**

输出五折 214 点、原生失败折数、原生／有理各自更低折数、原生／三次基线各自更低折数、认证复核状态和三参数最小值／中位数／最大值／范围。图包含五折 RMSE、原生／有理 RMSE 比值和参数相对于五折中位数的变化；认证拟合不得作为留出曲线。

Run: `python scripts/analyze_chwirut1_native_holdout.py`

Expected: `validate_summary` 返回空列表并生成真实 JSON／PNG。

Run: `python -m unittest tests.test_chwirut1_native_holdout tests.test_chwirut1_external_protocol -v`

Expected: 全部 PASS，旧有理覆盖哈希不变。

```bash
git add scripts/analyze_chwirut1_native_holdout.py tests/test_chwirut1_native_holdout.py validation/chwirut1-native-holdout.json papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png
git commit -m "research: compare native Chwirut1 on identical holdouts"
git push origin main
```

---

### Task 3: 第三十五阶段报告、证据与交付

**Files:**
- Create: `docs/CHWIRUT1_NATIVE_HOLDOUT_2026-11-09.md`
- Create: `scripts/build_frontier_chwirut1_native_holdout_word.py`
- Create: `tests/test_frontier_chwirut1_native_holdout_word.py`
- Create: `papers/前沿共生Chwirut1原生指数同折对照_图文完整版.docx`
- Create: `validation/frontier-chwirut1-native-holdout-word.json`
- Create: `tests/test_chwirut1_native_integration.py`
- Modify: `scripts/build_frontier_word.py`
- Modify: `scripts/export_evidence_packet.py`
- Modify: `scripts/build_frontier_knowledge_graph.py`
- Modify: `README.md`
- Modify: `docs/UPSTREAM_INTERFACES.md`

**Interfaces:**
- Consumes: Task 2 的 JSON、PNG 和提交记录。
- Produces: `REPORT_MODE="chwirut1_native_holdout"`、一幅实际图、四个 Word 表格、两个 OMML 公式、证据 `chwirut1-native-holdout-comparison` 与跨原生模型限制链。

- [ ] **Step 1: 写报告与证据失败测试**

报告测试检查图哈希、2 个公式、4 个表格、全部折的胜负、重复距离边界和同族限制，禁止“原生指数模型全面最优”。证据测试检查 214 点、22 个距离、认证复核非留出、逐折胜负、无界移植、无独立模型族主张和失败保留；更新累计计数前运行并确认失败。

- [ ] **Step 2: 新增独立 Word 模式并构建**

```python
if REPORT_MODE == "chwirut1_native_holdout":
    replacements = {
        "图：`papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png`。": "![](papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png)\n\n**图 42｜Chwirut1 原生指数与有理候选同折对照（第 1 幅，共 1 幅）**  \n**插入位置**：§5「图件与跨原生模型比较」；顺序第 1 幅，共 1 幅。",
    }
    subtitle = "214 个相同留出观测、22 个距离分组与同族模型边界"
elif REPORT_MODE == "enso_native_holdout":
    replacements = {
        "图：`papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png`。": "![](papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png)\n\n**图 41｜ENSO 原生 Fourier 与有理候选同折对照（第 1 幅，共 1 幅）**  \n**插入位置**：§5「图件与跨模型比较」；顺序第 1 幅，共 1 幅。",
    }
    subtitle = "168 个相同留出点、五折周期模型对照与证明边界"
```

Run: `python scripts/build_frontier_chwirut1_native_holdout_word.py`

Expected: OOXML／OPC 通过，一幅原图、四个表格、两个原生公式；无视觉渲染时明确披露。

- [ ] **Step 3: 接入证据和图谱**

新证据必须连接 Chwirut1 旧预测—证明解离、Chwirut2 同族限制、NIST 已知答案、Roszman1／ENSO 原生对照和原生无界限制。新图不得修改旧 Chwirut1、十组对照或极值审计。

Run: `python scripts/export_evidence_packet.py`

Run: `python scripts/build_frontier_knowledge_graph.py --extend`

Run: `python -m unittest tests.test_chwirut1_native_integration tests.test_knowledge_graph -v`

Expected: 全部 PASS，无悬空边。

- [ ] **Step 4: 全量复验、提交与远端核验**

Run: `python -m unittest discover -s tests`

Run: `python scripts/validate_extreme_reporting.py --check`

Run: `python scripts/validate_extreme_reporting_v2.py --check`

Run: `python scripts/validate_extreme_corpus.py --check`

Run: `python scripts/export_evidence_packet.py --check`

Run: `python scripts/build_catalog.py --check`

Expected: 全部 PASS。敏感信息扫描和差异格式检查通过后：

```bash
git add -A
git commit -m "research: report native Chwirut1 exponential holdout comparison"
git push origin main
git ls-remote origin main
git status --short
```

Expected: 远端与本地一致，工作区干净，长期研究目标保持开放。
