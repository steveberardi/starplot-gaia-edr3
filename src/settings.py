import pyarrow as pa

SCHEMA = pa.schema(
    [
        pa.field("pk", pa.int64(), nullable=False),
        pa.field("ra", pa.float64(), nullable=False),
        pa.field("dec", pa.float64(), nullable=False),
        pa.field("magnitude", pa.float64(), nullable=False),
        pa.field("bv", pa.float64(), nullable=False),
        pa.field("constellation_id", pa.string(), nullable=False),
        pa.field("hip", pa.float64(), nullable=True),
        pa.field("tyc", pa.string(), nullable=True),
        pa.field("parallax_mas", pa.float64(), nullable=False),
        pa.field("ra_mas_per_year", pa.float64(), nullable=False),
        pa.field("dec_mas_per_year", pa.float64(), nullable=False),
        pa.field("epoch_year", pa.int64(), nullable=False),
        pa.field("geometry", pa.binary(), nullable=False),
        pa.field("healpix_index", pa.int64(), nullable=False),
    ]
)
