import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, ImageRun,
  ImportedXmlComponent, LevelFormat, PageBreak, PageNumber, Packer, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
  convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_collected_docx.js /absolute/path/output.docx");
const root = path.dirname(outputPath);
const manifest = JSON.parse(fs.readFileSync(path.join(root, "manifest.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const headingFont = { ascii: "Arial", hAnsi: "Arial", cs: "Arial", eastAsia: "Microsoft YaHei" };
const palette = { dark: "263238", primary: "37474F", light: "78909C", border: "D8E0E3", fill: "EEF3F6" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 24, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 150, line: 300 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: convertInchesToTwip(0.33) } });
const heading = (text, level = 1) => para(run(text, { bold: true, font: headingFont, size: level === 1 ? 30 : level === 2 ? 26 : 24, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
  spacing: { before: 240, after: 120 },
});
const stripMd = (value) => String(value)
  .replace(/\*\*(.*?)\*\*/g, "$1")
  .replace(/`([^`]*)`/g, "$1")
  .replace(/\*([^*]+)\*/g, "$1")
  .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1（$2）")
  .trim();
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level }) => {
    const indent = Math.max(0, level - 1) * 360;
    return `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${indent}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r></w:p>`;
  }).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-3&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const tocEntries = [];
const children = [
  para(run("前沿共生研究简报合订本", { bold: true, font: headingFont, size: 42, color: palette.dark }), { alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 300 } }),
  para(run("跨库证据 · 方法学负结果 · 可复现基础设施", { font: headingFont, size: 28, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 600 } }),
  para(run("千界花园学术系统 · 前沿共生计划", { size: 24 }), { alignment: AlignmentType.CENTER }),
  para(run("2026 年 10 月", { size: 24 }), { alignment: AlignmentType.CENTER }),
  para(run("研究简报／预印本草案，未同行评议", { bold: true, size: 24, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { before: 480 } }),
  para(run("花园流水线初稿，经数值、来源与证据边界核验修订", { size: 22, color: palette.light }), { alignment: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),
  heading("目录", 1),
  para(run("打开文档后可更新目录域以刷新页码。", { italics: true, color: palette.light })),
];

function tableFromRows(rows) {
  const width = 9000;
  const columns = rows[0].length;
  const cellWidth = Math.floor(width / columns);
  const widths = Array.from({ length: columns }, (_, i) => i === columns - 1 ? width - cellWidth * (columns - 1) : cellWidth);
  const makeRow = (row, isHeader) => new TableRow({ children: row.map((value, index) => new TableCell({
    width: { size: widths[index], type: WidthType.DXA },
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
    children: [para(run(stripMd(value), { size: 18, bold: isHeader }), { spacing: { after: 40, line: 240 } })],
  })) });
  return new Table({ width: { size: width, type: WidthType.DXA }, columnWidths: widths, rows: rows.map((row, index) => makeRow(row, index === 0)) });
}

function pngSize(buffer) {
  if (buffer.length < 24 || buffer.toString("ascii", 1, 4) !== "PNG") throw new Error("Not a PNG asset");
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

for (const item of manifest.papers) {
  const folder = path.join(root, item.folder);
  const lines = fs.readFileSync(path.join(folder, item.file), "utf8").split(/\r?\n/);
  children.push(new Paragraph({ children: [new PageBreak()] }));
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line === "---" || line === "=======") continue;
    if (line.startsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const current = lines[i].trim();
        if (!/^\|[\s:|-]+\|$/.test(current)) tableLines.push(current.slice(1, -1).split("|").map((cell) => cell.trim()));
        i++;
      }
      i--;
      if (tableLines.length) children.push(tableFromRows(tableLines));
      continue;
    }
    const image = line.match(/^!\[(.*?)\]\((.*?)\)$/);
    if (image) {
      const file = path.join(folder, image[2]);
      const buffer = fs.readFileSync(file);
      const size = pngSize(buffer);
      const width = Math.min(600, size.width);
      children.push(para(new ImageRun({ type: "png", data: buffer, transformation: { width, height: width * size.height / size.width } }), { alignment: AlignmentType.CENTER }));
      continue;
    }
    if (line.startsWith("### ")) {
      const text = stripMd(line.slice(4));
      tocEntries.push({ title: text, level: 2 });
      children.push(heading(text, 2));
    } else if (line.startsWith("## ")) {
      const text = stripMd(line.slice(3));
      tocEntries.push({ title: text, level: 1 });
      children.push(heading(text, 1));
    } else if (line.startsWith("# ")) {
      children.push(para(run(stripMd(line.slice(2)), { bold: true, font: headingFont, size: 36, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { after: 180 } }));
    } else if (line.startsWith("**") && line.endsWith("**") && !line.startsWith("**关键词")) {
      children.push(para(run(stripMd(line), { italics: true, size: 22 }), { alignment: AlignmentType.CENTER }));
    } else if (line.startsWith("*图注")) {
      children.push(para(run(stripMd(line), { italics: true, size: 20, color: palette.light }), { alignment: AlignmentType.CENTER }));
    } else if (line.startsWith("> ")) {
      children.push(para(run(stripMd(line.slice(2)), { size: 22, color: palette.primary }), { indent: { left: 360 }, shading: { type: ShadingType.CLEAR, fill: "F5F7F8" } }));
    } else if (/^[-] /.test(line)) {
      children.push(para(run(stripMd(line.slice(2))), { numbering: { reference: "paper-bullets", level: 0 } }));
    } else if (/^\d+\. /.test(line)) {
      children.push(para(run(stripMd(line.replace(/^\d+\. /, ""))), { numbering: { reference: "paper-numbers", level: 0 } }));
    } else if (line.startsWith("$$") || line.startsWith("\\[") || line.startsWith("\\(")) {
      children.push(para(run(line, { font: { ascii: "Consolas", hAnsi: "Consolas", cs: "Consolas", eastAsia: "SimSun" }, size: 20 }), { alignment: AlignmentType.CENTER }));
    } else {
      children.push(body(stripMd(line)));
    }
  }
}
children.splice(8, 0, toc(tocEntries));
children.splice(9, 0, new Paragraph({ children: [new PageBreak()] }));

const doc = new Document({
  styles: { paragraphStyles: [
    { id: "TOC1", name: "TOC 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 22 }, paragraph: { spacing: { after: 100, line: 280 } } },
    { id: "TOC2", name: "TOC 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 20 }, paragraph: { spacing: { after: 80, line: 260 } } },
  ] },
  features: { updateFields: true },
  numbering: { config: [
    { reference: "paper-bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 240 } } } }] },
    { reference: "paper-numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 240 } } } }] },
  ] },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: { default: new Header({ children: [para(run("前沿共生研究简报合订本", { bold: true, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT] }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
console.log(`Wrote ${outputPath}; ${tocEntries.length} TOC entries; ${manifest.papers.length} papers`);
