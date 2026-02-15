#!/bin/bash
# 使用多种方法尝试生成 PDF

echo "正在尝试生成 PDF..."

# 方法1: 使用 pandoc + wkhtmltopdf (如果可用)
if command -v wkhtmltopdf &> /dev/null; then
    echo "使用 wkhtmltopdf..."
    pandoc draft.md -o output.pdf --pdf-engine=wkhtmltopdf
    exit 0
fi

# 方法2: 使用已安装的 md-to-pdf (本地版本)
if [ -f "node_modules/.bin/md-to-pdf" ]; then
    echo "使用 md-to-pdf..."
    ./node_modules/.bin/md-to-pdf draft.md
    exit 0
fi

# 方法3: 使用文本转 PDF 的简单方法
echo "生成 HTML 版本..."
pandoc draft.md -o draft_paper.html --standalone 2>/dev/null

echo ""
echo "==================================="
echo "由于系统限制，PDF 生成遇到以下问题："
echo "1. 缺少 LaTeX 环境 (xelatex/pdflatex)"
echo "2. 无法安装 md-to-pdf (权限问题)"
echo "3. 无法下载 Chromium (网络问题)"
echo ""
echo "已生成 HTML 版本: draft_paper.html"
echo ""
echo "替代方案："
echo "1. 在浏览器中打开 draft_paper.html，然后使用'打印为 PDF'功能"
echo "2. 使用在线 Markdown 转 PDF 工具（如 md2pdf.netlify.app）"
echo "3. 使用 Typora 等 Markdown 编辑器导出 PDF"
echo "4. 使用 VS Code + Markdown PDF 插件"
echo "==================================="
