from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import time

from starplot import Star, OpticPlot, DSO, Observer, _
from starplot.models import Binoculars, Refractor
from starplot.styles import PlotStyle, extensions
from starplot.data.catalogs import Catalog
from starplot.callables import color_by_bv

HERE = Path(__file__).resolve().parent
BUILD_PATH = HERE / "build"

gaia = Catalog(
    # path=Path("/Volumes/Blue2TB/build/gdr3/") / "**" / "*.parquet",
    # path=BUILD_PATH / "edr3" / "**" / "*.parquet",
    path=Path("/Volumes/starship500/build/gaia-18-c") / "**" / "*.parquet",
    hive_partitioning=True,
    healpix_nside=4,
    spatial_query_method="healpix",
)

start = time.time()

# ctr = 0
# for n in range(193):
#     results = Star.find(
#         where=[
#             _.healpix_index == n
#         ],
#         catalog=gaia,
#     )
#     count = len(results)
#     ctr += count
#     print(n, count, ctr)


# print("total")
# print(ctr)

# duration = time.time() - start

# print(duration)
# exit()


def size(star: Star) -> float:
    """Very simple sizer by magnitude for optic plots"""
    m = star.magnitude

    if m < 4.6:
        return (9 - m) ** 3.6 * 9
    elif m < 5.85:
        return (9 - m) ** 3.6 * 9
    elif m < 9:
        return (13 - m) ** 1.8 * 9
    elif m < 12:
        return 4.8 * 6
    elif m < 14:
        return 10

    return 3


def alpha(star: Star) -> float:
    """Very simple sizer by magnitude for optic plots"""
    m = star.magnitude

    if m < 10:
        return 1
    elif m < 12:
        return 0.9
    elif m < 15:
        return 0.85

    return 0.6


dt = datetime(2023, 12, 16, 21, 0, 0, tzinfo=ZoneInfo("US/Pacific"))

style = PlotStyle().extend(
    extensions.GRAYSCALE_DARK,
    # extensions.BLUE_NIGHT,
    # extensions.GRADIENT_TRUE_NIGHT,
    extensions.OPTIC,
    {"star": {"marker": {"color": "#fff", "edge_color": "#fff"}}},
)

observer = Observer(
    dt=dt,
    lat=33.363484,
    lon=-116.836394,
)

target = DSO.get(m="13")
# target = DSO.get(ngc="869")
target = DSO.get(ngc="5139")
# target = DSO.get(m="11")
p = OpticPlot(
    ra=target.ra,
    dec=target.dec,
    observer=observer,
    # Refractor Telescope
    optic=Refractor(
        focal_length=714,
        eyepiece_focal_length=8,
        eyepiece_fov=100,
    ),
    # optic=Binoculars(
    #     fov=65,
    #     magnification=35,
    # ),
    style=style,
    resolution=4096,
    scale=0.25,
    raise_on_below_horizon=False,
    debug=True,
)
p.stars(
    where=[_.magnitude < 18, _.magnitude > 9],
    where_labels=[False],
    catalog=gaia,
    alpha_fn=alpha,
    size_fn=size,
    # style__marker__symbol="star_4"
    # color_fn=color_by_bv,
)
# p.globular_clusters(where=[_.ngc=="5139"])
p.stars(
    where=[_.magnitude <= 9],
    where_labels=[False],
    alpha_fn=alpha,
    size_fn=size,
    # style__marker__symbol="star_4"
    # color_fn=color_by_bv,
)
# print(p.magnitude_range)
p.export("m13.png", padding=0.1, transparent=True)


# p = OpticPlot(
#     ra=2.3450*15,
#     dec=57.1375,
#     observer=observer,
#     # Refractor Telescope
#     optic=Refractor(
#         focal_length=714,
#         eyepiece_focal_length=13,
#         eyepiece_fov=100,
#     ),
#     style=style,
#     resolution=4096,
#     scale=0.5,
#     raise_on_below_horizon=False,
#     debug=True,
# )
# p.stars(
#     where=[_.magnitude < 16],
#     where_labels=[False],
#     catalog=gaia,
#     alpha_fn=alpha,
#     size_fn=size,
#     # color_fn=color_by_bv,
# )

# p.export("double.png", padding=0.1, transparent=True)
