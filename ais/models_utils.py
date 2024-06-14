from .models import AiProjectResult


def get_ai_project_result_by_uuid(uuid):
    try:
        result_obj = AiProjectResult.objects.using("postgres").get(uuid=uuid)
        return result_obj
    except AiProjectResult.DoesNotExist:
        # 记录不存在 返回错误
        return None


def updata_ai_project_result_status(uuid, status, percentage=0, error=None):
    try:
        result_obj = AiProjectResult.objects.using("postgres").get(uuid=uuid)
        result_obj.status = status
        result_obj.progress = percentage

        if error:
            result_obj.output = {
                "error": error,
            }
        else:
            result_obj.output = None

        result_obj.save()
        return True
    except AiProjectResult.DoesNotExist:
        # 记录不存在 返回错误
        return False


def updata_ai_project_result_results(uuid, status, percentage=0, result={}, error=None):
    try:
        result_obj = AiProjectResult.objects.using("postgres").get(uuid=uuid)
        result_obj.status = status
        result_obj.progress = percentage

        if error:
            result_obj.output = {
                "result": "",
                "error": error,
            }
        else:
            result_obj.output = {
                "result": result,
                "error": "",
            }

        result_obj.save()
        return True
    except AiProjectResult.DoesNotExist:
        # 记录不存在 返回错误
        return False
