from fastapi import FastAPI
from rio_tiler.io import Reader

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/rgbnir.png")
async def make_image():
    with Reader()