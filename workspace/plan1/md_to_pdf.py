#!/usr/bin/env python3
"""
将 draft.md 转换为 PDF
使用 Markdown -> HTML -> PDF 流程
"""

import markdown
from weasyprint import HTML, CSS
import os

# 读取 Markdown 文件
with open('draft.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# 转换 Markdown 为 HTML
html_content = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'toc']
)

# 添加 HTML 头部和样式
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>功率二极管反向恢复特性与载流子寿命及掺杂浓度的定量关系研究</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm;
            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
            }}
        }}
        
        body {{
            font-family: "Hiragino Sans GB", "SimHei", "DejaVu Sans", sans-serif;
            font-size: 11pt;
            line-height: 1.8;
            color: #333;
        }}
        
        h1 {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin-top: 2cm;
            margin-bottom: 1cm;
            line-height: 1.4;
        }}
        
        h2 {{
            font-size: 14pt;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            border-bottom: 1pt solid #333;
            padding-bottom: 0.3em;
        }}
        
        h3 {{
            font-size: 12pt;
            font-weight: bold;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
        }}
        
        h4 {{
            font-size: 11pt;
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }}
        
        p {{
            text-align: justify;
            margin-bottom: 0.8em;
            text-indent: 2em;
        }}
        
        /* 摘要特殊样式 */
        h2:contains("摘要") + p,
        h2:contains("摘要") ~ p:first-of-type {{
            text-indent: 0;
        }}
        
        /* 关键词样式 */
        p strong {{
            font-weight: bold;
        }}
        
        /* 表格样式 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            font-size: 10pt;
        }}
        
        th, td {{
            border: 1pt solid #333;
            padding: 8pt;
            text-align: center;
        }}
        
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        
        /* 图片样式 */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }}
        
        /* 公式样式 */
        code {{
            font-family: "Courier New", monospace;
            background-color: #f5f5f5;
            padding: 0.2em 0.4em;
            font-size: 10pt;
        }}
        
        /* 参考文献样式 */
        ol {{
            padding-left: 2em;
        }}
        
        li {{
            margin-bottom: 0.5em;
            text-align: justify;
        }}
        
        /* 列表样式 */
        ul {{
            padding-left: 2em;
        }}
        
        ul li {{
            margin-bottom: 0.3em;
        }}
        
        /* 强调文字 */
        strong {{
            font-weight: bold;
        }}
        
        em {{
            font-style: italic;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

# 保存 HTML 文件（可选，用于调试）
with open('draft.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("正在生成 PDF...")

# 使用 weasyprint 生成 PDF
HTML(string=html_template).write_pdf(
    '功率二极管反向恢复特性与载流子寿命及掺杂浓度的定量关系研究.pdf'
)

print("✅ PDF 生成成功！")
print("文件名: 功率二极管反向恢复特性与载流子寿命及掺杂浓度的定量关系研究.pdf")
