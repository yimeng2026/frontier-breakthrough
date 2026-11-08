# Roszman1 Native Identifiability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不重新拟合的前提下，审计 Roszman1 原生四参数反正切模型五个冻结训练折的局部可识别性、参数稳定性与留出预测敏感度，并交付可复现证据和原生图文报告。

**Architecture:** 以 `validation/roszman1-native-holdout.json` 的冻结参数、训练 RSS 和逐折分配为唯一拟合输入，以原始 NIST 数据重建训练设计。新脚本使用解析雅可比和既有列归一化／SVD／Delta-method 口径，不修改原生拟合、候选界或历史文件；独立协议、结果、图、报告和图谱节点保持版本隔离。

**Tech Stack:** Python 3.12、NumPy、SciPy、Matplotlib、unittest、JSON、既有 Pandoc／python-docx／OOXML 验证流水线。

## Global Constraints

- 在当前 `main` 内联执行；用户已明确授权直接修改、提交和推送，不创建工作树或子代理。
- 协议必须先于任何新分析执行而提交并推送；测试先失败，再实现，再全量复验。
- 不重新拟合、不更换参数、折分、起点或模型，不移植有理模型的椭球、参数盒或连续分母证书。
- 局部秩、条件数、标准误、相关系数和 Delta-method 敏感度都不是全局结构可识别性、物理内生性、概率校准或独立实验证据。
- 原始数据尾随空格和 Markdown 硬换行不清理；提交前执行敏感信息扫描与差异格式检查。
- 所有 Bash 调用使用中文、通俗、约 8—10 字的 `description`。

---

### Task 1: 冻结原生可识别性审计协议

**Files:**
- Create: `validation/roszman1-native-identifiability-protocol.json`
- Create: `docs/superpowers/plans/2026-11-09-roszman1-native-identifiability.md`
- Test: `tests/test_roszman1_native_identifiability_protocol.py`

**Interfaces:**
- Consumes: `validation/roszman1-native-holdout.json` SHA-256 `c8678e4635a23a9bf7a59233259c48c4307911df4dd50cf6e102cc8cb975e90e`；`data/Roszman1.dat` SHA-256 `fb526231ae6b02929e3de54e072e259b3d87424089abd4b1015ffb946b1e0ab0`。
- Produces: `frozen_before_roszman1_native_identifiability` 协议状态、四个参数顺序 `b1,b2,b3,b4`、20 个训练点／折、解析雅可比、SVD 与 Delta-method 规则、独立输出路径。

- [ ] **Step 1: 写协议结构测试**

```python
import json
from pathlib import Path


def test_native_identifiability_protocol_is_frozen():
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "validation/roszman1-native-identifiability-protocol.json").read_text(encoding="utf-8"))
    assert protocol["status"] == "frozen_before_roszman1_native_identifiability"
    assert protocol["inputs"]["native_holdout"]["sha256"] == "c8678e4635a23a9bf7a59233259c48c4307911df4dd50cf6e102cc8cb975e90e"
    assert protocol["jacobian_rule"]["parameter_order"] == ["b1", "b2", "b3", "b4"]
    assert protocol["jacobian_rule"]["train_points_per_fold"] == 20
    assert protocol["decision"]["refit"] is False
    assert protocol["decision"]["global_structural_identifiability_proved"] is False
```

- [ ] **Step 2: 先运行测试确认文件缺失**

Run: `python -m unittest tests.test_roszman1_native_identifiability_protocol -v`

Expected: FAIL，`FileNotFoundError`，因为协议尚未创建。

- [ ] **Step 3: 写入冻结协议**

协议必须包含以下可执行字段和公式，不以自然语言代替机器规则：

