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
async def make_image_cog():
    with Reader("static/rgbnir_cog.tif") as image:
        imgdata = image.preview([1, 2, 3])  # band-1, 2, 3
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")
