# ENSO Native Fourier Holdout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在完全相同的 168 个留出点上比较 ENSO 原生九参数 Fourier 模型、已冻结三次／三次有理候选和三次多项式基线，并形成跨模型族、可追溯的预测证据与原生图文报告。

**Architecture:** 新建独立协议、分析脚本、结果和报告，复用不变的数据加载与误差指标函数。全 168 点 NIST 认证拟合只检查公式实现；五折模型只在训练段拟合，逐点连接既有有理结果，不修改任何历史覆盖、界或参数。

**Tech Stack:** Python 3.12、NumPy、SciPy `curve_fit`、Matplotlib、unittest、JSON、既有 Pandoc／python-docx／OOXML 流水线。

## Global Constraints

- 在当前 `main` 内联执行，用户已授权直接修改、提交和推送，不创建工作树或子代理。
- 协议先于任何原生拟合提交并推送；测试先失败，再实现，再全量复验。
- 冻结 NIST 两组起点、LM `maxfev=200000`、五个连续月份区间和失败规则；不因结果新增起点、周期约束、缩放或折分。
- 全数据认证拟合不是留出证据；有理分母、椭球、盒和连续安全证书不移植到原生 Fourier 模型。
- 不宣称概率校准、物理内生、绝对模型排名、独立实验或普适周期规律。
- 所有 Bash 调用使用中文、通俗、约 8—10 字的 `description`。

---

### Task 1: 冻结 ENSO 原生同折对照协议

**Files:**
- Create: `validation/enso-native-holdout-protocol.json`
- Create: `docs/superpowers/plans/2026-11-09-enso-native-holdout.md`
- Create: `tests/test_enso_native_holdout_protocol.py`

**Interfaces:**
- Consumes: `data/ENSO.dat` SHA-256 `0c644f45b0e586cb1bb0613bad68f63c704efadacd086e768468d33d83f3e5d9`；`validation/enso-ellipsoid-coverage.json` SHA-256 `6d930ad31dbb4affbd41dd7a362814a6e1614b19246e3133eca1edf33cf37ba7`。
- Produces: `frozen_before_enso_native_holdout` 状态、九参数顺序、两个周期非零规则、五段月份范围、认证参数与 RSS、输出路径。

- [ ] **Step 1: 写协议失败测试**

```python
import json
from pathlib import Path


def test_enso_native_protocol_freezes_model_and_folds():
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "validation/enso-native-holdout-protocol.json").read_text(encoding="utf-8"))
    assert protocol["status"] == "frozen_before_enso_native_holdout"
    assert protocol["native_rule"]["parameters"] == ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9"]
    assert protocol["fold_rule"]["ranges"] == {"1": [1, 34], "2": [35, 68], "3": [69, 102], "4": [103, 135], "5": [136, 168]}
    assert protocol["decision"]["certified_full_fit_used_as_holdout"] is False
    assert protocol["decision"]["rational_bounds_transferred_to_native"] is False
```

- [ ] **Step 2: 确认测试因协议缺失而失败**

Run: `python -m unittest tests.test_enso_native_holdout_protocol -v`

Expected: FAIL，`FileNotFoundError`。

- [ ] **Step 3: 写入原生公式、起点和已知答案**

```json
{
  "status": "frozen_before_enso_native_holdout",
  "native_rule": {
    "parameters": ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9"],
    "equation": "y=b1+b2*cos(2*pi*x/12)+b3*sin(2*pi*x/12)+b5*cos(2*pi*x/b4)+b6*sin(2*pi*x/b4)+b8*cos(2*pi*x/b7)+b9*sin(2*pi*x/b7)+e",
    "starts": [
      {"b1": 11.0, "b2": 3.0, "b3": 0.5, "b4": 40.0, "b5": -0.7, "b6": -1.3, "b7": 25.0, "b8": -0.3, "b9": 1.4},
      {"b1": 10.0, "b2": 3.0, "b3": 0.5, "b4": 44.0, "b5": -1.5, "b6": 0.5, "b7": 26.0, "b8": -0.1, "b9": 1.5}
    ],
    "optimizer": "scipy.optimize.curve_fit method=lm,maxfev=200000,full_output=true; select lowest finite training RSS",
    "singular_rule": "b4=0 or b7=0 returns non-finite predictions; no replacement by certified fits or post-hoc bounds"
  },
  "fold_rule": {
    "ranges": {"1": [1, 34], "2": [35, 68], "3": [69, 102], "4": [103, 135], "5": [136, 168]},
    "construction": "Inclusive integer month ranges identical to the frozen rational folds"
  },
  "known_answer_rule": {
    "certified_parameters": {"b1": 10.510749193, "b2": 3.0762128085, "b3": 0.53280138227, "b4": 44.311088700, "b5": -1.6231428586, "b6": 0.52554493756, "b7": 26.887614440, "b8": 0.21232288488, "b9": 1.4966870418},
    "certified_rss": 788.53978668,
    "parameter_relative_tolerance": 0.00001,
    "parameter_absolute_tolerance": 0.00000001,
    "rss_absolute_tolerance": 0.000001,
    "evidence_class": "known_answer_reproduction_not_holdout"
  },
  "decision": {
    "certified_full_fit_used_as_holdout": false,
    "rational_bounds_transferred_to_native": false,
    "native_deterministic_bounds_claimed": false,
    "native_probability_calibration_claimed": false,
    "native_physical_law_validated": false,
    "independent_physical_experiment_claimed": false,
    "failed_fits_hidden": false
  }
}
```

