#!/usr/bin/env python3
"""Validate the curated registry and generate its human-readable catalog."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "projects.json"
OUTPUT = ROOT / "docs" / "GLOBAL_PROJECTS.md"
REQUIRED = {
    "id", "name", "domain", "kind", "owner", "source", "evidenceTier",
    "adoption", "localStatus", "collaboration", "notes",
}
DOMAINS = {"national", "math", "science", "biology", "physics", "infrastructure"}
TIERS = {"peer_reviewed", "official_artifact", "preprint", "watch"}
ADOPTIONS = {"P0_local", "P1_adapt", "P2_watch", "P3_external"}
STATUSES = {"pending", "installed", "verified", "deferred", "external"}
TITLES = {
    "national": "国家与国际计划",
    "math": "AI for Math",
    "science": "通用 AI for Science 与科研代理",
    "biology": "AI for Biology",
    "physics": "AI for Physics 与材料",
    "infrastructure": "公共科研基础设施",
}


def load_and_validate() -> dict:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    projects = payload["projects"]
    ids = [p["id"] for p in projects]
    assert len(ids) == len(set(ids)), "project id 必须唯一"
    for project in projects:
        missing = REQUIRED - project.keys()
        assert not missing, f"{project.get('id')}: 缺少 {sorted(missing)}"
        assert project["domain"] in DOMAINS
        assert project["evidenceTier"] in TIERS
        assert project["adoption"] in ADOPTIONS
        assert project["localStatus"] in STATUSES
        parsed = urlparse(project["source"])
        assert parsed.scheme == "https" and parsed.netloc, project["id"]
        assert all(str(project[k]).strip() for k in REQUIRED), project["id"]
        if project["adoption"] == "P3_external":
            assert project["localStatus"] in {"external", "deferred"}
    return payload


def render(payload: dict) -> str:
    projects = payload["projects"]
    domain_counts = Counter(p["domain"] for p in projects)
    adoption_counts = Counter(p["adoption"] for p in projects)
    lines = [
        "# 全球前沿项目、模型与战略设施目录",
        "",
        f"更新日期：{payload['updated']}　条目数：{len(projects)}",
        "",
        "> 本目录是有来源、可持续维护的初始集合，不声称一次性穷尽全球所有项目。条目进入目录不代表其主张已被独立复现，也不代表我们已与相关机构建立合作。",
        "",
        "## 配合而非重复建设",
        "",
        "- **战略设施**：国家实验室、大科学装置和自动实验平台提供我们缺少的条件；我们提供公开数据复核、交叉问题建模、轻量基准与知识接口。",
        "- **上游项目**：保留原始来源、作者与许可证；优先使用配置、插件和小适配器，只有真实且有普遍价值的改进才回馈上游。",
        "- **成果引用**：`source` 是项目或官方工件入口；论文 DOI 可在 notes 补充。目录中的名字不是我们的成果或合作方。",
        "- **本地状态**：`verified` 仅指本机指定样例已验证，不等于理论、实验或临床有效。",
        "",
        "## 概览",
        "",
        "| 维度 | 数量 |",
        "|---|---:|",
    ]
    for domain in TITLES:
        lines.append(f"| {TITLES[domain]} | {domain_counts[domain]} |")
    lines.extend(["", "| 采用策略 | 数量 |", "|---|---:|"])
    for adoption in ("P0_local", "P1_adapt", "P2_watch", "P3_external"):
        lines.append(f"| {adoption} | {adoption_counts[adoption]} |")
    for domain, title in TITLES.items():
        lines.extend([
            "", f"## {title}", "",
            "| 项目 | 类型 | 证据 | 策略 / 本地状态 | 我们的互补角色 | 来源 |",
            "|---|---|---|---|---|---|",
        ])
        for p in (x for x in projects if x["domain"] == domain):
            name = p["name"].replace("|", "\\|")
            role = p["collaboration"].replace("|", "\\|")
            lines.append(
                f"| {name} | {p['kind']} | {p['evidenceTier']} | "
                f"{p['adoption']} / {p['localStatus']} | {role} | [官方或注明来源]({p['source']}) |"
            )
        lines.append("")
        for p in (x for x in projects if x["domain"] == domain):
            lines.append(f"- **{p['name']}**：{p['notes']}")
    lines.extend([
        "", "## 待补证据与持续扩展", "",
        "- 英国条目的原始政府文件、CCF 观察计划发起方原文仍需补齐。",
        "- 未通过官方源核实的同名仓库不进入正式目录，也不以个人镜像冒充官方项目。",
        "- 每周新增项目必须同时给出互补贡献、验证门槛和退出条件；只收藏、无行动的条目降级为观察项。",
        "- 大型权重、数据集和设施默认外部复用；只有明确科学问题、许可证和资源预算同时满足时才本地化。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="只校验并检查生成文档是否最新")
    args = parser.parse_args()
    payload = load_and_validate()
    rendered = render(payload)
    if args.check:
        assert OUTPUT.exists(), "缺少生成的目录，请运行 scripts/build_catalog.py"
        assert OUTPUT.read_text(encoding="utf-8") == rendered, "目录不是最新，请重新生成"
        print(f"OK: {len(payload['projects'])} projects; catalog is current")
    else:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"Wrote {OUTPUT} ({len(payload['projects'])} projects)")


if __name__ == "__main__":
    main()
