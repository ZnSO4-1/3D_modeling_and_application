from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "flowchart_progressive_tin_filter.png"
FONT_PATH = Path(r"C:\WINDOWS\Fonts\simsun.ttc")

W, H = 2200, 1350
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


def rounded_box(x, y, w, h, title, subtitle="", title_size=30, sub_size=21):
    draw.rounded_rectangle((x, y, x + w, y + h), 22, fill=FILL, outline=BORDER, width=4)
    if subtitle:
        centered_text((x + 20, y + 14, x + w - 20, y + 64), title, font(title_size), TEXT)
        centered_text((x + 22, y + 70, x + w - 22, y + h - 14), subtitle, font(sub_size), SUB)
    else:
        centered_text((x + 20, y + 18, x + w - 20, y + h - 18), title, font(title_size), TEXT)


def terminator(x, y, w, h, text):
    draw.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=DARK, outline=DARK, width=3)
    centered_text((x, y, x + w, y + h), text, font(27), (255, 255, 255))


def diamond(cx, cy, w, h, text):
    pts = [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]
    draw.polygon(pts, fill=FILL, outline=BORDER)
    draw.line(pts + [pts[0]], fill=BORDER, width=4)
    centered_text((cx - w // 2 + 35, cy - h // 2 + 25, cx + w // 2 - 35, cy + h // 2 - 25), text, font(24), TEXT)


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


def label(x, y, text):
    centered_text((x - 70, y - 20, x + 70, y + 20), text, font(21), TEXT)


centered_text((0, 34, W, 96), "渐进式三角网滤波算法流程图", font(46), TEXT)

terminator(110, 160, 260, 90, "开始")
rounded_box(470, 130, 410, 150, "输入 LAS 点云", "读取 X、Y、Z 坐标\n并进行必要去噪")
rounded_box(1010, 130, 410, 150, "点云格网划分", "按照设定网格尺寸\n组织局部点集")
rounded_box(1550, 130, 430, 150, "选取初始地面种子点", "在每个格网内选取局部最低点\n作为初始地面点")

rounded_box(1550, 450, 430, 150, "构建初始地形参考面", "由种子点建立初始三角网\n或近似地形面")
rounded_box(1010, 450, 410, 150, "计算候选点关系", "计算候选点到参考面的\n高差或坡度关系")
diamond(675, 525, 360, 210, "是否满足\n高差 / 坡度阈值？")

rounded_box(110, 450, 370, 150, "加入地面点集合", "将候选点判定为地面点\n并参与后续地形面更新")
rounded_box(110, 760, 370, 150, "判为非地面点", "保留为植被、建筑物\n或其他非地面目标")
diamond(675, 835, 360, 210, "是否还有\n未分类候选点？")

rounded_box(1010, 760, 410, 150, "更新地形参考面", "用新增地面点逐步更新\n三角网或近似地形面")
rounded_box(1550, 760, 430, 150, "输出地面点成果", "保存渐进式三角网滤波\n地面点 LAS 文件")
terminator(990, 1095, 260, 90, "结束")

arrow(370, 205, 470, 205)
arrow(880, 205, 1010, 205)
arrow(1420, 205, 1550, 205)
arrow(1765, 280, 1765, 450)
arrow(1550, 525, 1420, 525)
arrow(1010, 525, 855, 525)

arrow(495, 525, 480, 525)
label(515, 490, "是")
arrow(675, 630, 675, 730)
label(730, 685, "否")
arrow(675, 940, 675, 1040)
label(730, 985, "否")
arrow(855, 835, 1010, 835)
label(925, 800, "是")
arrow(1420, 835, 1530, 835)

# Iteration loop from updated surface back to candidate relation.
draw.line((1215, 760, 1215, 675, 1215, 600), fill=LINE, width=6)
arrow(1215, 600, 1215, 600)
draw.line((1215, 600, 1215, 600), fill=LINE, width=6)
arrow(1215, 760, 1215, 600)
label(1285, 675, "迭代")

arrow(480, 835, 495, 835)
arrow(675, 1040, 1120, 1095)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(OUT)