协议另冻结输入哈希、逐点 fold/x/y 连接、RMSE／MAE／最大残差、168 点原生与有理汇总、三次基线无逐点预测时不计算汇总、输出 `validation/enso-native-holdout.json` 和 `papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png`，拒绝覆盖。

- [ ] **Step 4: 验证并推送协议**

Run: `python -m unittest tests.test_enso_native_holdout_protocol tests.test_enso_external_protocol -v`

Expected: 全部 PASS，且未运行原生拟合。

```bash
git add validation/enso-native-holdout-protocol.json docs/superpowers/plans/2026-11-09-enso-native-holdout.md tests/test_enso_native_holdout_protocol.py
git commit -m "research: freeze ENSO native Fourier holdout comparison"
git push origin main
```

---

### Task 2: 实现九参数原生拟合与逐折对照

**Files:**
- Create: `scripts/analyze_enso_native_holdout.py`
- Create: `tests/test_enso_native_holdout.py`
- Create: `validation/enso-native-holdout.json`
- Create: `papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png`

**Interfaces:**
- Consumes: Task 1 协议；`load_observations`、`error_metrics`、`sha256`。
- Produces: `native_model(x,b1,b2,b3,b4,b5,b6,b7,b8,b9)`、`fit_native(x,y,starts)`、`analyze()`、`validate_summary(summary)`、`render_figure(summary)`。

- [ ] **Step 1: 写公式与零周期失败测试**

```python
def test_native_fourier_formula_and_zero_periods(self):
    module = self.load_module()
    p = (10.0, 3.0, 0.5, 44.0, -1.5, 0.5, 26.0, -0.1, 1.5)
    x = np.array([1.0, 12.0, 60.0])
    expected = p[0] + p[1]*np.cos(2*np.pi*x/12) + p[2]*np.sin(2*np.pi*x/12) + p[4]*np.cos(2*np.pi*x/p[3]) + p[5]*np.sin(2*np.pi*x/p[3]) + p[7]*np.cos(2*np.pi*x/p[6]) + p[8]*np.sin(2*np.pi*x/p[6])
    np.testing.assert_allclose(module.native_model(x, *p), expected, rtol=0, atol=1e-14)
    self.assertTrue(np.isnan(module.native_model(x, *p[:3], 0.0, *p[4:])[0]))
    self.assertTrue(np.isnan(module.native_model(x, *p[:6], 0.0, *p[7:])[0]))
```

- [ ] **Step 2: 写已知答案、五折与最终输出失败测试**

测试断言：认证参数和 RSS 在协议容差内；每折 34／34／34／33／33 点，原生指标由逐点残差重算，既有有理指标和预测逐点完全相等；记录全部起点、训练 RSS、选中起点和周期参数；无隐藏失败、无原生界继承；输出与重新分析一致且 PNG 真实。

Run: `python -m unittest tests.test_enso_native_holdout -v`

Expected: FAIL，`Missing native ENSO analysis`。

- [ ] **Step 3: 实现原生模型与冻结起点拟合**

```python
import numpy as np


def native_model(x, b1, b2, b3, b4, b5, b6, b7, b8, b9):
    x = np.asarray(x, dtype=float)
    if b4 == 0 or b7 == 0:
        return np.full(x.shape, np.nan, dtype=float)
    annual = 2 * np.pi * x / 12
    long_1 = 2 * np.pi * x / b4
    long_2 = 2 * np.pi * x / b7
    return (
        b1 + b2*np.cos(annual) + b3*np.sin(annual)
        + b5*np.cos(long_1) + b6*np.sin(long_1)
        + b8*np.cos(long_2) + b9*np.sin(long_2)
    )
```

