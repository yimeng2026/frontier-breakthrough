# OpenAI 与指数时间假说：证据状态和行动边界

核查日期：2026-10-31

## 结论

OpenAI 公开材料称其模型在 2026-10-16 得到关于 3-SAT 的自然语言反驳，10-17 完成 Lean 形式化，并公开了原始研究材料。Russell Impagliazzo、Ramamohan Paturi、Ryan Williams 组织公开审查，但相关页面同时强调参与不等于认证。

因此当前最稳妥的表述是：**这是高重要性的证伪候选，具有公开形式化材料，仍不能替代独立审查和学术共同体验证。**

## 它不等于什么

- 不等于 P＝NP；指数时间假说的失败本身不提供多项式时间算法。
- 不等于所有 NP 问题突然易于工程求解；渐近上界、常数、参数范围和可实现性是不同问题。
- 不等于现实密码系统立即失效；安全性还取决于具体构造、参数、攻击模型和实际成本。
- 不等于“数学直觉失效”或“数学不再是最简语言”；它首先改变的是一个复杂性假设的证据状态。
- 不等于 OpenAI 仓库内所有结果都已完成同行评议或 Lean 验证。

## 可计算主张的边界

项目 `preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/README.md` 是原始主张的入口；`lean/docs/378.md` 是形式化材料入口。公开 overview 给出的方向是固定 `k≥2` 时对 `k`-CNF 满足赋值计数的次指数时间界，指数包含 `n/(log n)^(1/2+o(1))`。此处只转述其主张，不在未独立构建 Lean、复核依赖和公理边界时声称我们验证了定理。

## 对我们的方法启发

1. **证明成本不是数学层级的普适定律**：自动证明可能改变搜索和验证成本，但不能推出“层级越高、费用按某固定函数增长”。
2. **形式化与解释要分工**：Lean 可检查形式推导，不自动决定物理意义、现实对应或科学重要性。
3. **公开反例比立场更有用**：若候选反驳经审查成立，应更新依赖该假设的下界表述；若失败，应公开反例所在，而非维护立场。
4. **真正的配合方式**：做小范围可重放检查、依赖清单、术语对照和反例测试；不重复宣布“我们也推翻 ETH”。

## 行动清单

- 跟踪 OpenAI 原始仓库、形式化文件和公开审查者的后续意见。
- 后续在有 Lean 工具链时选择一个小文件独立构建，记录版本和全部警告。
- 检查本研究文本是否把 ETH 当成已成立前提；有则改成条件句。
- 不将模型产出、验证时长或算力账单直接换算成数学真理等级。

## 原始来源

- OpenAI 学术共同体说明：https://openai.com/index/building-scientific-understanding-with-academic-communities/
- OpenAI 数学原始材料：https://github.com/openai/math
- ETH 候选反驳目录：https://github.com/openai/math/tree/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026
- 形式化入口：https://github.com/openai/math/blob/main/lean/docs/378.md