```json
{
  "status": "frozen_before_roszman1_native_identifiability",
  "inputs": {
    "native_holdout": {
      "file": "validation/roszman1-native-holdout.json",
      "sha256": "c8678e4635a23a9bf7a59233259c48c4307911df4dd50cf6e102cc8cb975e90e"
    },
    "data": {
      "file": "data/Roszman1.dat",
      "sha256": "fb526231ae6b02929e3de54e072e259b3d87424089abd4b1015ffb946b1e0ab0",
      "observations": 25
    }
  },
  "jacobian_rule": {
    "parameter_order": ["b1", "b2", "b3", "b4"],
    "train_points_per_fold": 20,
    "db1": "1",
    "db2": "-x",
    "db3": "-(x-b4)/(pi*((x-b4)^2+b3^2))",
    "db4": "-b3/(pi*((x-b4)^2+b3^2))",
    "singular_rule": "x=b4 is excluded and non-finite Jacobians are retained as failures"
  },
  "local_rule": {
    "rank_tolerance": "max(J.shape)*eps*largest_scaled_singular_value",
    "covariance": "sigma2*pinv(Js.T@Js,rcond=1e-12,hermitian=True)/outer(column_norms,column_norms)",
    "sigma2": "training_RSS/(20-4)",
    "prediction_sd": "sqrt(max(0,sigma2*Jtest@pinv(Js.T@Js)@Jtest.T diagonal)); descriptive delta method only"
  },
  "decision": {
    "refit": false,
    "global_structural_identifiability_proved": false,
    "physical_parameter_endogeneity_proved": false,
    "calibrated_prediction_intervals_produced": false,
    "rational_bounds_transferred_to_native": false
  }
}
```

另冻结：五个折的 x 分配直接来自 `validation/roszman1-native-holdout-protocol.json`；输出为 `validation/roszman1-native-identifiability.json` 和 `papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png`；禁止覆盖。

- [ ] **Step 4: 验证协议并提交推送**

Run: `python -m unittest tests.test_roszman1_native_identifiability_protocol tests.test_roszman1_native_holdout -v`

Expected: 全部 PASS，且尚未执行新可识别性分析。

```bash
git add validation/roszman1-native-identifiability-protocol.json docs/superpowers/plans/2026-11-09-roszman1-native-identifiability.md tests/test_roszman1_native_identifiability_protocol.py
git commit -m "research: freeze Roszman1 native identifiability audit"
git push origin main
```

---

### Task 2: 解析雅可比与五折局部诊断

**Files:**
- Create: `scripts/analyze_roszman1_native_identifiability.py`
- Create: `tests/test_roszman1_native_identifiability.py`
- Create: `validation/roszman1-native-identifiability.json`
- Create: `papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png`

**Interfaces:**
- Consumes: Task 1 协议；既有 `native_model(x,b1,b2,b3,b4)`、`load_observations(path,count,sha256)`、`error_metrics(y,prediction)`、`sha256(path)`。
- Produces: `native_jacobian(x, parameters) -> numpy.ndarray[20,4]`、`analyze() -> dict`、`validate_summary(summary) -> list[str]`、`render_figure(summary) -> None`。

- [ ] **Step 1: 写解析雅可比和冻结输入失败测试**

```python
def test_analytic_jacobian_matches_central_difference(self):
    module = self.load_module()
    parameters = {"b1": 0.2, "b2": -0.000005, "b3": 1200.0, "b4": -150.0}
    x = np.array([-1000.0, -500.0, -200.0])
    analytic = module.native_jacobian(x, parameters)
    numeric = np.empty_like(analytic)
    for index, name in enumerate(["b1", "b2", "b3", "b4"]):
        step = 1.0e-5 * max(1.0, abs(parameters[name]))
        upper = dict(parameters)
        lower = dict(parameters)
        upper[name] += step
        lower[name] -= step
        values = list(upper.values())
        numeric[:, index] = (module.native_model(x, *values) - module.native_model(x, *list(lower.values()))) / (2 * step)
    np.testing.assert_allclose(analytic, numeric, rtol=1.0e-6, atol=1.0e-8)
```

另写五折测试：每折 20 训练点、5 留出点、参数与冻结结果完全相等、测试 RMSE 完全相等、雅可比形状为 `(20,4)`、条件数有限且不小于 1、局部预测标准差非负、失败与秩亏不被改写为成功。

- [ ] **Step 2: 运行测试确认实现缺失**

Run: `python -m unittest tests.test_roszman1_native_identifiability -v`

