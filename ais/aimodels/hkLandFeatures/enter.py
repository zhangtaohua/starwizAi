import os
import pickle
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import AnyStr, Optional

import cv2
import numpy as np
from django.conf import settings
from django_q.tasks import Task, async_task, result
from osgeo import gdal

from ais.models import AiProjectResultStatus, Download, DownloadStatus
from ais.models_utils import updata_ai_project_result_results, updata_ai_project_result_status
from utils.clipTiff import clip_tiff_by_band, clip_tiff_by_trans, clip_tiff_by_wrap
from utils.download import download_file, verify_file
from utils.fileCommon import create_directory
from utils.geoCommon import get_bbox_from_geojson

warnings.filterwarnings("ignore")

# model_path = "/app/ais/aimodels/hkLandFeatures/XR07.pickle"
current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
model_path = os.path.join(current_directory, "XR07.pickle")


def read_tif(filepath):
    dataset = gdal.Open(filepath)
    if dataset is None:
        print("Error: Unable to open the input TIFF file.")
        sys.exit(1)
    im_data = dataset.ReadAsArray(0, 0, dataset.RasterXSize, dataset.RasterYSize)
    return im_data


def get_predict(defined_model, input_tif, output_png):
    try:
        # 读取tif数据基本信息
        # print("开始 get_predict 目录", defined_model, input_tif, output_png)
        im_data = read_tif(input_tif)
        # 打开训练文件
        file = open(defined_model, "rb")
        rf_model = pickle.load(file)
        file.close()
        print("图片信息", im_data, rf_model)

        data = np.zeros((im_data.shape[0], im_data.shape[1] * im_data.shape[2]))
        for i in range(im_data.shape[0]):
            data[i] = im_data[i].flatten()
        data = data.swapaxes(0, 1)

        # 进行分类预测
        pred = rf_model.predict(data)
        pred = pred.reshape(im_data.shape[1], im_data.shape[2]) * 255
        pred = pred.astype(np.uint8)

        # 对图像进行滤波去噪点和颜色赋值
        kernel = np.ones((2, 2), np.uint8)
        temp = cv2.medianBlur(pred, 9)  # 中值滤波
        original_color = np.array([255, 255, 255])  # 原始颜色为白色
        replacement_color = np.array([0, 200, 100])
        image_rgb = cv2.cvtColor(temp, cv2.COLOR_GRAY2RGB)
        mask = np.all(image_rgb == original_color, axis=-1)
        image_rgb[mask] = replacement_color
        image_rgb[~mask] = [255, 255, 255]
        cv2.imwrite(output_png, image_rgb)
        return True
    except FileNotFoundError as e:
        print(e.with_traceback())
        print(f"Error: File not found.{e}")
        return False
    except Exception as e:
        print(e.with_traceback())
        return False


def check_and_download_file(file_url: AnyStr):
    # 有可能要执行下面语句才可以拿到 settings 中变量
    #  django.setup()

    # 1 获取数据库 下载表，如果已下载且完整直接返回
    print("检查文件", file_url)
    file_path = settings.DOWNLOAD_TIFF_PATH
    file_name = file_url.strip("/").rsplit("/", 1)[-1]
    whole_file_name = os.path.join(file_path, file_name)

    try:
        file_obj = Download.objects.using("postgres").get(name=file_name)
        # 文件已下载直接返回
        if file_obj.status == DownloadStatus.DOWNLOAD_SUCCESS.value:
            return file_obj.asset_path

    except Download.DoesNotExist:
        print(f"{file_name} 文件未下载")

    # 文件不存在 开始下载
    try_downloads_count = int(settings.MAX_TRY_DOWNLOADS_TIMES)
    all_down_file = None
    for _ in range(try_downloads_count):
        all_down_file = download_file(file_url, whole_file_name)
        if all_down_file:
            break

    if all_down_file:
        downlaod_obj = Download.objects.using("postgres").create(
            name=file_name,
            asset_path=whole_file_name,
            md5="",
            status=DownloadStatus.DOWNLOAD_SUCCESS.value,
            # created_at=datetime.utcnow(),
            # updated_at=datetime.utcnow(),
        )
        downlaod_obj.save(using="postgres")
        return whole_file_name
    else:
        return None


def task_finish(task: Task):
    print("任务完成", task)
    task_result = result(task.id)
    print("task_result", task_result)
    # todo 要不要通知 golang 程序处理完成呢？


