# Repository Integrity Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立全仓库一致性审计，自动检查本地链接、报告图片、Word 清单哈希、证据图谱、全集计数和近期协议输入，并交付可重复验收、问题报告与原生 Word。

**Architecture:** 以 `validation/repository-integrity-rules.json` 冻结检查范围和阈值，以独立脚本生成结构化报告。检查只针对可机器验证的事实，不将历史文本中的旧计数简单判为错误；动态计数同时核对 JSON 与 README，避免固定数字再次过期。

**Tech Stack:** Python 标准库、unittest、JSON、Matplotlib、既有 Pandoc／python-docx／OOXML 流水线。

## Global Constraints

- 在当前 `main` 内联执行，用户已授权直接修改、提交和推送，不创建工作树或子代理。
- 旧报告、旧协议、旧清单和旧 Word 不改写；发现真实漂移时先记录，再按新版本修复。
- 不联网核验外部来源，不将本地结构一致性误称为科学真实性、视觉验收或独立实验。
- 所有 Bash 调用使用中文、通俗、约 8—10 字的 `description`。

---

### Task 1: 冻结审计规则与失败测试

**Files:**
- Create: `validation/repository-integrity-rules.json`
- Create: `docs/superpowers/plans/2026-11-09-repository-integrity-audit.md`
- Create: `tests/test_repository_integrity.py`

**Interfaces:**
- Consumes: README、`docs/*.md`、`validation/*word.json`、证据包、知识图谱、全集清单及近期协议。
- Produces: `frozen_repository_integrity_audit` 规则、检查组、最小链接数和协议输入清单。

- [ ] **Step 1: 冻结检查范围**

```json
{
  "status": "frozen_repository_integrity_audit",
  "readme": {"minimum_local_links": 84},
  "figures": {"minimum_document_links": 44},
  "word_manifests": {"minimum_count": 36},
  "corpus_v2": {"documents": 23, "companion_required": 12, "descriptive_only": 7, "complete": 4, "non_null_hashes": 22, "historical_originals": 10},
  "protocols": [
    "validation/external-bound-decomposition-v5-protocol.json",
    "validation/internal-external-bound-comparison-v5-protocol.json",
    "validation/maximum-full-composition-v2-protocol.json",
    "validation/roszman1-native-holdout-protocol.json",
    "validation/roszman1-native-identifiability-protocol.json",
    "validation/enso-native-holdout-protocol.json",
    "validation/enso-native-holdout-protocol-amendment-01.json",
    "validation/chwirut1-native-holdout-protocol.json",
    "validation/chwirut1-native-holdout-protocol-amendment-01.json",
    "validation/extreme-corpus-v2-audit.json"
  ],
  "decision": {"external_web_checked": false, "visual_qa_claimed": false, "scientific_truth_claimed": false}
}
```

- [ ] **Step 2: 写审计失败测试**

```python
def test_repository_audit_is_clean():
    module = load_audit_module()
    report = module.audit()
    assert report["error_count"] == 0, report["errors"]
    assert report["groups"]["readme_local_links"]["count"] >= 84
    assert report["groups"]["document_figure_links"]["count"] >= 44
    assert report["groups"]["word_manifests"]["count"] >= 36
    assert report["groups"]["protocol_inputs"]["count"] == 10


def test_broken_readme_link_is_detected():
    module = load_audit_module()
    report = module.audit(readme_text="# [broken](docs/missing-file.md)")
    assert any("Broken README link" in error for error in report["errors"])
```

另写 Word 清单篡改、图谱悬空边、计数不一致和最终 `audit()==stored_report` 测试。

- [ ] **Step 3: 确认测试因实现缺失而失败**

Run: `python -m unittest tests.test_repository_integrity -v`

Expected: FAIL，`Missing repository integrity audit`。

- [ ] **Step 4: 先推送规则与计划**

Run: `python -c "import json; p=json.load(open('validation/repository-integrity-rules.json',encoding='utf-8')); print(p['status'])"`

Expected: `frozen_repository_integrity_audit`。

```bash
git add validation/repository-integrity-rules.json docs/superpowers/plans/2026-11-09-repository-integrity-audit.md
git commit -m "research: freeze repository integrity audit rules"
git push origin main
```

---

### Task 2: 实现结构化审计与负例拒绝

**Files:**
- Create: `scripts/audit_repository_integrity.py`
- Create: `validation/repository-integrity-report.json`
- Modify: `tests/test_repository_integrity.py`

**Interfaces:**
- Consumes: Task 1 规则和仓库文件。
- Produces: `audit(readme_text=None) -> dict`、`audit_docx_manifest(path) -> list[str]`、`main() -> None`、`--check` 防陈旧报告。

- [ ] **Step 1: 实现链接与图片检查**

