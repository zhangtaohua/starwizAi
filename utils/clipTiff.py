import os

import matplotlib.pyplot as plt
from osgeo import gdal, ogr, osr

os.environ["PROJ_LIB"] = r"C:\Python312\Lib\site-packages\pyproj\proj_dir\share\proj"


def correct_tiff_with_extent_and_srs(src_ds, width, height, bbox, srs_epsg=4326):

    # Set the spatial reference system
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(srs_epsg)
    src_ds.SetProjection(srs.ExportToWkt())

    # Calculate geotransform
    minX, minY, maxX, maxY = bbox
    pixel_width = (maxX - minX) / width
    pixel_height = (maxY - minY) / height
    geotransform = (minX, pixel_width, 0, maxY, 0, -pixel_height)
    src_ds.SetGeoTransform(geotransform)

    return src_ds


def clip_tiff_by_trans(input_tiff, output_tiff, bbox, input_bbox):
    """
    Clip a raster by a bounding box and save it as a new TIFF file.

    :param input_tiff: Path to the input TIFF file.
    :param output_tiff: Path to the output TIFF file.
    :param bbox: Bounding box as a tuple (minX, minY, maxX, maxY).
    """
    # 打开输入 TIFF 文件
    src_ds = gdal.Open(input_tiff)
    if src_ds is None:
        raise FileNotFoundError(f"Cannot open input TIFF file: {input_tiff}")

    # 获取地理变换参数和投影信息
    width = src_ds.RasterXSize  # 获取数据宽度
    height = src_ds.RasterYSize  # 获取数据高度
    outbandsize = src_ds.RasterCount  # 获取数据波段数

    projection = src_ds.GetProjection()  # 获取投影信息

    if outbandsize < 1:
        raise ValueError("Input TIFF file raster count is less 1")

    # 本来数据正常是可以不要的
    if not projection:
        if input_bbox and len(input_bbox):
            correct_tiff_with_extent_and_srs(src_ds, width, height, input_bbox, 4326)
        else:
            raise ValueError("Input TIFF not have projection and no input bbox")

    # Get the georeference info
    transform = src_ds.GetGeoTransform()  # 获取仿射矩阵信息
    if transform is None:
        raise ValueError("Input TIFF file is not georeferenced.")

    projection = src_ds.GetProjection()

    # 计算像素坐标范围
    min_x, min_y, max_x, max_y = bbox
    x_origin = transform[0]
    y_origin = transform[3]
    pixel_width = transform[1]
    pixel_height = transform[5]

    # 计算像素范围
    x_offset = int((min_x - x_origin) / pixel_width)
    y_offset = int((max_y - y_origin) / pixel_height)
    x_size = int((max_x - min_x) / pixel_width)
    y_size = int((max_y - min_y) / abs(pixel_height))

    # 进行裁剪
    gdal.Translate(output_tiff, src_ds, srcWin=[x_offset, y_offset, x_size, y_size], format="GTiff")

    # 关闭数据集
    src_ds = None
    print(f"裁剪完成，输出文件保存至: {output_tiff}")
    return True


def clip_tiff_by_band(input_tiff, output_tiff, bbox, input_bbox):
    """
    Clip a raster by a bounding box and save it as a new TIFF file.

    :param input_tiff: Path to the input TIFF file.
    :param output_tiff: Path to the output TIFF file.
    :param bbox: Bounding box as a tuple (minX, minY, maxX, maxY).
    """
    # Open the input TIFF file
    src_ds = gdal.Open(input_tiff)
    if src_ds is None:
        raise FileNotFoundError(f"Cannot open input TIFF file: {input_tiff}")

    width = src_ds.RasterXSize  # 获取数据宽度
    height = src_ds.RasterYSize  # 获取数据高度
    outbandsize = src_ds.RasterCount  # 获取数据波段数
    datatype = src_ds.GetRasterBand(1).DataType

    projection = src_ds.GetProjection()  # 获取投影信息

    if outbandsize < 1:
        raise ValueError("Input TIFF file raster count is less 1")

    if not projection:
        if input_bbox and len(input_bbox):
            correct_tiff_with_extent_and_srs(src_ds, width, height, input_bbox, 4326)
        else:
            raise ValueError("Input TIFF not have projection and no input bbox")

    # Get the georeference info
    transform = src_ds.GetGeoTransform()
    if transform is None:
        raise ValueError("Input TIFF file is not georeferenced.")

    min_x, min_y, max_x, max_y = bbox
    x_origin = transform[0]
    y_origin = transform[3]
    pixel_width = transform[1]
    pixel_height = transform[5]

    # Calculate the offset and size of the subset
    # todo
    # 这里还有问题的，当画的边界超出了要注意处理。
    x_offset = int((min_x - x_origin) / pixel_width)
    y_offset = int((max_y - y_origin) / pixel_height)
    x_size = int((max_x - min_x) / pixel_width)
    y_size = int((max_y - min_y) / abs(pixel_height))

    print("infos1", min_x, min_y, max_x, max_y, "\r\n")
    print("infos2", x_origin, y_origin, pixel_width, pixel_height, "\r\n")
    print("infos3", x_offset, y_offset, x_size, y_size, "\r\n")

    # Create the output TIFF file
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(output_tiff, x_size, y_size, outbandsize, datatype)
    if out_ds is None:
        raise RuntimeError(f"Cannot create output TIFF file: {output_tiff}")

    # Write the subset to the output file
    for i in range(1, outbandsize + 1):
        in_band = src_ds.GetRasterBand(i)
        subset = in_band.ReadAsArray(x_offset, y_offset, x_size, y_size)
        out_band = out_ds.GetRasterBand(i)
        out_band.WriteArray(subset)

    # Flush the cache and close the datasets
    out_ds.FlushCache()

    # Set the georeference info to the output file
    new_transform = (
        transform[0] + x_offset * pixel_width,
        pixel_width,
        transform[2],
        transform[3] + y_offset * pixel_height,
        transform[4],
        pixel_height,
    )
    out_ds.SetGeoTransform(new_transform)
    if not projection:
        # Set the spatial reference system
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        out_ds.SetProjection(srs.ExportToWkt())
    else:
        out_ds.SetProjection(src_ds.GetProjection())

    out_ds = None
    src_ds = None

    print(f"Clipping completed. Output saved to {output_tiff}")
    return True


