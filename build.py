import csv
import time
import logging
import math
import multiprocessing

from logging.handlers import QueueHandler

from pathlib import Path

import polars as pl
from shapely.geometry import Point
from skyfield.api import position_of_radec, load_constellation_map

from starplot import Star
from starplot.data import Catalog

from utils import get_bv_v

__version__ = "0.1.0"

HERE = Path(__file__).resolve().parent
DATA_PATH = Path("/Volumes/Blue2TB/gaia/gdr3/")
BUILD_PATH = HERE / "build"

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# console_handler = logging.StreamHandler()
# file_handler = logging.FileHandler("build.log", mode='a')
# logger.addHandler(console_handler)
# logger.addHandler(file_handler)
# formatter = logging.Formatter(
#     "{asctime} - {levelname} - {message}",
#     style="{",
#     datefmt="%Y-%m-%d %H:%M",
# )
# console_handler.setFormatter(formatter)
# file_handler.setFormatter(formatter)


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


def stars(index, logger):
    source_path = DATA_PATH / "gaia_source"
    source_filenames = sorted(list(source_path.glob("*.csv.gz")))

    try:
        gaia_source_filename = source_filenames[index]
    except IndexError:
        logger.error(f"Index does not exist: {index}")
        return

    catalog_length = 0
    skipped_no_mag = 0
    crossmatches_hip = 0
    crossmatches_tyc = 0
    # over_threshold_count = 0

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
        parallax_mas = round(row["parallax"] or 0, 6)
        ra_mas_per_year = round(row["pmra"] or 0, 6)
        dec_mas_per_year = round(row["pmdec"] or 0, 6)

        # Find constellation
        pos = position_of_radec(ra / 15, dec)
        constellation_id = constellation_map(pos).lower()

        source_id = row["source_id"]
        hip = crossmatch_hip.get(source_id)
        tyc = crossmatch_tyc.get(source_id)
        star = Star(
            pk=source_id,
            ra=ra,
            dec=dec,
            hip=hip,
            tyc=tyc,
            magnitude=round(v, 2),
            bv=round(bv, 2),
            constellation_id=constellation_id,
            parallax_mas=parallax_mas,
            ra_mas_per_year=ra_mas_per_year,
            dec_mas_per_year=dec_mas_per_year,
            epoch_year=row["ref_epoch"],
            geometry=Point(ra, dec),
        )
        if hip:
            crossmatches_hip += 1

        elif tyc:
            crossmatches_tyc += 1

        yield star
        catalog_length += 1

    duration = round(time.time() - time_start, 4)
    logger.info(f"{gaia_source_filename.name} done in {duration}")

    logger.info(f"skipped_no_mag = {skipped_no_mag:,}")
    logger.info(f"catalog_length = {catalog_length:,}")
    logger.info(f"crossmatches_hip = {crossmatches_hip:,}")
    logger.info(f"crossmatches_tyc = {crossmatches_tyc:,}")
    # logger.info(f"over_threshold_count = {over_threshold_count:,}")


def build(index, logger):
    """Builds a single source file"""
    logger.info(f"Building... {index}")
    Catalog.build(
        objects=stars(index, logger),
        path=BUILD_PATH / "edr3",
        chunk_size=1_000_000,
        columns=[
            "pk",
            "ra",
            "dec",
            "magnitude",
            "bv",
            "constellation_id",
            "hip",
            "tyc",
            "parallax_mas",
            "ra_mas_per_year",
            "dec_mas_per_year",
            "epoch_year",
            "geometry",
        ],
        sorting_columns=["magnitude"],
        partition_columns=["healpix_index"],
        compression="snappy",
        row_group_size=100_000,
        healpix_nside=8,
    )


def init_listener():
    root = logging.getLogger()
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("build.log", mode="a")
    formatter = logging.Formatter(
        "%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)
    root.addHandler(file_handler)


def logger_process(queue):
    init_listener()
    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import sys
            import traceback

            traceback.print_exc(file=sys.stderr)


def init_worker(queue):
    log_handler = QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(log_handler)
    root.setLevel(logging.INFO)


def worker_process(queue, chunk, worker_id):
    init_worker(queue)
    name = multiprocessing.current_process().name
    logger = logging.getLogger(f"build.{worker_id}")
    logger.info(f"Starting worker: {name} | {chunk}")

    for index in chunk:
        build(index, logger)

    logger.info(f"Worker finished: {name} | {chunk}")


def chunks(items, n):
    """Yield successive n-sized chunks from items"""
    for i in range(0, len(items), n):
        yield items[i : i + n]


def main():
    time_start = time.time()

    # 3387 total files

    start = 0
    stop = 3390  # inclusive

    num_workers = 10

    items = [n for n in range(start, stop + 1)]
    chunk_size = math.ceil(len(items) / num_workers)
    items_chunked = list(chunks(items, chunk_size))

    queue = multiprocessing.Queue(-1)

    listener = multiprocessing.Process(target=logger_process, args=(queue,))
    listener.start()

    log_handler = QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(log_handler)
    root.setLevel(logging.INFO)
    logger = logging.getLogger("build.main")
    logger.info(f"Starting {num_workers} workers...")

    workers = []
    for i, chunk in enumerate(items_chunked):
        worker = multiprocessing.Process(
            target=worker_process,
            args=(queue, chunk, i + 2),  # add 2 cause first process is listener
        )
        workers.append(worker)
        worker.start()
    for w in workers:
        w.join()

    duration = time.time() - time_start
    average = round(duration / len(items), 2)
    logger.info(f"Done: {start} -> {stop}")
    logger.info(f"Duration: {round(duration, 4)} | Average: {average}")

    queue.put_nowait(None)
    listener.join()


if __name__ == "__main__":
    main()
