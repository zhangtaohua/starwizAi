from enum import Enum

from django.db import models
from django.utils import timezone


# Create your models here.
class AiProjectResult(models.Model):
    uuid = models.UUIDField()
    name = models.CharField(max_length=191)
    description = models.CharField(max_length=191)

    input = models.JSONField()

    output = models.JSONField()

    progress = models.PositiveIntegerField()
    status = models.CharField(max_length=191)

    user_id = models.CharField(max_length=191)
    ai_model_uuid = models.CharField(max_length=191)
    ai_project_uuid = models.CharField(max_length=191)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_project_results"  # 表名


class AiProjectResultStatus(Enum):
    CREATE = "created"
    IDLE = "idle"

    PARAMS_VALID_SUCCESS = "params_valid_success"
    PARAMS_VALID_FAILED = "params_valid_failed"

    FILE_DOWNLOADING = "file_downloading"
    FILE_DOWNLOAD_SUCCESS = "file_download_success"
    FILE_DOWNLOAD_FAILED = "file_download_failed"

    FILE_PROCESSING = "file_processing"
    FILE_PROCESS_SUCCESS = "file_process_success"
    FILE_PROCESS_FAILED = "file_process_failed"

    AI_PROCESSING = "ai_processing"
    AI_PROCESS_SUCCESS = "ai_process_success"
    AI_PROCESS_FAILED = "ai_process_failed"
    AI_PROCESS_DONE = "ai_process_done"


# 下载库记录模型
class DownloadModelManager(models.Manager):
    def get_queryset(self):
        return super(DownloadModelManager, self).get_queryset().filter(deleted_at__isnull=True)


class Download(models.Model):
    name = models.CharField(max_length=191)
    asset_path = models.CharField(max_length=191)
    md5 = models.CharField(max_length=191)
    status = models.CharField(max_length=191)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # objects = DownloadModelManager()  # 使用自定义的 Manager
    # all_objects = models.Manager()  # 使用 Django 的默认 Manager

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self, *args, **kwargs):
        super(Download, self).delete(*args, **kwargs)

    class Meta:
        db_table = "downloads"  # 表名


class DownloadStatus(Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    DOWNLOAD_CHECKING = "download_checking"
    DOWNLOAD_SUCCESS = "download_success"
    DOWNLOAD_FAILED = "download_failed"
