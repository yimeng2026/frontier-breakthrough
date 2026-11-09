# Frontier Breakthrough · 前沿共生计划

以公开证据为入口、以可复现验证为基础、以真实回馈为目标的跨学科研究计划。我们不复制大科学装置，不把“收藏项目”当成“追赶”，也不以跨学科叙事代替实验。

## 工作方式

1. **先接上游**：保留原项目、作者、许可证和引用关系；能调用、复用、扩展的，不另造同名轮子。
2. **再做复核**：公开数据与合成基准先证明工具正确，再进入真实跨域验证；区分复现、适配与新发现。
3. **形成互补**：战略设施提供实验与算力，我们提供问题结构化、跨域对照、轻量验证、数据质量与可复现接口。
4. **最后回馈**：只有真实错误、可执行复现、基准和经许可证允许的改进才形成 issue 或 PR；不批量打扰维护者。

## 文件入口

- [项目章程](docs/PROJECT_CHARTER.md)：研究问题、协作边界、验收和退出条件。
- [全球项目与设施目录](docs/GLOBAL_PROJECTS.md)：由结构化数据生成，持续维护而非自称穷尽全球。
- [OpenAI 与 ETH 证据复核](docs/OPENAI_ETH_REVIEW.md)：候选反驳、形式化和独立审查的区别。
- [D 盘本地化与适配](docs/LOCALIZATION_PLAN.md)：轻量实跑、重任务门槛与运行记录。
- [定期消化机制](docs/RESEARCH_AUTOMATION.md)：检索—筛选—复现—回馈的闭环。
- [机器可读目录](data/projects.json)：每项均有官方来源、证据级别、协作角色和本地状态。
- [上游接口与证据契约](docs/UPSTREAM_INTERFACES.md)：真实跨库验证、统一 JSON 接口及组件边界。
- [跨域证据包](exports/frontier-evidence.json)：六十一项已执行检查的结构化结果与限制。
- [外部模型族限制文本修订审计](validation/external-scope-limitations-amendment-01-audit.json)：三份修订副本、原始文件与协议哈希、仅文档文本变更的完整记录。
- [五条主线扩展工作包](docs/EXPANSION_2026-11-08.md)：真实留出、形式化反例、化学跨库、材料跨库和知识图谱的首轮成果。
- [第二轮续展报告](docs/CONTINUATION_2026-11-08.md)：Eckerle4 双尾外推与 cvc5 交叉求解器复核。
- [第三阶段有理模型报告](docs/RATIONAL_2026-11-08.md)：Hahn1 高温外推与分母边界。
- [第四阶段压力测试报告](docs/STRESS_2026-11-08.md)：三个数据集共 15 折连续区间留出，保留 Hahn1 第 1 折失效与稳健性边界。
- [第五阶段失效机制报告](docs/MECHANISM_2026-11-08.md)：局部可识别性、第 1 折两个低温数值单极点及旧证明不可迁移的边界。
- [第六阶段 Thurber 前瞻验收](docs/PROSPECTIVE_2026-11-09.md)：新数据集四折通过、一折预测区极点与预测失败，保留整体未通过结论。
- [第七阶段 Kirby2 跨次数验收](docs/KIRBY2_2026-11-09.md)：二次有理模型五折均获有限支持，同时保留外推衰减和高条件数边界。
- [第八阶段跨数据集综合](docs/CROSS_DATASET_2026-11-09.md)：统一有理诊断内核，13／15 折符合验收，区分事后重建与数据集前瞻证据。
- [第九阶段精确区间根证明](docs/EXACT_ROOTS_2026-11-09.md)：有理系数 Sturm 根隔离、13 折 unsat、2 折 sat 及快照边界。
- [第十阶段参数盒稳定性](docs/BOX_STABILITY_2026-11-09.md)：连续参数盒无根证明，13 折正安全半径、11 折封顶、2 折有限半径括号。
- [第十一阶段参数盒预测界](docs/PREDICTION_BOUNDS_2026-11-09.md)：13 折 369 点精确保守上界，揭示无根不等于高精度。
- [第十二阶段协方差椭球比较](docs/ELLIPSOID_BOUNDS_2026-11-09.md)：同一半径下 369 点椭球上界全部收紧，保留区域与证据边界。
- [第十三阶段椭球连续区间证明](docs/ELLIPSOID_INTERVAL_2026-11-09.md)：13 折平方支撑连续安全，0 折未认证，2 折有根。
- [第十四阶段 Filip 外部覆盖](docs/FILIP_COVERAGE_2026-11-09.md)：候选模型五折均优于基线，82 点无越界，独立盒不适用。
- [第十五阶段可复用外部覆盖协议](docs/EXTERNAL_COVERAGE_2026-11-09.md)：通用驱动、MGH17 新数据对照与 115 点描述性汇总。
- [第十六阶段 Gauss1 外部反例](docs/GAUSS1_EXTERNAL_COVERAGE_2026-11-09.md)：250 点中 190 点可给界、60 点不可用，三数据对照保留预测失败与证据边界。
- [第十七阶段 Gauss1 界失效机制](docs/GAUSS1_BOUND_MECHANISM_2026-11-09.md)：190 点界复核、同点误差—平移分解与三类宽界机制。
- [第十八阶段三数据界组成对照](docs/EXTERNAL_BOUND_DECOMPOSITION_2026-11-09.md)：305 点算术一致性、三数据主导项分布与机制异质性。
- [第十九阶段内外部界组成对照](docs/INTERNAL_EXTERNAL_BOUND_COMPARISON_2026-11-09.md)：674 个可用点的六组分布、两类不适用边界与范围分离。
- [第二十阶段 Misra1a 预测—证明解离](docs/MISRA1A_COVERAGE_2026-11-09.md)：14 点小样本、4 点可用界、连续安全与界宽度审计。
- [第二十一阶段四外部与七组界组成对照](docs/BOUND_COMPARISON_V2_2026-11-09.md)：379 点外部范围、678 个可用点及新旧版本差异。
- [第二十二阶段 Chwirut1 同族外部审计](docs/CHWIRUT1_COVERAGE_2026-11-09.md)：214 点、83 点可用界、最低 RMSE 折零可用界与数据亲缘边界。
- [第二十三阶段五外部与八组界组成对照](docs/BOUND_COMPARISON_V3_2026-11-09.md)：593 点外部范围、761 个可用点、Chwirut1 增量及同族数据边界。
- [第二十四阶段 ENSO 周期数据预测—证明解离](docs/ENSO_COVERAGE_2026-11-09.md)：168 点、135 点可用界、131 对收紧比较与第 5 折零可用界。
- [第二十五阶段六外部与九组界组成对照](docs/BOUND_COMPARISON_V4_2026-11-09.md)：761 点外部范围、896 个可用点及 ENSO 最大界实际残差主导反例。
- [第二十六阶段最大界点与全点组成审计](docs/MAXIMUM_FULL_COMPOSITION_2026-11-09.md)：8／9 组类别一致、6 组低于中位占比及最大界宽比审计。
- [第二十七阶段极值报告分层写作与验收协议](docs/EXTREME_REPORTING_PROTOCOL.md)：L0 极值描述、L1 全点分布与 L2 限定机制解释的机器验收。
- [第二十八阶段既有报告极值表述分级复核](docs/EXTREME_REPORTING_CORPUS_AUDIT.md)：16 份文档全集分级、10 份联读要求与原文哈希保持。
- [第二十九阶段 Roszman1 预测—证明解离](docs/ROSZMAN1_COVERAGE_2026-11-09.md)：25 点量子缺陷实测数据、5 点可用界、逐折反例与平移主导界审计。
- [第三十阶段七外部与十组界组成对照](docs/BOUND_COMPARISON_V5_2026-11-09.md)：786 点外部范围、901 个可用点、Roszman1 小样本增量与历史版本保持。
- [第三十一阶段十组最大界与全点组成审计](docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md)：9／10 组类别一致、6 组低于中位占比及小样本描述性百分位边界。
- [第三十二阶段 Roszman1 原生反正切模型同折对照](docs/ROSZMAN1_NATIVE_HOLDOUT_2026-11-09.md)：相同 25 个留出点、逐折胜负、折间稳定性与原生证明边界。
- [第三十三阶段 Roszman1 原生参数可识别性与稳定性](docs/ROSZMAN1_NATIVE_IDENTIFIABILITY_2026-11-09.md)：五折解析雅可比、局部条件、参数变化与留出敏感度。
- [第三十四阶段 ENSO 原生 Fourier 模型同折对照](docs/ENSO_NATIVE_HOLDOUT_2026-11-09.md)：168 个相同留出月份、逐折胜负、已知答案分层与周期变化。
- [第三十五阶段 Chwirut1 原生指数模型同折对照](docs/CHWIRUT1_NATIVE_HOLDOUT_2026-11-09.md)：214 个相同留出观测、22 个距离分组、计数修订与同族边界。
- [第三十六阶段极值相关报告全集分级（第二版）](docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md)：23 份文档、12 份联读、7 份描述、4 份完整与历史哈希保持。
- [第三十七阶段全仓库一致性审计](docs/REPOSITORY_INTEGRITY_2026-11-09.md)：本地链接、Word 哈希、证据图谱、全集计数和协议输入的确定性验收。
- [第三十八阶段三数据原生模型同折对照综合](docs/NATIVE_CROSS_DATASET_SYNTHESIS_2026-11-09.md)：15 折、407 个配对留出点、逐点胜负与指标方向的受限综合。
- [第三十九阶段 Roszman1 第 4 折误差贡献分解](docs/ROSZMAN1_NATIVE_FOLD4_ERROR_DECOMPOSITION_2026-11-09.md)：五个冻结点、残差权重恒等式与单点贡献移除诊断。
- [第四十阶段 Chwirut1 原生参数可识别性与分母诊断](docs/CHWIRUT1_NATIVE_IDENTIFIABILITY_2026-11-09.md)：五折解析雅可比、逐折自由度、参数补偿与原生极点诊断。
- [第四十一阶段 ENSO 原生周期参数可识别性与谐波补偿](docs/ENSO_NATIVE_IDENTIFIABILITY_2026-11-09.md)：五折九参数解析雅可比、周期—振幅补偿与局部敏感度。
- [第四十二阶段三模型局部可识别性受限综合](docs/NATIVE_IDENTIFIABILITY_CROSS_MODEL_2026-11-09.md)：15 折、407 个留出观测、敏感度比值与模型专有病征。
- [第四十三阶段三模型局部敏感度固定阈值覆盖审计](docs/NATIVE_SENSITIVITY_THRESHOLD_COVERAGE_2026-11-09.md)：407 点、1221 次固定阈值判定、逐点违规与聚合错觉。
- [第四十四阶段 Chwirut1 原生椭球连续分母与保守预测界](docs/CHWIRUT1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md)：五折连续分母证书、22 个原生包络与宽度信息审计。
- [第四十五阶段 Chwirut1 原生椭球半径敏感性与临界半径](docs/CHWIRUT1_NATIVE_ELLIPSOID_RADIUS_SENSITIVITY_2026-11-09.md)：五折解析临界半径、25 个案例与包络宽度敏感性。
- [第四十六阶段 Roszman1 原生反正切椭球奇异证书与预测界](docs/ROSZMAN1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md)：五折奇异临界半径、20 个可用包络与第 5 折跨零反例。
- [第四十七阶段 ENSO 原生 Fourier 正周期与连续预测包络](docs/ENSO_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md)：五折正周期证书、168 个原生包络与信息宽度审计，区分物理周期、联合最优性和中心一致性。
- [第四十八阶段 ENSO 原生椭球半径敏感性与正周期失效边界](docs/ENSO_NATIVE_ELLIPSOID_RADIUS_SENSITIVITY_2026-11-09.md)：五折六半径、30 个案例、942 个可用包络、两个正周期失效反例与显式计数修正。
- [第四十九阶段三模型原生椭球包络受限综合](docs/NATIVE_ELLIPSOID_CROSS_MODEL_SYNTHESIS_2026-11-09.md)：15 折、407 点、402 个可用点、210 个包络与仅限数据集内部的归一化审计。
- [第五十阶段 ENSO 条件周期切片联合支撑与全域反例](docs/ENSO_CONDITIONAL_PERIOD_SLICE_BOUNDS_2026-11-09.md)：168 个切片、672 次候选评价、199 次外推反例与完整支撑方向修正。
- [ENSO 条件周期切片界原生 Word 图文版](papers/前沿共生ENSO条件周期切片界_图文完整版.docx)：一幅四联实图、五个 Word 表格、三个原生 OMML 公式，含目录、页眉和页码。
- [三模型原生椭球包络综合原生 Word 图文版](papers/前沿共生三模型原生椭球包络综合_图文完整版.docx)：一幅四联实图、五个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [ENSO 原生椭球半径敏感性原生 Word 图文版](papers/前沿共生ENSO原生椭球半径敏感性_图文完整版.docx)：一幅四联实图、五个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [ENSO 原生椭球连续界原生 Word 图文版](papers/前沿共生ENSO原生椭球连续界_图文完整版.docx)：一幅四联实图、五个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Roszman1 原生椭球奇异界原生 Word 图文版](papers/前沿共生Roszman1原生椭球奇异界_图文完整版.docx)：一幅四联实图、五个 Word 表格、三个原生 OMML 公式，含目录、页眉和页码。
- [Chwirut1 原生椭球半径敏感性原生 Word 图文版](papers/前沿共生Chwirut1原生椭球半径敏感性_图文完整版.docx)：一幅四联实图、五个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Chwirut1 原生椭球连续界原生 Word 图文版](papers/前沿共生Chwirut1原生椭球连续界_图文完整版.docx)：一幅四联实图、四个 Word 表格、四个原生 OMML 公式，含目录、页眉和页码。
- [三模型敏感度阈值覆盖原生 Word 图文版](papers/前沿共生三模型敏感度阈值覆盖_图文完整版.docx)：一幅四联实图、四个 Word 表格、一个原生 OMML 公式，含目录、页眉和页码。
- [三模型局部可识别性综合原生 Word 图文版](papers/前沿共生三模型局部可识别性综合_图文完整版.docx)：一幅四联实图、五个 Word 表格、一个原生 OMML 公式，含目录、页眉和页码。
- [ENSO 原生参数可识别性原生 Word 图文版](papers/前沿共生ENSO原生参数可识别性_图文完整版.docx)：一幅六联实图、六个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Chwirut1 原生参数可识别性原生 Word 图文版](papers/前沿共生Chwirut1原生参数可识别性_图文完整版.docx)：一幅六联实图、六个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Roszman1 第 4 折误差分解原生 Word 图文版](papers/前沿共生Roszman1第4折误差分解_图文完整版.docx)：一幅四联实图、五个 Word 表格、三个原生 OMML 公式，含目录、页眉和页码。
- [三数据原生同折综合原生 Word 图文版](papers/前沿共生三数据原生同折综合_图文完整版.docx)：一幅四联实图、六个 Word 表格、七个原生 OMML 公式，含目录、页眉和页码。
- [全仓库一致性审计原生 Word 图文版](papers/前沿共生仓库完整性审计_图文完整版.docx)：一幅实图、五个 Word 表格、一个原生 OMML 公式，含目录、页眉和页码。
- [极值报告全集分级第二版原生 Word 图文版](papers/前沿共生极值报告全集分级V2_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Chwirut1 原生指数同折对照原生 Word 图文版](papers/前沿共生Chwirut1原生指数同折对照_图文完整版.docx)：一幅三联实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [ENSO 原生周期同折对照原生 Word 图文版](papers/前沿共生ENSO原生周期同折对照_图文完整版.docx)：一幅三联实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Roszman1 原生参数可识别性原生 Word 图文版](papers/前沿共生Roszman1原生参数可识别性_图文完整版.docx)：一幅四联实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Roszman1 原生反正切同折对照原生 Word 图文版](papers/前沿共生Roszman1原生反正切同折对照_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [第三十一阶段十组极值审计原生 Word 图文版](papers/前沿共生第三十一阶段十组极值审计_图文完整版.docx)：一幅三联实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [七外部与十组界组成原生 Word 图文版](papers/前沿共生七外部与十组界组成对照_图文完整版.docx)：两幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Roszman1 预测—证明解离原生 Word 图文版](papers/前沿共生Roszman1预测证明解离_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [既有报告极值表述分级复核原生 Word 图文版](papers/前沿共生既有报告极值表述分级复核_图文完整版.docx)：三联实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [极值报告写作与验收协议原生 Word 图文版](papers/前沿共生极值报告写作与验收协议_图文完整版.docx)：三联实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [最大界与全点组成原生 Word 图文版](papers/前沿共生最大界与全点组成审计_图文完整版.docx)：三联实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [六外部与九组界组成原生 Word 图文版](papers/前沿共生六外部与九组界组成对照_图文完整版.docx)：两幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [ENSO 预测—证明解离原生 Word 图文版](papers/前沿共生ENSO预测证明解离_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [五外部与八组界组成原生 Word 图文版](papers/前沿共生五外部与八组界组成对照_图文完整版.docx)：两幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Chwirut1 预测—证明解离原生 Word 图文版](papers/前沿共生Chwirut1预测证明解离_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [四外部与七组界组成原生 Word 图文版](papers/前沿共生四外部与七组界组成对照_图文完整版.docx)：两幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Misra1a 预测—证明解离原生 Word 图文版](papers/前沿共生Misra1a预测证明解离_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [内外部界组成原生 Word 图文版](papers/前沿共生内外部界组成对照_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [三数据界组成原生 Word 图文版](papers/前沿共生外部界组成对照_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Gauss1 界失效机制原生 Word 图文版](papers/前沿共生Gauss1界失效机制_图文完整版.docx)：一幅实图、四个 Word 表格、九个原生 OMML 公式，含目录、页眉和页码。
- [Gauss1 外部反例原生 Word 图文版](papers/前沿共生Gauss1外部反例_图文完整版.docx)：三幅实图、四个 Word 表格、一个原生 OMML 公式，含目录、页眉和页码。
- [外部覆盖协议原生 Word 图文版](papers/前沿共生外部覆盖协议_图文完整版.docx)：两幅实图、四个 Word 表格、一个原生 OMML 公式，含目录、页眉和页码。
- [Filip 外部覆盖原生 Word 图文版](papers/前沿共生Filip外部覆盖_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [椭球连续区间原生 Word 图文版](papers/前沿共生椭球连续区间证明_图文完整版.docx)：一幅实图、三个 Word 表格、四个原生 OMML 公式，含目录、页眉和页码。
- [协方差椭球原生 Word 图文版](papers/前沿共生协方差椭球预测界_图文完整版.docx)：一幅实图、四个 Word 表格、十个原生 OMML 公式，含目录、页眉和页码。
- [参数盒预测界原生 Word 图文版](papers/前沿共生参数盒预测界_图文完整版.docx)：一幅实图、三个 Word 表格、十二个原生 OMML 公式，含目录、页眉和页码。
- [参数盒稳定性原生 Word 图文版](papers/前沿共生参数盒稳定性_图文完整版.docx)：一幅实图、三个 Word 表格、十四个原生 OMML 公式，含目录、页眉和页码。
- [精确区间根证明原生 Word 图文版](papers/前沿共生精确区间根证明_图文完整版.docx)：一幅实图、四个 Word 表格、三个原生 OMML 公式，含目录、页眉和页码。
- [跨数据集综合原生 Word 图文版](papers/前沿共生有理模型跨数据集综合_图文完整版.docx)：一幅实图、四个 Word 表格、两个原生 OMML 公式，含目录、页眉和页码。
- [Kirby2 原生 Word 图文版](papers/前沿共生Kirby2跨次数验收_图文完整版.docx)：一幅实图、四个 Word 表格、九个原生 OMML 公式，含目录、页眉和页码。
- [Thurber 原生 Word 图文版](papers/前沿共生Thurber前瞻验收_图文完整版.docx)：一幅实图、四个 Word 表格、十三个原生 OMML 公式，含目录、页眉和页码。
- [失效机制原生 Word 图文版](papers/前沿共生Hahn1失效机制诊断_图文完整版.docx)：一幅实图、四个 Word 表格、十四个原生 OMML 公式，含目录、页眉和页码。
- [压力测试原生 Word 图文版](papers/前沿共生压力测试与失效边界_图文完整版.docx)：一幅实图、四个 Word 表格、三个原生 OMML 公式，含目录、页眉和页码。
- [有理模型原生 Word 图文版](papers/前沿共生有理模型与分母边界_图文完整版.docx)：一幅实图、四个 Word 表格、七个原生 OMML 公式，含目录、页眉和页码。
- [续展原生 Word 图文版](papers/前沿共生续展_双尾外推与求解器复核_图文完整版.docx)：一幅实图、四个 Word 表格、七个原生 OMML 公式，含目录、页眉和页码。
- [扩展工作包原生 Word 图文版](papers/前沿共生扩展工作包_图文完整版.docx)：两幅实图、三个 Word 表格、五个原生 OMML 公式，含目录、页眉和页码。
- [主张—证据—反例—实验图谱](exports/frontier-knowledge-graph.json)：281 个节点、770 条边，支持与反例均可追溯到实际文件。
- [研究简报合订本（Word）](papers/前沿共生研究简报_合订本.docx)：三篇长文、十三幅图，附真实证据与复现路径。
- [研究简报合订本（Markdown）](papers/前沿共生研究简报_合订本.md)：便于审阅和继续修订的文本版本。

## 文档交付约定

研究总报告除 Markdown／JSON／脚本外，均额外提供原生 Word 图文版。图片按章节与顺序嵌入，表格保留为 Word 表格，公式使用原生 OMML，包含目录、页眉和页码；每份文档通过 OOXML／OPC 验证，视觉预览不可用时明确披露。

## 证据原则

- 同行评议、正式论文、官方代码/数据、预印本和观察项分开标记；论文存在不等于结果被独立复现。
- 本地验证只说明“本机、该版本、该样例”的结果，不自动推广成普适规律。
- 任何新规律必须接受留出数据、跨条件、量纲、基线和负结果检验。
- 化学数据异常先排查单位、算法、结构与实验条件，不能把差异直接称为造假。
- 不把外部设施或论文写成我们的合作方、成果或能力。

## 当前范围

首批目录聚焦有公开来源的国家/国际计划、AI for Math、AI for Science、AI for Biology、AI for Physics 及基础设施。它是可持续扩展的样本，不是一次性穷尽全球的名单。

## 本地使用

```bash
python scripts/build_catalog.py --check
python -m unittest discover -s tests -v
```

项目文档在 `C:\Users\一梦\Documents\kimi\workspace\frontier-breakthrough`；科研运行环境优先放在 `D:\research-engines`，环境、模型和缓存不进入 Git。