README 链接使用 `re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)`，跳过含 URI scheme 的目标，逐一检查相对路径存在。报告图片使用逐行 `line.startswith("图：")` 和 `re.findall(r"`([^`]+)`", line)` 提取路径，检查文件存在；不处理计划目录中的代码示例。

- [ ] **Step 2: 实现 Word、证据与协议检查**

`audit_docx_manifest` 必须检查 `status=="passed"`、`papers/<file>` 存在、实际字节数和 SHA-256 与清单一致。证据包检查 `snapshotFiles` 存在；图谱检查节点 ID 唯一、来源文件存在、边无悬空；README 图谱数字与 JSON 当前数量一致；证据项中文数量与 JSON 当前数量一致。

协议只遍历 `inputs`、`input`、`original_protocol`、`previous_spec`、`previous_check`，检查其中 `file` 与 `sha256` 对应文件存在且哈希一致，不检查旧实现哈希，避免把允许的历史包装器变化误判为数据漂移。

- [ ] **Step 3: 生成报告并运行负例**

Run: `python scripts/audit_repository_integrity.py`

Expected: 生成 `validation/repository-integrity-report.json`，错误数 0，包含各组计数和 `external_web_checked=false`、`visual_qa_claimed=false`、`scientific_truth_claimed=false`。

Run: `python -m unittest tests.test_repository_integrity -v`

Expected: 全部 PASS；损坏链接、Word 哈希篡改、悬空边和计数漂移均被拒绝。

```bash
git add scripts/audit_repository_integrity.py tests/test_repository_integrity.py validation/repository-integrity-report.json
git commit -m "research: implement repository integrity audit"
git push origin main
```

---

### Task 3: 第三十七阶段报告、图件与证据交付

**Files:**
- Create: `docs/REPOSITORY_INTEGRITY_2026-11-09.md`
- Create: `scripts/build_repository_integrity_figure.py`
- Create: `papers/44_仓库完整性审计/fig44_repository_integrity.png`
- Create: `scripts/build_frontier_repository_integrity_word.py`
- Create: `tests/test_frontier_repository_integrity_word.py`
- Create: `papers/前沿共生仓库完整性审计_图文完整版.docx`
- Create: `validation/frontier-repository-integrity-word.json`
- Create: `tests/test_repository_integrity_integration.py`
- Modify: `scripts/build_frontier_word.py`
- Modify: `scripts/export_evidence_packet.py`
- Modify: `scripts/build_frontier_knowledge_graph.py`
- Modify: `README.md`
- Modify: `docs/UPSTREAM_INTERFACES.md`

**Interfaces:**
- Consumes: Task 2 的结构化报告。
- Produces: 一幅审计组图、四个 Word 表格、一个 OMML 哈希恒等式、证据 `repository-integrity-audit` 和图谱实验 `experiment-repository-integrity-audit`。

- [ ] **Step 1: 生成审计组图**

图包含本地链接、图片路径、Word 清单、证据快照、图谱来源和协议输入六组计数，标题显示实际通过数量与错误数 0，不将结构检查画成科学成功率。

Run: `python scripts/build_repository_integrity_figure.py`

Expected: 真实 PNG 和动态计数。

- [ ] **Step 2: 写 Word 失败测试并构建**

测试检查图哈希、1 个哈希恒等式、4 个表格、错误数 0、历史保留及 `visual_qa_claimed=false`。先确认构建器缺失，再添加 `REPORT_MODE="repository_integrity"`。

Run: `python scripts/build_frontier_repository_integrity_word.py`

Run: `python -m unittest tests.test_frontier_repository_integrity_word -v`

Expected: OOXML／OPC 和测试全部 PASS；无视觉渲染时明确披露。

- [ ] **Step 3: 接入证据和图谱**

证据包含各组计数、错误数 0、报告哈希和边界声明。图谱新增一个实验节点及三条边：知识主线包含、检验知识完整性、旧全集实验支持仓库审计；累计计数测试先失败再更新。

Run: `python scripts/export_evidence_packet.py`

Run: `python scripts/build_frontier_knowledge_graph.py --extend`

Run: `python -m unittest tests.test_repository_integrity_integration tests.test_knowledge_graph -v`

Expected: 全部 PASS，无悬空边。

- [ ] **Step 4: 全量复验与最终审计**

Run: `python -m unittest discover -s tests`

Run: `python scripts/audit_repository_integrity.py --check`

Run: `python scripts/validate_extreme_reporting.py --check`

Run: `python scripts/validate_extreme_reporting_v2.py --check`

Run: `python scripts/validate_extreme_corpus.py --check`

Run: `python scripts/validate_extreme_corpus_v2.py --check`

Run: `python scripts/export_evidence_packet.py --check`

Run: `python scripts/build_catalog.py --check`

Expected: 全部 PASS。敏感信息扫描和差异格式检查通过后：

```bash
git add -A
git commit -m "research: report repository integrity audit"
git push origin main
git ls-remote origin main
git status --short
```

Expected: 远端与本地一致，工作区干净，长期研究目标保持开放。