Expected: FAIL，`Missing native identifiability analysis`。

- [ ] **Step 3: 实现解析雅可比**

```python
import numpy as np


def native_jacobian(x, parameters):
    x = np.asarray(x, dtype=float)
    b3 = float(parameters["b3"])
    b4 = float(parameters["b4"])
    shifted = x - b4
    denominator = shifted ** 2 + b3 ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.column_stack([
            np.ones_like(x),
            -x,
            -shifted / (np.pi * denominator),
            -b3 / (np.pi * denominator),
        ])
```

每折严格按既有 `native_holdout["folds"]` 取冻结参数，不调用 `curve_fit`。训练掩码由协议的五个留出 x 列表构造，训练 RSS 必须与冻结 `training_rss` 在 `rtol=1e-9, atol=1e-12` 内一致，留出指标必须与冻结 `native_test_metrics` 完全相等。

- [ ] **Step 4: 实现局部协方差与敏感度**

```python
column_norms = np.linalg.norm(jacobian, axis=0)
scaled = jacobian / column_norms
singular = np.linalg.svd(scaled, compute_uv=False)
tolerance = max(jacobian.shape) * np.finfo(float).eps * singular[0]
rank = int(np.sum(singular > tolerance))
unit_covariance = np.linalg.pinv(scaled.T @ scaled, rcond=1.0e-12, hermitian=True)
sigma2 = training_rss / 16
covariance = sigma2 * unit_covariance / np.outer(column_norms, column_norms)
standard_errors = np.sqrt(np.diag(covariance))
correlation = np.clip(covariance / np.outer(standard_errors, standard_errors), -1.0, 1.0)
test_scaled = native_jacobian(test_x, parameters) / column_norms
prediction_variances = sigma2 * np.einsum("ij,jk,ik->i", test_scaled, unit_covariance, test_scaled)
prediction_sd = np.sqrt(np.maximum(prediction_variances, 0.0))
```

输出每折原始／缩放奇异值、数值秩、列范数、参数标准误、相关矩阵、最大非对角相关绝对值、留出点局部预测标准差和逐折参数最小值／最大值／中位数。明确 `local_linearization=True`、`calibrated_interval=False`、`global_identifiability=False`。

- [ ] **Step 5: 生成图并验证新旧结果**

Run: `python scripts/analyze_roszman1_native_identifiability.py`

Expected: 生成五折诊断 JSON 和真实 PNG；`validate_summary` 返回空列表。

Run: `python -m unittest tests.test_roszman1_native_identifiability tests.test_roszman1_native_holdout -v`

Expected: 全部 PASS，旧原生结果哈希不变。

```bash
git add scripts/analyze_roszman1_native_identifiability.py tests/test_roszman1_native_identifiability.py validation/roszman1-native-identifiability.json papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png
git commit -m "research: diagnose Roszman1 native parameter stability"
git push origin main
```

---

### Task 3: 第三十三阶段原生图文报告

**Files:**
- Create: `docs/ROSZMAN1_NATIVE_IDENTIFIABILITY_2026-11-09.md`
- Create: `scripts/build_frontier_roszman1_native_identifiability_word.py`
- Create: `tests/test_frontier_roszman1_native_identifiability_word.py`
- Create: `papers/前沿共生Roszman1原生参数可识别性_图文完整版.docx`
- Create: `validation/frontier-roszman1-native-identifiability-word.json`
- Modify: `scripts/build_frontier_word.py`

**Interfaces:**
- Consumes: Task 2 的冻结 JSON 与 PNG。
- Produces: `REPORT_MODE="roszman1_native_identifiability"`、一幅实际图、四个 Word 表格、两个 OMML 公式、目录和页码。

- [ ] **Step 1: 写报告失败测试**

测试必须断言实际图哈希一致、`EXPECTED={"math":2,"images":1,"tables":4}`，并检查报告同时包含“预测稳定不等于参数唯一”“局部线性化”“不是概率区间”和五折实际指标，禁止出现“已证明全局可识别”。

- [ ] **Step 2: 运行测试确认构建器缺失**

Run: `python -m unittest tests.test_frontier_roszman1_native_identifiability_word -v`

