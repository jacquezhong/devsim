# %%
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 获取所有字体
fonts = set([f.name for f in fm.fontManager.ttflist])

# 常见中文字体列表
chinese_fonts = [
    'STHeiti', 'SimHei', 'Microsoft YaHei', 'PingFang SC',
    'Hiragino Sans GB', 'STHeiti', 'WenQuanYi Micro Hei',
    'Noto Sans CJK SC', 'FangSong', 'KaiTi'
]

# 找到第一个可用的中文字体
available_chinese_font = None
for font in chinese_fonts:
    if font in fonts:
        available_chinese_font = font
        break

if available_chinese_font:
    plt.rcParams['font.sans-serif'] = [available_chinese_font]
    plt.rcParams['axes.unicode_minus'] = False
    print(f"已设置中文字体: {available_chinese_font}")
else:
    print("警告：未找到可用的中文字体！")
# %%
import matplotlib.pyplot as plt

# 方法1：指定一个已知的中文字体（推荐）
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB']
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 然后正常绘图
plt.plot([1, 2, 3], [1, 4, 9])
plt.title('中文标题')
plt.xlabel('X轴')
plt.ylabel('Y轴')
plt.show()
# %%
