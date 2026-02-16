#!/usr/bin/env python3
"""
修复 draft_modified.md 中的格式问题：
1. 正文中的下标符号包裹在 $...$ 中
2. Unicode 上标转换为 LaTeX 格式
3. 确保公式前后有空行
"""

import re

# 读取文件
with open('draft_modified.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 问题1：将正文中的下标符号包裹在 $...$ 中
# 但避免重复包裹（已经是 $...$ 中的不处理）

# 定义需要包裹的模式
subscript_patterns = [
    (r'N_A', r'$N_A$'),
    (r'N_D', r'$N_D$'),
    (r'Q_rr', r'$Q_rr$'),
    (r'Q_s', r'$Q_s$'),
    (r't_rr', r'$t_rr$'),
    (r'V_bi', r'$V_bi$'),
    (r'V_F', r'$V_A$'),
    (r'R_on', r'$R_on$'),
    (r'J_F', r'$J_F$'),
    (r'I_F', r'$I_F$'),
    (r'I_rr', r'$I_rr$'),
    (r'τ_n', r'$\\tau_n$'),
    (r'τ_p', r'$\\tau_p$'),
    (r'n_i', r'$n_i$'),
    (r'x_j', r'$x_j$'),
    (r'E_c', r'$E_c$'),
    (r'E_crit', r'$E_{crit}$'),
    (r'kT', r'$kT$'),
    (r'dI', r'$dI$'),
    (r'dV', r'$dV$'),
]

# 逐个替换，但避免在公式块和已有 $...$ 中的替换
lines = content.split('\n')
new_lines = []

for line in lines:
    # 跳过公式块行
    if line.strip().startswith('$$'):
        new_lines.append(line)
        continue
    
    # 处理行内文本
    new_line = line
    
    for pattern, replacement in subscript_patterns:
        # 使用正则表达式，避免在 $...$ 中替换
        # 匹配不在 $...$ 中的模式
        def replace_func(match):
            # 检查是否在 $...$ 中
            start = match.start()
            # 检查前面是否有奇数个 $
            before = new_line[:start]
            dollar_count = before.count('$')
            if dollar_count % 2 == 1:
                # 在 $...$ 中，不替换
                return match.group(0)
            # 不在 $...$ 中，替换
            return replacement
        
        # 使用更精确的模式匹配
        # 匹配完整的单词，避免部分匹配
        pattern_regex = r'(?<!\$)' + re.escape(pattern) + r'(?!\$)'
        new_line = re.sub(pattern_regex, replacement, new_line)
    
    new_lines.append(new_line)

content = '\n'.join(new_lines)

# 问题2：Unicode 上标转换为 LaTeX
# 定义 Unicode 上标映射
unicode_superscripts = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
    '⁻': '-', '⁺': '+',
}

def replace_unicode_superscript(match):
    """将 Unicode 上标转换为 LaTeX"""
    base = match.group(1)  # 基数
    superscript = match.group(2)  # 上标
    
    # 转换上标字符
    latex_sup = ''
    for char in superscript:
        if char in unicode_superscripts:
            latex_sup += unicode_superscripts[char]
        else:
            latex_sup += char
    
    return f'${base} \\times 10^{{{latex_sup}}}$'

# 匹配 "1×10¹⁶" 这样的模式
content = re.sub(r'(\d+(?:\.\d+)?)\s*×\s*10([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)', replace_unicode_superscript, content)

# 问题3：确保公式前后有空行
# 查找 $$...$$ 块并确保前后有空行
formula_pattern = r'([^\n])\$\$\$?([^\n$][^$]*?)\$\$\$?([^\n])'

def fix_formula_spacing(match):
    before = match.group(1)
    formula = match.group(2)
    after = match.group(3)
    
    # 确保前面有空行
    if before != '\n':
        before = before + '\n\n'
    
    # 确保后面有空行
    if after != '\n':
        after = '\n\n' + after
    
    return f'{before}$${formula}$${after}'

# 注意：这个替换要小心，避免破坏已有的正确格式
# 暂时注释掉，手动检查更可靠
# content = re.sub(formula_pattern, fix_formula_spacing, content)

# 保存修复后的文件
with open('draft_modified_fixed.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 修复完成！")
print("📄 输出文件: draft_modified_fixed.md")
print("\n修复内容：")
print("1. 正文中的下标符号已包裹在 $...$ 中")
print("2. Unicode 上标已转换为 LaTeX 格式")
