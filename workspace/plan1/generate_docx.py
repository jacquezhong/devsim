#!/usr/bin/env python3
"""
从 draft.md 生成 功率二极管反向恢复特性研究.docx
使用 Word 原生 OMML 公式格式（可编辑）
"""

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import re
import os


def add_formula_with_omml(para, latex_str):
    """
    添加 Word 原生公式（OMML格式，可编辑）
    使用简化方法：直接构建 OMML XML
    """
    latex = latex_str.strip()
    if latex.startswith('$') and latex.endswith('$'):
        latex = latex[1:-1]
    
    # 简化 LaTeX
    latex = latex.replace('\\times', '×').replace('\\cdot', '·')
    latex = latex.replace('\\approx', '≈').replace('\\propto', '∝')
    latex = latex.replace('\\leq', '≤').replace('\\geq', '≥')
    latex = latex.replace('\\left', '').replace('\\right', '')
    latex = latex.replace('\\ln', 'ln')
    latex = latex.replace('\\text{', '').replace('}', '')
    latex = latex.replace('\\begin{cases}', '').replace('\\end{cases}', '')
    latex = latex.replace('\\\\', '; ')
    
    try:
        # 构建简单的 OMML XML
        omml_xml = build_simple_omml(latex)
        if omml_xml:
            from docx.oxml import parse_xml
            element = parse_xml(omml_xml)
            para._p.append(element)
            return True
    except Exception as e:
        pass
    
    # 失败时使用文本下标
    add_text_with_subscripts(para, latex)
    return False


def build_simple_omml(latex):
    """
    构建简单的 OMML XML
    """
    # 转义 XML 特殊字符
    latex = latex.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    parts = []
    i = 0
    while i < len(latex):
        # 分数
        frac_match = re.match(r'\\frac\{([^}]+)\}\{([^}]+)\}', latex[i:])
        if frac_match:
            num = escape_xml(frac_match.group(1))
            den = escape_xml(frac_match.group(2))
            parts.append(f'<m:f><m:num><m:r><m:t>{num}</m:t></m:r></m:num><m:den><m:r><m:t>{den}</m:t></m:r></m:den></m:f>')
            i += frac_match.end()
            continue
        
        # 根号
        sqrt_match = re.match(r'\\sqrt\{([^}]+)\}', latex[i:])
        if sqrt_match:
            arg = escape_xml(sqrt_match.group(1))
            parts.append(f'<m:rad><m:radPr><m:hideDeg m:val="1"/></m:radPr><m:deg/><m:e><m:r><m:t>{arg}</m:t></m:r></m:e></m:rad>')
            i += sqrt_match.end()
            continue
        
        # 下标
        sub_match = re.match(r'([a-zA-Zτ])_\{?([a-zA-Z0-9]+)\}?', latex[i:])
        if sub_match:
            base = sub_match.group(1)
            sub = sub_match.group(2)
            parts.append(f'<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>{base}</m:t></m:r></m:e><m:sub><m:r><m:t>{sub}</m:t></m:r></m:sub></m:sSub>')
            i += sub_match.end()
            continue
        
        # 上标
        sup_match = re.match(r'([0-9.]+)?×?10\^\{?([0-9\-]+)\}?', latex[i:])
        if sup_match:
            base = sup_match.group(1) or ''
            sup = sup_match.group(2)
            if base:
                parts.append(f'<m:r><m:t>{base}×10</m:t></m:r><m:sSup><m:e/><m:sup><m:r><m:t>{sup}</m:t></m:r></m:sup></m:sSup>')
            else:
                parts.append(f'<m:r><m:t>10</m:t></m:r><m:sSup><m:e/><m:sup><m:r><m:t>{sup}</m:t></m:r></m:sup></m:sSup>')
            i += sup_match.end()
            continue
        
        # 普通字符
        if latex[i] in '+-=×·≈∝≤≥()[]/':
            parts.append(f'<m:r><m:t>{latex[i]}</m:t></m:r>')
        elif latex[i].isalnum() or latex[i] in ' ;,.':
            if latex[i].isalpha():
                parts.append(f'<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>{latex[i]}</m:t></m:r>')
            else:
                parts.append(f'<m:r><m:t>{latex[i]}</m:t></m:r>')
        
        i += 1
    
    if parts:
        return f'<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">{"".join(parts)}</m:oMath>'
    return None


