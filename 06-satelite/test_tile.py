from rio_tiler.io import Reader
import sys

try:
    # タイル座標を指定してテスト
    z, x, y = 11, 1828, 752
    
    with Reader("http://fileserver/rgbnir_cog.tif") as image:
        try:
            print(f"ファイルに接続できました")
            # タイルを生成してみる
            imgdata = image.tile(x, y, z, indexes=(1, 2, 3), resampling_method="bilinear")
            print(f"タイル生成に成功しました: {imgdata}")
            sys.exit(0)
        except Exception as tile_error:
            print(f"タイル生成でエラーが発生: {str(tile_error)}")
            sys.exit(2)
except Exception as e:
    print(f"ファイル接続でエラーが発生: {str(e)}")
    sys.exit(1)
