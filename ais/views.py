import json

from utils.response import json_response_error_with_msg, json_response_with_data

from .aimodels.hkLandFeatures.enter import StartProcess as hongkong_land_features_start_process
from .aimodels.shipsDetect.enter import StartProcess as ships_detect_start_process
from .aimodels.yolact.enter import StartProcess as yolact_start_process
from .models_utils import get_ai_project_result_by_uuid

# Create your views here.


# 用于响应 go 服务端 通知开始进行 AI 处理
def process(request):
    body = json.loads(request.body)
    # 较验请求参数
    result_uuid = body.get("uuid")
    ai_model_code = body.get("ai_model_code")

    if (result_uuid is None) or (ai_model_code is None):
        return json_response_error_with_msg("参数错误，请检测参数")
    else:
        # 获取 数据库记录
        result_obj = get_ai_project_result_by_uuid(result_uuid)
        if result_obj is None:
            # 记录不存在 返回错误
            return json_response_error_with_msg("记录不存在")

        # 根据模型 code 选择不同的模型进行处理
        if ai_model_code == "YOLACT":
            yolact_input_params = {"name": "yolact"}
            resData = yolact_start_process(yolact_input_params)
            return json_response_with_data(resData)
        elif ai_model_code == "HongkongLandFeatures":
            input_params = result_obj.input
            input_params["meta"] = {
                "uuid": result_obj.uuid,
                "name": result_obj.uuid,
                "user_id": result_obj.user_id,
                "ai_model_uuid": result_obj.ai_model_uuid,
                "ai_project_uuid": result_obj.ai_project_uuid,
            }
            resData = hongkong_land_features_start_process(input_params)
            return json_response_with_data(resData)
        elif ai_model_code == "shipsDetect":
            input_params = result_obj.input
            input_params["meta"] = {
                "uuid": result_obj.uuid,
                "name": result_obj.uuid,
                "user_id": result_obj.user_id,
                "ai_model_uuid": result_obj.ai_model_uuid,
                "ai_project_uuid": result_obj.ai_project_uuid,
            }
            resData = ships_detect_start_process(input_params)
            return json_response_with_data(resData)
