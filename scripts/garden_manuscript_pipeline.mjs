import { spawn, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { once } from "node:events";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const garden = process.env.GARDEN_ROOT || "C:/Users/一梦/Documents/kimi/workspace/bloombloomgarden-improvements";
const outputDir = path.join(root, "garden");
const draftsDir = path.join(outputDir, "drafts");
fs.mkdirSync(draftsDir, { recursive: true });
const reportPath = path.join(outputDir, "run-report.json");
const serviceLog = path.join(outputDir, "service.log");
const readJson = (name) => JSON.parse(fs.readFileSync(path.join(root, name), "utf8"));
const drug = readJson("validation/drug-target-structure.json");
const selectivity = readJson("validation/ca-selectivity.json");
const stability = readJson("validation/ca-document-stability.json");
const token = randomBytes(32).toString("hex");
let child;
const report = { startedAt: new Date().toISOString(), lawPackages: [], pipelines: [], errors: [], serversStopped: false };

function source(label, locator) { return { label, locator }; }
function event(detail) { return [{ at: "2026-10-31", action: "verified_snapshot", detail }]; }
const packages = [
  {
    id: "ACETAZOLAMIDE-CHAIN-20261031", version: 1, kind: "effective_mapping",
    title: "乙酰唑胺—CA II—实验结构的可审计证据链", domain: "化学信息学 · 结构生物学",
    status: "DEMONSTRATED",
    statement: "CHEMBL20/PubChem 1986 的化合物身份、CHEMBL205/P00918 的靶点、3HS4 entity 1 的 260 aa 序列与 AZM 配体可逐层复核。",
    summary: "跨库映射和本地计算通过；Ki=12 nM 仅属于 CHEMBL657848，potential_duplicate=1 保留。",
    metrics: [
      { label: "CA II 序列一致长度", value: 260, note: "P00918 与 3HS4 entity 1 逐字符一致" },
      { label: "单 assay Ki / nM", value: drug.ki_nM, note: `pChEMBL 重算 ${drug.pchembl_recomputed}` },
      { label: "3HS4 分辨率 / Å", value: drug.resolution_A, note: "X 射线实验复合物，AZM entity 4" },
    ],
    parameters: [{ name: "跨库映射", meaning: "身份、序列、实验结构的分层对应", unit: "布尔与计数", sourceType: "DERIVED", status: "verified" }],
    validations: [
      { level: "database_crosscheck", label: "化合物 InChIKey", status: "PASS", evidence: "CHEMBL20 与 PubChem CID 1986 完全一致" },
      { level: "sequence_check", label: "CA II 全长序列", status: "PASS", evidence: "P00918 与 3HS4 entity 1 的 260 aa 一致" },
      { level: "structure_check", label: "实验复合物", status: "PASS", evidence: "3HS4 的 AZM entity 4，分辨率 1.1 Å" },
    ],
    counterexamples: [], limitations: ["单一 Ki 不外推为统一效力或临床结论", "potential_duplicate=1 是审计警告而非自动造假证据"],
    nextAction: "将方法可比性纳入跨文档定量分析，不把结构存在当作活性复现。",
    sources: [source("ChEMBL", "CHEMBL20/CHEMBL205/CHEMBL657848"), source("PubChem", "CID 1986"), source("RCSB PDB", "3HS4 entity 1 and entity 4"), source("UniProt", "P00918")],
    evidenceHistory: event("化合物、靶点、序列和实验结构快照已核对"),
  },
  {
    id: "CA-SELECTIVITY-SENSITIVITY-20261031", version: 1, kind: "empirical",
    title: "CA I/II 表观活性比的文档与方法依赖性", domain: "生物活性数据 · 敏感性分析",
    status: "LIMITED_SUPPORT",
    statement: "六组文档的 CA I/II 表观 Ki 比值从 20.8333 到 75；方法信息不足时不支持固定选择性常数。",
    summary: "仅一组明确双方均为酯酶方法；其余五组方法细节不足，不执行跨文献合并估计。",
    metrics: [
      { label: "文档配对数", value: stability.document_count, note: "不同文档不自动等于独立实验" },
      { label: "最小表观比值", value: stability.ratio_min, note: "CHEMBL1146805，明确同酯酶方法" },
      { label: "最大表观比值", value: stability.ratio_max, note: "其他方法信息不完整文档" },
      { label: "极差倍数", value: stability.max_min_fold, note: "最大值 / 最小值" },
    ],
    parameters: [
      { name: "表观 Ki 比", meaning: "CA I Ki / CA II Ki", unit: "无量纲", sourceType: "DERIVED", status: "not_a_universal_constant" },
      { name: "assay 可比性", meaning: "是否明确相同实验方法", unit: "文档计数", sourceType: "BOUNDARY", status: "1/6 explicit matched" },
    ],
    validations: [
      { level: "method_match", label: "明确同酯酶方法", status: "LIMITED", evidence: "六组中仅 CHEMBL1146805 明确匹配" },
      { level: "cross_document_stability", label: "固定比值稳定性", status: "FAIL", evidence: "表观比值覆盖 20.8333–75，相差 3.6 倍" },
      { level: "independent_replication", label: "独立实验复现", status: "NOT_APPLICABLE", evidence: "本次是 ChEMBL 数据复核，未执行湿实验" },
    ],
    counterexamples: ["20.8333 与 75 的文档配对比值不支持单一固定常数"],
    limitations: ["五组 assay 方法信息不足", "重复标记和相同数值限制独立解释", "没有置信区间或临床外推"],
    nextAction: "获取原始论文实验段落和真正的独立重复，再决定是否进行同方法分层统计。",
    sources: stability.pairs.map((p) => source(`ChEMBL ${p.document_chembl_id}`, `${p.ca_i_activity}/${p.ca_ii_activity}; ${p.method_status}`)),
    evidenceHistory: event("六组文档配对完成方法分层和比值敏感性分析"),
  },
  {
    id: "REPRODUCIBLE-ENGINEERING-20261031", version: 1, kind: "protocol",
    title: "轻量可复现科研引擎的上游协作协议", domain: "AI for Science · 科研基础设施",
    status: "DESIGN_READY",
    statement: "将已知答案、公开快照和限制写成可重放包，可为上游提供验证与接口，但不冒充新科学发现。",
    summary: "PySINDy、Z3、RDKit、PyMatGen 在 D 盘完成指定样例；跨库证据链保留原始快照。",
    metrics: [
      { label: "本地引擎", value: 4, note: "PySINDy、Z3、RDKit、PyMatGen" },
      { label: "PySINDy 最大系数误差", value: 3.136190275787598e-05, note: "已知线性系统的数值微分误差" },
      { label: "硅密度重算 / g·cm⁻³", value: 2.3128002565764314, note: "与 Materials Project 结构快照一致" },
    ],
    parameters: [{ name: "验证层级", meaning: "已知答案、公开快照、跨库核对与实验验证分层", unit: "层级", sourceType: "BOUNDARY", status: "local_replay_only" }],
    validations: [
      { level: "local_replay", label: "四个指定引擎样例", status: "PASS", evidence: "D 盘隔离环境实际运行并保存 JSON" },
      { level: "external_experiment", label: "独立实验验证", status: "NOT_APPLICABLE", evidence: "本协议不声称湿实验或外部认证" },
    ],
    counterexamples: ["已知答案恢复不能证明真实数据中的新规律", "DFT 外部带隙不能因结构密度一致而宣称本地重算"],
    limitations: ["结果仅限指定版本和样例", "上游数据和算法口径必须随结果保存"],
    nextAction: "将同一协议扩展到公开真实数据的留出验证，并保留负结果。",
    sources: [source("PySINDy", "validation/pysindy.json"), source("Z3", "validation/z3.json"), source("RDKit", "validation/rdkit.json"), source("PyMatGen", "validation/pymatgen.json")],
    evidenceHistory: event("四个本地引擎及统一证据协议已形成"),
  },
];

async function freePort() {
  const server = net.createServer();
  server.unref();
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  const port = server.address().port;
  await new Promise((resolve) => server.close(resolve));
  return port;
}

async function request(origin, route, method = "GET", body, timeoutMs = 240_000) {
  const response = await fetch(origin + route, {
    method,
    headers: { Accept: "application/json", Authorization: `Bearer ${token}`, ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await response.text();
  let payload;
  try { payload = JSON.parse(text); } catch { throw new Error(`${route} 返回非 JSON：${text.slice(0, 300)}`); }
  if (!response.ok) throw new Error(`${route} HTTP ${response.status}: ${text.slice(0, 1000)}`);
  return payload;
}

async function stopService() {
  if (!child || (child.exitCode !== null && child.signalCode !== null)) { report.serversStopped = true; return; }
  if (process.platform === "win32") {
    spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore", shell: false, windowsHide: true, timeout: 15_000 });
  } else child.kill("SIGTERM");
  await Promise.race([once(child, "exit"), new Promise((resolve) => setTimeout(resolve, 5000))]);
  report.serversStopped = child.exitCode !== null || child.signalCode !== null;
}

async function main() {
  const port = await freePort();
  const origin = `http://127.0.0.1:${port}`;
  const nextCli = path.join(garden, "node_modules", "next", "dist", "bin", "next");
  const logFd = fs.openSync(serviceLog, "w");
  child = spawn(process.execPath, [nextCli, "dev", "--hostname", "127.0.0.1", "--port", String(port)], {
    cwd: garden,
    env: { ...process.env, GARDEN_AGENT_TOKEN: token, GARDEN_USE_CLUSTER: "0", HOST: "127.0.0.1", NODE_ENV: "development" },
    stdio: ["ignore", logFd, logFd], shell: false, windowsHide: true,
  });
  fs.closeSync(logFd);
  const deadline = Date.now() + 90_000;
  for (;;) {
    if (child.exitCode !== null && child.signalCode !== null) throw new Error("花园研究服务启动失败，请检查 service.log");
    try { if ((await fetch(origin + "/", { signal: AbortSignal.timeout(2000) })).ok) break; } catch { /* starting */ }
    if (Date.now() >= deadline) throw new Error("等待花园研究服务就绪超时");
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  for (const pkg of packages) {
    try {
      await request(origin, "/api/research/law-packages", "POST", pkg);
      report.lawPackages.push({ id: pkg.id, created: true });
    } catch (error) {
      if (!String(error.message).includes("409")) throw error;
      report.lawPackages.push({ id: pkg.id, created: false, existing: true });
    }
    const readback = await request(origin, `/api/research/law-packages/${pkg.id}`);
    if (readback.data?.id !== pkg.id) throw new Error(`证据包 ${pkg.id} 回读不一致`);
  }

  const panel = await request(origin, "/api/research/panels", "POST", {
    name: `前沿共生研究简报评议组 ${Date.now()}`,
    description: "只核对实际证据、数值、方法和限制，不替代真实同行评议。",
    domain: "cross-database-reproducibility",
    strategy: { evidenceFirst: true, rejectUnsupportedClaims: true },
  });
  report.panelId = panel.data.id;
  const definitions = [
    { key: "01-evidence-chain", title: "乙酰唑胺—碳酸酐酶 II 的跨库证据链", evidence: packages[0], instruction: "撰写跨库数据核型研究简报，重点区分身份核验、结构证据和活性边界。" },
    { key: "02-selectivity-stability", title: "CA I/II 表观活性比为什么不应当作固定常数", evidence: packages[1], instruction: "撰写负结果与敏感性分析研究简报，明确 6 组文档、20.8333–75、3.6 倍和仅 1 组明确同方法。" },
    { key: "03-reproducible-engines", title: "轻量可复现科研引擎的协作方法", evidence: packages[2], instruction: "撰写科研基础设施方法简报，区分已知答案、公开快照复核与新发现。" },
  ];
  const recoverOnly = process.env.GARDEN_RECOVER_ONLY === "1";
  const existingPipelines = recoverOnly ? (await request(origin, "/api/research/pipelines")).data : [];
  if (process.env.GARDEN_UPLOAD_FINAL === "1") {
    const paperManifest = JSON.parse(fs.readFileSync(path.join(root, "papers", "manifest.json"), "utf8"));
    report.finalUploads = [];
    for (const item of paperManifest.papers) {
      const pipeline = existingPipelines.find((candidate) => candidate.id === item.pipelineId);
      if (!pipeline) throw new Error(`未找到修订流水线：${item.pipelineId}`);
      const stage = pipeline.stages.find((candidate) => candidate.name === "revision");
      const content = fs.readFileSync(path.join(root, "papers", item.folder, item.file), "utf8");
      await request(origin, `/api/research/pipelines/${pipeline.id}/stages/${stage.id}`, "PUT", {
        content,
        feedback: "数值、来源与证据边界核验修订；研究简报／预印本草案，未同行评议。",
        status: "active",
      });
      const readback = await request(origin, `/api/research/pipelines/${pipeline.id}/stages/${stage.id}`);
      if (readback.data?.content?.length !== content.length) throw new Error(`修订稿回读长度不一致：${item.file}`);
      report.finalUploads.push({ pipelineId: pipeline.id, stageId: stage.id, file: path.join("papers", item.folder, item.file), contentLength: content.length, readback: true });
    }
    return;
  }
  if (process.env.GARDEN_INSPECT_ONLY === "1") {
    report.inspection = existingPipelines.filter((item) => definitions.some((definition) => definition.title === item.title)).map((item) => ({
      id: item.id,
      title: item.title,
      status: item.status,
      currentStage: item.currentStage,
      stages: item.stages.map((stage) => ({ id: stage.id, name: stage.name, status: stage.status, score: stage.score, contentLength: stage.content?.length || 0 })),
    }));
    return;
  }
  const selectedDefinitions = process.env.GARDEN_DRAFT_KEY
    ? definitions.filter((definition) => definition.key === process.env.GARDEN_DRAFT_KEY)
    : definitions;
  if (selectedDefinitions.length === 0) throw new Error(`未知 GARDEN_DRAFT_KEY：${process.env.GARDEN_DRAFT_KEY}`);
  await Promise.all(selectedDefinitions.map(async (definition) => {
    let data;
    if (recoverOnly) {
      data = existingPipelines.find((item) => item.title === definition.title);
      if (!data) throw new Error(`未找到待回收流水线：${definition.title}`);
    } else {
      const pipeline = await request(origin, "/api/research/pipelines", "POST", {
        title: definition.title,
        description: "研究简报／预印本草案；未同行评议。只能使用给定证据，不得创造实验、数值或参考文献。",
        panelId: report.panelId,
      });
      data = pipeline.data;
    }
    const stage = data.stages.find((item) => item.name === "draft");
    let content = stage.content;
    if (!content) {
      const previousContent = JSON.stringify({
        documentType: "研究简报／预印本草案，未同行评议",
        requiredStructure: ["摘要", "一、引言（必须有1.4）", "二、理论模型", "三、数值结果", "四、讨论", "五、结论", "参考文献", "附录复现路径"],
        evidence: {
          id: definition.evidence.id,
          statement: definition.evidence.statement,
          summary: definition.evidence.summary,
          metrics: definition.evidence.metrics,
          limitations: definition.evidence.limitations,
        },
        instruction: definition.instruction,
        prohibitions: ["不得虚构实验、作者、期刊接收或 DOI", "不得添加给定证据之外的数值", "不得把数据库复核写成独立实验复现"],
      });
      const generated = await request(origin, `/api/research/pipelines/${data.id}/stages/${stage.id}`, "PUT", {
        autoGenerate: true,
        topic: definition.title,
        targetModule: "frontier-breakthrough/research-notes",
        previousContent,
        maxTokens: 12288,
        timeoutMs: 600000,
        maxRetries: 0,
      }, 295_000);
      content = generated.data.content;
    }
    if (!content) throw new Error(`流水线 ${data.id} 未返回初稿内容`);
    const draftPath = path.join(draftsDir, `${definition.key}.json`);
    fs.writeFileSync(draftPath, JSON.stringify({ status: "unverified_llm_draft", pipelineId: data.id, stageId: stage.id, title: definition.title, content }, null, 2) + "\n", "utf8");
    report.pipelines.push({ key: definition.key, pipelineId: data.id, stageId: stage.id, draft: path.relative(root, draftPath), status: "unverified_llm_draft", recovered: recoverOnly });
  }));
}

try {
  await main();
} catch (error) {
  report.errors.push(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
} finally {
  await stopService();
  report.finishedAt = new Date().toISOString();
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + "\n", "utf8");
  console.log(JSON.stringify({ ok: report.errors.length === 0, lawPackages: report.lawPackages.length, pipelines: report.pipelines.length, errors: report.errors, serversStopped: report.serversStopped, report: path.relative(root, reportPath) }, null, 2));
}
