from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, TiffImagePlugin
from scipy import ndimage

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHINESE_FONT = Path(r"C:\WINDOWS\Fonts\simsun.ttc")
plt.rcParams["font.sans-serif"] = ["SimSun", "Microsoft YaHei", "Noto Sans CJK SC"]
plt.rcParams["axes.unicode_minus"] = False


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_LAS = PROJECT_ROOT / "data" / "20251126150027848.las"
OUTDIR = PROJECT_ROOT / "outputs"
OUTDIR.mkdir(exist_ok=True)

GRID_RES = 0.5
CHUNK_RECORDS = 1_000_000
TITLE = (20, 20, 20)
SUB = (80, 80, 80)
LINE = (40, 40, 40)


def font(size: int):
    if CHINESE_FONT.exists():
        return ImageFont.truetype(str(CHINESE_FONT), size=size)
    return ImageFont.load_default()


def read_las_header(path: Path) -> dict:
    with path.open("rb") as f:
        header = bytearray(f.read(375))
    if header[:4] != b"LASF":
        raise ValueError(f"{path} is not a LAS file")
    header_size = struct.unpack_from("<H", header, 94)[0]
    offset_to_points = struct.unpack_from("<I", header, 96)[0]
    point_format = header[104] & 0b00111111
    record_len = struct.unpack_from("<H", header, 105)[0]
    point_count = struct.unpack_from("<I", header, 107)[0]
    scale = struct.unpack_from("<ddd", header, 131)
    offset = struct.unpack_from("<ddd", header, 155)
    bounds = struct.unpack_from("<dddddd", header, 179)
    return {
        "header": header,
        "header_size": header_size,
        "offset_to_points": offset_to_points,
        "point_format": point_format,
        "record_len": record_len,
        "point_count": point_count,
        "scale": np.array(scale, dtype=np.float64),
        "offset": np.array(offset, dtype=np.float64),
        "bounds": bounds,
    }


def las_point_dtype(record_len: int) -> np.dtype:
    return np.dtype(
        {
            "names": ["X", "Y", "Z", "flags", "classification"],
            "formats": ["<i4", "<i4", "<i4", "u1", "u1"],
            "offsets": [0, 4, 8, 14, 15],
            "itemsize": record_len,
        }
    )


def load_xyz(path: Path, info: dict):
    dtype = las_point_dtype(info["record_len"])
    mm = np.memmap(
        path,
        dtype=dtype,
        mode="r",
        offset=info["offset_to_points"],
        shape=(info["point_count"],),
    )
    scale = info["scale"]
    offset = info["offset"]
    x = mm["X"].astype(np.float64) * scale[0] + offset[0]
    y = mm["Y"].astype(np.float64) * scale[1] + offset[1]
    z = mm["Z"].astype(np.float64) * scale[2] + offset[2]
    return mm, x, y, z


def grid_min_surface(x: np.ndarray, y: np.ndarray, z: np.ndarray, res: float):
    xmin, xmax = float(x.min()), float(x.max())
    ymin, ymax = float(y.min()), float(y.max())
    nx = int(np.floor((xmax - xmin) / res)) + 1
    ny = int(np.floor((ymax - ymin) / res)) + 1
    ix = np.clip(((x - xmin) / res).astype(np.int32), 0, nx - 1)
    iy = np.clip(((y - ymin) / res).astype(np.int32), 0, ny - 1)

    grid = np.full((ny, nx), np.inf, dtype=np.float32)
    np.minimum.at(grid, (iy, ix), z.astype(np.float32))
    mask = np.isfinite(grid)

    nearest_idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    filled = grid[tuple(nearest_idx)]
    return filled, mask, (xmin, ymin, nx, ny, res), ix, iy


def progressive_tin_like_filter(x, y, z, res=GRID_RES) -> tuple[np.ndarray, np.ndarray]:
    """A grid-seeded progressive TIN-style filter.

    It starts from local minimum seed points, progressively smooths the seed
    surface, and accepts points close to the interpolated terrain surface.
    """
    min_grid, mask, grid_info, ix, iy = grid_min_surface(x, y, z, res)
    surface = min_grid.copy()
    for sigma, threshold in [(1.0, 0.25), (2.0, 0.45), (3.0, 0.70)]:
        smooth = ndimage.gaussian_filter(surface, sigma=sigma)
        surface = np.minimum(surface + threshold * 0.35, smooth + threshold * 0.65)
    dz = z - surface[iy, ix]
    ground = (dz >= -0.20) & (dz <= 0.75)
    return ground, surface


