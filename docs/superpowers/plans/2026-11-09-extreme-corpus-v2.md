# Extreme Corpus V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将极值相关报告全集分级从 16 份扩展到第三十五阶段的 23 份，保留旧协议、原文、旧验证器和旧收据，并交付新版机器验收、图谱和原生图文报告。

**Architecture:** 新建 `extreme-corpus-v2-audit.json` 作为冻结清单，以独立验证器检查 12 份联读、7 份描述、4 份完整及逐文件哈希。新报告只约束阅读方式，不批量改写历史；新图、Word、证据和图谱均使用 v2 路径，避免破坏旧结果自身哈希。

**Tech Stack:** JSON、Python、unittest、Matplotlib、既有 Pandoc／python-docx／OOXML 流水线。

## Global Constraints

- 在当前 `main` 内联执行，用户已授权直接修改、提交和推送，不创建工作树或子代理。
- 旧 `validation/extreme-corpus-audit.json`、`validation/extreme-corpus-check.json`、`scripts/validate_extreme_corpus.py` 和 16 份原文不改写。
- 新版总数固定为 23：`companion_required=12`、`descriptive_only=7`、`complete=4`；旧 10 份冻结联读原文必须保持字节一致。
- `docs/UPSTREAM_INTERFACES.md` 持续更新，故其 `original_sha256=null`；其余 22 份按冻结时哈希验收，后续变更必须另立版本。
- 分级不等于物理真实性证明；`complete` 只表示该文档包含其主张所需证据和限制。
- 所有 Bash 调用使用中文、通俗、约 8—10 字的 `description`。

---

### Task 1: 冻结 23 份文档的分级清单

**Files:**
- Create: `validation/extreme-corpus-v2-audit.json`
- Create: `docs/superpowers/plans/2026-11-09-extreme-corpus-v2.md`

**Interfaces:**
- Consumes: 旧 16 份清单和当前文档哈希。
- Produces: `frozen_extreme_corpus_v2_classification`、23 项文档记录、历史协议／收据哈希、必需联读文件和保留文本。

- [ ] **Step 1: 写明分类与数量**

新版沿用旧 16 项分级，新增：

```json
[
  {"file": "docs/ROSZMAN1_COVERAGE_2026-11-09.md", "claim_level": "distribution_summary", "review_status": "companion_required"},
  {"file": "docs/BOUND_COMPARISON_V5_2026-11-09.md", "claim_level": "distribution_summary", "review_status": "companion_required"},
  {"file": "docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md", "claim_level": "mechanism_interpretation", "review_status": "complete"},
  {"file": "docs/ROSZMAN1_NATIVE_HOLDOUT_2026-11-09.md", "claim_level": "maximum_only", "review_status": "descriptive_only"},
  {"file": "docs/ROSZMAN1_NATIVE_IDENTIFIABILITY_2026-11-09.md", "claim_level": "mechanism_interpretation", "review_status": "complete"},
  {"file": "docs/ENSO_NATIVE_HOLDOUT_2026-11-09.md", "claim_level": "maximum_only", "review_status": "descriptive_only"},
  {"file": "docs/CHWIRUT1_NATIVE_HOLDOUT_2026-11-09.md", "claim_level": "maximum_only", "review_status": "descriptive_only"}
]
```

清单必须同时记录：

```json
{
  "status": "frozen_extreme_corpus_v2_classification",
  "document_count": 23,
  "companion_required_count": 12,
  "complete_count": 4,
  "descriptive_only_count": 7,
  "corpus_document": "docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md",
  "required_companions": [
    "docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md",
    "docs/EXTREME_REPORTING_PROTOCOL.md",
    "docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md"
  ],
  "required_preservation_text": "原始 Markdown 与旧 Word 均不改写",
  "previous_document_count": 16,
  "previous_frozen_companion_original_count": 10
}
```

- [ ] **Step 2: 冻结历史协议和当前文件哈希**

历史协议和收据分别为 `validation/extreme-corpus-audit.json` SHA-256 `a592ddf56e6dfb590c2beaf6bc407fd94fd09be71f58929f6719cda045472c6f`、`validation/extreme-corpus-check.json` SHA-256 `79d095887b24939c44e9cfb9afce8c4875cb2a05f007d120e472ab84a3b2e4ef`。

