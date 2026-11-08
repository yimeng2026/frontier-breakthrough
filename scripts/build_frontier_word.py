"""Build the Frontier expansion report as a native illustrated Word document."""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/EXPANSION_2026-11-08.md"
OUTPUT = ROOT / "papers/前沿共生扩展工作包_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-word.json"
EXPECTED = {"math": 5, "images": 2, "tables": 3}
TITLE = "前沿共生计划扩展工作包：首轮五条主线"
REPORT_MODE = "expansion"
WORKSPACE = ROOT.parent
SHARED = WORKSPACE / ".worktrees/provider-main-integration/research/physical-intuition"
sys.path.insert(0, str(SHARED))
from build_total_word import audit_docx_package, normalize_math_commands, paragraph_ancestor, scale_extent  # noqa: E402


def prepare_frontier_markdown(source):
    source = normalize_math_commands(source.replace("\r\n", "\n").replace("\r", "\n"))
    heading = f"# {TITLE}\n"
    if source.startswith(heading):
        source = source[len(heading):].lstrip("\n")
    if REPORT_MODE == "internal_external_bound_comparison":
        replacements = {
            "图：`papers/24_内外部界组成对照/fig24_internal_external_bound_comparison.png`。": "![](papers/24_内外部界组成对照/fig24_internal_external_bound_comparison.png)\n\n**图 24｜内外部六组同点界组成对照（第 1 幅，共 1 幅）**  \n**插入位置**：§4「最大界位置不能替代全点分布」；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "674 点算术对照、六组分布与两类不适用边界"
    elif REPORT_MODE == "external_bound_decomposition":
        replacements = {
            "图：`papers/22_外部界组成对照/fig22_external_bound_decomposition.png`。": "![](papers/22_外部界组成对照/fig22_external_bound_decomposition.png)\n\n**图 22｜三数据同点界组成与平移占比分布（第 1 幅，共 1 幅）**  \n**插入位置**：§4「最大残差上界的同点组成」；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "305 点算术一致性、60 点不可用与三数据机制异质性"
    elif REPORT_MODE == "gauss1_bound_mechanism":
        replacements = {
            "图：`papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png`。": "![](papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png)\n\n**图 21｜Gauss1 分母可用性边界与残差上界（第 1 幅，共 1 幅）**  \n**插入位置**：§4「最大残差界位置的同点组成」；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "190 点界复核、60 点不可用、同点误差分解与两类失效尺度"
    elif REPORT_MODE == "gauss1_coverage":
        replacements = {
            "图：`papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png`。": "![](papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png)\n\n**图 18｜Filip 候选预测与逐点界可用性（第 1 幅，共 3 幅）**  \n**插入位置**：§4「三幅图件与读图顺序」；顺序第 1 幅，共 3 幅。",
            "图：`papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png`。": "![](papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png)\n\n**图 19｜MGH17 候选预测与逐点界可用性（第 2 幅，共 3 幅）**  \n**插入位置**：图 18 之后；顺序第 2 幅，共 3 幅。",
            "图：`papers/20_Gauss1椭球覆盖/fig20_gauss1_ellipsoid_coverage.png`。": "![](papers/20_Gauss1椭球覆盖/fig20_gauss1_ellipsoid_coverage.png)\n\n**图 20｜Gauss1 候选预测失败与逐点界可用性（第 3 幅，共 3 幅）**  \n**插入位置**：图 19 之后；顺序第 3 幅，共 3 幅。",
        }
        subtitle = "365 点总量、305 点可用界、60 点不可用与 13／15 折连续安全"
    elif REPORT_MODE == "external_coverage":
        replacements = {
            "图：`papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png`。": "![](papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png)\n\n**图 18｜Filip 候选预测与逐点界可用性（第 1 幅，共 2 幅）**  \n**插入位置**：§3「图件与证据等级」；顺序第 1 幅，共 2 幅。",
            "图：`papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png`。": "![](papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png)\n\n**图 19｜MGH17 候选预测与逐点界可用性（第 2 幅，共 2 幅）**  \n**插入位置**：图 18 之后；顺序第 2 幅，共 2 幅。",
        }
        subtitle = "通用驱动、115 点覆盖与两种独立盒边界"
    elif REPORT_MODE == "filip_coverage":
        replacements = {
            "图：`papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png`。": "![](papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png)\n\n**图 18｜Filip 外部候选预测与逐点界可用性**  \n**插入位置**：§3「逐点覆盖与界的宽度」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "82 点全部覆盖、五折连续安全与候选模型边界"
    elif REPORT_MODE == "ellipsoid_interval":
        replacements = {
            "图：`papers/17_椭球连续区间/fig17_ellipsoid_interval_safety.png`。": "![](papers/17_椭球连续区间/fig17_ellipsoid_interval_safety.png)\n\n**图 17｜协方差椭球连续区间平方支撑证明**  \n**插入位置**：§3「十三折连续区间验收结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "13 折连续无根证明与平方支撑边界"
    elif REPORT_MODE == "ellipsoid_bounds":
        replacements = {
            "图：`papers/16_椭球与参数盒/fig16_ellipsoid_box_comparison.png`。": "![](papers/16_椭球与参数盒/fig16_ellipsoid_box_comparison.png)\n\n**图 16｜协方差椭球与独立参数盒逐点比较**  \n**插入位置**：§3「全部适用点的比较结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "369 点全部收紧与相关结构边界"
    elif REPORT_MODE == "prediction_bounds":
        replacements = {
            "图：`papers/15_参数盒预测界/fig15_prediction_box_bounds.png`。": "![](papers/15_参数盒预测界/fig15_prediction_box_bounds.png)\n\n**图 15｜认证参数盒内逐点预测与残差上界**  \n**插入位置**：§3「结果：13 折有界，但信息质量差异巨大」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "13 折逐点保守上界与无根不等于高精度"
    elif REPORT_MODE == "box_stability":
        replacements = {
            "图：`papers/14_参数盒稳定性/fig14_parameter_box_stability.png`。": "![](papers/14_参数盒稳定性/fig14_parameter_box_stability.png)\n\n**图 14｜连续参数盒无根认证半径**  \n**插入位置**：§3「十五折结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "连续参数盒、13 折正安全半径与保守边界"
    elif REPORT_MODE == "exact_roots":
        replacements = {
            "图：`papers/13_精确区间根证明/fig13_exact_interval_roots.png`。": "![](papers/13_精确区间根证明/fig13_exact_interval_roots.png)\n\n**图 13｜精确 Sturm 根隔离与双求解器复核**  \n**插入位置**：§3「十五折精确结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "有理系数 Sturm 根隔离、13 折 unsat 与 2 折 sat"
    elif REPORT_MODE == "cross_dataset":
        replacements = {
            "图：`papers/12_跨数据集验收综合/fig12_rational_cross_dataset.png`。": "![](papers/12_跨数据集验收综合/fig12_rational_cross_dataset.png)\n\n**图 12｜有理模型跨数据集统一验收综合**  \n**插入位置**：§4「三个数据集的整体结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "统一诊断内核、13／15 折验收与证据等级边界"
    elif REPORT_MODE == "kirby2":
        replacements = {
            "图：`papers/11_Kirby2前瞻验收/fig11_kirby2_prospective_gate.png`。": "![](papers/11_Kirby2前瞻验收/fig11_kirby2_prospective_gate.png)\n\n**图 11｜Kirby2 二次有理模型五折前瞻验收**  \n**插入位置**：§5「阳性结果仍需保留的三个边界」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "二次有理模型、五折有限支持与高条件数边界"
    elif REPORT_MODE == "prospective":
        replacements = {
            "图：`papers/10_Thurber前瞻验收/fig10_thurber_prospective_gate.png`。": "![](papers/10_Thurber前瞻验收/fig10_thurber_prospective_gate.png)\n\n**图 10｜Thurber 数据集前瞻验收：极点、条件数与预测支持**  \n**插入位置**：§5「第 1 折失效位置」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "预测区极点、最低数值可识别性与五折验收"
    elif REPORT_MODE == "mechanism":
        replacements = {
            "图：`papers/09_Hahn1失效机制/fig09_hahn1_fold1_identifiability.png`。": "![](papers/09_Hahn1失效机制/fig09_hahn1_fold1_identifiability.png)\n\n**图 09｜Hahn1 第 1 折局部条件、预测敏感度与双极点**  \n**插入位置**：§4「失效链条与不可转移的证明」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "局部可识别性、两个低温极点与不可转移的分母证明"
    elif REPORT_MODE == "stress":
        replacements = {
            "图：`papers/08_跨数据集压力测试/fig08_grouped_stress.png`。": "![](papers/08_跨数据集压力测试/fig08_grouped_stress.png)\n\n**图 08｜跨数据集连续区间压力测试**  \n**插入位置**：§3「全部 15 折结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "连续区间压力测试、Hahn1 第 1 折失败与稳健性边界"
    elif REPORT_MODE == "rational":
        replacements = {
            "图：`papers/07_有理模型外推/fig07_hahn1_high_temperature.png`。": "![](papers/07_有理模型外推/fig07_hahn1_high_temperature.png)\n\n**图 07｜Hahn1 高温有理模型外推**  \n**插入位置**：§2.2「高温外推结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "Hahn1 高温外推、三次多项式基线与分母边界"
    elif REPORT_MODE == "continuation":
        replacements = {
            "图：`papers/06_第二真实数据外推/fig06_eckerle4_two_tail.png`。": "![](papers/06_第二真实数据外推/fig06_eckerle4_two_tail.png)\n\n**图 06｜Eckerle4 双尾外推检验**  \n**插入位置**：§2.2「双尾结果」之后；顺序第 1 幅，共 1 幅。",
        }
        subtitle = "Eckerle4 双尾外推与 cvc5 交叉求解器复核"
    else:
        replacements = {
            "图：`papers/04_真实数据留出/fig04_chwirut_holdout.png`。": "![](papers/04_真实数据留出/fig04_chwirut_holdout.png)\n\n**图 04｜NIST Chwirut2 高距离留出检验**  \n**插入位置**：§2.2「结果」之后；顺序第 1 幅，共 2 幅。",
            "图：`papers/05_材料跨库复核/fig05_material_crosscheck.png`。": "![](papers/05_材料跨库复核/fig05_material_crosscheck.png)\n\n**图 05｜MP／OQMD／PyMatGen 材料跨库复核**  \n**插入位置**：§5「材料：同结构并不保证同 DFT 数值」的结果表之后；顺序第 2 幅，共 2 幅。",
        }
        subtitle = "真实数据留出、形式化反例、化学跨库、材料跨库与知识连接"
    for original, replacement in replacements.items():
        if original not in source:
            raise ValueError(f"Missing figure anchor: {original}")
        source = source.replace(original, replacement, 1)
    date_match = re.search(r"^\*\*日期\*\*：(\d{4}-\d{2}-\d{2})", source, re.MULTILINE)
    report_date = date_match.group(1) if date_match else "2026-11-08"
    metadata = f"""---
title: "{TITLE}"
subtitle: "{subtitle}"
date: "{report_date}"
toc-title: "目录"
---

"""
    return metadata + source


def main():
    from docx import Document  # noqa: F401
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor, Twips

    workspace = WORKSPACE
    pandoc = workspace / "tools/pandoc/pandoc-3.6.4/pandoc.exe"
    skill = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word")
    reference = skill / "assets/reference.docx"
    verify_dir = skill / "scripts/verify"
    docx_entry = skill / "scripts/docx.py"
    for required in [SOURCE, pandoc, reference, verify_dir, docx_entry]:
        if not required.exists():
            raise FileNotFoundError(required)

    def run_command(command, cwd=None):
        completed = subprocess.run(
            [str(item) for item in command], cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=300, check=False,
        )
        print(completed.stdout, end="")
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout)
        return completed

    def add_page_field(paragraph):
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instruction = OxmlElement("w:instrText")
        instruction.set(qn("xml:space"), "preserve")
        instruction.text = " PAGE "
        separate = OxmlElement("w:fldChar")
        separate.set(qn("w:fldCharType"), "separate")
        text = OxmlElement("w:t")
        text.text = "1"
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        for element in [begin, instruction, separate, text, end]:
            run._r.append(element)

    def page_break():
        paragraph = OxmlElement("w:p")
        run = OxmlElement("w:r")
        br = OxmlElement("w:br")
        br.set(qn("w:type"), "page")
        run.append(br)
        paragraph.append(run)
        return paragraph

    def set_font(style, latin, cjk, size, bold=None, color=None):
        style.font.name = latin
        style.font.size = Pt(size)
        if bold is not None:
            style.font.bold = bold
        if color is not None:
            style.font.color.rgb = RGBColor.from_string(color)
        style._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), cjk)

    with tempfile.TemporaryDirectory(dir=ROOT, prefix=".frontier-word-") as temporary:
        temporary = Path(temporary)
        markdown = temporary / "source.md"
        markdown.write_text(prepare_frontier_markdown(SOURCE.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        base_docx = temporary / "base.docx"
        run_command([
            pandoc, markdown, "-o", base_docx,
            "--from=markdown+tex_math_single_backslash", "--to=docx", "--standalone",
            "--toc", "--toc-depth=3", f"--reference-doc={reference}", f"--resource-path={ROOT}",
        ], cwd=ROOT)
        work = temporary / "work"
        run_command([sys.executable, verify_dir / "prep.py", base_docx, "-o", work])
        sys.path.insert(0, str(verify_dir))
        import opc

        with opc.edit_docx(str(work / "unpacked")) as document:
            for section in document.sections:
                section.page_width = Cm(21.0)
                section.page_height = Cm(29.7)
                section.top_margin = Cm(2.0)
                section.bottom_margin = Cm(2.0)
                section.left_margin = Cm(2.2)
                section.right_margin = Cm(2.2)
                section.gutter = Cm(0)
                section.header_distance = Cm(0.9)
                section.footer_distance = Cm(0.9)
                section.different_first_page_header_footer = True
                header = section.header.paragraphs[0]
                header.text = TITLE
                header.style = document.styles["Normal"]
                header.alignment = WD_ALIGN_PARAGRAPH.CENTER
                header.paragraph_format.first_line_indent = Cm(0)
                for run in header.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(8.5)
                    run.font.color.rgb = RGBColor.from_string("66727A")
                    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "SimSun")
                footer = section.footer.paragraphs[0]
                footer.clear()
                footer.style = document.styles["Normal"]
                footer.paragraph_format.first_line_indent = Cm(0)
                add_page_field(footer)

            for style in document.styles:
                fonts = style._element.get_or_add_rPr().get_or_add_rFonts()
                if fonts.get(qn("w:ascii")) or fonts.get(qn("w:hAnsi")):
                    fonts.set(qn("w:eastAsia"), "SimSun")
            normal = document.styles["Normal"]
            set_font(normal, "Times New Roman", "SimSun", 10.5)
            normal.paragraph_format.line_spacing = 1.35
            normal.paragraph_format.space_after = Pt(6)
            normal.paragraph_format.first_line_indent = Cm(0.74)
            for name, size, color in [
                ("Title", 23, "263238"),
                ("Subtitle", 13, "52636C"),
                ("Heading 1", 16, "263238"),
                ("Heading 2", 13, "37474F"),
                ("Heading 3", 11.5, "455A64"),
            ]:
                if name in document.styles:
                    style = document.styles[name]
                    set_font(style, "Arial", "Microsoft YaHei", size, bold=name != "Subtitle", color=color)
                    style.paragraph_format.first_line_indent = Cm(0)
                    style.paragraph_format.space_before = Pt(14 if name.startswith("Heading") else 0)
                    style.paragraph_format.space_after = Pt(8)
                    style.paragraph_format.keep_with_next = True
            if "Source Code" in document.styles:
                set_font(document.styles["Source Code"], "Consolas", "SimSun", 8.5)
                document.styles["Source Code"].paragraph_format.first_line_indent = Cm(0)

            section = document.sections[0]
            max_width = section.page_width - section.left_margin - section.right_margin
            max_height = section.page_height - section.top_margin - section.bottom_margin - Cm(1.5)
            for shape in document.inline_shapes:
                width, height = scale_extent(shape.width, shape.height, max_width, max_height)
                shape.width, shape.height = width, height
                paragraph_element = paragraph_ancestor(shape._inline)
                if paragraph_element is not None:
                    from docx.text.paragraph import Paragraph
                    paragraph = Paragraph(paragraph_element, document)
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    paragraph.paragraph_format.first_line_indent = Cm(0)
                    paragraph.paragraph_format.keep_with_next = True
                    paragraph.paragraph_format.space_before = Pt(8)
                    paragraph.paragraph_format.space_after = Pt(4)

            for table in document.tables:
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                table.autofit = False
                columns = list(table._tbl.tblGrid.gridCol_lst)
                current = [max(1, int(column.get(qn("w:w")) or 1)) for column in columns]
                total = sum(current)
                available = round(max_width / 635)
                scaled = [max(1, round(value * available / total)) for value in current]
                scaled[-1] += available - sum(scaled)
                for index, column in enumerate(table.columns):
                    column.width = Twips(scaled[index])
                for row_index, row in enumerate(table.rows):
                    if row_index == 0:
                        tr_pr = row._tr.get_or_add_trPr()
                        if tr_pr.find(qn("w:tblHeader")) is None:
                            tr_pr.insert(0, OxmlElement("w:tblHeader"))
                    for column_index, cell in enumerate(row.cells):
                        cell.width = Twips(scaled[min(column_index, len(scaled) - 1)])
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.first_line_indent = Cm(0)
                            paragraph.paragraph_format.space_before = Pt(1)
                            paragraph.paragraph_format.space_after = Pt(1)
                            paragraph.paragraph_format.line_spacing = 1.15
                            for run in paragraph.runs:
                                run.font.size = Pt(8.5 if len(scaled) >= 5 else 9)
                                run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "SimSun")
                                if row_index == 0:
                                    run.font.bold = True

            for paragraph in document.paragraphs:
                if re.match(r"图 \d+", paragraph.text) and "插入位置" in paragraph.text:
                    paragraph.paragraph_format.first_line_indent = Cm(0)
                    paragraph.paragraph_format.keep_together = True
                    paragraph.paragraph_format.space_after = Pt(10)
                    for run in paragraph.runs:
                        run.font.size = Pt(9)

            body = document._body._element
            toc = body.find(qn("w:sdt"))
            if toc is None:
                raise ValueError("Pandoc did not produce a native TOC")
            toc.addprevious(page_break())
            toc.addnext(page_break())
            settings = document.settings._element
            update = settings.find(qn("w:updateFields"))
            if update is None:
                update = OxmlElement("w:updateFields")
                settings.append(update)
            update.set(qn("w:val"), "true")

        import zipfile
        rels_target = work / "unpacked/word/_rels/footnotes.xml.rels"
        if not rels_target.exists():
            with zipfile.ZipFile(work / "baseline.docx") as baseline:
                if "word/_rels/footnotes.xml.rels" in baseline.namelist():
                    rels_target.write_bytes(baseline.read("word/_rels/footnotes.xml.rels"))

        run_command([sys.executable, verify_dir / "opc.py", "pack", work / "unpacked", OUTPUT])
        run_command([sys.executable, docx_entry, "validate", OUTPUT])

    errors = audit_docx_package(OUTPUT, EXPECTED)
    if errors:
        raise ValueError(errors)
    import hashlib
    import zipfile
    with zipfile.ZipFile(OUTPUT) as archive:
        document_xml = archive.read("word/document.xml")
        footer_xml = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
        if b"TOC" not in document_xml or b"PAGE" not in footer_xml:
            raise ValueError("Native TOC or PAGE field is missing")
    report = {
        "status": "passed",
        "file": OUTPUT.name,
        "bytes": OUTPUT.stat().st_size,
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "native_math_objects": EXPECTED["math"],
        "embedded_images": EXPECTED["images"],
        "native_tables": EXPECTED["tables"],
        "native_toc_and_page_field": True,
        "validation_gate": "passed",
        "visual_qa": "Unavailable: no directly executable node.exe in this runtime; no LibreOffice fallback",
    }
    VALIDATION.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(OUTPUT), "validation": str(VALIDATION), **report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