def cloth_simulation_like_filter(x, y, z, res=GRID_RES) -> tuple[np.ndarray, np.ndarray]:
    """A lightweight cloth-simulation-style filter.

    The inverted terrain is represented on a cloth grid. The cloth is smoothed
    iteratively while constrained by the local minimum terrain surface.
    """
    min_grid, mask, grid_info, ix, iy = grid_min_surface(x, y, z, res)
    cloth = min_grid.copy()
    for _ in range(12):
        smooth = ndimage.uniform_filter(cloth, size=5)
        cloth = np.maximum(min_grid, 0.65 * smooth + 0.35 * cloth)
    cloth = ndimage.gaussian_filter(cloth, sigma=1.2)
    dz = z - cloth[iy, ix]
    ground = (dz >= -0.25) & (dz <= 0.55)
    return ground, cloth


def denoise_by_elevation(z: np.ndarray) -> np.ndarray:
    """Remove obvious high/low elevation outliers before ground filtering."""
    low, high = np.quantile(z, [0.001, 0.999])
    return (z >= low) & (z <= high)


def update_header_for_subset(header: bytearray, records: np.ndarray, info: dict, selected_indices: np.ndarray):
    new_header = bytearray(header[: info["offset_to_points"]])
    count = int(selected_indices.size)
    struct.pack_into("<I", new_header, 107, count)

    # Legacy number of points by return, LAS 1.2 supports 5 uint32 counters.
    return_counts = np.zeros(5, dtype=np.uint32)
    returns = records["flags"][selected_indices] & 0b00000111
    for i in range(1, 6):
        return_counts[i - 1] = np.count_nonzero(returns == i)
    struct.pack_into("<IIIII", new_header, 111, *[int(v) for v in return_counts])

    scale = info["scale"]
    offset = info["offset"]
    xs = records["X"][selected_indices].astype(np.float64) * scale[0] + offset[0]
    ys = records["Y"][selected_indices].astype(np.float64) * scale[1] + offset[1]
    zs = records["Z"][selected_indices].astype(np.float64) * scale[2] + offset[2]
    struct.pack_into("<dddddd", new_header, 179, xs.max(), xs.min(), ys.max(), ys.min(), zs.max(), zs.min())
    return new_header


def write_las_subset(path: Path, source_path: Path, records: np.ndarray, info: dict, mask: np.ndarray):
    selected = np.flatnonzero(mask)
    header = update_header_for_subset(info["header"], records, info, selected)
    raw_dtype = np.dtype((np.void, info["record_len"]))
    raw = np.memmap(
        source_path,
        dtype=raw_dtype,
        mode="r",
        offset=info["offset_to_points"],
        shape=(info["point_count"],),
    )
    with path.open("wb") as f:
        f.write(header)
        for start in range(0, selected.size, CHUNK_RECORDS):
            part = selected[start : start + CHUNK_RECORDS]
            f.write(raw[part].tobytes())
    return selected.size


def make_dem(x, y, z, ground_mask, res=GRID_RES):
    gx, gy, gz = x[ground_mask], y[ground_mask], z[ground_mask]
    xmin, xmax = float(x.min()), float(x.max())
    ymin, ymax = float(y.min()), float(y.max())
    nx = int(np.floor((xmax - xmin) / res)) + 1
    ny = int(np.floor((ymax - ymin) / res)) + 1
    ix = np.clip(((gx - xmin) / res).astype(np.int32), 0, nx - 1)
    iy = np.clip(((gy - ymin) / res).astype(np.int32), 0, ny - 1)
    dem = np.full((ny, nx), np.inf, dtype=np.float32)
    np.minimum.at(dem, (iy, ix), gz.astype(np.float32))
    valid = np.isfinite(dem)
    nearest_idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    dem = dem[tuple(nearest_idx)]
    dem = ndimage.gaussian_filter(dem, sigma=0.8)
    return dem, (xmin, ymin, res)


