from django.http import HttpResponse, JsonResponse


def json_response_error_with_msg(msg):
    return JsonResponse(
        {
            "code": 7,
            "success": False,
            "msg": msg,
            "data": None,
        },
        json_dumps_params={"ensure_ascii": False},
        safe=False,
    )


def json_response_with_data(data, msg="操作成功"):
    return JsonResponse(
        {
            "code": 0,
            "success": True,
            "msg": msg,
            "data": data,
        },
        json_dumps_params={"ensure_ascii": False},
        safe=False,
    )
