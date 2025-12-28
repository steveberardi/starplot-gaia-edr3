from pathlib import Path


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
            # logger.info(f"HIP={bigsky_star.hip} | {f} diff -> {diff}")
            over_threshold = True

    return over_threshold
