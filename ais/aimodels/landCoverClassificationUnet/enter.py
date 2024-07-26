import os
import warnings

import numpy as np
import torch
import torch.nn.functional as F
from django.conf import settings
from django_q.tasks import Task, async_task, result
from PIL import Image
from torchvision import transforms

from ais.models import AiProjectResultStatus
from ais.models_utils import updata_ai_project_result_results, updata_ai_project_result_status
from ais.utils.ai_tools import ai_process_common_preparation

from .unet import UNet

warnings.filterwarnings("ignore")

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
model_path = os.path.join(current_directory, "weights/CP_epoch30.pth")

test_input_tiff = os.path.join(current_directory, "test/sat.jpg")


def preprocess_image(pil_img, scale):
    w, h = pil_img.size
    newW, newH = int(scale * w), int(scale * h)
    assert newW > 0 and newH > 0, "Scale is too small"
    pil_img = pil_img.resize((newW, newH))

    img_nd = np.array(pil_img)

    if len(img_nd.shape) == 2:
        img_nd = np.expand_dims(img_nd, axis=2)

    # HWC to CHW
    img_trans = img_nd.transpose((2, 0, 1))
    if img_trans.max() > 1:
        img_trans = img_trans / 255
    return img_trans


def predict_img(net, full_img, device, scale_factor=1, out_threshold=0.5):
    net.eval()

    img = torch.from_numpy(preprocess_image(full_img, scale_factor))

    img = img.unsqueeze(0)
    img = img.to(device=device, dtype=torch.float32)

    with torch.no_grad():
        output = net(img)
        # print(output)
        if net.n_classes > 1:
            probs = F.softmax(output, dim=1)
        else:
            probs = torch.sigmoid(output)

        probs = probs.squeeze(0)

        height, width = probs.shape[1], probs.shape[2]

        ## convert probabilities to class index and then to RGB
        ###################################################
        mapping = {
            0: (0, 255, 255),  # urban_land
            1: (255, 255, 0),  # agriculture
            2: (255, 0, 255),  # rangeland
            3: (0, 255, 0),  # forest_land
            4: (0, 0, 255),  # water
            5: (255, 255, 255),  # barren_land
            6: (0, 0, 0),
        }  # unknown
        class_idx = torch.argmax(probs, dim=0)
        image = torch.zeros(height, width, 3, dtype=torch.uint8)

        for k in mapping:

            idx = class_idx == torch.tensor(k, dtype=torch.uint8)
            validx = idx == 1
            image[validx, :] = torch.tensor(mapping[k], dtype=torch.uint8)

        image = image.permute(2, 0, 1)

        tf = transforms.Compose([transforms.ToPILImage(), transforms.Resize(full_img.size[1]), transforms.ToTensor()])

        image = image.permute(1, 2, 0)
        image = image.squeeze().cpu().numpy()

    return image, class_idx


def get_predict(defined_model, input_png, output_name):
    try:
        net = UNet(n_channels=3, n_classes=7)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("加载Land模型 和GPU", defined_model, device)

        net.to(device=device)
        net.load_state_dict(torch.load(defined_model, map_location=device))

        img = Image.open(input_png)

        # Splitting input directory from the file name
        name = input_png.split("/")[-1]
        # Removing the file extension
        name = name.split(".")[0]
        seg, mask_indices = predict_img(net=net, full_img=img, scale_factor=0.2, out_threshold=0.5, device=device)

        im = Image.fromarray(seg)
        im.save(output_name)
        print("Land模型 结果", mask_indices)
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
                ai_result = get_predict(model_path, test_input_tiff, output_result_file_name)
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
    print("Land Cover Classification start processing\r\n")
    # 2 开启异步任务处理
    async_task(task_start, input_params, q_options={"task_name": input_params.get("uuid"), "hook": task_finish})

    # 3 返回相应处理状态
    return None
