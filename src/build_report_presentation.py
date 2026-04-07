from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PPTX = OUT / "三维激光雷达建模作业_简明报告.pptx"

SLIDE_W = 12192000
SLIDE_H = 6858000


def emu(v: float) -> int:
    return int(v)


def text_shape(shape_id, x, y, w, h, text, size=2600, bold=False, align="l", color="111111"):
    paras = text.split("\n")
    p_xml = []
    for p in paras:
        p_xml.append(
            f"""<a:p><a:pPr algn="{align}"/><a:r><a:rPr lang="zh-CN" sz="{size}" {'b="1"' if bold else ''}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr><a:t>{escape(p)}</a:t></a:r></a:p>"""
        )
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{shape_id}" name="Text {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
  <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{''.join(p_xml)}</p:txBody>
</p:sp>"""


def image_shape(shape_id, rel_id, x, y, w, h):
    return f"""
<p:pic>
  <p:nvPicPr><p:cNvPr id="{shape_id}" name="Picture {shape_id}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
  <p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
  <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>"""


def slide_xml(shapes: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    {shapes}
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def rels_xml(rels):
    body = []
    for rid, typ, target in rels:
        body.append(f'<Relationship Id="{rid}" Type="{typ}" Target="{target}"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(body)}</Relationships>"""


def content_types(nslides: int, media_files):
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    overrides += [
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, nslides + 1)
    ]
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  {''.join(overrides)}
</Types>"""


def presentation_xml(nslides: int):
    ids = "".join([f'<p:sldId id="{255+i}" r:id="rId{i+1}"/>' for i in range(1, nslides + 1)])
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


MASTER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""

LAYOUT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>"""

THEME = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme"><a:themeElements><a:clrScheme name="Office"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F497D"/></a:dk2><a:lt2><a:srgbClr val="EEECE1"/></a:lt2><a:accent1><a:srgbClr val="4F81BD"/></a:accent1><a:accent2><a:srgbClr val="C0504D"/></a:accent2><a:accent3><a:srgbClr val="9BBB59"/></a:accent3><a:accent4><a:srgbClr val="8064A2"/></a:accent4><a:accent5><a:srgbClr val="4BACC6"/></a:accent5><a:accent6><a:srgbClr val="F79646"/></a:accent6><a:hlink><a:srgbClr val="0000FF"/></a:hlink><a:folHlink><a:srgbClr val="800080"/></a:folHlink></a:clrScheme><a:fontScheme name="Office"><a:majorFont><a:latin typeface="SimSun"/><a:ea typeface="宋体"/></a:majorFont><a:minorFont><a:latin typeface="SimSun"/><a:ea typeface="宋体"/></a:minorFont></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme></a:themeElements></a:theme>"""


def create():
    images = {
        "workflow": OUT / "terrain_workflow.png",
        "raw": OUT / "raw_point_cloud.png",
        "filter": OUT / "filter_comparison.png",
        "dem": OUT / "dem_tin_preview.png",
    }
    slides = []
    slide_rels = []

    slides.append(slide_xml(
        text_shape(2, 700000, 900000, 10800000, 900000, "三维激光雷达建模作业", size=4200, bold=True, align="ctr")
        + text_shape(3, 1300000, 2100000, 9800000, 2400000, "处理数据：20251126150027848.las\n主要任务：点云去噪、两种地面滤波、DEM 生成与成果展示\n输出成果：ground_tin.las、ground_csf.las、dem_tin.tif、成果截图", size=2600, align="ctr")
    ))
    slide_rels.append([])

    slides.append(slide_xml(
        text_shape(2, 400000, 250000, 11200000, 500000, "地形级三维构建技术流程", size=3200, bold=True, align="ctr")
        + image_shape(3, "rId2", 1100000, 950000, 10000000, 5200000)
    ))
    slide_rels.append([("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "../media/workflow.png")])

    slides.append(slide_xml(
        text_shape(2, 400000, 250000, 11200000, 500000, "原始点云截图", size=3200, bold=True, align="ctr")
        + image_shape(3, "rId2", 1200000, 950000, 9600000, 5200000)
    ))
    slide_rels.append([("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "../media/raw.png")])

    slides.append(slide_xml(
        text_shape(2, 400000, 250000, 11200000, 500000, "点云滤波效果对比", size=3200, bold=True, align="ctr")
        + image_shape(3, "rId2", 500000, 950000, 11200000, 4700000)
    ))
    slide_rels.append([("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "../media/filter.png")])

    slides.append(slide_xml(
        text_shape(2, 400000, 250000, 11200000, 500000, "DEM 成果效果截图", size=3200, bold=True, align="ctr")
        + image_shape(3, "rId2", 1200000, 950000, 9600000, 5200000)
    ))
    slide_rels.append([("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "../media/dem.png")])

    slides.append(slide_xml(
        text_shape(2, 600000, 450000, 11000000, 600000, "实验结论", size=3400, bold=True, align="ctr")
        + text_shape(3, 900000, 1300000, 10400000, 4000000, "1. 通过高程分位数约束完成明显离群点去噪。\n2. 分别采用渐进式三角网滤波思想和布料滤波思想提取地面点。\n3. 基于渐进式三角网滤波地面点生成 0.5 m 分辨率 DEM，并保存为 GeoTIFF。\n4. 输出成果可用于后续地形级三维建模实验报告整理。", size=2600, align="l")
    ))
    slide_rels.append([])

    with ZipFile(PPTX, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(len(slides), images))
        z.writestr("_rels/.rels", rels_xml([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "ppt/presentation.xml")]))
        pres_rels = [("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "slideMasters/slideMaster1.xml")]
        pres_rels += [(f"rId{i+1}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", f"slides/slide{i}.xml") for i in range(1, len(slides)+1)]
        z.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        z.writestr("ppt/_rels/presentation.xml.rels", rels_xml(pres_rels))
        z.writestr("ppt/slideMasters/slideMaster1.xml", MASTER)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels_xml([
            ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
            ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "../theme/theme1.xml"),
        ]))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels_xml([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "../slideMasters/slideMaster1.xml")]))
        z.writestr("ppt/theme/theme1.xml", THEME)
        z.writestr("docProps/core.xml", '<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>三维激光雷达建模作业</dc:title></cp:coreProperties>')
        z.writestr("docProps/app.xml", '<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Codex</Application></Properties>')
        for i, s in enumerate(slides, start=1):
            z.writestr(f"ppt/slides/slide{i}.xml", s)
            rels = [("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml")]
            rels.extend(slide_rels[i - 1])
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels_xml(rels))
        for name, path in images.items():
            z.write(path, f"ppt/media/{name}.png")
    print(PPTX)


if __name__ == "__main__":
    create()