def save_dem_geotiff(path: Path, dem: np.ndarray, transform_info):
    xmin, ymin, res = transform_info
    dem_out = np.flipud(dem).astype(np.float32)
    img = Image.fromarray(dem_out)
    if img.mode != "F":
        img = img.convert("F")
    ifd = TiffImagePlugin.ImageFileDirectory_v2()
    # GeoTIFF core tags: ModelPixelScaleTag and ModelTiepointTag.
    ifd[33550] = (res, res, 0.0)
    ymax = ymin + dem.shape[0] * res
    ifd[33922] = (0.0, 0.0, 0.0, xmin, ymax, 0.0)
    img.save(path, tiffinfo=ifd)
    # World file companion for GIS software that ignores minimal GeoTIFF tags.
    tfw = path.with_suffix(".tfw")
    tfw.write_text(f"{res}\n0\n0\n{-res}\n{xmin + res / 2}\n{ymax - res / 2}\n", encoding="utf-8")


def save_dem_preview(path: Path, dem: np.ndarray):
    plt.figure(figsize=(8, 5), dpi=180)
    plt.imshow(dem, cmap="terrain", origin="lower")
    plt.colorbar(label="Elevation / m")
    plt.title("DEM 成果预览")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def sample_indices(n: int, max_points: int = 250_000):
    rng = np.random.default_rng(42)
    if n <= max_points:
        return np.arange(n)
    return rng.choice(n, size=max_points, replace=False)


def save_point_cloud_preview(path: Path, x, y, z, mask=None, title="Point cloud"):
    if mask is None:
        idx = sample_indices(x.size)
    else:
        candidates = np.flatnonzero(mask)
        idx = candidates[sample_indices(candidates.size, max_points=180_000)]
    plt.figure(figsize=(8, 5), dpi=180)
    sc = plt.scatter(x[idx], y[idx], c=z[idx], s=0.08, cmap="viridis")
    plt.gca().set_aspect("equal", adjustable="box")
    plt.colorbar(sc, label="Elevation / m")
    plt.title(title)
    plt.xlabel("X / m")
    plt.ylabel("Y / m")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def save_filter_comparison(path: Path, x, y, z, tin_ground, csf_ground):
    idx = sample_indices(x.size, max_points=220_000)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=180)
    for ax, mask, title in [
        (axes[0], tin_ground, "渐进式三角网滤波结果"),
        (axes[1], csf_ground, "布料滤波结果"),
    ]:
        labels = mask[idx].astype(int)
        ax.scatter(x[idx], y[idx], c=labels, s=0.08, cmap="coolwarm")
        ax.set_title(title)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X / m")
        ax.set_ylabel("Y / m")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def save_flowchart(path: Path):
    im = Image.new("RGB", (1600, 900), "white")
    d = ImageDraw.Draw(im)
    f_title = font(34)
    f_box = font(22)
    f_small = font(17)
    d.text((800, 40), "地形级三维构建技术流程", fill=TITLE, font=f_title, anchor="mm")
    boxes = [
        (80, 140, "LAS 原始点云", "读取点云坐标与属性"),
        (420, 140, "点云去噪", "剔除明显离群点"),
        (760, 140, "地面滤波", "TIN 滤波 / 布料滤波"),
        (1100, 140, "地面点 LAS", "保存地面点成果"),
        (420, 500, "DEM 插值", "地面点格网化"),
        (760, 500, "GeoTIFF 输出", "保存 DEM 栅格"),
        (1100, 500, "成果展示", "截图与报告整理"),
    ]
    for x0, y0, title, sub in boxes:
        d.rounded_rectangle((x0, y0, x0 + 250, y0 + 120), radius=18, outline=LINE, width=3)
        d.text((x0 + 125, y0 + 42), title, fill=TITLE, font=f_box, anchor="mm")
        d.text((x0 + 125, y0 + 82), sub, fill=SUB, font=f_small, anchor="mm")
    for a, b in [((330, 200), (420, 200)), ((670, 200), (760, 200)), ((1010, 200), (1100, 200)),
                 ((1225, 260), (545, 500)), ((670, 560), (760, 560)), ((1010, 560), (1100, 560))]:
        arrow_on_draw(d, *a, *b)
    im.save(path)


