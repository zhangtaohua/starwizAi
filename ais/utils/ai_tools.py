import os
import warnings
from datetime import datetime
from typing import AnyStr

from django.conf import settings

from ais.models import AiProjectResultStatus, Download, DownloadStatus
from utils.clipTiff import clip_tiff_by_band, clip_tiff_by_trans, clip_tiff_by_wrap, clip_tiff_to_img_by_wrap
from utils.download import download_file, verify_file
from utils.fileCommon import create_directory
from utils.geoCommon import get_bbox_from_geojson

warnings.filterwarnings("ignore")


def check_and_download_file(file_url: AnyStr, save_file_path_name: AnyStr = ""):
    # 有可能要执行下面语句才可以拿到 settings 中变量
    # django.setup()

    # 1 获取数据库 下载表，如果已下载且完整直接返回
    print("Info: check file url", file_url)
    file_path = settings.DOWNLOAD_TIFF_PATH
    # 要处理的 tiff 原始文件名。
    file_name = file_url.strip("/").rsplit("/", 1)[-1]
    save_path_name = os.path.join(file_path, file_name)
    if save_file_path_name != "":
        save_path_name = save_file_path_name

    try:
        file_obj = Download.objects.using("postgres").get(name=file_name)
        # 文件已下载直接返回
        if file_obj.status == DownloadStatus.DOWNLOAD_SUCCESS.value:
            return file_obj.asset_path

    except Download.DoesNotExist:
        print(f"Info: {file_name} did not downloaded!")
        print("Info: start download……")

    # 文件不存在 开始下载
    try_downloads_count = int(settings.MAX_TRY_DOWNLOADS_TIMES)
    downloaded_file = None
    for _ in range(try_downloads_count):
        downloaded_file = download_file(file_url, save_path_name)
        if downloaded_file:
            break
        else:
            downloaded_file = None

    if downloaded_file:
        downlaod_obj = Download.objects.using("postgres").create(
            name=file_name,
            asset_path=save_path_name,
            md5="",
            status=DownloadStatus.DOWNLOAD_SUCCESS.value,
            # created_at=datetime.utcnow(),
            # updated_at=datetime.utcnow(),
        )
        downlaod_obj.save(using="postgres")
        return save_path_name
    else:
        return None


def ai_process_common_preparation(input_params, **kwds):
    # 1 参数准备处理
    meta_data = input_params.get("meta")
    result_uuid = meta_data.get("uuid")
    user_id = meta_data.get("user_id")
    ai_model_code = meta_data.get("ai_model_code")
    area = input_params.get("area")

    # 用于生成随时间的AI分析结果存储目录。
    now = datetime.now()
    time_dir = now.strftime("%Y-%m-%d")

    origin_data = input_params.get("data")
    if origin_data:
        origin_data = origin_data.get("data")

    # 要下载处理的 tiff 目标的 远程Url地址。
    target_origin_tiff_url = None
    # 要下载处理的 tiff 目标的 原始bbox。
    target_origin_bbox = None
    if origin_data:
        target_origin_tiff_url = origin_data.get("assets")
        target_origin_tiff_url = target_origin_tiff_url.get("tiff").get("href")
        target_origin_bbox = origin_data.get("bbox")

    # AI 输出结果目录
    output_result_dir = os.path.join(settings.AI_RESULTS_PATH, user_id, time_dir, str(result_uuid))
    # AI 输出结果返回给前端的目录
    output_result_url = os.path.join(settings.AI_RESULTS_URL, user_id, time_dir, str(result_uuid))

    # 下载的tiff 文件路径和名称
    target_download_tiff_url = ""
    target_download_tiff = ""

    # 进入AI 处理过程得到的 中间结果 tiff 和 jpg 等
    # 比如 当为area 处理时，需要进行裁剪的tiff url
    target_md_tiff_url = ""
    target_md_tiff = ""

    target_md_jpg_url = ""
    target_md_jpg = ""

    target_md_png_url = ""
    target_md_png = ""

    target_md_bbox = None

    # 2 确认输入文件是否存在，不存在则下载
    if target_origin_tiff_url:
        target_download_tiff = check_and_download_file(target_origin_tiff_url)
        base_dir = str(settings.BASE_DIR)
        target_download_tiff_url = target_download_tiff.rsplit(base_dir, 1)[-1]

    print("target_download_tiff_url", target_download_tiff, target_download_tiff_url)
    # 3 处理模型需要参数
    # 如果文件下载成功，就继续处理
    if target_download_tiff:

        if area == "area":  # 处理部分范围
            extent = input_params.get("extent")
            if extent:
                target_md_bbox = get_bbox_from_geojson(extent)
                print("target_md_bbox: ", target_md_bbox)

                hand_tiff_name = "handle.tif"
                hand_jpg_name = "handle.jpg"
                hand_png_name = "handle.png"

                target_md_tiff_url = os.path.join(output_result_url, hand_tiff_name)
                target_md_tiff = os.path.join(output_result_dir, hand_tiff_name)

                target_md_jpg_url = os.path.join(output_result_url, hand_jpg_name)
                target_md_jpg = os.path.join(output_result_dir, hand_jpg_name)

                target_md_png_url = os.path.join(output_result_url, hand_png_name)
                target_md_png = os.path.join(output_result_dir, hand_png_name)

                # 创建存储目录
                create_directory(target_md_tiff)

                is_need_tiff = kwds.get("is_need_tiff")
                if is_need_tiff:
                    # 裁剪tiff
                    clip_tiff_by_trans(target_download_tiff, target_md_tiff, target_md_bbox, target_origin_bbox)
                    # clip_tiff_by_band(target_download_tiff, target_md_tiff, target_md_bbox, target_origin_bbox)

                # 剪裁成 jpg
                is_need_jpg = kwds.get("is_need_jpg")
                if is_need_jpg:
                    clip_tiff_to_img_by_wrap(target_download_tiff, target_md_jpg, target_md_bbox)

                # 剪裁成 jpg
                is_need_png = kwds.get("is_need_png")
                if is_need_png:
                    clip_tiff_to_img_by_wrap(target_download_tiff, target_md_png, target_md_bbox)
            else:
                print("Error: Extent not found when processing")

                return {
                    "error": True,
                    "status": AiProjectResultStatus.FILE_PROCESS_FAILED.value,
                    "result_uuid": result_uuid,
                }

        elif area == "whole":
            print("whole process second stage")
    else:
        # 文件下载失败有问题 记录日志
        print("Error: File is not exist, AI cannot goon handling")
        target_md_tiff = ""
        target_md_bbox = None

        return {
            "error": True,
            "status": AiProjectResultStatus.FILE_DOWNLOAD_FAILED.value,
            "result_uuid": result_uuid,
        }

    return {
        "error": False,
        "status": "",
        "result_uuid": result_uuid,
        "user_id": user_id,
        "ai_model_code": ai_model_code,
        "area": area,
        "target_origin_tiff_url": target_origin_tiff_url,
        "target_download_tiff_url": target_download_tiff_url,
        "target_download_tiff": target_download_tiff,
        "target_md_tiff_url": target_md_tiff_url,
        "target_md_tiff": target_md_tiff,
        "target_md_bbox": target_md_bbox,
        "target_md_jpg_url": target_md_jpg_url,
        "target_md_jpg": target_md_jpg,
        "target_md_png_url": target_md_png_url,
        "target_md_png": target_md_png,
        "output_result_url": output_result_url,
        "output_result_dir": output_result_dir,
    }
