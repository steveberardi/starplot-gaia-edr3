# starplot-gaia-dr3

Star catalog builder for [Starplot](https://github.com/steveberardi/starplot), using data from Gaia DR3.

1. `make install` to create virtual environment
2. `make build-*` to build catalog files (see `Makefile` for possible values of `*`). This command will:
    - Build the catalog files
    - Squash parquet files into one per partition
    - Archive all files (preserving partition folders) into 2 GB tar files
3. Releases are created manually for this catalog
