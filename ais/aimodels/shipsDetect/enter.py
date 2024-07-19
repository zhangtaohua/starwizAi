import os
import pickle
import sys
import traceback
import warnings
from datetime import datetime
from pathlib import Path
from typing import AnyStr, Optional

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from django.conf import settings
from django_q.tasks import Task, async_task, result
from osgeo import gdal
from ultralytics import YOLO
from yolov5.detect import run

from ais.models import AiProjectResultStatus
from ais.models_utils import updata_ai_project_result_results, updata_ai_project_result_status
from ais.utils.ai_tools import check_and_download_file
from utils.clipTiff import clip_tiff_by_band, clip_tiff_by_trans, clip_tiff_by_wrap, clip_tiff_to_img_by_wrap
from utils.fileCommon import create_directory
from utils.geoCommon import get_bbox_from_geojson

warnings.filterwarnings("ignore")

# model_path = "/app/ais/aimodels/hkLandFeatures/XR07.pickle"
current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
ship_model_path = os.path.join(current_directory, "weights/ships.pt")
airplane_model_path = os.path.join(current_directory, "weights/airplane.pt")

ship_test_input_tiff = os.path.join(current_directory, "tiff/ship.jpg")
airplane_test_input_tiff = os.path.join(current_directory, "tiff/airplane.jpg")


def get_single_gray_img(filepath, outpath):
    dataset = gdal.Open(filepath)
    if dataset is None:
        print("Error: Unable to open the input TIFF file.")
        sys.exit(1)
    raster_count = dataset.RasterCount
    if raster_count > 0:
        band = dataset.GetRasterBand(1)
        band_array = band.ReadAsArray()
        plt.imsave(outpath, band_array, cmap=plt.cm.gray)
        return True
    else:
        return False


def get_predict(defined_model, input_png, output_dir, ai_model_code="ShipsDetect"):
    try:
        # print("加载船只模型", defined_model)
        # model = YOLO(defined_model)
        # print("船只模型", model)
        # results = model(input_png)
        # print("get_predict", results)
        target_device = "cpu"
        if torch.cuda.is_available():
            target_device = "gpu"

        print("使用 device", target_device)
        input_souce = ship_test_input_tiff
        defined_model = ship_model_path

        if ai_model_code == "AirplanesDetect":
            input_souce = airplane_test_input_tiff
            defined_model = airplane_model_path

        run(
            weights=defined_model,
            save_txt=True,
            save_crop=True,
            save_conf=True,
            source=input_souce,
            device=target_device,
            hide_labels=True,
            project=output_dir,
            name="detectResults",
        )
        return True
    except FileNotFoundError as e:
        print(f"Error: File not found.{e}")
        return False
    except Exception as e:
        # print(e.with_traceback(traceback.extract_stack()))
        print(e.with_traceback(None))
        return False


def task_finish(task: Task):
    print("任务完成", task)
    task_result = result(task.id)
    print("任务结果：", task_result)
    # todo 要不要通知 golang 程序处理完成呢？


