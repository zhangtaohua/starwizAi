import os
import sys
import traceback
import warnings

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
from ais.utils.ai_tools import ai_process_common_preparation

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
            # target_device = "gpu"
            # target_device = "cuda"
            # count = torch.cuda.device_count()
            target_device = 0

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
        torch.cuda.empty_cache()
        return True
    except FileNotFoundError as e:
        torch.cuda.empty_cache()
        print(f"Error: File not found.{e}")
        return False
    except Exception as e:
        # print(e.with_traceback(traceback.extract_stack()))
        print(e.with_traceback(None))
        torch.cuda.empty_cache()
        return False


def task_finish(task: Task):
    task_result = result(task.id)
    print("Q2 Task finished", task.id, task)
    print("Q2 Task Result:", task_result)
    # todo 要不要通知 golang 程序处理完成呢？


def task_start(input_params):
    print("Q2 Task Start:", input_params, type(input_params), "\r\n")

    # 1 参数准备处理
    meta_data = input_params.get("meta")
    result_uuid = meta_data.get("uuid")

    # 更新 数据库 AI 处理结果进度
    updata_ai_project_result_status(result_uuid, AiProjectResultStatus.IDLE.value, 1)

    md = ai_process_common_preparation(input_params)
    if md.get("error"):
        md_status = md.get("status")
        if md_status == AiProjectResultStatus.FILE_DOWNLOAD_FAILED.value:
            updata_ai_project_result_status(
                result_uuid, AiProjectResultStatus.FILE_DOWNLOAD_FAILED.value, 100, "Download file failed!"
            )
        elif md_status == AiProjectResultStatus.FILE_PROCESS_FAILED.value:
            updata_ai_project_result_status(
                result_uuid,
                AiProjectResultStatus.FILE_PROCESS_FAILED.value,
                100,
                "Extent not found when processing",
            )

        # 数据
        return {"error": True}

    updata_ai_project_result_status(result_uuid, AiProjectResultStatus.FILE_DOWNLOAD_SUCCESS.value, 10)

    # 真正进行 AI 处理

    area = md.get("area")
    ai_model_code = md.get("ai_model_code")
    target_download_tiff_url = md.get("target_download_tiff_url")

    target_md_tiff_url = md.get("target_md_tiff_url")
    target_md_tiff = md.get("target_md_tiff")

    target_md_bbox = md.get("target_md_bbox")

    output_result_url = md.get("output_result_url")
    output_result_dir = md.get("output_result_dir")

    # 4 开启新的进程进行后台处理
    try_ai_count = int(settings.MAX_TRY_AI_PROCESS_TIMES)
    for _ in range(try_ai_count):
        if area == "area" and target_md_tiff:
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
                is_single = get_single_gray_img(target_md_tiff, output_single_gray_name)
                if is_single:
                    ai_result = get_predict(ship_model_path, output_single_gray_name, output_result_dir, ai_model_code)
                    if ai_result:
                        save_res = {
                            "base_dir_url": settings.PRODUCT_ASSETS_BASE_DIR,
                            "input_origin_tiff": target_download_tiff_url,
                            "input_process_tiff": target_md_tiff_url,
                            "output_png": output_png_url,
                            "area": area,
                            "output_bbox": target_md_bbox,
                        }
                        updata_ai_project_result_results(
                            result_uuid, AiProjectResultStatus.AI_PROCESS_DONE.value, 100, save_res
                        )
                    else:
                        updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)
                else:
                    updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)
            except Exception as e:
                print("AI Task Failed", e)
                ai_result = False
                updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_FAILED.value, 100)

            if ai_result:
                break

        elif area == "whole":
            print("whole process third stage")
            break
            # 4 处理结果 并 返回
            # updata_ai_project_result_status(result_uuid, AiProjectResultStatus.AI_PROCESS_DONE.value, 100)
    return {"error": False, "extent": "", "result": ""}


def StartProcess(input_params):
    # 1 较验项目参数是否正确
    print("Object Detection start processing\r\n")
    # 2 开启异步任务处理
    async_task(task_start, input_params, q_options={"task_name": input_params.get("uuid"), "hook": task_finish})

    # 3 返回相应处理状态
    return None
