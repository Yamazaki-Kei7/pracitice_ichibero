from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles

app = FastAPI()
app.mount("/", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/rgbnir.png")
async def make_image():
    with Reader("static/rgbnir.tif", options={"unscale": 0.1}) as image:
        imgdata = image.read([1, 2, 3])
    png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/rgbnir_cog.png")
async def make_image_cog(scale_min: float, scale_max: float):
    with Reader("static/rgbnir_cog.tif") as image:
        imgdata = image.preview([1, 2, 3])  # band-1, 2, 3
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/ndvi.png")
async def make_image_ndvi():
    with Reader("static/rgbnir_cog.tif") as image:
        imgdata = image.preview(expression="(b4-b1)/(b4+b1)")
        imgdata.rescale(((0, 1),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/rgbnir_remote_cog.png")
async def make_image_remote_cog(scale_min: float, scale_max: float):
    with Reader("http://fileserver/rgbnir_cog.tif") as image:
        imgdata = image.preview([1, 2, 3])
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/rgbnir_remote_cog_part.png")
async def make_image_remote_cog_part(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    max_size: int = 256,
    scale_min: float = 0,
    scale_max: float = 2000,
):
    with Reader(
        "http://fileserver/rgbnir_cog.tif",
    ) as image:
        imgdata = image.part(
            bbox=(minx, miny, maxx, maxy),
            indexes=(1, 2, 3),
            dst_crs="EPSG:32654",
            max_size=max_size,
        )
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/tiles/{z}/{x}/{y}.webp")
async def make_image_remote_cog_tile(
    z: int,
    x: int,
    y: int,
    scale_min: float = 0,
    scale_max: float = 2000,
):
    with Reader("http://fileserver/rgbnir_cog.tif") as image:
        imgdata = image.tile(x, y, z, indexes=(1, 2, 3), resampling_methos="bilinear")
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")
