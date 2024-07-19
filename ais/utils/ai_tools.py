import os
import warnings
from typing import AnyStr

from django.conf import settings

from ais.models import Download, DownloadStatus
from utils.download import download_file, verify_file

warnings.filterwarnings("ignore")


def check_and_download_file(file_url: AnyStr, save_file_path_name: AnyStr = ""):
    # 有可能要执行下面语句才可以拿到 settings 中变量
    # django.setup()

    # 1 获取数据库 下载表，如果已下载且完整直接返回
    print("Info: check file url", file_url)
    file_path = settings.DOWNLOAD_TIFF_PATH
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