22 份非接口文档记录当前哈希；`docs/UPSTREAM_INTERFACES.md` 使用 `original_sha256=null`，避免入口更新造成循环失效。清单不得包含计划文件、脚本、Word 或本新版报告自身。

- [ ] **Step 3: 校验 JSON 并先推送清单**

Run: `python -c "import json; p=json.load(open('validation/extreme-corpus-v2-audit.json',encoding='utf-8')); assert len(p['documents'])==23; print('OK: 23-document corpus frozen')"`

Run: `python -m unittest tests.test_extreme_corpus -v`

Expected: 旧 16 份测试全部 PASS，新清单尚未运行验证器。

```bash
git add validation/extreme-corpus-v2-audit.json docs/superpowers/plans/2026-11-09-extreme-corpus-v2.md
git commit -m "research: freeze 23-document extreme corpus classification"
git push origin main
```

---

### Task 2: 独立验证器与全集补充报告

**Files:**
- Create: `scripts/validate_extreme_corpus_v2.py`
- Create: `tests/test_extreme_corpus_v2.py`
- Create: `docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md`
- Create: `validation/extreme-corpus-v2-check.json`

**Interfaces:**
- Consumes: Task 1 清单与原文。
- Produces: `validate_corpus(corpus_text=None) -> list[str]`、`build_check() -> dict`、`--check` 防陈旧收据。

- [ ] **Step 1: 写验证器失败测试**

```python
def test_23_documents_have_expected_classes():
    module = load_validator()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert len(spec["documents"]) == 23
    assert sum(item["review_status"] == "companion_required" for item in spec["documents"]) == 12
    assert sum(item["review_status"] == "descriptive_only" for item in spec["documents"]) == 7
    assert sum(item["review_status"] == "complete" for item in spec["documents"]) == 4
    assert module.validate_corpus() == []
```

另写：空文本拒绝所有联读文档；旧 10 份哈希不变；新增 7 份分类准确；缺失文件、篡改哈希和缺联读路径均被拒绝；最终 `build_check()` 与收据一致。

Run: `python -m unittest tests.test_extreme_corpus_v2 -v`

Expected: FAIL，`Missing v2 corpus validator`。

- [ ] **Step 2: 实现独立验证器**

```python
def validate_corpus(corpus_text=None):
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if corpus_text is None:
        corpus_path = ROOT / spec["corpus_document"]
        corpus_text = corpus_path.read_text(encoding="utf-8") if corpus_path.is_file() else ""
    errors = []
    documents = spec["documents"]
    if len(documents) != 23:
        errors.append("Expected 23 documents")
    for item in documents:
        path = ROOT / item["file"]
        if not path.is_file():
            errors.append(f"Missing reviewed document: {item['file']}")
            continue
        if item["file"] not in corpus_text:
            errors.append(f"Corpus does not classify {item['file']}")
        if item["review_status"] not in corpus_text:
            errors.append(f"Corpus missing review status for {item['file']}")
        if item["original_sha256"] is not None and sha256(path) != item["original_sha256"]:
            errors.append(f"Document hash changed: {item['file']}")
    for companion in spec["required_companions"]:
        if companion not in corpus_text:
            errors.append(f"Corpus missing companion: {companion}")
    if spec["required_preservation_text"] not in corpus_text:
        errors.append("Corpus does not preserve original Markdown and old Word")
    return errors
```

收据必须包含总数、三类数量、23 份哈希匹配数、旧 10 份原文未变数、错误列表、全集文档／清单／验证器哈希、历史协议／收据哈希和 `previous_files_preserved=true`。`--check` 必须拒绝陈旧收据，首次生成拒绝覆盖。

- [ ] **Step 3: 写全集补充报告并验收**

报告必须逐一列出 23 份文档及理由，明确新增 2 份联读、2 份完整、3 份描述，保留原文和历史收据。全文出现精确保留句“原始 Markdown 与旧 Word 均不改写”，并链接三份必需联读文档。

