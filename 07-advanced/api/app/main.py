import httpx
import psycopg2
import psycopg2.pool
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from rio_tiler.io import Reader

from app.model import PoiCreate, PoiUpdate

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
)

pool = psycopg2.pool.SimpleConnectionPool(
    dsn="postgresql://postgres:postgres@postgis:5432/postgres", minconn=2, maxconn=4
)


def get_connection():
    try:
        conn = pool.getconn()
        yield conn
    finally:
        pool.putconn(conn)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/points")
def get_points(bbox: str, conn=Depends(get_connection)):
    # クエリパラメータbboxの値をチェック
    _bbox = bbox.split(",")
    if len(_bbox) != 4:
        raise ValueError(
            "bboxの値が不正です。minx,miny,maxx,maxyの順で指定してください。"
        )
    minx, miny, maxx, maxy = list(map(float, _bbox))

    with conn.cursor() as cur:
        cur.execute(
            """SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(ST_AsGeoJSON(points.*)::json), '[]'::json)
            )
            FROM points
            WHERE geom && ST_MakeEnvelope(%(minx)s, %(miny)s, %(maxx)s, %(maxy)s, 4326)
            LIMIT 1000""",
            {
                "minx": minx,
                "miny": miny,
                "maxx": maxx,
                "maxy": maxy,
            },
        )
        res = cur.fetchall()
    return res[0][0]


@app.post("/points")
def create_point(data: PoiCreate, conn=Depends(get_connection)):
    """
    pointsテーブルに地物を追加する
    """
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO points (geom) VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326))",
            (data.longitude, data.latitude),
        )
        conn.commit()

        # 作成した地物のIDを取得
        cur.execute("SELECT lastval()")
        res = cur.fetchone()
        _id = res[0]

        # 作成した地物の情報を取得
        cur.execute(
            "SELECT id, ST_X(geom) as logtitude, ST_Y(geom) as latitude FROM points WHERE id = %s",
            (_id,),
        )
        id, longitude, latitude = cur.fetchone()

    # 作成した地物をGeoJSONとして返す
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "id": id,
        },
    }


@app.delete("/points/{id}")
def delete_point(id: int, conn=Depends(get_connection)):
    """
    pointsテーブルから地物を削除する
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM points WHERE id = %s", (id,))
        conn.commit()

    return Response(status_code=204)


@app.patch("/points/{id}")
def update_point(id: int, data: PoiUpdate, conn=Depends(get_connection)):
    """
    pointsテーブルの地物を更新する
    """
    # 更新対象のポイントが存在するか確認
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM points WHERE id = %s)", (id,))
        exists = cur.fetchone()[0]
        if not exists:
            raise HTTPException(
                status_code=404, detail="指定されたIDのポイントが見つかりません"
            )

        # 緯度・経度の両方が更新対象になる場合
        if data.longitude is not None and data.latitude is not None:
            cur.execute(
                "UPDATE points SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326) WHERE id = %s",
                (data.longitude, data.latitude, id),
            )
        # 経度のみ更新する場合
        elif data.longitude is not None:
            cur.execute(
                "UPDATE points SET geom = ST_SetSRID(ST_MakePoint(%s, ST_Y(geom)), 4326) WHERE id = %s",
                (data.longitude, id),
            )
        # 緯度のみ更新する場合
        elif data.latitude is not None:
            cur.execute(
                "UPDATE points SET geom = ST_SetSRID(ST_MakePoint(ST_X(geom), %s), 4326) WHERE id = %s",
                (data.latitude, id),
            )
        else:
            # 更新するデータがない場合は現在のデータを返す
            pass

        conn.commit()

        # 更新した地物の情報を取得
        cur.execute(
            "SELECT id, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM points WHERE id = %s",
            (id,),
        )
        id, longitude, latitude = cur.fetchone()

    # 更新した地物をGeoJSONとして返す
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "id": id,
        },
    }


async def search_dataset(
    minx: float, miny: float, maxx: float, maxy: float, limit: int = 12
):
    """STACを使って衛星画像を検索"""

    url = "http://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items"
    params = {
        "limit": limit,
        "bbox": f"{minx},{miny},{maxx},{maxy}",
    }
    headers = {
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params, headers=headers)
        res.raise_for_status()
        dataset = res.json()

        return dataset


@app.get("/points/{point_id}/satellite.jpg")
async def satelite_preview(
    point_id: int, max_size: int = 256, conn=Depends(get_connection)
):
    """DBに登録された地点を指定して、その地点を含む衛生画像を検索"""
    if max_size > 1024:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    # pointsテーブルから指定したIDのデータを取得
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ST_X(geom) as longitude, ST_Y(geom) as latitude FROM points WHERE id = %s",
            (point_id,),
        )
        res = cur.fetchone()

    # データが存在しない場合は404エラーを返す
    if not res:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    longtitude, latitude = res

    # 衛生画像を検索
    # 便宜上、地点の周囲0.01度の範囲で検索
    buffer = 0.01
    minx = longtitude - buffer
    miny = latitude - buffer
    maxx = longtitude + buffer
    maxy = latitude + buffer

    result = await search_dataset(minx, miny, maxx, maxy, limit=1)
    if len(result["features"]) == 0:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    feature = result["features"][0]
    cog_url = feature["assets"]["visual"]["href"]

    with Reader(cog_url) as src:
        img = src.preview(max_size=max_size)
    jpg = img.render(img_format="JPEG")

    return Response(content=jpg, media_type="image/jpg")