Expected: FAIL，`Missing native identifiability Word builder`。

- [ ] **Step 3: 新增独立报告模式**

```python
if REPORT_MODE == "roszman1_native_identifiability":
    replacements = {
        "图：`papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png`。": "![](papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png)\n\n**图 40｜Roszman1 原生参数局部可识别性与稳定性（第 1 幅，共 1 幅）**  \n**插入位置**：§5「图件与解释边界」；顺序第 1 幅，共 1 幅。",
    }
    subtitle = "五折解析雅可比、参数稳定性与局部预测敏感度"
elif REPORT_MODE == "roszman1_native_holdout":
    replacements = {
        "图：`papers/39_Roszman1原生反正切对照/fig39_roszman1_native_holdout.png`。": "![](papers/39_Roszman1原生反正切对照/fig39_roszman1_native_holdout.png)\n\n**图 39｜Roszman1 原生反正切与有理候选同折对照（第 1 幅，共 1 幅）**  \n**插入位置**：§5「图件与模型族解释」；顺序第 1 幅，共 1 幅。",
    }
    subtitle = "相同 25 个留出点、五折模型族对照与原生证明边界"
```

报告必须将 NIST 已知答案、局部诊断、概率区间和物理内生性分成不同证据等级。

- [ ] **Step 4: 构建并验收 Word**

Run: `python scripts/build_frontier_roszman1_native_identifiability_word.py`

Expected: OOXML／OPC 通过；一幅原图、四个表格、两个原生公式；没有视觉渲染时明确记录，不称为视觉验收。

Run: `python -m unittest tests.test_frontier_roszman1_native_identifiability_word -v`

Expected: 全部 PASS。

---

### Task 4: 证据图谱、入口与完整交付

**Files:**
- Modify: `scripts/export_evidence_packet.py`
- Modify: `scripts/build_frontier_knowledge_graph.py`
- Modify: `tests/test_expansion.py`
- Modify: `tests/test_knowledge_graph.py`
- Create: `tests/test_roszman1_native_identifiability_integration.py`
- Modify: `README.md`
- Modify: `docs/UPSTREAM_INTERFACES.md`

**Interfaces:**
- Consumes: Task 2 和 Task 3 的全部输出。
- Produces: 新证据 `roszman1-native-identifiability`，以及“局部秩不等于全局可识别性”“预测稳定不等于参数唯一”的主张—反例—协议—限制链。

- [ ] **Step 1: 先写证据与图谱失败测试**

证据测试断言五折、20／5 点、无重拟合、参数与原生冻结结果一致、无概率区间或全局可识别性主张。图谱测试断言新证据同时连接原生对照、NIST 已知答案、协议和限制节点；更新累计计数前先运行并确认失败。

- [ ] **Step 2: 生成证据和图谱并联调**

Run: `python scripts/export_evidence_packet.py`

Run: `python scripts/build_frontier_knowledge_graph.py --extend`

Run: `python -m unittest tests.test_roszman1_native_identifiability_integration tests.test_knowledge_graph -v`

Expected: 全部 PASS，无悬空边或缺失来源文件。

- [ ] **Step 3: 全量验证**

Run: `python -m unittest discover -s tests`

Run: `python scripts/validate_extreme_reporting.py --check`

Run: `python scripts/validate_extreme_reporting_v2.py --check`

Run: `python scripts/validate_extreme_corpus.py --check`

Run: `python scripts/export_evidence_packet.py --check`

Run: `python scripts/build_catalog.py --check`

Expected: 全部 PASS；旧原生拟合、旧有理覆盖、九组与十组结果均未改变。

- [ ] **Step 4: 敏感信息、差异、提交和远端核验**

运行敏感信息扫描和 `git diff --check -- . ':(exclude)data/*.dat' ':(exclude)docs/*.md'`，确认无令牌、无意外空白错误后：

```bash
git add -A
git commit -m "research: report Roszman1 native parameter stability"
git push origin main
git ls-remote origin main
git status --short
```

Expected: 远端哈希与本地一致，工作区干净；长期研究目标保持开放，不标记为全部完成。