def task_start(input_params):
    print("任务开始处理：", input_params, type(input_params), "\r\n")
    # 1 参数准备处理
    meta_data = input_params.get("meta")
    result_uuid = meta_data.get("uuid")
    user_id = meta_data.get("user_id")
    ai_model_code = meta_data.get("ai_model_code")
    area = input_params.get("area")

    # 用于生成随时间的AI分析结果存储目录。
    now = datetime.now()
    time_dir = now.strftime("%Y-%m-%d")

    # 更新 数据库 AI 处理结果进度
    updata_ai_project_result_status(result_uuid, AiProjectResultStatus.IDLE.value, 1)

    origin_data = input_params.get("data")
    if origin_data:
        origin_data = origin_data.get("data")

    # 要下载处理的 tiff 目标的 远程Url地址。
    target_tiff_url = None
    # 要下载处理的 tiff 目标的 原始bbox。
    target_origin_bbox = None
    if origin_data:
        target_tiff_url = origin_data.get("assets")
        target_tiff_url = target_tiff_url.get("tiff").get("href")
        target_origin_bbox = origin_data.get("bbox")

    # 下载的tiff 文件路径和名称
    target_dw_inputfile_path_name = ""

    # 进入AI 处理过程得到的 中间结果 tiff 和 jpg 等
    output_tiff = ""
    output_jpg = ""
    output_bbox = None
    # AI 输出结果目录
    output_result_dir = os.path.join(settings.AI_RESULTS_PATH, user_id, time_dir, str(result_uuid))
    # AI 输出结果返回给前端的目录
    output_result_url = os.path.join(settings.AI_RESULTS_URL, user_id, time_dir, str(result_uuid))

    # 当为area 处理时，裁剪的tiff url
    output_process_tiff_url = ""
    output_png_url = ""

    # 2 确认输入文件是否存在，不存在则下载
    if target_tiff_url:
        target_dw_inputfile_path_name = check_and_download_file(target_tiff_url)

    # 3 处理模型需要参数
    # 如果文件下载成功，就继续处理
    if target_dw_inputfile_path_name:
        updata_ai_project_result_status(result_uuid, AiProjectResultStatus.FILE_DOWNLOAD_SUCCESS.value, 10)

        if area == "area":  # 处理部分范围
            extent = input_params.get("extent")
            if extent:
                output_bbox = get_bbox_from_geojson(extent)
                print("output_bbox: ", output_bbox)

                hand_tiff_name = "handle.tif"

                output_process_tiff_url = os.path.join(output_result_url, hand_tiff_name)
                output_tiff = os.path.join(output_result_dir, hand_tiff_name)
                output_jpg = os.path.join(output_result_dir, "handle.jpg")

                # 创建存储目录
                create_directory(output_tiff)
                # 裁剪tiff
                clip_tiff_by_trans(target_dw_inputfile_path_name, output_tiff, output_bbox, target_origin_bbox)
                # clip_tiff_by_band(target_dw_inputfile_path_name, output_tiff, output_bbox, target_origin_bbox)

                # 剪裁成 png jpg
                clip_tiff_to_img_by_wrap(target_dw_inputfile_path_name, output_jpg, output_bbox)
            else:
                print("Error: Extent not found when processing")
                updata_ai_project_result_status(
                    result_uuid,
                    AiProjectResultStatus.FILE_PROCESS_FAILED.value,
                    100,
                    "Extent not found when processing",
                )
        elif area == "whole":
            print("whole process second stage")
    else:
        # 文件下载失败有问题 记录日志
        print("Error: File is not exist, AI cannot goon handling")
        output_tiff = ""
        output_bbox = None
        updata_ai_project_result_status(
            result_uuid, AiProjectResultStatus.FILE_DOWNLOAD_FAILED.value, 100, "Download file failed!"
        )
        return None

    # 4 开启新的进程进行后台处理
    try_ai_count = int(settings.MAX_TRY_AI_PROCESS_TIMES)
    for _ in range(try_ai_count):
        if area == "area" and output_tiff:
            # 更新处理进度
            updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESSING.value, 20)
            output_png_file_name = "detectResults/ship.jpg"
            if ai_model_code == "AirplanesDetect":
                output_png_file_name = "detectResults/airplane.jpg"

            output_png_url = os.path.join(output_result_url, output_png_file_name)

            output_result_file_name = os.path.join(output_result_dir, output_png_file_name)
            output_single_gray_name = os.path.join(output_result_dir, "single_gray.png")
            ai_result = False
            try:
                is_single = get_single_gray_img(output_tiff, output_single_gray_name)
                if is_single:
                    ai_result = get_predict(ship_model_path, output_jpg, output_result_dir, ai_model_code)
                    if ai_result:
                        save_res = {
                            "base_dir_url": settings.PRODUCT_ASSETS_BASE_DIR,
                            "input_origin_tiff": target_dw_inputfile_path_name,
                            "input_process_tiff": output_process_tiff_url,
                            "output_png": output_png_url,
                            "area": area,
                            "output_bbox": output_bbox,
                        }
                        updata_ai_project_result_results(
                            result_uuid, AiProjectResultStatus.AI_PROCESS_DONE.value, 100, save_res
                        )
                    else:
                        updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)
                else:
                    updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)
            except Exception as e:
                print("AI 任务失败", e)
                ai_result = False
                updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)

            if ai_result:
                break

        elif area == "whole":
            print("whole process third stage")
            break
            # 4 处理结果 并 返回
            # updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_DONE.value, 100)
    return {"extent": "", "result": ""}


def StartProcess(input_params):
    # 1 较验项目参数是否正确
    print("船只识别任务开始处理：\r\n")
    # 2 开启异步任务处理
    async_task(task_start, input_params, q_options={"task_name": input_params.get("uuid"), "hook": task_finish})

    # 3 返回相应处理状态
    return None
