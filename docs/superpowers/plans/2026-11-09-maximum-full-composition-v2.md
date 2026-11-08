# 十组最大界与全点组成新版审计实施计划

**日期**：2026-11-09  
**执行位置**：`frontier-breakthrough` 当前 `main`；用户已明确允许直接修改、提交和推送，不创建工作树或子代理。

## 目标与保留义务

在 `exports/internal-external-bound-comparison-v5.json` 上新增十组只读事后审计，分开报告最大点类别、全点中位占比、描述性百分位和最大／中位界宽比。保留九组协议、脚本、结果、图、Markdown、Word、验收收据及其哈希，不把九组结论改写为十组结论。

## 已审查的兼容风险

- 旧 `build_maximum_full_composition_audit.py` 把 `8/9 match` 和 `6 below` 写进图题，并把自身 SHA-256 写入旧结果；直接修改会破坏历史复验。
- 新版使用独立包装器，临时向未修改的旧分析函数提供新协议后立即恢复全局状态；新图由新版包装器按实际计数生成动态标题。
- 旧三级验收规则是数据数量无关的，可以原样复用；新版另写验收收据，不覆盖 `extreme-reporting-check.json`。
- 这是事后描述性审计，不是概率代表性、物理因果、独立实验或原生 Roszman1 模型验证。

## 任务 1：冻结并推送十组审计协议

1. 新建 `validation/maximum-full-composition-v2-protocol.json`，冻结输入 `exports/internal-external-bound-composition-v5.json` 及 SHA-256 `e5681ed6dc7f55b53704ec4fb75f0d43043288e36cfcad381eaa010256177190`。
2. 预写验收数：10 组、9 组最大点类别与多数一致、仅 Gauss1 不一致、9 组最大点平移主导、仅 ENSO 最大点实际残差主导、6 组最大点占比低于中位、4 组高于中位，最大界宽比仍属 Gauss1。
3. 冻结 Roszman1 检查：5 个可用点、最大点占比 0.9978338090532987、中位占比 0.9933691737124666、描述性百分位 1.0、界宽比 1.2203221902706693。
4. 在任何新版分析代码执行前，运行 JSON 与旧测试检查，单独提交并推送协议。

## 任务 2：先失败测试，再实现十组审计

1. 新建 `tests/test_maximum_full_composition_v2_audit.py`，先确认因缺少新版构建器而失败。
2. 测试总数、反例名单、Roszman1 数值、旧九组输出不变、动态图题、真实 PNG 和拒绝过度解释。
3. 新建 `scripts/build_maximum_full_composition_audit_v2.py`；旧脚本保持逐字节不变。
4. 输出 `exports/maximum-full-composition-audit-v2.json` 和 `papers/38_十组最大界与全点组成/fig38_maximum_full_composition_v2.png`，拒绝覆盖。
5. 运行新旧测试，检查生成图，提交并推送机器结果。

## 任务 3：独立验收新版三级契约

1. 先写失败测试，覆盖 L0、L1、L2、伪造典型性主张和数值篡改的拒绝行为。
2. 新建 `scripts/validate_extreme_reporting_v2.py`，复用不变的 `validate_report` 和规则文件，输出 `validation/extreme-reporting-v2-check.json`。
3. 验证收据记录十组、L2、零错误、新版报告哈希和规则哈希；旧收据保持不变。

## 任务 4：生成第三十一阶段原生图文报告

1. 新建 `docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md`，与九组报告分开，保留所有反例和范围限制。
2. 先写 Word 失败测试，再新增 `scripts/build_frontier_maximum_full_composition_v2_word.py` 和 `maximum_full_composition_v2` 报告分支。
3. 新 Word 使用一幅十组三联原图、四个原生表格、两个原生 OMML 公式，含目录、页眉和页码。
4. 通过 OOXML／OPC 结构验证；没有视觉渲染时明确记录，不称为视觉验收。

## 任务 5：接入证据、图谱与入口并全量交付

1. 证据包新增十组审计条目，图谱新增证据、反例、协议和限制节点；更新计数测试前先确认正确失败。
2. 更新 `README.md` 和 `docs/UPSTREAM_INTERFACES.md`，保留九组历史链接。
3. 运行全量单元测试、两级极值收据检查、全集分级检查、证据包和目录一致性检查。
4. 核对新旧协议、输入、脚本、结果、图和 Word 哈希，执行敏感信息扫描及 `git diff --check`。
5. 提交并推送，使用 `git ls-remote origin main` 核对远端，不将长期研究目标标记为完成。