def clip_tiff_by_wrap(input_tiff, output_tiff, bbox):
    """
    Clip a raster by a bounding box and save it as a new TIFF file using gdal.Warp.

    :param input_tiff: Path to the input TIFF file.
    :param output_tiff: Path to the output TIFF file.
    :param bbox: Bounding box as a tuple (minX, minY, maxX, maxY).
    """
    # gdalwarp -t_srs EPSG:4326 -te 114.14943 22.30447 114.15556 22.31311 -of JPEG 油尖旺区_卫图_20181004_Level_19.tif out.png
    try:
        dirName, filename = os.path.split(output_tiff)
        if not os.path.exists(dirName):
            os.makedirs(dirName, 777)

        # Define the bounding box
        minX, minY, maxX, maxY = bbox

        # Use gdal.Warp to clip the raster
        warp_options = gdal.WarpOptions(outputBounds=(minX, minY, maxX, maxY), format="GTiff", dstSRS="EPSG:4326")
        result = gdal.Warp(output_tiff, input_tiff, options=warp_options)

        # Check if the result is None
        if result is None:
            raise RuntimeError(f"Failed to clip the raster using the provided bounding box: {bbox}")

        # Close the dataset
        result = None
        print(f"Clipping completed. Output saved to {output_tiff}")
        return True
    except Exception as e:
        print(e)
        return False


def clip_tiff_to_img_by_wrap(input_tiff, output_img, bbox):
    """
    Clip a raster by a bounding box and save it as a new TIFF file using gdal.Warp.

    :param input_tiff: Path to the input TIFF file.
    :param output_img: Path to the output Image file.
    :param bbox: Bounding box as a tuple (minX, minY, maxX, maxY).
    """
    # gdalwarp -t_srs EPSG:4326 -te 114.14943 22.30447 114.15556 22.31311 -of JPEG 油尖旺区_卫图_20181004_Level_19.tif out.png
    try:
        dirName, filename = os.path.split(output_img)
        if not os.path.exists(dirName):
            os.makedirs(dirName, 777)

        # Define the bounding box
        minX, minY, maxX, maxY = bbox

        # Use gdal.Warp to clip the raster
        warp_options = gdal.WarpOptions(outputBounds=(minX, minY, maxX, maxY), format="MEM", dstSRS="EPSG:4326")
        result = gdal.Warp(output_img, input_tiff, options=warp_options)

        # Check if the result is None
        if result is None:
            raise RuntimeError(f"Failed to clip the raster using the provided bounding box: {bbox}")

        driver = gdal.GetDriverByName("JPEG")
        driver.CreateCopy(output_img, result)

        # Close the dataset
        result = None
        print(f"Clipping completed. Output saved to {output_img}")
        return True
    except Exception as e:
        print(e)
        return False


def clip_tiff_to_png_by_wrap(input_tiff, output_img, bbox):
    """
    Clip a raster by a bounding box and save it as a new TIFF file using gdal.Warp.

    :param input_tiff: Path to the input TIFF file.
    :param output_img: Path to the output Image file.
    :param bbox: Bounding box as a tuple (minX, minY, maxX, maxY).
    """
    # gdalwarp -t_srs EPSG:4326 -te 114.14943 22.30447 114.15556 22.31311 -of JPEG 油尖旺区_卫图_20181004_Level_19.tif out.png
    try:
        dirName, filename = os.path.split(output_img)
        if not os.path.exists(dirName):
            os.makedirs(dirName, 777)

        # Define the bounding box
        minX, minY, maxX, maxY = bbox

        # Use gdal.Warp to clip the raster
        warp_options = gdal.WarpOptions(outputBounds=(minX, minY, maxX, maxY), format="PNG", dstSRS="EPSG:4326")
        result = gdal.Warp(output_img, input_tiff, options=warp_options)

        # Check if the result is None
        if result is None:
            raise RuntimeError(f"Failed to clip the raster using the provided bounding box: {bbox}")

        # 获取波段数
        raster_count = result.RasterCount
        if raster_count == 1:
            band = result.GetRasterBand(1)
            band_array = band.ReadAsArray()
            plt.imsave(output_img, band_array, cmap=plt.cm.gray)
        # Close the dataset
        result = None
        print(f"Clipping completed. Output saved to {output_img}")
        return True
    except Exception as e:
        print(e)
        return False
