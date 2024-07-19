import os

import numpy as np
from osgeo import gdal, ogr, osr

from .fileCommon import delete_and_rename_file


def gdal_read_tiff(filepath):
    dataset = gdal.Open(filepath)
    if dataset is None:
        print("Error: Unable to open the input TIFF file.")
        return None
    return dataset


def gdal_read_tif_to_array(filepath):
    dataset = gdal.Open(filepath)
    if dataset is None:
        print("Error: Unable to open the input TIFF file.")
        return None
    im_data = dataset.ReadAsArray(0, 0, dataset.RasterXSize, dataset.RasterYSize)
    return im_data


# 没有测试
def gdal_tiff_16Byte_to_8Byte(input):
    # 读取tiff数据
    ds = gdal_read_tiff(input)
    assert ds

    info = gdal.Info(ds, format="json")
    bands = info["bands"]
    band_len = len(bands)
    assert ds
    bands_map = [[], [], [], []]
    # print(info)
    for band in range(ds.RasterCount):
        band += 1
        srcband = ds.GetRasterBand(band)
        if srcband is None:
            continue
        maxmin = srcband.ComputeRasterMinMax(True)
        bands_map[band - 1] = [maxmin[0], maxmin[1]]

    data_type = info["bands"][0]["type"]

    # 获取文件前缀（不包含扩展名的部分）
    file_prefix = os.path.splitext(input)[0]
    # 获取文件后缀（扩展名）
    file_suffix = os.path.splitext(input)[1]
    output = file_prefix + file_suffix.split(".")[0] + "_scale." + file_suffix.split(".")[1]

    if data_type != "Byte":

        if band_len < 3:
            # print("小于三波段，按单波段处理")
            # 读取栅格数据
            band = ds.GetRasterBand(1)
            data = band.ReadAsArray()
            # 将数据展平为一维数组
            data_flat = data.flatten()
            # 计算数据的累积分布函数（CDF）
            sorted_data = np.sort(data_flat)
            # 查找2%和98%处的像素值
            value_at_2_percentile = np.percentile(sorted_data, 2)
            value_at_98_percentile = np.percentile(sorted_data, 98)
            cmd = (
                f"gdal_translate -ot Byte -a_nodata 0  -r average -of GTiff "
                f"-scale_1 {value_at_2_percentile} {value_at_98_percentile} 0 255 -b 1 {input}  {output} "
            )
            print(cmd)
            os.system(cmd)
            ds = None
            delete_and_rename_file(input, output)

        else:
            flags = 1
            ds = None
            # print("数据为3波段以及以上，按多波段处理")
            scale_1_min = bands_map[0][0]
            scale_1_max = bands_map[0][1]
            scale_2_min = bands_map[1][0]
            scale_2_max = bands_map[1][1]
            scale_3_min = bands_map[2][0]
            scale_3_max = bands_map[2][1]
            # print("生成多波段rgb格式影像")
            cmd_scale = (
                f"gdal_translate -ot Byte -a_nodata 0  -r average  -of GTiff  -scale_3 {scale_3_min} {scale_3_max} 0 255 -b 1"
                f" -scale_2 {scale_2_min} {scale_2_max} 0 255 -b 2"
                f" -scale_1 {scale_1_min} {scale_1_max} 0 255 -b 3"
                f" {input} {output}"
            )
            print(cmd_scale)
            os.system(cmd_scale)

            delete_and_rename_file(input, output)


# 没有测试
def png_to_tiff(source, bbox):
    try:
        base = os.path.splitext(source)[0] + ".tif"
        ds = gdal.Open(source)
        # print(base)
        gt = gdal.Translate(
            base,
            ds,
            outputBounds=bbox,
            format="GTiff",
            outputSRS="EPSG:4326",
            creationOptions=["SRC_METHOD=NO_GEOTRANSFORM"],
        )
        gt = None
        return base
    except Exception as e:
        print("png2tiff error: ", e)
        return None


# 没有测试
def tiff_to_png(source, out):
    try:
        # tmp = "tmp/" + str(uuid.UUID) + ".tif"
        gdal_tiff_16Byte_to_8Byte(source)
        # ds = gdal.Warp(tmp, source,
        #                options=gdal.WarpOptions(dstSRS="EPSG:4326", format="GTiff", outputType=gdal.GDT_Byte))
        ds = gdal.Open(source)
        info = gdal.Info(ds=ds, format="json")
        size = info["size"]
        size = str(size[0]) + "x" + str(size[1])
        center = info["cornerCoordinates"]["center"]
        bbox = info["cornerCoordinates"]
        bbox_str_arr = []
        ul = bbox["upperLeft"]
        ll = bbox["lowerLeft"]
        lr = bbox["lowerRight"]
        ur = bbox["upperRight"]
        bbox_str_arr.append([str(ul[0]), str(ul[1])])
        bbox_str_arr.append([str(ll[0]), str(ll[1])])
        bbox_str_arr.append([str(lr[0]), str(lr[1])])
        bbox_str_arr.append([str(ur[0]), str(ur[1])])

        opt = gdal.TranslateOptions(format="PNG", height=1024, width=1024)
        gdal.Translate(out, source, options=opt)
        # os.remove(tmp)
        center_str = str(center[0]) + "," + str(center[1])
        return center_str, bbox_str_arr, size
    except Exception as e:
        print(e)
        return None, None, None


def create_tiff_with_extent_and_srs(output_tiff, width, height, bbox, srs_epsg=4326):
    """
    Create a TIFF file with specified extent and spatial reference system.

    :param output_tiff: Path to the output TIFF file.
    :param width: Width of the output TIFF in pixels.
    :param height: Height of the output TIFF in pixels.
    :param bbox: Bounding box as a tuple (minX, minY, maxX, maxY).
    :param srs_epsg: EPSG code for the spatial reference system. Default is 4326.
    """
    # Create a new raster dataset
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(output_tiff, width, height, 1, gdal.GDT_Byte)

    if not dataset:
        raise RuntimeError(f"Failed to create output TIFF file: {output_tiff}")

    # Set the spatial reference system
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(srs_epsg)
    dataset.SetProjection(srs.ExportToWkt())

    # Calculate geotransform
    minX, minY, maxX, maxY = bbox
    pixel_width = (maxX - minX) / width
    pixel_height = (maxY - minY) / height
    geotransform = (minX, pixel_width, 0, maxY, 0, -pixel_height)
    dataset.SetGeoTransform(geotransform)

    # Write some data to the raster band (optional)
    band = dataset.GetRasterBand(1)
    band.Fill(0)  # Fill the band with zeros (or any other value if needed)
    band.FlushCache()

    # Close the dataset
    dataset = None
    print(f"TIFF file created with extent and SRS: {output_tiff}")


def get_extent_from_tiff(filepath):
    print("GetGeoTransform", filepath)
    dataset = gdal.Open(filepath)
    # 获取纬度和经度信息
    geo_transform = dataset.GetGeoTransform()
    min_longitude = geo_transform[0]
    latitude_pixel_size = geo_transform[5]
    max_longitude = min_longitude + dataset.RasterXSize * geo_transform[1]
    min_latitude = geo_transform[3] + dataset.RasterYSize * geo_transform[5]
    latitude_pixel_size *= -1
    max_latitude = min_latitude - dataset.RasterYSize * geo_transform[5]
    # return min_longitude, max_longitude, min_latitude, max_latitude
    return [
        (min_longitude, min_latitude),
        (min_longitude, max_latitude),
        (max_longitude, max_latitude),
        (max_longitude, min_latitude),
    ]
