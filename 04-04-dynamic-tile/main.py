import psycopg2
import psycopg2.pool
from fastapi import Depends, FastAPI, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI()
pool = psycopg2.pool.SimpleConnectionPool(
    dsn="postgresql://postgres:postgres@postgis:5432/postgres", minconn=2, maxconn=4
)


def get_connection():
    try:
        conn = pool.getconn()
        yield conn
    finally:
        pool.putconn(conn)


@app.get("/vector/{z}/{x}/{y}.pbf")
def get_tile(z: int, x: int, y: int, conn=Depends(get_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """WITH mvtgeom AS (
                SELECT ST_AsMVTGeom(ST_Transform(geom, 3857), ST_TileEnvelope(%(z)s, %(x)s, %(y)s)) AS geom
                FROM admin
                WHERE ST_Transform(geom, 3857) && ST_TileEnvelope(%(z)s, %(x)s, %(y)s)
            )
            SELECT ST_AsMVT(mvtgeom.*, 'vector')
            FROM mvtgeom; """,
            {"z": z, "x": x, "y": y},
        )
        val = cur.fetchone()[0]
    return Response(
        content=val.tobytes(), media_type="application/vnd.mapbox-vector-tile"
    )


app.mount("/", StaticFiles(directory="static"), name="static")
