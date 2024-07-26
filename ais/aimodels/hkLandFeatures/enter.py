import os
import pickle
import sys
import warnings

import cv2
import numpy as np
from django.conf import settings
from django_q.tasks import Task, async_task, result
from osgeo import gdal

from ais.models import AiProjectResultStatus
from ais.models_utils import updata_ai_project_result_results, updata_ai_project_result_status
from ais.utils.ai_tools import ai_process_common_preparation

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

            output_png_file_name = "result.jpg"
            output_png_url = os.path.join(output_result_url, output_png_file_name)
            output_result_file_name = os.path.join(output_result_dir, output_png_file_name)

            ai_result = False
            try:
                ai_result = get_predict(model_path, target_md_tiff, output_result_file_name)
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
    print("HK Random Forest Classifier start processing\r\n")
    # 2 开启异步任务处理
    async_task(task_start, input_params, q_options={"task_name": input_params.get("uuid"), "hook": task_finish})

    # 3 返回相应处理状态
    return None
