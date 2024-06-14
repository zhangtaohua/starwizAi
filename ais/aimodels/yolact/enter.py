import time

from django_q.tasks import Task, async_task, result


def task_finish(task: Task):
    print("任务完成", task)
    task_result = result(task.id)
    print("task_result", task_result)


def task_start(inputParams):
    print("开始", inputParams)
    time.sleep(1)
    print("我睡了10s", inputParams["name"])
    time.sleep(2)
    print("我睡了2s", inputParams["name"])
    time.sleep(3)
    print("我睡了3s", inputParams["name"])
    return {"input": inputParams}


def StartProcess(request):
    print(request)
    # 1 较验项目结果是否存在，以及参数是否正确

    # 2 开始新的进程进行后台处理

    # 3 返回相应处理状态
    async_task(
        task_start,
        request,
        q_options={
            "task_name": request["name"],
            "hook": task_finish,
        },
    )

    return None
