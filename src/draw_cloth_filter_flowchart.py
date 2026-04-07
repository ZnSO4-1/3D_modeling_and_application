from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "flowchart_cloth_filter.png"
OUT2 = ROOT / "outputs" / "flowchart_cloth_filter.png"
FONT_PATH = Path(r"C:\WINDOWS\Fonts\simsun.ttc")

W, H = 1800, 1700
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


def centered_text(draw, box, text, fnt, fill=TEXT, spacing=6):
    x0, y0, x1, y1 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.multiline_text(
        (x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2),
        text,
        font=fnt,
        fill=fill,
        spacing=spacing,
        align="center",
    )


def arrow(draw, x1, y1, x2, y2, width=6, head=22):
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


def node(draw, cx, y, w, h, title, subtitle="", title_size=29, sub_size=20):
    x = cx - w // 2
    draw.rounded_rectangle((x, y, x + w, y + h), 20, fill=FILL, outline=BORDER, width=4)
    if subtitle:
        centered_text(draw, (x + 20, y + 12, x + w - 20, y + 56), title, font(title_size), TEXT)
        centered_text(draw, (x + 22, y + 60, x + w - 22, y + h - 12), subtitle, font(sub_size), SUB)
    else:
        centered_text(draw, (x + 20, y + 14, x + w - 20, y + h - 14), title, font(title_size), TEXT)
    return (x, y, x + w, y + h)


def terminator(draw, cx, y, w, h, text):
    x = cx - w // 2
    draw.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=DARK, outline=DARK, width=3)
    centered_text(draw, (x, y, x + w, y + h), text, font(28), (255, 255, 255))
    return (x, y, x + w, y + h)


def diamond(draw, cx, cy, w, h, text):
    pts = [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]
    draw.polygon(pts, fill=FILL)
    draw.line(pts + [pts[0]], fill=BORDER, width=4)
    centered_text(draw, (cx - w // 2 + 38, cy - h // 2 + 26, cx + w // 2 - 38, cy + h // 2 - 26), text, font(24), TEXT)


def label(draw, x, y, text):
    centered_text(draw, (x - 90, y - 24, x + 90, y + 24), text, font(21), TEXT)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    cx = W // 2
    main_w = 700
    main_h = 118

    title = "\u5e03\u6599\u6ee4\u6ce2\u7b97\u6cd5\u6d41\u7a0b\u56fe"
    centered_text(d, (0, 35, W, 100), title, font(46), TEXT)

    terminator(d, cx, 130, 280, 78, "\u5f00\u59cb")
    node(d, cx, 245, main_w, main_h, "\u8f93\u5165 LAS \u70b9\u4e91", "\u8bfb\u53d6\u5750\u6807\u5e76\u8fdb\u884c\u5fc5\u8981\u53bb\u566a")
    node(d, cx, 395, main_w, main_h, "\u70b9\u4e91\u9ad8\u7a0b\u53cd\u8f6c", "\u5c06\u5730\u5f62\u4e0a\u4e0b\u5173\u7cfb\u53cd\u8f6c\uff0c\u4f7f\u5730\u9762\u4f4e\u70b9\u6210\u4e3a\u652f\u6491\u533a\u57df")
    node(d, cx, 545, main_w, main_h, "\u5efa\u7acb\u89c4\u5219\u5e03\u6599\u7f51\u683c", "\u8bbe\u7f6e\u5e03\u6599\u8282\u70b9\u3001\u683c\u7f51\u5206\u8fa8\u7387\u3001\u521a\u5ea6\u548c\u5e73\u6ed1\u7ea6\u675f")
    node(d, cx, 695, main_w, main_h, "\u5e03\u6599\u8fed\u4ee3\u4e0b\u843d", "\u5728\u91cd\u529b\u4e0e\u5185\u90e8\u7ea6\u675f\u4f5c\u7528\u4e0b\u9010\u6b65\u8d34\u5408\u53cd\u8f6c\u5730\u5f62")
    diamond(d, cx, 910, 500, 185, "\u5e03\u6599\u5f62\u6001\n\u662f\u5426\u7a33\u5b9a\uff1f")
    node(d, cx, 1035, main_w, main_h, "\u5f62\u6210\u5e03\u6599\u8fd1\u4f3c\u9762", "\u7a33\u5b9a\u540e\u7684\u5e03\u6599\u5f62\u6001\u8fd1\u4f3c\u771f\u5b9e\u5730\u8868")
    node(d, cx, 1185, main_w, main_h, "\u8ba1\u7b97\u70b9\u9762\u5782\u76f4\u8ddd\u79bb", "\u8ba1\u7b97\u539f\u59cb\u70b9\u4e91\u5230\u5e03\u6599\u8fd1\u4f3c\u9762\u7684\u8ddd\u79bb")
    diamond(d, cx, 1395, 500, 185, "\u8ddd\u79bb\u662f\u5426\n\u5c0f\u4e8e\u9608\u503c\uff1f")

    left_cx, right_cx = 430, 1370
    node(d, left_cx, 1485, 560, 120, "\u5224\u5b9a\u4e3a\u5730\u9762\u70b9", "\u70b9\u63a5\u8fd1\u5e03\u6599\u9762\uff0c\u52a0\u5165\u5730\u9762\u70b9\u96c6\u5408", 27, 18)
    node(d, right_cx, 1485, 560, 120, "\u5224\u5b9a\u4e3a\u975e\u5730\u9762\u70b9", "\u70b9\u8fdc\u79bb\u5e03\u6599\u9762\uff0c\u4f5c\u4e3a\u690d\u88ab\u6216\u5efa\u7b51\u7269\u7b49\u76ee\u6807", 27, 18)

    # Main vertical arrows.
    arrow(d, cx, 208, cx, 245)
    arrow(d, cx, 363, cx, 395)
    arrow(d, cx, 513, cx, 545)
    arrow(d, cx, 663, cx, 695)
    arrow(d, cx, 813, cx, 818)
    arrow(d, cx, 1003, cx, 1035)
    label(d, cx - 110, 1016, "\u662f")
    arrow(d, cx, 1153, cx, 1185)
    arrow(d, cx, 1303, cx, 1305)

    # Iteration loop, kept outside the main nodes.
    d.line((cx + 250, 910, 1570, 910, 1570, 754, cx + main_w // 2, 754), fill=LINE, width=6)
    arrow(d, 1570, 754, cx + main_w // 2, 754)
    label(d, 1460, 875, "\u5426\uff0c\u7ee7\u7eed\u8fed\u4ee3")

    # Threshold branches.
    arrow(d, cx - 250, 1395, left_cx + 280, 1545)
    label(d, 600, 1478, "\u662f")
    arrow(d, cx + 250, 1395, right_cx - 280, 1545)
    label(d, 1200, 1478, "\u5426")

    img.save(OUT)
    img.save(OUT2)
    print(OUT)


if __name__ == "__main__":
    main()
