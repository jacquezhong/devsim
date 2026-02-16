#!/usr/bin/env python3
"""
从 draft_modified.md 生成 draft.docx
不是用工具转换，而是读取内容重新生成
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import re
import os

def create_docx():
    # 创建文档
    doc = Document()
    
    # 设置中文字体
    doc.styles['Normal'].font.name = 'SimSun'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    doc.styles['Normal'].font.size = Pt(10.5)  # 五号字
    
    # 读取 markdown 文件
    with open('draft_modified.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析并添加内容
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 处理标题
        if line.startswith('# '):
            # 一级标题
            title = line[2:]
            heading = doc.add_heading(title, level=0)
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(18)
                run.font.bold = True
                
        elif line.startswith('## '):
            # 二级标题
            title = line[3:]
            heading = doc.add_heading(title, level=1)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(14)
                run.font.bold = True
                
        elif line.startswith('### '):
            # 三级标题
            title = line[4:]
            heading = doc.add_heading(title, level=2)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(12)
                run.font.bold = True
                
        elif line.startswith('#### '):
            # 四级标题
            title = line[5:]
            heading = doc.add_heading(title, level=3)
            for run in heading.runs:
                run.font.name = 'SimHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
                run.font.size = Pt(10.5)
                run.font.bold = True
                
        # 处理图片
        elif line.startswith('!['):
            # 提取图片路径和标题
            match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match:
                caption = match.group(1)
                img_path = match.group(2)
                
                # 添加图片
                if os.path.exists(img_path):
                    doc.add_paragraph()  # 空行
                    para = doc.add_paragraph()
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = para.add_run()
                    run.add_picture(img_path, width=Inches(5.5))
                    
                    # 添加图注
                    caption_para = doc.add_paragraph()
                    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    caption_run = caption_para.add_run(caption)
                    caption_run.font.size = Pt(9)
                    caption_run.font.name = 'SimSun'
                    caption_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                    doc.add_paragraph()  # 空行
                else:
                    print(f"⚠️  图片不存在: {img_path}")
                    
        # 处理表格
        elif '|' in line and '---' not in line and i > 0 and '---' in lines[i-1]:
            # 表格内容
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            
            if len(table_lines) >= 2:  # 至少有表头和分隔行
                # 解析表格
                headers = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
                rows = []
                for table_line in table_lines[2:]:  # 跳过表头和分隔行
                    if table_line.strip():
                        row = [cell.strip() for cell in table_line.split('|')[1:-1]]
                        if row:
                            rows.append(row)
                
                if headers and rows:
                    # 添加表格
                    table = doc.add_table(rows=1+len(rows), cols=len(headers))
                    table.style = 'Light Grid Accent 1'
                    
                    # 表头
                    for j, header in enumerate(headers):
                        cell = table.rows[0].cells[j]
                        cell.text = header
                        for para in cell.paragraphs:
                            for run in para.runs:
                                run.font.bold = True
                                run.font.size = Pt(9)
                    
                    # 数据行
                    for row_idx, row_data in enumerate(rows):
                        for col_idx, cell_data in enumerate(row_data):
                            if col_idx < len(headers):
                                cell = table.rows[row_idx+1].cells[col_idx]
                                cell.text = cell_data
                                for para in cell.paragraphs:
                                    for run in para.runs:
                                        run.font.size = Pt(9)
                    
                    doc.add_paragraph()  # 空行
            continue
            
        # 处理公式（简化处理，用文本表示）
        elif line.startswith('$$') and line.endswith('$$'):
            # 行间公式
            formula = line[2:-2].strip()
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(formula)
            run.font.italic = True
            run.font.size = Pt(10.5)
            doc.add_paragraph()  # 空行
            
        # 处理列表
        elif line.startswith('- **') or line.startswith('* **'):
            # 加粗列表项
            text = line[2:]
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 去掉加粗标记
            para = doc.add_paragraph(text, style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            
        elif line.startswith('- ') or line.startswith('* '):
            # 普通列表项
            text = line[2:]
            para = doc.add_paragraph(text, style='List Bullet')
            para.paragraph_format.left_indent = Inches(0.25)
            
        # 处理普通段落
        elif line:
            # 处理加粗文本
            text = line
            text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', text)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            
            # 处理行内公式
            text = re.sub(r'\$([^$]+)\$', r'\1', text)
            
            if text.strip():
                para = doc.add_paragraph(text)
                para.paragraph_format.first_line_indent = Inches(0.5)  # 首行缩进
                
        i += 1
    
    # 保存文档
    output_path = 'draft.docx'
    doc.save(output_path)
    print(f"✅ Word文档已生成: {output_path}")
    
    # 显示文件信息
    file_size = os.path.getsize(output_path) / 1024
    print(f"📄 文件大小: {file_size:.1f} KB")
    
    return output_path

if __name__ == '__main__':
    create_docx()
    print("\n" + "="*70)
    print("生成完成！")
    print("="*70)
