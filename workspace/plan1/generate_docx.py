#!/usr/bin/env python3
"""
从 draft_modified.md 生成 功率二极管反向恢复特性研究.docx
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
    """
    latex = latex_str.strip()
    if latex.startswith('$') and latex.endswith('$'):
        latex = latex[1:-1]
    
    # 检查复杂环境
    if '\\begin{cases}' in latex or '\\end{cases}' in latex:
        add_formula_as_text(para, latex)
        return False
    
    try:
        # 构建 OMML
        omml_xml = latex_to_omml(latex)
        if omml_xml:
            from docx.oxml import parse_xml
            element = parse_xml(omml_xml)
            para._p.append(element)
            return True
    except Exception as e:
        print(f"  公式转换失败: {e}")
    
    # 失败时回退到文本
    add_formula_as_text(para, latex)
    return False


def latex_to_omml(latex):
    """
    将 LaTeX 转换为 OMML XML
    """
    # 保留希腊字母，不要转换为英文
    greek_map = {
        '\\tau': 'τ', '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ',
        '\\delta': 'δ', '\\epsilon': 'ε', '\\theta': 'θ', '\\lambda': 'λ',
        '\\mu': 'μ', '\\pi': 'π', '\\sigma': 'σ', '\\phi': 'φ',
        '\\omega': 'ω', '\\rho': 'ρ', '\\eta': 'η', '\\kappa': 'κ',
    }
    
    for eng, grk in greek_map.items():
        latex = latex.replace(eng, grk)
    
    # 预定义替换
    latex = latex.replace('\\times', '×').replace('\\cdot', '·')
    latex = latex.replace('\\approx', '≈').replace('\\propto', '∝')
    latex = latex.replace('\\leq', '≤').replace('\\geq', '≥')
    latex = latex.replace('\\left', '').replace('\\right', '')
    latex = latex.replace('\\ln', 'ln')
    latex = latex.replace('\\', '')  # 移除剩余反斜杠
    latex = latex.replace('{', '').replace('}', '')
    latex = latex.replace('text', '')
    
    # 转义 XML
    latex = latex.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 分词处理
    tokens = tokenize_formula(latex)
    
    # 构建 OMML
    parts = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # 分数: a/b
        if token == '/' and i > 0 and i < len(tokens) - 1:
            if parts:
                num = parts.pop()
            else:
                num = '<m:r><m:t>1</m:t></m:r>'
            den = build_run(tokens[i+1])
            parts.append(f'<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>')
            i += 2
            continue
        
        # 下标模式: X _ Y (N _ A)
        if token == '_' and i > 0 and i + 1 < len(tokens):
            # 获取前一个标记作为 base（需要弹出）
            if parts and i > 0:
                prev_token = tokens[i-1]
                # 移除之前添加的 base
                parts.pop()
                sub = tokens[i + 1]
                parts.append(build_subscript(prev_token, sub))
                i += 2
                continue
        
        # 上标模式: X ^ Y
        if token == '^' and i > 0 and i + 1 < len(tokens):
            if parts:
                parts.pop()  # 移除 base
                base = tokens[i-1]
                sup = tokens[i + 1]
                parts.append(build_superscript(base, sup))
                i += 2
                continue
        
        # 普通标记
        if token in '+-=×·≈∝≤≥(),;':
            parts.append(f'<m:r><m:t>{token}</m:t></m:r>')
        elif token.strip() and token != '_' and token != '^':
            parts.append(build_run(token))
        
        i += 1
    
    if parts:
        return f'<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">{ "".join(parts) }</m:oMath>'
    return None


def tokenize_formula(formula):
    """
    将公式字符串分词，正确处理科学计数法
    """
    tokens = []
    i = 0
    formula = formula.strip()
    
    while i < len(formula):
        # 跳过空格
        if formula[i].isspace():
            i += 1
            continue
        
        # 运算符和标点
        if formula[i] in '+-=×·≈∝≤≥(),;/_^':
            tokens.append(formula[i])
            i += 1
            continue
        
        # 科学计数法: 1×10^-8 或 1×10^8
        sci_match = re.match(r'(\d+(?:\.\d+)?)×10\^(-?\d+)', formula[i:])
        if sci_match:
            tokens.append(sci_match.group(1))  # 系数
            tokens.append('×')
            tokens.append('10')
            tokens.append('^')
            tokens.append(sci_match.group(2))  # 指数
            i += sci_match.end()
            continue
        
        # 纯数字
        if formula[i].isdigit() or formula[i] == '.':
            j = i
            while j < len(formula) and (formula[j].isdigit() or formula[j] == '.'):
                j += 1
            tokens.append(formula[i:j])
            i = j
            continue
        
        # 变量名（希腊字母、英文）
        if formula[i].isalpha():
            j = i
            while j < len(formula) and formula[j].isalpha():
                j += 1
            tokens.append(formula[i:j])
            i = j
            continue
        
        i += 1
    
    return tokens


def build_run(text):
    """构建普通运行文本"""
    # 判断是否为变量（斜体）
    is_var = any(c.isalpha() for c in text)
    if is_var:
        return f'<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>{text}</m:t></m:r>'
    else:
        return f'<m:r><m:t>{text}</m:t></m:r>'


