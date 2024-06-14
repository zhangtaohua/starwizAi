import json


def get_bbox_from_geojson(geojson):
    """
    从 GeoJSON 数据中提取边界框（bbox）

    :param geojson: GeoJSON 数据（可以是字典或 JSON 字符串）
    :return: bbox 元组 (min_x, min_y, max_x, max_y)
    """
    # 如果传入的是字符串，将其解析为字典
    if isinstance(geojson, str):
        geojson = json.loads(geojson)

    # 初始化 bbox 值
    min_x, min_y, max_x, max_y = float("inf"), float("inf"), float("-inf"), float("-inf")

    # 遍历 GeoJSON 对象中的所有几何对象
    def update_bbox(coords):
        nonlocal min_x, min_y, max_x, max_y
        for coord in coords:
            if isinstance(coord[0], (float, int)):  # 处理点
                x, y = coord[0], coord[1]
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            else:  # 处理嵌套的坐标（如多边形、折线等）
                update_bbox(coord)

    def extract_geometries(geometry):
        if geometry["type"] == "GeometryCollection":
            for geom in geometry["geometries"]:
                extract_geometries(geom)
        else:
            update_bbox(geometry["coordinates"])

    if geojson["type"] == "FeatureCollection":
        for feature in geojson["features"]:
            extract_geometries(feature["geometry"])
    elif geojson["type"] == "Feature":
        extract_geometries(geojson["geometry"])
    else:
        extract_geometries(geojson)

    return [min_x, min_y, max_x, max_y]


if __name__ == "__main__":
    # 示例 GeoJSON 数据 get_bbox_from_geojson
    geojson_data = ""
    geojson = json.loads(geojson_data)
    bbox = get_bbox_from_geojson(geojson)
    print(f"BBOX: {bbox}")