def arrow_on_draw(d, x1, y1, x2, y2, width=4, head=16):
    d.line((x1, y1, x2, y2), fill=LINE, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    left = (x2 - head * math.cos(ang) + head * 0.55 * math.sin(ang), y2 - head * math.sin(ang) - head * 0.55 * math.cos(ang))
    right = (x2 - head * math.cos(ang) - head * 0.55 * math.sin(ang), y2 - head * math.sin(ang) + head * 0.55 * math.cos(ang))
    d.polygon([(x2, y2), left, right], fill=LINE)


def write_report_md(path: Path, stats: dict):
    path.write_text(
        f"""# 三维激光雷达建模作业实验报告素材

## 1. 技术方案
本作业选取 `{INPUT_LAS.name}` 作为堤防激光雷达 LAS 数据。处理流程为：读取 LAS 点云，先采用高程分位数约束剔除明显离群点，再分别采用渐进式三角网滤波思想和布料滤波思想提取地面点，输出地面点 LAS 文件；在地面点基础上按 {GRID_RES} m 分辨率格网化生成 DEM，并保存为 GeoTIFF 文件。

## 2. 滤波原理
渐进式三角网滤波以局部最低点作为初始地面种子点，逐步构建并更新地形参考面，根据点到地形参考面的高差阈值判断地面点。本程序采用格网最低点作为种子面，并通过逐级平滑与阈值约束模拟渐进式地面面片生长。

布料滤波将地形点云反转后，用一张具有平滑约束的“布料”覆盖在反转地形上，布料稳定后的形态近似地表，点到布料面的距离小于阈值时判定为地面点。本程序以格网最低面为约束面，通过多次平滑迭代形成布料近似面，并据此分类地面点。

## 3. 程序输出
- 原始点数：{stats['total_points']:,}
- 去噪后参与滤波点数：{stats['clean_points']:,}
- 渐进式三角网滤波地面点数：{stats['tin_ground']:,}
- 布料滤波地面点数：{stats['csf_ground']:,}
- DEM 分辨率：{GRID_RES} m
- DEM 栅格尺寸：{stats['dem_shape'][1]} × {stats['dem_shape'][0]}

## 4. 成果文件
- `ground_tin.las`
- `ground_csf.las`
- `dem_tin.tif`
- `dem_tin.tfw`
- `raw_point_cloud.png`
- `filter_comparison.png`
- `dem_tin_preview.png`
- `terrain_workflow.png`
""",
        encoding="utf-8",
    )


def main():
    if not INPUT_LAS.exists():
        raise FileNotFoundError(
            f"Input LAS not found: {INPUT_LAS}\n"
            "Place 20251126150027848.las in the data/ directory, "
            "or edit INPUT_LAS in src/terrain_lidar_assignment.py."
        )
    info = read_las_header(INPUT_LAS)
    print("LAS info:", info["point_count"], "points, format", info["point_format"])
    records, x, y, z = load_xyz(INPUT_LAS, info)

    clean_mask = denoise_by_elevation(z)
    tin_clean, tin_surface = progressive_tin_like_filter(x[clean_mask], y[clean_mask], z[clean_mask])
    csf_clean, cloth_surface = cloth_simulation_like_filter(x[clean_mask], y[clean_mask], z[clean_mask])
    tin_ground = np.zeros(z.shape, dtype=bool)
    csf_ground = np.zeros(z.shape, dtype=bool)
    tin_ground[np.flatnonzero(clean_mask)] = tin_clean
    csf_ground[np.flatnonzero(clean_mask)] = csf_clean

    tin_count = write_las_subset(OUTDIR / "ground_tin.las", INPUT_LAS, records, info, tin_ground)
    csf_count = write_las_subset(OUTDIR / "ground_csf.las", INPUT_LAS, records, info, csf_ground)

    dem, transform_info = make_dem(x, y, z, tin_ground)
    save_dem_geotiff(OUTDIR / "dem_tin.tif", dem, transform_info)

    save_point_cloud_preview(OUTDIR / "raw_point_cloud.png", x, y, z, title="原始点云高程渲染")
    save_point_cloud_preview(OUTDIR / "ground_tin_preview.png", x, y, z, tin_ground, title="渐进式三角网滤波地面点")
    save_filter_comparison(OUTDIR / "filter_comparison.png", x, y, z, tin_ground, csf_ground)
    save_dem_preview(OUTDIR / "dem_tin_preview.png", dem)
    save_flowchart(OUTDIR / "terrain_workflow.png")

    stats = {
        "total_points": int(info["point_count"]),
        "clean_points": int(np.count_nonzero(clean_mask)),
        "tin_ground": int(tin_count),
        "csf_ground": int(csf_count),
        "dem_shape": tuple(int(v) for v in dem.shape),
    }
    write_report_md(OUTDIR / "experiment_report_material.md", stats)
    print("Done. Outputs:", OUTDIR)


if __name__ == "__main__":
    main()
