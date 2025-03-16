import psycopg2
import psycopg2.pool
from fastapi import Depends, FastAPI, Response, status
from fastapi.staticfiles import StaticFiles

from app.models import PoiCreate, PoiUpdate

app = FastAPI()

pool = psycopg2.pool.SimpleConnectionPool(
    dsn="postgresql://postgres:postgres@postgis:5432/postgres", minconn=2, maxconn=20
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


@app.post("/pois")
def create_poi(data: PoiCreate, conn=Depends(get_connection)):
    """POIテーブルに地物を追加"""

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO poi (name, geom) VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))",
            (data.name, data.longitude, data.latitude),
        )
        conn.commit()

        # 作成した地物のIDを取得
        cur.execute("SELECT lastval()")
        res = cur.fetchone()
        _id = res[0]
        # 作成した地物の情報を取得
        cur.execute(
            "SELECT id, name, ST_X(geom) as longtitude, ST_Y(geom) as latitude FROM poi WHERE id = %s",
            (_id,),
        )
        id, name, longtitude, latitude = cur.fetchone()

    # 作成した地物をGeoJSONとして返す
    return {
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


@app.get("/pois_sql")
def get_pois_sql(conn=Depends(get_connection)):
    import json

    with conn.cursor() as cur:
        cur.execute("SELECT ST_AsGeoJSON(poi.*) FROM poi")
        res = cur.fetchall()

    features = [json.loads(row[0]) for row in res]

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@app.get("/pois_sql2")
def get_pois_sql2(bbox: str, conn=Depends(get_connection)):
    """
    PoIテーブルの地物をGeoJSONとして返す。GeoJSON-FeatureCollectionはSQLで生成
    """

    # クエリパラメータbboxの値をチェック
    _bbox = bbox.split(",")
    if len(_bbox) != 4:
        raise ValueError(
            "bboxの値が不正です。minx,miny,maxx,maxyの順でカンマ区切りで指定してください。"
        )
    minx, miny, maxx, maxy = list(map(float, _bbox))

    with conn.cursor() as cur:
        # As Geojson
        cur.execute(
            """SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(ST_AsGeoJSON(poi.*)::json), '[]'::json)
            )
            FROM poi
            WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
            LIMIT 100 """,
            (minx, miny, maxx, maxy),
        )
        res = cur.fetchone()
    return res[0]


@app.delete("/pois/{id}")
def delete_poi(id: int, conn=Depends(get_connection)):
    """POIテーブルの地物を削除"""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM poi WHERE id = %s", (id,))
        conn.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.patch("/pois/{poi_id}")
def update_poi(poi_id: int, data: PoiUpdate, conn=Depends(get_connection)):
    """POIテーブルの地物を更新"""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM poi WHERE id = %s", (poi_id,))
        if not cur.fetchone():
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        # 更新
        cur.execute(
            """
            UPDATE poi
            SET name = COALESCE(%s, name),
                geom = ST_SetSRID(ST_MakePoint(COALESCE(%s, ST_X(geom)), COALESCE(%s, ST_Y(geom))), 4326)
            WHERE id = %s
            """,
            (data.name, data.longitude, data.latitude, poi_id),
        )
        conn.commit()

        # 更新した地物の情報を取得
        cur.execute(
            "SELECT id, name, ST_X(geom) as longtitude, ST_Y(geom) as latitude FROM poi WHERE id = %s",
            (poi_id,),
        )
        _id, name, longtitude, latitude = cur.fetchone()

    # 更新した地物をGeoJSONとして返す
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longtitude, latitude],
        },
        "properties": {
            "id": _id,
            "name": name,
        },
    }


@app.get("/pois/tiles/{z}/{x}/{y}.pbf")
def get_pois_tiles(z: int, x: int, y: int, conn=Depends(get_connection)):
    """POIテーブルの地物をMVTとして返す"""

    with conn.cursor() as cur:
        cur.execute(
            """WITH mvtgeom AS (
                SELECT ST_AsMVTGeom(
                    ST_Transform(geom, 3857), ST_TileEnvelope(%(z)s, %(x)s, %(y)s)) AS geom, id, name
                FROM poi
                WHERE ST_Transform(geom, 3857) && ST_TileEnvelope(%(z)s, %(x)s, %(y)s)
            )
            SELECT ST_AsMVT(mvtgeom.*, 'poi', 4096, 'geom')
            FROM mvtgeom;""",
            {"z": z, "x": x, "y": y},
        )
        val = cur.fetchone()[0]

    return Response(
        content=val.tobytes(),
        media_type="application/vnd.mapbox-vector-tile",
    )


app.mount("/", StaticFiles(directory="static"), name="static")
