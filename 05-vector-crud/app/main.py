import psycopg2
import psycopg2.pool
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

pool = psycopg2.pool.SimpleConnectionPool(
    dsn="postgresql://postgres:postgres@postgis:5432/postgres", minconn=2, maxconn=4
)


def get_connection():
    conn = pool.getconn()
    yield conn
    pool.putconn(conn)


@app.get("/pois")
def get_pois(conn=Depends(get_connection)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, ST_X(geom) as longtitude, ST_Y(geom) as latitude FROM poi"
        )
        res = cur.fetchall()

    # GeoJSON-Featureの配列
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [longtitude, latitude],
            },
            "properties": {
                "id": id,
                "name": name,
            },
        }
        for id, name, longtitude, latitude in res
    ]

    # GeoJSON-FeatureCollectionとしてレスポンス
    return {
        "type": "FeatureCollection",
        "features": features,
    }


app.mount("/", StaticFiles(directory="static"), name="static")