def escape_xml(text):
    """转义 XML 特殊字符"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def add_text_with_subscripts(para, text):
    """添加带下标的文本"""
    subscript_patterns = [
        ('Q_{rr}', 'Q', 'rr'), ('Q_rr', 'Q', 'rr'),
        ('t_{rr}', 't', 'rr'), ('t_rr', 't', 'rr'),
        ('V_{bi}', 'V', 'bi'), ('V_bi', 'V', 'bi'),
        ('V_F', 'V', 'F'), ('V_A', 'V', 'A'),
        ('R_{on}', 'R', 'on'), ('R_on', 'R', 'on'),
        ('N_A', 'N', 'A'), ('N_D', 'N', 'D'),
        ('J_F', 'J', 'F'), ('I_F', 'I', 'F'),
        ('I_{rr}', 'I', 'rr'), ('I_rr', 'I', 'rr'),
        ('τ_n', 'τ', 'n'), ('τ_p', 'τ', 'p'),
        ('n_i', 'n', 'i'), ('x_j', 'x', 'j'),
        ('E_c', 'E', 'c'), ('E_{crit}', 'E', 'crit'),
        ('kT', 'k', 'T'), ('dI', 'd', 'I'), ('dV', 'd', 'V'),
    ]
    
    i = 0
    while i < len(text):
        matched = False
        for pattern, base, sub in sorted(subscript_patterns, key=lambda x: -len(x[0])):
            clean = pattern.replace('\\', '').replace('{', '').replace('}', '')
            simple = pattern.replace('_{', '').replace('}', '')
            
            if i + len(clean) <= len(text) and (text[i:i+len(clean)] == clean or text[i:i+len(simple)] == simple):
                run = para.add_run(base)
                run.font.italic = True
                run.font.name = 'Times New Roman'
                run = para.add_run(sub)
                run.font.subscript = True
                run.font.size = Pt(9)
                run.font.name = 'Times New Roman'
                i += len(clean)
                matched = True
                break
        
        if not matched:
            if i < len(text) - 1 and text[i] == '^' and (text[i+1].isdigit() or text[i+1] in '+-'):
                j = i + 2 if text[i+1] in '+-' else i + 1
                while j < len(text) and text[j].isdigit():
                    j += 1
                if j > i + 1:
                    run = para.add_run(text[i+1:j])
                    run.font.superscript = True
                    run.font.size = Pt(9)
                    i = j
                    matched = True
            
            if not matched:
                run = para.add_run(text[i])
                run.font.name = 'Times New Roman'
                i += 1


def process_inline_formatting(para, text):
    """处理行内格式（粗体、斜体、公式）"""
    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|\$[^$]+\$)', text)
    
    for part in parts:
        if not part:
            continue
        
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            run = para.add_run(part[2:-2])
            run.font.bold = True
            run.font.name = 'Times New Roman'
        elif part.startswith('*') and part.endswith('*') and len(part) > 2 and not part.startswith('**'):
            run = para.add_run(part[1:-1])
            run.font.italic = True
            run.font.name = 'Times New Roman'
        elif part.startswith('$') and part.endswith('$') and len(part) > 2:
            add_formula_with_omml(para, part[1:-1])
        else:
            if part.strip():
                add_text_with_subscripts(para, part)


def create_docx():
    """主函数"""
    workspace_dir = '/Users/lihengzhong/Documents/repo/devsim/workspace/plan1'
    os.chdir(workspace_dir)
    
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    style.font.size = Pt(10.5)
    
    with open('draft.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        if not line:
            i += 1
            continue
        
        # 标题
        if line.startswith('# ') and not line.startswith('## '):
            heading = doc.add_heading(line[2:], level=0)
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(16)
                run.font.bold = True
            doc.add_paragraph()
        
        elif line.startswith('## '):
            heading = doc.add_heading(line[3:], level=1)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(14)
                run.font.bold = True
        
        elif line.startswith('### '):
            heading = doc.add_heading(line[4:], level=2)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(12)
                run.font.bold = True
        
        elif line.startswith('#### '):
            heading = doc.add_heading(line[5:], level=3)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(10.5)
                run.font.bold = True
        
        # 图片
        elif line.startswith('!['):
            match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match and os.path.exists(match.group(2)):
                doc.add_paragraph()
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                para.add_run().add_picture(match.group(2), width=Inches(5.5))
                
                caption = doc.add_paragraph()
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = caption.add_run(match.group(1))
                run.font.size = Pt(9)
                run.font.name = 'SimSun'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                doc.add_paragraph()
        
        # 行间公式
        elif line.startswith('$$') and line.endswith('$$') and len(line) > 4:
            doc.add_paragraph()
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_formula_with_omml(para, line[2:-2])
            doc.add_paragraph()
        
        # 多行公式
        elif line.startswith('$$') and not line.endswith('$$'):
            formula_lines = [line[2:]]
            i += 1
            while i < len(lines) and not lines[i].strip().endswith('$$'):
                formula_lines.append(lines[i].strip())
                i += 1
            if i < len(lines):
                formula_lines.append(lines[i].strip()[:-2])
            doc.add_paragraph()
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_formula_with_omml(para, '\n'.join(formula_lines))
            doc.add_paragraph()
        
        # 表格
        elif line.startswith('**表') and line.endswith('**'):
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(line[2:-2])
            run.font.bold = True
            run.font.name = 'SimSun'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
        
        elif '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            
            if len(table_lines) >= 3:
                headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                rows = [[c.strip() for c in row.split('|')[1:-1]] for row in table_lines[2:] if row.strip()]
                
                if headers and rows:
                    table = doc.add_table(rows=1+len(rows), cols=len(headers))
                    table.style = 'Light Grid Accent 1'
                    
                    for j, h in enumerate(headers):
                        table.rows[0].cells[j].text = h
                        for p in table.rows[0].cells[j].paragraphs:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            for r in p.runs:
                                r.font.bold = True
                                r.font.size = Pt(9)
                    
                    for ri, row in enumerate(rows):
                        for ci, cell in enumerate(row):
                            if ci < len(headers):
                                table.rows[ri+1].cells[ci].text = cell
                                for p in table.rows[ri+1].cells[ci].paragraphs:
                                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    for r in p.runs:
                                        r.font.size = Pt(9)
                    
                    doc.add_paragraph()
            continue
        
        # 列表
        elif re.match(r'^[\-\*]\s+\*\*', line):
            para = doc.add_paragraph(style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            process_inline_formatting(para, re.sub(r'^[\-\*]\s+', '', line))
        
        elif line.startswith('- ') or line.startswith('* '):
            para = doc.add_paragraph(style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            process_inline_formatting(para, line[2:])
        
        # 参考文献
        elif re.match(r'^\[\d+\]', line):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            process_inline_formatting(para, line)
        
        # 普通段落
        else:
            para = doc.add_paragraph()
            para.paragraph_format.first_line_indent = Inches(0.5)
            process_inline_formatting(para, line)
        
        i += 1
    
    output_path = '功率二极管反向恢复特性研究.docx'
    doc.save(output_path)
    print(f"✅ Word文档已生成: {output_path}")
    print(f"📄 文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
    print(f"📍 保存位置: {os.path.abspath(output_path)}")
    
    return output_path


if __name__ == '__main__':
    create_docx()
    print("\n" + "="*70)
    print("生成完成！公式现在应该可以在Word中编辑了。")
    print("="*70)
