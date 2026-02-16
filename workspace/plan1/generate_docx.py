#!/usr/bin/env python3
"""
从 draft.md 生成 功率二极管反向恢复特性研究.docx
使用 Word 原生 OMML 公式格式和正确的粗体渲染
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import parse_xml
import re
import os

try:
    from latex2mathml.converter import convert as latex_to_mathml
    from mathml2omml import convert as mathml_to_omml
    MATH_SUPPORT = True
except ImportError:
    print("⚠️  未安装 latex2mathml 或 mathml2omml，公式将以文本形式显示")
    print("   安装命令: pip install latex2mathml mathml2omml")
    MATH_SUPPORT = False


def add_omml_formula(para, latex_formula):
    """
    将 LaTeX 公式转换为 OMML 并添加到段落
    如果转换失败，使用优化的文本替代方案
    """
    if not MATH_SUPPORT:
        # 备用方案：使用文本下标
        add_formula_as_text(para, latex_formula)
        return
    
    try:
        # 简化公式，移除可能导致问题的复杂语法
        simplified = simplify_latex(latex_formula)
        
        # LaTeX -> MathML -> OMML
        mathml = latex_to_mathml(simplified)
        omml = mathml_to_omml(mathml)
        
        # 解析 OMML XML
        omml_element = parse_xml(omml)
        para._p.append(omml_element)
    except Exception as e:
        # 失败时使用优化的文本替代
        add_formula_as_text(para, latex_formula)


def simplify_latex(latex):
    """
    简化 LaTeX 公式，移除不支持的复杂语法
    """
    # 移除 cases 环境（Word 公式不支持）
    if '\\begin{cases}' in latex:
        # 转换为简单文本表示
        latex = re.sub(r'\\begin\{cases\}(.*?)\\end\{cases\}', 
                       lambda m: m.group(1).replace('\\\\', '; '), 
                       latex, flags=re.DOTALL)
    
    # 简化 frac 为 / 
    latex = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\\1)/(\\2)', latex)
    
    # 简化 left/right
    latex = latex.replace('\\left', '').replace('\\right', '')
    
    # 简化 times 和 cdot
    latex = latex.replace('\\times', '×').replace('\\cdot', '·')
    
    # 简化 approx
    latex = latex.replace('\\approx', '≈').replace('\\propto', '∝')
    
    # 简化 ln
    latex = latex.replace('\\ln', 'ln')
    
    # 简化 sqrt
    latex = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\\1)', latex)
    
    return latex


def add_formula_as_text(para, latex):
    """
    将 LaTeX 公式以优化的文本形式显示（带下标/上标）
    """
    # 清理 LaTeX
    text = latex.strip()
    
    # 转换常见数学符号
    replacements = [
        (r'\\times', '×'), (r'\\cdot', '·'),
        (r'\\approx', '≈'), (r'\\propto', '∝'),
        (r'\\leq', '≤'), (r'\\geq', '≥'),
        (r'\\ln', 'ln'), (r'\\frac', ''), 
        (r'\\left', ''), (r'\\right', ''),
        (r'\\begin\{cases\}', ''), (r'\\end\{cases\}', ''),
        (r'\\\\', '; '),
        (r'\{', ''), (r'\}', ''),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    # 使用下标/上标渲染
    add_text_with_subscripts(para, text)


def add_text_with_subscripts(para, text):
    """
    解析文本中的下标/上标符号并正确渲染为文本格式
    支持的格式：N_A, τ_n, Q_rr, V_bi, R_on, t_rr, 10^14 等
    """
    # 定义下标模式 (基础字符, 下标字符)
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
        ('E_c', 'E', 'c'), ('E_{crit}', 'E', 'crit'), ('E_crit', 'E', 'crit'),
        ('kT', 'k', 'T'), ('dI', 'd', 'I'), ('dV', 'd', 'V'),
    ]
    
    i = 0
    while i < len(text):
        matched = False
        
        # 尝试匹配下标模式（按长度降序，确保先匹配长的）
        for pattern, base, sub in sorted(subscript_patterns, key=lambda x: -len(x[0])):
            pattern_clean = pattern.replace('\\', '').replace('{', '').replace('}', '')
            pattern_simple = pattern.replace('_{', '').replace('}', '')
            
            if i + len(pattern_clean) <= len(text) and \
               (text[i:i+len(pattern_clean)] == pattern_clean or 
                (i + len(pattern_simple) <= len(text) and text[i:i+len(pattern_simple)] == pattern_simple)):
                # 添加基础字符（斜体）
                run = para.add_run(base)
                run.font.italic = True
                run.font.name = 'Times New Roman'
                # 添加下标字符
                run = para.add_run(sub)
                run.font.subscript = True
                run.font.size = Pt(9)
                run.font.name = 'Times New Roman'
                i += len(pattern_clean)
                matched = True
                break
        
        if not matched:
            # 检查是否是上标数字（如 ^14, ^-3）
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
                # 处理 LaTeX 转义字符
                if text[i:i+2] == '\\' and i + 1 < len(text):
                    # 跳过反斜杠，添加下一个字符
                    i += 1
                    if i < len(text):
                        run = para.add_run(text[i])
                        run.font.name = 'Times New Roman'
                        i += 1
                else:
                    # 添加普通字符
                    run = para.add_run(text[i])
                    run.font.name = 'Times New Roman'
                    i += 1


def process_inline_formatting(para, text):
    """
    处理行内的粗体、斜体和公式
    支持：**粗体**, *斜体*, $公式$
    """
    # 分割文本，保留分隔符
    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|\$[^$]+\$)', text)
    
    for part in parts:
        if not part:
            continue
            
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            # 粗体
            content = part[2:-2]
            run = para.add_run(content)
            run.font.bold = True
            run.font.name = 'Times New Roman'
            
        elif part.startswith('*') and part.endswith('*') and len(part) > 2 and not part.startswith('**'):
            # 斜体
            content = part[1:-1]
            run = para.add_run(content)
            run.font.italic = True
            run.font.name = 'Times New Roman'
            
        elif part.startswith('$') and part.endswith('$') and len(part) > 2:
            # 行内公式
            formula = part[1:-1]
            add_omml_formula(para, formula)
            
        else:
            # 普通文本，处理下标
            if part.strip():
                add_text_with_subscripts(para, part)


def create_docx():
    """主函数：从 draft.md 生成 docx"""
    
    # 工作目录
    workspace_dir = '/Users/lihengzhong/Documents/repo/devsim/workspace/plan1'
    os.chdir(workspace_dir)
    
    # 创建文档
    doc = Document()
    
    # 设置默认字体
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    style.font.size = Pt(10.5)
    
    # 读取markdown文件
    with open('draft.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # 跳过空行
        if not line:
            i += 1
            continue
        
        # 处理一级标题
        if line.startswith('# ') and not line.startswith('## '):
            title = line[2:].strip()
            heading = doc.add_heading(title, level=0)
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(16)
                run.font.bold = True
            doc.add_paragraph()
        
        # 处理二级标题
        elif line.startswith('## '):
            title = line[3:].strip()
            heading = doc.add_heading(title, level=1)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(14)
                run.font.bold = True
        
        # 处理三级标题
        elif line.startswith('### '):
            title = line[4:].strip()
            heading = doc.add_heading(title, level=2)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(12)
                run.font.bold = True
        
        # 处理四级标题
        elif line.startswith('#### '):
            title = line[5:].strip()
            heading = doc.add_heading(title, level=3)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(10.5)
                run.font.bold = True
        
        # 处理图片
        elif line.startswith('!['):
            match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match:
                caption = match.group(1)
                img_path = match.group(2)
                
                if os.path.exists(img_path):
                    doc.add_paragraph()
                    para = doc.add_paragraph()
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = para.add_run()
                    try:
                        run.add_picture(img_path, width=Inches(5.5))
                    except Exception as e:
                        print(f"⚠️  图片加载失败: {img_path} - {e}")
                    
                    # 图注
                    caption_para = doc.add_paragraph()
                    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    caption_run = caption_para.add_run(caption)
                    caption_run.font.size = Pt(9)
                    caption_run.font.name = 'SimSun'
                    caption_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                    doc.add_paragraph()
                else:
                    print(f"⚠️  图片不存在: {img_path}")
        
        # 处理行间公式
        elif line.startswith('$$') and line.endswith('$$') and len(line) > 4:
            formula = line[2:-2].strip()
            if formula:
                doc.add_paragraph()
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_omml_formula(para, formula)
                doc.add_paragraph()
        
        # 处理多行公式
        elif line.startswith('$$') and not line.endswith('$$'):
            formula_lines = [line[2:].strip()]
            i += 1
            while i < len(lines) and not lines[i].strip().endswith('$$'):
                formula_lines.append(lines[i].strip())
                i += 1
            if i < len(lines):
                formula_lines.append(lines[i].strip()[:-2].strip())
            formula = '\n'.join(formula_lines)
            if formula:
                doc.add_paragraph()
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_omml_formula(para, formula)
                doc.add_paragraph()
        
        # 处理表格标题
        elif line.startswith('**表') and line.endswith('**'):
            table_title = line[2:-2]
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(table_title)
            run.font.bold = True
            run.font.size = Pt(10.5)
            run.font.name = 'SimSun'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
        
        # 处理表格
        elif '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            
            if len(table_lines) >= 3:
                headers = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
                rows = []
                for table_line in table_lines[2:]:
                    if table_line.strip():
                        row = [cell.strip() for cell in table_line.split('|')[1:-1]]
                        if row and any(cell for cell in row):
                            rows.append(row)
                
                if headers and rows:
                    table = doc.add_table(rows=1+len(rows), cols=len(headers))
                    table.style = 'Light Grid Accent 1'
                    
                    for j, header in enumerate(headers):
                        if j < len(headers):
                            cell = table.rows[0].cells[j]
                            cell.text = header
                            for para in cell.paragraphs:
                                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                for run in para.runs:
                                    run.font.bold = True
                                    run.font.size = Pt(9)
                    
                    for row_idx, row_data in enumerate(rows):
                        for col_idx, cell_data in enumerate(row_data):
                            if col_idx < len(headers):
                                cell = table.rows[row_idx+1].cells[col_idx]
                                cell.text = cell_data
                                for para in cell.paragraphs:
                                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    for run in para.runs:
                                        run.font.size = Pt(9)
                    
                    doc.add_paragraph()
            continue
        
        # 处理加粗列表项
        elif re.match(r'^[\-\*]\s+\*\*', line):
            text = re.sub(r'^[\-\*]\s+', '', line)
            para = doc.add_paragraph(style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            process_inline_formatting(para, text)
        
        # 处理普通列表项
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:]
            para = doc.add_paragraph(style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            process_inline_formatting(para, text)
        
        # 处理参考文献
        elif re.match(r'^\[\d+\]', line):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            process_inline_formatting(para, line)
        
        # 处理普通段落（包含粗体、斜体、公式）
        else:
            para = doc.add_paragraph()
            para.paragraph_format.first_line_indent = Inches(0.5)
            process_inline_formatting(para, line)
        
        i += 1
    
    # 保存文档
    output_path = '功率二极管反向恢复特性研究.docx'
    doc.save(output_path)
    print(f"✅ Word文档已生成: {output_path}")
    
    file_size = os.path.getsize(output_path) / 1024
    print(f"📄 文件大小: {file_size:.1f} KB")
    print(f"📍 保存位置: {os.path.abspath(output_path)}")
    
    if not MATH_SUPPORT:
        print("\n⚠️  提示：如需更好的公式显示效果，请安装:")
        print("   pip install latex2mathml mathml2omml")
    
    return output_path


if __name__ == '__main__':
    create_docx()
    print("\n" + "="*70)
    print("生成完成！请检查粗体和公式是否正确显示。")
    print("="*70)
