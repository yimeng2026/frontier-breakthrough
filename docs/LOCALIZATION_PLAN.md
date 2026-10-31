# D 盘本地化、适配与验证记录

核查日期：2026-10-31

## 资源与安装原则

- C 盘约 300 GB，检查时可用了约 3.8 GB；D 盘约 626 GB，可用约 324 GB。环境、包缓存和临时目录因此放到 `D:\research-engines`。
- 本机可用 Python 3.12.16、Git 2.47.1、Node 24.21.0；本次 PATH 检查未发现 Docker、Conda、Julia、CMake、Java 或 `nvidia-smi`。未发现命令不等于硬件绝对不存在，重任务启动前需再次核实。
- 不为“项目齐全”下载全部模型。大模型、自动实验、大科学装置与国家实验室保留为外部复用或战略协作对象。
- 环境和缓存不提交 Git；只提交运行脚本、依赖锁定和不含敏感信息的验证结果。

## 首批实际落地

| 引擎 | 安装位置 | 版本 | 实际结果 | 证据边界 |
|---|---|---|---|---|
| PySINDy | `D:\research-engines\pysindy-env` | 2.1.0 | 对 `x'=-2x, y'=y` 恢复 `x'=-2.00003136x`、`y'=1.00000404y`，非对角项为 0 | 已知合成系统的引擎验证，不是新物理规律 |
| Z3 | `D:\research-engines\z3-env` | 5.3.3.0 | `x>0 ∧ x+1≤0` 为 UNSAT；`x²<0` 为 UNSAT | 两个实数约束的已知答案，不是通用定理证明 |
| RDKit | `D:\research-engines\rdkit-env` | 2026.9.1 | 乙酰唑胺规范结构与 PubChem CID 1986 一致，分子式 `C4H6N4O3S2`，精确质量差小于 `1e-6 Da` | 数据库计算属性对照，不是湿实验验证 |
| PyMatGen | `D:\research-engines\pymatgen-env` | 2026.10.24 | 从 Materials Project 的 Si 公开结构重算密度 `2.3128002566 g/cm³` 和空间群 `Fd-3m (227)` | 结构派生量复核；DFT 带隙和稳定性未在本地重算 |

锁定依赖快照保存在仓库 `requirements/`，原始冻结文件也在 `D:\research-engines\*-requirements.txt`。环境会随验证需求增长，静态文档不固定总磁盘占用。

## 重跑命令

在项目根目录执行：

```bash
D:\research-engines\pysindy-env\Scripts\python.exe scripts\verify_pysindy.py
D:\research-engines\z3-env\Scripts\python.exe scripts\verify_z3.py
D:\research-engines\rdkit-env\Scripts\python.exe scripts\verify_rdkit.py
D:\research-engines\pymatgen-env\Scripts\python.exe scripts\verify_pymatgen.py
python scripts\verify_pdb_uniprot.py
```

机器可读结果位于 `validation/pysindy.json`、`validation/z3.json`、`validation/rdkit.json`、`validation/pymatgen.json` 和 `validation/pdb-uniprot.json`。外部原始快照使用对应数据源名称单独保存，不与本地计算结果混写。

## 化学数据核对示范

输入 SMILES 经 PubChem 解析为 CID 1986；本地与数据库的规范结构、分子式一致。

- RDKit 默认 TPSA 为 **115.04 Å²**，启用 `includeSandP=True` 后为 **151.66 Å²**；PubChem 快照为整数 **152**。按相同整数显示精度一致，说明比较时必须记录 S/P 口径与舍入。
- RDKit Crippen MolLogP 为 **−0.8561**，PubChem XLogP 为 **−0.3**。这是不同算法的输出，不能预设二者相等，也不能凭差异指认数据造假。
- 本地精确质量为 **221.988132052 Da**，PubChem 为 **221.98813241 Da**，绝对差约 **3.58×10⁻⁷ Da**。

这个案例的意义是形成“结构归一—算法口径—单位—来源—精度”的审计链，而不是证明某个值在所有软件中必须相同。

## 失败与修复记录

1. 初始 pip 镜像没有返回三个包的候选版本；改用官方 `https://pypi.org/simple` 后安装成功。未把镜像问题误报为项目不存在。
2. PySINDy 2.1.0 默认库产生 6 个特征，第一次形状断言失败；显式使用无偏置、无交互的一次多项式库后完成验证。数值微分仍有约 `3.14×10⁻⁵` 最大系数误差，未宣称精确恢复。
3. 化学验证先遇到 TPSA 预设差异，随后又发现两种 LogP 算法差异；最终保留所有原始数值，取消不合理的等价断言，而不是篡改计算结果。

## 下一阶段门槛

1. **真实规律辨识**：选择有公开出处和独立切分的数据；PySINDy、PySR/AI Feynman 共享基线，只有跨条件验证后才讨论规律。
2. **形式化**：Lean/LeanDojo 需要工具链与版本匹配；先选一个小定理，不承诺本地构建整个 OpenAI 数学仓库。
3. **材料与物理**：先安装 PyMatGen 等轻量接口，连接 Materials Project；CP2K、Quantum ESPRESSO 和 GPU 框架等重工具须另有构建/算力环境。
4. **生物**：优先公开数据的 Biopython/RDKit 小验证；大模型权重、蛋白设计和虚拟细胞训练不因目录收录而自动下载。
5. **回馈上游**：只有在真实复现中发现可重复的问题，才提交带版本和日志的 issue；通用适配先作为独立插件，尊重原项目许可证。