def build_subscript(base, sub):
    """构建下标"""
    base_run = build_run(base)
    sub_run = build_run(sub)
    return f'<m:sSub><m:e>{base_run}</m:e><m:sub>{sub_run}</m:sub></m:sSub>'


def build_superscript(base, sup):
    """构建上标"""
    if base:
        base_run = build_run(base)
        # 对于 10^n 这种，base 是空的
        sup_run = build_run(sup)
        return f'<m:sSup><m:e>{base_run}</m:e><m:sup>{sup_run}</m:sup></m:sSup>'
    else:
        sup_run = build_run(sup)
        return f'<m:sSup><m:e/><m:sup>{sup_run}</m:sup></m:sSup>'


def add_formula_as_text(para, latex):
    """
    将公式以文本形式显示（带下标/上标）
    """
    # 清理
    latex = latex.replace('\\', '').replace('{', '').replace('}', '')
    latex = latex.replace('text', '')
    latex = latex.replace('times', '×').replace('cdot', '·')
    latex = latex.replace('approx', '≈').replace('propto', '∝')
    latex = latex.replace('leq', '≤').replace('geq', '≥')
    latex = latex.replace('ln', 'ln')
    latex = latex.replace('begin', '').replace('end', '').replace('cases', '')
    latex = latex.replace('&', '&amp;')
    
    # 下标/上标模式
    patterns = [
        (r'Q_{rr}', 'Q', 'rr'), (r'Q_rr', 'Q', 'rr'),
        (r't_{rr}', 't', 'rr'), (r't_rr', 't', 'rr'),
        (r'V_{bi}', 'V', 'bi'), (r'V_bi', 'V', 'bi'),
        (r'V_F', 'V', 'F'), (r'V_A', 'V', 'A'),
        (r'R_{on}', 'R', 'on'), (r'R_on', 'R', 'on'),
        (r'N_A', 'N', 'A'), (r'N_D', 'N', 'D'),
        (r'J_F', 'J', 'F'), (r'I_F', 'I', 'F'),
        (r'I_{rr}', 'I', 'rr'), (r'I_rr', 'I', 'rr'),
        (r'τ_n', 'τ', 'n'), (r'τ_p', 'τ', 'p'),
        (r'n_i', 'n', 'i'), (r'x_j', 'x', 'j'),
        (r'E_c', 'E', 'c'), (r'E_crit', 'E', 'crit'),
        (r'kT', 'k', 'T'), (r'dI', 'd', 'I'), (r'dV', 'd', 'V'),
    ]
    
    i = 0
    text = latex
    while i < len(text):
        matched = False
        
        # 检查下标模式
        for pattern, base, sub in sorted(patterns, key=lambda x: -len(x[0])):
            p = pattern.replace('\\', '').replace('{', '').replace('}', '')
            if i + len(p) <= len(text) and text[i:i+len(p)] == p:
                run = para.add_run(base)
                run.font.italic = True
                run.font.name = 'Times New Roman'
                run = para.add_run(sub)
                run.font.subscript = True
                run.font.size = Pt(9)
                run.font.name = 'Times New Roman'
                i += len(p)
                matched = True
                break
        
        if not matched:
            # 检查上标
            sup_match = re.match(r'10\^(-?\d+)', text[i:])
            if sup_match:
                run = para.add_run('10')
                run.font.name = 'Times New Roman'
                run = para.add_run(sup_match.group(1))
                run.font.superscript = True
                run.font.size = Pt(9)
                i += sup_match.end()
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


def add_text_with_subscripts(para, text):
    """处理文本中的下标"""
    patterns = [
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
        ('E_c', 'E', 'c'), ('E_crit', 'E', 'crit'),
        ('kT', 'k', 'T'), ('dI', 'd', 'I'), ('dV', 'd', 'V'),
    ]
    
    i = 0
    while i < len(text):
        matched = False
        
        for pattern, base, sub in sorted(patterns, key=lambda x: -len(x[0])):
            p = pattern.replace('\\', '').replace('{', '').replace('}', '')
            if i + len(p) <= len(text) and text[i:i+len(p)] == p:
                run = para.add_run(base)
                run.font.italic = True
                run.font.name = 'Times New Roman'
                run = para.add_run(sub)
                run.font.subscript = True
                run.font.size = Pt(9)
                run.font.name = 'Times New Roman'
                i += len(p)
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


def create_docx():
    """主函数"""
    workspace_dir = '/Users/lihengzhong/Documents/repo/devsim/workspace/plan1'
    os.chdir(workspace_dir)
    
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    style.font.size = Pt(10.5)
    
    # 使用 draft_modified.md
    with open('draft_modified.md', 'r', encoding='utf-8') as f:
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
        
        # 表格标题
        elif line.startswith('**表') and line.endswith('**'):
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(line[2:-2])
            run.font.bold = True
            run.font.name = 'SimSun'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
        
        # 表格
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
    
    return output_path


if __name__ == '__main__':
    create_docx()
    print("\n" + "="*70)
    print("生成完成！使用 draft_modified.md 作为输入。")
    print("="*70)
