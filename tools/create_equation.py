import lxml.etree as etree
from docx import Document
from docx.oxml import parse_xml
import latex2mathml.converter

def add_simple_omml(doc, latex_str):
    # 1. LaTeX -> MathML -> OMML
    mathml = latex2mathml.converter.convert(latex_str)
    
    # 转换逻辑
    xslt = etree.XSLT(etree.parse("MML2OMML.XSL"))
    omml_tree = xslt(etree.fromstring(mathml.encode('utf-8')))
    
    # 2. 转换为纯净字符串并移除 XML 声明头
    omml_str = etree.tostring(omml_tree, encoding='unicode', with_tail=False)
    if '?>' in omml_str:
        omml_str = omml_str.split('?>')[-1].strip()

    # 3. 包装核心命名空间（这是能打开且不报错的关键）
    # 必须显式声明 xmlns:m，否则 parse_xml 认不出希腊字母对应的标签
    m_ns = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
    if 'xmlns:m=' not in omml_str:
        omml_str = omml_str.replace('<m:oMath', f'<m:oMath {m_ns}', 1)

    # 4. 插入段落
    p = doc.add_paragraph()
    p._element.append(parse_xml(omml_str))

if __name__ == '__main__':
    # --- 运行测试 ---
    doc = Document()
    # 希腊字母测试：alpha, beta, gamma, delta
    latex_eq = r"\alpha + \beta = \sqrt{\gamma^2 + \delta^2}\cdot \sum_{i=1}^{n}{x_i}"

    try:
        add_simple_omml(doc, latex_eq)
        doc.save("simple_greek_test.docx")
        print("生成成功！请检查 simple_greek_test.docx")
    except Exception as e:
        print(f"失败原因: {e}")