def task_start(input_params):
    print("任务开始处理：", input_params, type(input_params), "\r\n")
    # 1 确认输入文件是否存在，不存在则下载
    meta_data = input_params.get("meta")
    result_uuid = meta_data.get("uuid")
    user_id = meta_data.get("user_id")

    updata_ai_project_result_status(result_uuid, AiProjectResultStatus.IDLE.value, 1)

    origin_data = input_params.get("data")
    if origin_data:
        origin_data = origin_data.get("data")

    tiff_url = None
    origin_bbox = None
    if origin_data:
        tiff_url = origin_data.get("assets")
        tiff_url = tiff_url.get("tiff").get("href")
        origin_bbox = origin_data.get("bbox")

    input_file_name = ""
    output_tiff = ""
    output_bbox = None
    area = ""
    output_result_dir = ""
    tiff_file_name = tiff_url.strip("/").rsplit("/", 1)[-1]
    input_origin_tiff_url = os.path.join(settings.DOWNLOAD_TIFF_URL, tiff_file_name)
    input_process_tiff_url = ""
    output_png_url = ""

    if tiff_url:
        input_file_name = check_and_download_file(tiff_url)

    # 2 处理模型需要参数
    if input_file_name:
        updata_ai_project_result_status(result_uuid, AiProjectResultStatus.FILE_DOWNLOAD_SUCCESS.value, 10)

        area = input_params.get("area")
        if area == "area":  # 处理部分范围
            extent = input_params.get("extent")
            if extent:
                output_bbox = get_bbox_from_geojson(extent)
                print("bbox: ", output_bbox)
                now = datetime.now()
                time_dir = now.strftime("%Y-%m-%d")
                output_result_dir = os.path.join(settings.AI_RESULTS_PATH, user_id, time_dir, str(result_uuid))
                hand_tiff_name = "handle.tif"
                input_process_tiff_url = os.path.join(
                    settings.AI_RESULTS_URL, user_id, time_dir, str(result_uuid), hand_tiff_name
                )
                output_tiff = os.path.join(
                    settings.AI_RESULTS_PATH, user_id, time_dir, str(result_uuid), hand_tiff_name
                )
                create_directory(output_tiff)
                clip_tiff_by_trans(input_file_name, output_tiff, output_bbox, origin_bbox)
                # clip_tiff_by_band(input_file_name, output_tiff, output_bbox, origin_bbox)
    else:
        # 有问题 记录日志 文件无法下载等
        print("File is not exist, AI cannot handle")
        output_tiff = ""
        output_bbox = None
        updata_ai_project_result_status(
            result_uuid, AiProjectResultStatus.FILE_DOWNLOAD_FAILED.value, 100, "文件下载失败"
        )
        return None

    # 3 开启新的进程进行后台处理
    try_ai_count = int(settings.MAX_TRY_AI_PROCESS_TIMES)
    for _ in range(try_ai_count):
        if area == "area" and output_tiff:
            updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESSING.value, 20)
            output_png_file_name = "result.png"
            output_png_url = os.path.join(
                settings.AI_RESULTS_URL, user_id, time_dir, str(result_uuid), output_png_file_name
            )

            output_result_file_name = os.path.join(output_result_dir, output_png_file_name)
            ai_result = False
            try:
                ai_result = get_predict(model_path, output_tiff, output_result_file_name)
                if ai_result:
                    save_res = {
                        "base_dir_url": settings.PRODUCT_ASSETS_BASE_DIR,
                        "input_origin_tiff": input_origin_tiff_url,
                        "input_process_tiff": input_process_tiff_url,
                        "output_png": output_png_url,
                        "area": area,
                        "output_bbox": output_bbox,
                    }
                    updata_ai_project_result_results(
                        result_uuid, AiProjectResultStatus.AI_PROCESS_DONE.value, 100, save_res
                    )
                else:
                    updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)
            except Exception as e:
                print("AI 任务失败", e)
                ai_result = False
                updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)

            if ai_result:
                break

        elif area == "whole":
            print("whole 处理")
            break
            # 4 处理结果 并 返回
            # updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_DONE.value, 100)
    return {"extent": "", "result": ""}


def StartProcess(input_params):
    # 1 较验项目参数是否正确
    print("任务开始处理：", input_params, type(input_params), "\r\n")
    # 2 开启异步任务处理
    async_task(task_start, input_params, q_options={"task_name": input_params.get("uuid"), "hook": task_finish})

    # 3 返回相应处理状态
    return None