Run: `python scripts/validate_extreme_corpus_v2.py`

Run: `python scripts/validate_extreme_corpus_v2.py --check`

Run: `python -m unittest tests.test_extreme_corpus_v2 tests.test_extreme_corpus -v`

Expected: 全部 PASS，错误数为 0，旧验证器与旧收据不变。

```bash
git add scripts/validate_extreme_corpus_v2.py tests/test_extreme_corpus_v2.py docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md validation/extreme-corpus-v2-check.json
git commit -m "research: validate expanded extreme report corpus"
git push origin main
```

---

### Task 3: 分级图、原生 Word 与证据交付

**Files:**
- Create: `scripts/build_extreme_corpus_v2_figure.py`
- Create: `papers/43_极值全集分级V2/fig43_extreme_corpus_v2.png`
- Create: `scripts/build_frontier_extreme_corpus_v2_word.py`
- Create: `tests/test_frontier_extreme_corpus_v2_word.py`
- Create: `papers/前沿共生极值报告全集分级V2_图文完整版.docx`
- Create: `validation/frontier-extreme-corpus-v2-word.json`
- Create: `tests/test_extreme_corpus_v2_integration.py`
- Modify: `scripts/build_frontier_word.py`
- Modify: `scripts/export_evidence_packet.py`
- Modify: `scripts/build_frontier_knowledge_graph.py`
- Modify: `README.md`
- Modify: `docs/UPSTREAM_INTERFACES.md`

**Interfaces:**
- Consumes: Task 2 清单和收据。
- Produces: 一幅实际分级图、四个 Word 表格、两个 OMML 公式、证据 `extreme-corpus-v2-classification` 和图谱实验 `experiment-extreme-corpus-v2-classification`。

- [ ] **Step 1: 生成真实分级图**

图一为旧 16 与新 23 的三类计数对照，图二为新增 7 份文档的分类计数；标题必须显示 `12 companion / 7 descriptive / 4 complete`，不能把旧 16 的计数写成当前全集。

Run: `python scripts/build_extreme_corpus_v2_figure.py`

Expected: 生成真实 PNG，三类数量与清单一致。

- [ ] **Step 2: 写 Word 失败测试并构建**

测试检查图哈希、2 个公式、4 个表格、23／12／7／4、旧 10 份哈希保持、三份必需联读和禁用“新证据改写旧结论”。先确认构建器缺失，再添加 `REPORT_MODE="extreme_corpus_v2"`。

Run: `python scripts/build_frontier_extreme_corpus_v2_word.py`

Run: `python -m unittest tests.test_frontier_extreme_corpus_v2_word -v`

Expected: OOXML／OPC 与测试全部 PASS；无视觉渲染时明确披露。

- [ ] **Step 3: 接入证据与图谱**

证据指标包含 23 份分类、23 份哈希匹配、旧 10 份原文未变、错误数 0、历史协议／收据哈希和报告验收哈希。图谱新增一个实验节点及三条边：知识主线包含、检验知识完整性、旧全集实验支持新版实验；累计计数测试先失败再更新。

Run: `python scripts/export_evidence_packet.py`

Run: `python scripts/build_frontier_knowledge_graph.py --extend`

Run: `python -m unittest tests.test_extreme_corpus_v2_integration tests.test_knowledge_graph -v`

Expected: 全部 PASS，无悬空边。

- [ ] **Step 4: 全量复验、提交与远端核验**

Run: `python -m unittest discover -s tests`

Run: `python scripts/validate_extreme_reporting.py --check`

Run: `python scripts/validate_extreme_reporting_v2.py --check`

Run: `python scripts/validate_extreme_corpus.py --check`

Run: `python scripts/validate_extreme_corpus_v2.py --check`

Run: `python scripts/export_evidence_packet.py --check`

Run: `python scripts/build_catalog.py --check`

Expected: 全部 PASS。敏感信息扫描和差异格式检查通过后：

```bash
git add -A
git commit -m "research: report expanded extreme corpus classification"
git push origin main
git ls-remote origin main
git status --short
```

Expected: 远端与本地一致，工作区干净，长期研究目标保持开放。
