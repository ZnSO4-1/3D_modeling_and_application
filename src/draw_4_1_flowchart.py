from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "flowchart_4_1_technical_scheme.png"
FONT_PATH = Path(r"C:\WINDOWS\Fonts\simsun.ttc")

W, H = 2200, 1400
BG = (255, 255, 255)
LINE = (35, 35, 35)
BORDER = (55, 55, 55)
TEXT = (20, 20, 20)
SUB = (70, 70, 70)
FILL = (255, 255, 255)
DARK = (30, 30, 30)


def font(size: int):
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size=size)
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


def centered_text(box, text, fnt, fill=TEXT, spacing=6):
    x0, y0, x1, y1 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = x0 + (x1 - x0 - tw) / 2
    y = y0 + (y1 - y0 - th) / 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing, align="center")


def box(x, y, w, h, title, subtitle="", title_size=30, sub_size=21):
    draw.rounded_rectangle((x, y, x + w, y + h), 20, fill=FILL, outline=BORDER, width=4)
    if subtitle:
        centered_text((x + 20, y + 16, x + w - 20, y + 62), title, font(title_size), TEXT)
        centered_text((x + 22, y + 68, x + w - 22, y + h - 16), subtitle, font(sub_size), SUB)
    else:
        centered_text((x + 20, y + 18, x + w - 20, y + h - 18), title, font(title_size), TEXT)


def dark_ellipse(x, y, w, h, text):
    draw.ellipse((x, y, x + w, y + h), fill=DARK)
    centered_text((x, y, x + w, y + h), text, font(28), (255, 255, 255))


def arrow(x1, y1, x2, y2, width=6, head=22):
    draw.line((x1, y1, x2, y2), fill=LINE, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    left = (
        x2 - head * math.cos(ang) + head * 0.55 * math.sin(ang),
        y2 - head * math.sin(ang) - head * 0.55 * math.cos(ang),
    )
    right = (
        x2 - head * math.cos(ang) - head * 0.55 * math.sin(ang),
        y2 - head * math.sin(ang) + head * 0.55 * math.cos(ang),
    )
    draw.polygon([(x2, y2), left, right], fill=LINE)


centered_text((0, 35, W, 95), "激光 LAS 点云构建地形三维技术方案流程图", font(44), TEXT)

dark_ellipse(70, 170, 260, 100, "原始 LAS\n点云数据")
box(430, 145, 420, 150, "1. 点云读取与检查", "读取 X、Y、Z 坐标、点数规模、高程范围\n观察覆盖范围、起伏特征和异常点")
box(980, 145, 420, 150, "2. 点云去噪处理", "采用高程分位数约束\n剔除明显异常高程点和离群点")

box(520, 430, 460, 155, "3a. 渐进式三角网滤波", "以局部最低点为地面种子\n逐步构建地形参考面并按高差阈值判别")
box(1220, 430, 460, 155, "3b. 布料滤波", "反转点云地形并模拟布料覆盖\n按点到布料面的距离阈值提取地面点")

box(845, 730, 510, 150, "4. 地面点成果输出", "分别生成两种滤波方法的地面点成果\n保存为地面点 LAS 文件")
box(510, 1010, 460, 150, "5. DEM 构建", "基于地面点划分规则格网\n统计格网高程并进行邻近插值或平滑补全")
box(1230, 1010, 460, 150, "6. 成果输出与表达", "保存 DEM 为 GeoTIFF\n输出原始点云、滤波效果和 DEM 成果截图")

arrow(330, 220, 430, 220)
arrow(850, 220, 980, 220)
arrow(1190, 295, 750, 430)
arrow(1190, 295, 1450, 430)
arrow(750, 585, 950, 730)
arrow(1450, 585, 1250, 730)
arrow(950, 880, 740, 1010)
arrow(1250, 880, 1460, 1010)

box(760, 1215, 680, 90, "最终成果：地面点 LAS 文件、DEM GeoTIFF 文件、过程与成果截图", "", title_size=27)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(OUT)
