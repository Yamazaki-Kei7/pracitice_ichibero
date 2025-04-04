from fastapi import FastAPI, Response
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles

app = FastAPI()


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
