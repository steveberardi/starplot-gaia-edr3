from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import time

from starplot import Star, OpticPlot, DSO, Observer, _
from starplot.models import Refractor
from starplot.styles import PlotStyle, extensions
from starplot.data.catalogs import Catalog

HERE = Path(__file__).resolve().parent
BUILD_PATH = HERE / "build"

gaia = Catalog(
    path=BUILD_PATH / "edr3" / "**" / "*.parquet",
    hive_partitioning=True,
    healpix_nside=8,
)

start = time.time()

# results = Star.get(hip=32349)
results = Star.find(
    where=[
        _.healpix_index == 25,
        _.magnitude < 8,
        _.hip.notnull(),
    ],
    catalog=gaia,
)
print(len(results))
# p = results.to_polars()
# print(results.count())
# for s in results[:5]:
#     print(s.geometry)

# results = Star.find(where=[_.healpix_index == 1, _.magnitude < 8], catalog=gaia)
# print(results.count())

duration = time.time() - start

print(duration)
exit()


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

    return 3


def alpha(star: Star) -> float:
    """Very simple sizer by magnitude for optic plots"""
    m = star.magnitude

    if m < 10:
        return 1
    elif m < 12:
        return 0.7
    elif m < 14:
        return 0.6

    return 0.5


dt = datetime(2023, 12, 16, 21, 0, 0, tzinfo=ZoneInfo("US/Pacific"))

style = PlotStyle().extend(
    extensions.GRAYSCALE_DARK,
    extensions.OPTIC,
    {"star": {"marker": {"edge_color": "#fff"}}},
)

observer = Observer(
    dt=dt,
    lat=33.363484,
    lon=-116.836394,
)

target = DSO.get(m="13")
p = OpticPlot(
    ra=target.ra,
    dec=target.dec,
    observer=observer,
    # Refractor Telescope
    optic=Refractor(
        focal_length=714,
        eyepiece_focal_length=7,
        eyepiece_fov=82,
    ),
    style=style,
    resolution=4096,
    scale=0.56,
    raise_on_below_horizon=False,
    debug=True,
)
p.stars(
    where=[_.magnitude < 18],
    where_labels=[False],
    catalog=gaia,
    alpha_fn=alpha,
    size_fn=size,
    # color_fn=color_by_bv,
)

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
