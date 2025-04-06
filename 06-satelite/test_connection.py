from rio_tiler.io import Reader
import sys

try:
    with Reader("http://fileserver/rgbnir_cog.tif") as image:
        metadata = image.info()
        print("成功しました！")
        print(f"ファイルサイズ: {metadata.get('size', 'Unknown')}")
        print(f"画像の形状: {metadata.get('shape', 'Unknown')}")
        if hasattr(image, 'bounds'):
            print(f"地理境界: {image.bounds}")
        sys.exit(0)
except Exception as e:
    print(f"エラーが発生しました: {str(e)}")
    sys.exit(1)
