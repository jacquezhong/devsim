#!/usr/bin/env python3
"""
从 draft.md 生成 功率二极管反向恢复特性研究.docx
修复下标和公式显示问题
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import re
import os
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def add_symbol_with_subscript(para, text):
    """
    解析文本中的下标符号并正确渲染
    支持的格式：N_A, τ_n, Q_rr, V_bi, R_on, t_rr 等
    """
    # 定义需要下标的模式：(基础字符, 下标字符)
    # 顺序很重要，先匹配长的再匹配短的
    subscript_patterns = [
        (r'Q_{rr}', 'Q', 'rr'),
        (r'Q_rr', 'Q', 'rr'),
        (r't_{rr}', 't', 'rr'),
        (r't_rr', 't', 'rr'),
        (r'V_{bi}', 'V', 'bi'),
        (r'V_bi', 'V', 'bi'),
        (r'V_F', 'V', 'F'),
        (r'V_A', 'V', 'A'),
        (r'R_{on}', 'R', 'on'),
        (r'R_on', 'R', 'on'),
        (r'N_A', 'N', 'A'),
        (r'N_D', 'N', 'D'),
        (r'J_F', 'J', 'F'),
        (r'I_F', 'I', 'F'),
        (r'I_{rr}', 'I', 'rr'),
        (r'I_rr', 'I', 'rr'),
        (r'τ_n', 'τ', 'n'),
        (r'τ_p', 'τ', 'p'),
        (r'n_i', 'n', 'i'),
        (r'x_j', 'x', 'j'),
        (r'E_c', 'E', 'c'),
        (r'E_{crit}', 'E', 'crit'),
        (r'E_crit', 'E', 'crit'),
        (r'kT', 'k', 'T'),
    ]
    
    # 特殊字符：上标
    superscript_patterns = [
        (r'cm\^{-3}', 'cm', '-3'),
        (r'10\^\{(.+?)\}', '10', None),  # 需要特殊处理
    ]
    
    # 首先处理 LaTeX 格式的上标（如 10^{14}）
    text = re.sub(r'1\s*×\s*10\^{\s*([+-]?\d+)\s*}', r'1×10^\1', text)
    text = re.sub(r'10\^{\s*([+-]?\d+)\s*}', r'10^\1', text)
    
    # 替换 LaTeX 格式为普通文本
    text = text.replace(r'\times', '×')
    text = text.replace(r'\cdot', '·')
    text = text.replace(r'\leq', '≤')
    text = text.replace(r'\geq', '≥')
    text = text.replace(r'\approx', '≈')
    text = text.replace(r'\propto', '∝')
    text = text.replace(r'\ln', 'ln')
    text = text.replace(r'\left', '')
    text = text.replace(r'\right', '')
    text = text.replace(r'\frac', '')
    
    # 逐个处理下标模式
    i = 0
    while i < len(text):
        matched = False
        
        # 尝试匹配下标模式（按长度降序）
        for pattern, base, sub in sorted(subscript_patterns, key=lambda x: -len(x[0])):
            pattern_clean = pattern.replace('\\', '').replace('{', '').replace('}', '')
            pattern_simple = pattern.replace('_{', '').replace('}', '')
            if text[i:i+len(pattern_clean)] == pattern_clean or text[i:i+len(pattern_simple)] == pattern_simple:
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
                # 找到完整的数字
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
                # 添加普通字符
                run = para.add_run(text[i])
                run.font.name = 'Times New Roman'
                i += 1


def render_formula_as_image(latex_str, font_size=12, dpi=150):
    """
    将LaTeX公式渲染为图片
    """
    # 清理LaTeX字符串 - 处理已经转义的反斜杠
    latex_str = latex_str.strip()
    
    # 如果字符串已经被双重转义（\\），需要还原为单个反斜杠（\）
    if '\\\\' in latex_str:
        latex_str = latex_str.replace('\\\\', '\\')
    
    # 移除对齐符号
    latex_str = latex_str.replace('&', '')
    
    # 创建图形
    fig_width = min(8, max(2, len(latex_str) * 0.12))
    fig_height = 0.5 if 'cases' in latex_str or '\\' in latex_str else 0.35
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    try:
        ax.text(0.5, 0.5, f'${latex_str}$',
                ha='center', va='center', fontsize=font_size,
                transform=ax.transAxes)
    except Exception as e:
        # 如果失败，尝试简化公式
        print(f"  尝试简化公式: {latex_str[:50]}...")
        simple_str = latex_str.replace('\\', '').replace('{', '').replace('}', '')
        ax.text(0.5, 0.5, simple_str,
                ha='center', va='center', fontsize=font_size,
                transform=ax.transAxes)
    
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    # 保存到内存
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=dpi,
                bbox_inches='tight', pad_inches=0.05,
                facecolor='white', edgecolor='none')
    plt.close(fig)
    img_buffer.seek(0)
    
    return img_buffer


def add_formula_to_doc(doc, latex_str, display_mode=True):
    """
    向文档添加公式
    display_mode: True为行间公式（居中），False为行内
    """
    if display_mode:
        doc.add_paragraph()  # 空行
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        para = doc.add_paragraph()
    
    try:
        img_buffer = render_formula_as_image(latex_str)
        run = para.add_run()
        run.add_picture(img_buffer, height=Inches(0.35))
    except Exception as e:
        # 如果渲染失败，使用文本替代
        print(f"⚠️  公式渲染失败: {latex_str[:50]}... 错误: {e}")
        run = para.add_run(f"[{latex_str}]")
        run.font.italic = True
        run.font.size = Pt(10)
    
    if display_mode:
        doc.add_paragraph()  # 空行


def process_inline_text(doc, text, para=None):
    """
    处理包含行内公式和普通文本的段落
    """
    if para is None:
        para = doc.add_paragraph()
        para.paragraph_format.first_line_indent = Inches(0.5)
    
    # 分割行内公式和普通文本
    parts = re.split(r'(\$[^$]+\$)', text)
    
    for part in parts:
        if part.startswith('$') and part.endswith('$') and len(part) > 2:
            # 行内公式
            formula = part[1:-1]
            try:
                img_buffer = render_formula_as_image(formula, font_size=11)
                run = para.add_run()
                run.add_picture(img_buffer, height=Inches(0.25))
            except Exception as e:
                # 失败时使用文本下标
                print(f"⚠️  行内公式渲染失败，使用文本替代: {formula[:30]}...")
                add_symbol_with_subscript(para, formula)
        else:
            # 普通文本，处理下标
            if part.strip():
                add_symbol_with_subscript(para, part)
    
    return para


def create_docx():
    """主函数：从 draft.md 生成 docx"""
    
    # 创建工作目录
    workspace_dir = '/Users/lihengzhong/Documents/repo/devsim/workspace/plan1'
    os.chdir(workspace_dir)
    
    # 创建文档
    doc = Document()
    
    # 设置默认字体
    doc.styles['Normal'].font.name = 'Times New Roman'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    doc.styles['Normal'].font.size = Pt(10.5)
    
    # 读取markdown文件
    with open('draft.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # 跳过空行（但保留段落间距）
        if not line:
            i += 1
            continue
        
        # 处理一级标题（论文标题）
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
        
        # 处理二级标题（章节标题）
        elif line.startswith('## '):
            title = line[3:].strip()
            heading = doc.add_heading(title, level=1)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(14)
                run.font.bold = True
        
        # 处理三级标题（小节标题）
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
        
        # 处理行间公式 $$...$$
        elif line.startswith('$$') and line.endswith('$$'):
            formula = line[2:-2].strip()
            if formula:
                add_formula_to_doc(doc, formula, display_mode=True)
        
        # 处理多行公式（以$$开始）
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
                add_formula_to_doc(doc, formula, display_mode=True)
        
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
            # 收集表格所有行
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            
            # 解析表格
            if len(table_lines) >= 3:  # 表头 + 分隔 + 至少一行数据
                headers = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
                rows = []
                for table_line in table_lines[2:]:  # 跳过表头和分隔行
                    if table_line.strip():
                        row = [cell.strip() for cell in table_line.split('|')[1:-1]]
                        if row and any(cell for cell in row):
                            rows.append(row)
                
                if headers and rows:
                    table = doc.add_table(rows=1+len(rows), cols=len(headers))
                    table.style = 'Light Grid Accent 1'
                    
                    # 填充表头
                    for j, header in enumerate(headers):
                        if j < len(headers):
                            cell = table.rows[0].cells[j]
                            cell.text = header
                            for para in cell.paragraphs:
                                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                for run in para.runs:
                                    run.font.bold = True
                                    run.font.size = Pt(9)
                    
                    # 填充数据
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
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 移除加粗标记但保留内容
            para = doc.add_paragraph(style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            # 处理可能的行内公式
            if '$' in text:
                process_inline_text(doc, text, para)
            else:
                add_symbol_with_subscript(para, text)
        
        # 处理普通列表项
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:]
            para = doc.add_paragraph(style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            if '$' in text:
                process_inline_text(doc, text, para)
            else:
                add_symbol_with_subscript(para, text)
        
        # 处理参考文献 [1], [2] 等
        elif re.match(r'^\[\d+\]', line):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.25)
            para.paragraph_format.first_line_indent = Inches(-0.25)
            # 处理行内公式和文本
            if '$' in line:
                process_inline_text(doc, line, para)
            else:
                add_symbol_with_subscript(para, line)
        
        # 处理普通段落（包含行内公式）
        elif '$' in line:
            process_inline_text(doc, line)
        
        # 处理普通段落（不含公式，但可能有下标）
        else:
            para = doc.add_paragraph()
            para.paragraph_format.first_line_indent = Inches(0.5)
            add_symbol_with_subscript(para, line)
        
        i += 1
    
    # 保存文档
    output_path = '功率二极管反向恢复特性研究.docx'
    doc.save(output_path)
    print(f"✅ Word文档已生成: {output_path}")
    
    # 显示文件信息
    file_size = os.path.getsize(output_path) / 1024
    print(f"📄 文件大小: {file_size:.1f} KB")
    print(f"📍 保存位置: {os.path.abspath(output_path)}")
    
    return output_path


if __name__ == '__main__':
    create_docx()
    print("\n" + "="*70)
    print("生成完成！请检查公式和下标是否正确显示。")
    print("="*70)
