import csv
import time
import logging

from pathlib import Path

import polars as pl
from shapely.geometry import Point
from skyfield.api import load_constellation_map

from starplot import Star
from starplot.data import Catalog
from starplot.data.catalogs import BIG_SKY

from utils import get_bv_v

__version__ = "0.1.0"

HERE = Path(__file__).resolve().parent
DATA_PATH = Path("/Volumes/Blue2TB/gaia/gdr3/")
BUILD_PATH = HERE / "build"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("build.log", mode='a')
logger.addHandler(console_handler)
logger.addHandler(file_handler)
formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

constellation_map = load_constellation_map()

def read_crossmatch(source_path, cast=int):
    """Returns dictionary mapping Gaia source_id to external source id"""

    with open(source_path, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        return {
            int(row["source_id"]): cast(row["original_ext_source_id"]) for row in reader
        }


crossmatch_hip = read_crossmatch(
    source_path=DATA_PATH
    / "cross_match"
    / "hipparcos2_best_neighbor"
    / "Hipparcos2BestNeighbour.csv"
)
crossmatch_tyc = read_crossmatch(
    source_path=DATA_PATH
    / "cross_match"
    / "tycho2tdsc_merge_neighbourhood"
    / "tycho2tdsc_merge_neighbourhood.csv",
    cast=str,
)


def compare_stars(gaia_star, bigsky_star, threshold=0.25) -> bool:
    if not gaia_star or not bigsky_star:
        return

    over_threshold = False
    fields = ["magnitude", "bv", "ra", "dec"]

    for f in fields:
        gaia_value = getattr(gaia_star, f, None)
        bigsky_value = getattr(bigsky_star, f, None)
        if gaia_value is None or bigsky_value is None:
            continue
        diff = abs(gaia_value - bigsky_value)
        if diff > threshold:
            logger.info(f"HIP={bigsky_star.hip} | {f} diff -> {diff}")
            over_threshold = True

    return over_threshold


def stars(start=None, stop=None):
    source_path = DATA_PATH / "gaia_source"
    source_filenames = sorted(list(source_path.glob("*.csv.gz")))
    
    if start is not None and stop is not None:
        source_filenames = source_filenames[start:stop]
    else:
        start = 0
        stop = len(source_filenames)

    catalog_length = 0
    skipped_no_mag = 0
    crossmatches_hip = 0
    crossmatches_tyc = 0
    over_threshold_count = 0

    for i, gaia_source_filename in enumerate(source_filenames, start):
        logger.info(f"{i} / {stop}")
        logger.info(gaia_source_filename.name)
        time_start = time.time()

        df = pl.read_csv(
            source=gaia_source_filename,
            comment_prefix="#",
            null_values=["null"],
            columns=[
                "ra",
                "dec",
                "source_id",
                "ref_epoch",
                "parallax",
                "pmra",
                "pmdec",
                "phot_g_mean_mag",
                "bp_rp",
            ],
        )
        for row in df.iter_rows(named=True):
            phot_g_mean_mag, bp_rp = row["phot_g_mean_mag"], row["bp_rp"]
            if not phot_g_mean_mag or not bp_rp:
                skipped_no_mag += 1
                continue

            bv, v = get_bv_v(phot_g_mean_mag, bp_rp)

            ra = round(row["ra"], 6)
            dec = round(row["dec"], 6)

            # Find constellation
            # pos = position_of_radec(ra / 15, dec)
            constellation_id = None  # constellation_map(pos).lower()

            source_id = row["source_id"]
            hip = crossmatch_hip.get(source_id)
            tyc = crossmatch_tyc.get(source_id)
            star = Star(
                ra=ra,
                dec=dec,
                hip=hip,
                tyc=tyc,
                magnitude=v,
                bv=bv,
                constellation_id=constellation_id,
                parallax_mas=row["parallax"] or 0,
                ra_mas_per_year=row["pmra"] or 0,
                dec_mas_per_year=row["pmdec"] or 0,
                epoch_year=row["ref_epoch"],
                geometry=Point(ra, dec),
            )
            if hip:
                crossmatches_hip += 1

                # bigsky_star = Star.get(hip=hip, catalog=BIG_SKY)
                # if not bigsky_star:
                #     logger.warning(f">>>> HIP not in bigsky {hip}")
                # else:
                #     crossmatches_hip += 1
                #     over_threshold = compare_stars(star, bigsky_star)
                #     if over_threshold:
                #         over_threshold_count += 1

            elif tyc:
                crossmatches_tyc += 1

                # bigsky_star = Star.get(tyc=tyc, catalog=BIG_SKY)
                # if not bigsky_star:
                #     logger.warning(f">>>> TYC not in bigsky {tyc}")
                # else:    
                #     over_threshold = compare_stars(star, bigsky_star)
                #     if over_threshold:
                #         over_threshold_count += 1

            yield star
            catalog_length += 1

        duration = round(time.time() - time_start, 4)
        logger.info(f"{gaia_source_filename.name} done in {duration}")

    logger.info(f"skipped_no_mag = {skipped_no_mag:,}")
    logger.info(f"catalog_length = {catalog_length:,}")
    logger.info(f"crossmatches_hip = {crossmatches_hip:,}")
    logger.info(f"crossmatches_tyc = {crossmatches_tyc:,}")
    # logger.info(f"over_threshold_count = {over_threshold_count:,}")


def build():
    # Next chunk START should be previous chunk STOP
    start = 100
    stop = 200

    time_start = time.time()
    logger.info(f"Starting... [{start} : {stop}]")

    Catalog.build(
        objects=stars(start, stop),
        path=BUILD_PATH / "edr3",
        chunk_size=200_000,
        columns=[
            "ra",
            "dec",
            "magnitude",
            "bv",
            # "constellation_id",
            "parallax_mas",
            "ra_mas_per_year",
            "dec_mas_per_year",
            "epoch_year",
            "geometry",
        ],
        sorting_columns=["magnitude"],
        partition_columns=["healpix_index"],
        compression="snappy",
        row_group_size=200_000,
        healpix_nside=8,
    )
    duration = time.time() - time_start
    logger.info(f"Duration: {round(duration, 4)}")


if __name__ == "__main__":
    build()
