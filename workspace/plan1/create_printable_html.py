#!/usr/bin/env python3
"""
生成适合打印的 HTML 文件
用户可以在浏览器中打开并"打印为 PDF"
"""

import markdown
import re

# 读取 Markdown 文件
with open('draft.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# 转换 Markdown 为 HTML
html_body = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'toc', 'nl2br']
)

# 处理图片路径 - 转换为绝对路径或 data URL
import base64
from pathlib import Path

def image_to_data_url(match):
    alt_text = match.group(1)
    img_path = match.group(2)
    
    # 读取图片并转换为 base64
    try:
        with open(img_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
        
        # 获取文件扩展名
        ext = Path(img_path).suffix.lower()
        if ext == '.png':
            mime_type = 'image/png'
        elif ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        else:
            mime_type = 'image/png'
        
        return f'<img src="data:{mime_type};base64,{img_data}" alt="{alt_text}" style="max-width:100%;height:auto;display:block;margin:1em auto;"/>'
    except Exception as e:
        print(f"Warning: Could not embed image {img_path}: {e}")
        return match.group(0)

# 替换图片标签
html_body = re.sub(r'<img alt="([^"]*)" src="([^"]*)"[^/]*/?>', image_to_data_url, html_body)

# 创建完整的 HTML 文档
html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>功率二极管反向恢复特性与载流子寿命及掺杂浓度的定量关系研究</title>
    <style>
        /* 页面设置 */
        @page {{
            size: A4;
            margin: 2.5cm 2cm;
            
            @bottom-center {{
                content: counter(page);
                font-family: "Hiragino Sans GB", "SimHei", sans-serif;
                font-size: 10pt;
            }}
        }}
        
        /* 基础样式 */
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: "Hiragino Sans GB", "SimHei", "Microsoft YaHei", "DejaVu Sans", sans-serif;
            font-size: 11pt;
            line-height: 1.8;
            color: #333;
            max-width: 21cm;
            margin: 0 auto;
            padding: 2cm;
            background: white;
        }}
        
        /* 标题样式 */
        h1 {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin: 2cm 0 1cm 0;
            line-height: 1.4;
            color: #000;
        }}
        
        h2 {{
            font-size: 14pt;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            border-bottom: 2pt solid #333;
            padding-bottom: 0.3em;
            color: #000;
            page-break-after: avoid;
        }}
        
        h3 {{
            font-size: 12pt;
            font-weight: bold;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
            color: #000;
            page-break-after: avoid;
        }}
        
        h4 {{
            font-size: 11pt;
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.5em;
            color: #000;
        }}
        
        /* 段落样式 */
        p {{
            text-align: justify;
            margin-bottom: 0.8em;
            text-indent: 2em;
        }}
        
        /* 摘要和关键词 */
        h2 + p {{
            text-indent: 0;
        }}
        
        p strong {{
            font-weight: bold;
            color: #000;
        }}
        
        /* 表格样式 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5em 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }}
        
        th, td {{
            border: 1pt solid #333;
            padding: 8pt 6pt;
            text-align: center;
            vertical-align: middle;
        }}
        
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
            color: #000;
        }}
        
        tr:nth-child(even) {{
            background-color: #fafafa;
        }}
        
        /* 图片样式 */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1.5em auto;
            page-break-inside: avoid;
        }}
        
        /* 代码和公式 */
        code {{
            font-family: "Courier New", Consolas, monospace;
            background-color: #f5f5f5;
            padding: 0.2em 0.4em;
            font-size: 10pt;
            border-radius: 3px;
        }}
        
        pre {{
            background-color: #f5f5f5;
            padding: 1em;
            overflow-x: auto;
            font-size: 10pt;
            border-radius: 5px;
            margin: 1em 0;
        }}
        
        /* 列表样式 */
        ol, ul {{
            padding-left: 2em;
            margin-bottom: 0.8em;
        }}
        
        li {{
            margin-bottom: 0.5em;
            text-align: justify;
        }}
        
        /* 参考文献特殊样式 */
        ol li {{
            text-indent: 0;
            padding-left: 0.5em;
        }}
        
        /* 强调 */
        strong {{
            font-weight: bold;
            color: #000;
        }}
        
        em {{
            font-style: italic;
        }}
        
        /* 分页控制 */
        h2, h3, table, img {{
            page-break-inside: avoid;
        }}
        
        /* 打印优化 */
        @media print {{
            body {{
                padding: 0;
                background: white;
            }}
            
            .no-print {{
                display: none !important;
            }}
        }}
        
        /* 屏幕查看优化 */
        @media screen {{
            body {{
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
        }}
    </style>
</head>
<body>
    {html_body}
    
    <!-- 打印说明（屏幕显示时可见，打印时隐藏） -->
    <div class="no-print" style="margin-top: 3em; padding: 1em; background: #f0f0f0; border-radius: 5px;">
        <h3>📄 如何保存为 PDF</h3>
        <p><strong>方法1 - 浏览器打印（推荐）：</strong></p>
        <ol>
            <li>按 <kbd>Ctrl+P</kbd> (Windows/Linux) 或 <kbd>Cmd+P</kbd> (Mac)</li>
            <li>目标打印机选择"另存为 PDF"或"Save as PDF"</li>
            <li>纸张大小选择 A4</li>
            <li>边距选择"默认"或 2.5cm</li>
            <li>点击保存</li>
        </ol>
        
        <p><strong>方法2 - 使用在线工具：</strong></p>
        <ul>
            <li>访问 <a href="https://www.markdowntopdf.com/" target="_blank">markdowntopdf.com</a></li>
            <li>上传 draft.md 文件转换</li>
        </ul>
        
        <p><strong>方法3 - 使用 VS Code 插件：</strong></p>
        <ul>
            <li>安装 "Markdown PDF" 插件</li>
            <li>右键点击 draft.md 选择 "Markdown PDF: Export (pdf)"</li>
        </ul>
    </div>
</body>
</html>"""

# 保存 HTML 文件
output_filename = '功率二极管反向恢复特性与载流子寿命及掺杂浓度的定量关系研究.html'
with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(html_template)

print("=" * 70)
print("✅ HTML 文件生成成功！")
print("=" * 70)
print(f"\n文件名: {output_filename}")
print(f"大小: {len(html_template)/1024:.1f} KB")
print("\n图片已内嵌为 base64 编码，可离线查看")
print("\n使用方法:")
print("1. 在浏览器中打开此 HTML 文件")
print("2. 按 Ctrl+P (Win/Linux) 或 Cmd+P (Mac)")
print("3. 选择'另存为 PDF'")
print("4. 纸张选择 A4, 边距 2.5cm")
print("=" * 70)
