from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pymbtiles import MBtiles

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/vector/{z}/{x}/{y}.pbf")
def vectortile(z: int, x: int, y: int):
    # xyz -> tms
    y = 2**z - y - 1
    with MBtiles("vector.mbtiles") as src:
        tile_data  = src.read_tile(z=z, x=x, y=y)
    if tile_data is None:
        return Response(status_code=404)

    # MBTiles形式のタイルデータはgzip圧縮されているため、　content-encodingヘッダーが必要

    return Response(
        content=tile_data,
        media_type="application/vnd.mapbox-vector-tile",
        headers={"content-encoding": "gzip"},
    )

@app.get("/raster/{z}/{x}/{y}.png")
def rastertile(z: int, x: int, y: int):
    y = 2 ** z - y - 1 # zxy -> tms
    with MBtiles("raster.mbtiles") as src:
        tile_data = src.read_tile(z=z, x=x, y=y)
    if tile_data is None:
        return Response(status_code=404)
    return Response(content=tile_data, media_type="image/png")