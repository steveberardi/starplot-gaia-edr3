import os
import tarfile
from pathlib import Path

import click


def get_dir_size(p: Path):
    total = 0
    for entry in os.scandir(p):
        # Use entry.is_file() and entry.stat().st_size directly
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            # Recursively call function for subdirectories
            total += get_dir_size(entry.path)
    return total


def archive(paths, output_filename):
    with tarfile.open(output_filename, "w:gz") as tar:
        for p in paths:
            tar.add(p, arcname=p.name)


@click.command()
@click.option("--source", help="Source path of catalog data")
@click.option("--destination", help="Destination path of zipped files")
@click.option(
    "--max_filesize", default=2048, help="Max filesize per archived file, in MB"
)
def main(source, destination, max_filesize):
    source_path = Path(source)
    destination_path = Path(destination)
    partition_names = sorted(
        [item.name for item in source_path.iterdir() if item.is_dir()]
    )

    max_filesize_bytes = max_filesize * 1024 * 1024

    ctr = 0
    group_size = 0
    group_paths = []

    for partition_name in partition_names:
        path = Path(source_path / partition_name)
        dir_size = get_dir_size(str(path))
        if group_size + dir_size > max_filesize_bytes:
            output_filename = destination_path / f"gaia-dr3-p{ctr}.tar.gz"
            print(f"Archiving {output_filename} | {str(int(group_size / 1024**2))} MB")
            archive(group_paths, output_filename)
            group_paths = []
            group_size = 0
            ctr += 1
        group_paths.append(path)
        group_size += dir_size

    if group_paths:
        output_filename = destination_path / f"gaia-dr3-p{ctr}.tar.gz"
        print(f"Archiving {output_filename} | {str(int(group_size / 1024**2))} MB")
        archive(group_paths, output_filename)


if __name__ == "__main__":
    main()