`fit_native` 必须逐个运行两个起点，保存参数、训练 RSS、优化器消息、警告与异常，以最低有限训练 RSS 选择；不得调用全数据认证参数替代任何折的训练拟合。每个留出点保存原生预测、原生绝对残差、既有有理预测和既有有理绝对残差。

- [ ] **Step 4: 实现汇总、动态图和验证**

输出 `totals`：五折 168 点、原生失败折数、原生／有理各自更低折数、原生／三次基线各自更低折数、认证复核状态。输出九参数五折最小值／中位数／最大值／范围，特别是 b4、b7 周期变化。图包含五折 RMSE、原生／有理 RMSE 比值和 b4／b7 周期变化，不把认证拟合画成留出结果。

Run: `python scripts/analyze_enso_native_holdout.py`

Expected: `validate_summary` 返回空列表并生成真实 JSON／PNG。

Run: `python -m unittest tests.test_enso_native_holdout tests.test_enso_external_protocol -v`

Expected: 全部 PASS，旧有理覆盖哈希不变。

```bash
git add scripts/analyze_enso_native_holdout.py tests/test_enso_native_holdout.py validation/enso-native-holdout.json papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png
git commit -m "research: compare native ENSO Fourier model on identical holdouts"
git push origin main
```

---

### Task 3: 第三十四阶段报告、证据与交付

**Files:**
- Create: `docs/ENSO_NATIVE_HOLDOUT_2026-11-09.md`
- Create: `scripts/build_frontier_enso_native_holdout_word.py`
- Create: `tests/test_frontier_enso_native_holdout_word.py`
- Create: `papers/前沿共生ENSO原生周期同折对照_图文完整版.docx`
- Create: `validation/frontier-enso-native-holdout-word.json`
- Create: `tests/test_enso_native_integration.py`
- Modify: `scripts/build_frontier_word.py`
- Modify: `scripts/export_evidence_packet.py`
- Modify: `scripts/build_frontier_knowledge_graph.py`
- Modify: `README.md`
- Modify: `docs/UPSTREAM_INTERFACES.md`

**Interfaces:**
- Consumes: Task 2 的 JSON、PNG 和提交记录。
- Produces: `REPORT_MODE="enso_native_holdout"`、一幅实际图、四个 Word 表格、两个 OMML 公式、证据 `enso-native-holdout-comparison` 和完整图谱链。

- [ ] **Step 1: 写报告与证据失败测试**

报告测试检查图哈希、2 个公式、4 个表格、全部折的胜负和周期边界，禁止“原生周期模型全面最优”。证据测试检查 168 点、五折、认证复核非留出、逐折胜负、无界移植和失败保留；更新累计计数前运行并确认失败。

- [ ] **Step 2: 新增独立 Word 模式并构建**

```python
if REPORT_MODE == "enso_native_holdout":
    replacements = {
        "图：`papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png`。": "![](papers/41_ENSO原生周期对照/fig41_enso_native_holdout.png)\n\n**图 41｜ENSO 原生 Fourier 与有理候选同折对照（第 1 幅，共 1 幅）**  \n**插入位置**：§5「图件与周期参数解释」；顺序第 1 幅，共 1 幅。",
    }
    subtitle = "168 个相同留出点、五折周期模型对照与证明边界"
elif REPORT_MODE == "roszman1_native_identifiability":
    replacements = {
        "图：`papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png`。": "![](papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png)\n\n**图 40｜Roszman1 原生参数局部可识别性与稳定性（第 1 幅，共 1 幅）**  \n**插入位置**：§5「图件与解释边界」；顺序第 1 幅，共 1 幅。",
    }
    subtitle = "五折解析雅可比、参数稳定性与局部预测敏感度"
```

Run: `python scripts/build_frontier_enso_native_holdout_word.py`

Expected: OOXML／OPC 通过，一幅原图、四个表格、两个原生公式；无视觉渲染时明确披露。

- [ ] **Step 3: 接入证据和图谱**

新证据必须连接 ENSO 旧预测—证明解离、NIST 已知答案、逐折模型族反例和原生无界限制。新图不得修改旧 ENSO 结果、十组对照或极值审计。

Run: `python scripts/export_evidence_packet.py`

Run: `python scripts/build_frontier_knowledge_graph.py --extend`

Run: `python -m unittest tests.test_enso_native_integration tests.test_knowledge_graph -v`

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
git commit -m "research: report native ENSO Fourier holdout comparison"
git push origin main
git ls-remote origin main
git status --short
```

Expected: 远端与本地一致，工作区干净，长期研究目标保持开放。
