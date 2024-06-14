import hashlib
import os

import requests
from requests.adapters import HTTPAdapter, Retry


# 方案一
def get_content_length(url):
    try:
        response = requests.get(url, allow_redirects=True, stream=True)
        response.raise_for_status()

        # 获取Content-Length头
        file_size = response.headers.get("Content-Length")
        print("file_size", file_size)
        if file_size is None:
            print("无法获取文件大小")
            return None
        return int(file_size)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP错误: {http_err}")
    except Exception as err:
        print(f"其他错误: {err}")
    return None


# 方案二
def get_final_url(url):
    try:
        session = requests.Session()
        response = session.head(url, allow_redirects=True)
        final_url = response.url
        print("Final url:", final_url)
        if final_url is None:
            print("无法获取文件的最终地址")
            return None
        return response.url
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP错误: {http_err}")
    except Exception as err:
        print(f"其他错误: {err}")
    return None


def get_content_length_v2(url):
    final_url = get_final_url(url)
    with requests.get(final_url, stream=True) as response:
        response.raise_for_status()
        file_size = response.headers.get("Content-Length")
        if file_size is None:
            print("无法获取文件大小")
            return None
        return int(file_size)


# 方案三 未测试
def get_content_length_from_range(url):
    headers = {"Range": "bytes=0-1"}
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()
        content_range = response.headers.get("Content-Range")
        if content_range:
            total_length = content_range.split("/")[-1]
            return int(total_length)
        elif content_range is None:
            file_size = response.headers.get("Content-Length")
            if file_size is None:
                print("无法获取文件大小")
                return None
            return int(file_size)

        return None


def download_file(url, local_filename, max_retries=5):
    try:
        # 使用 requests 库的 Retry 机制进行多次下载尝试
        session = requests.Session()
        retries = Retry(total=max_retries, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))

        # 获取文件大小以支持断点续传
        file_size = get_content_length(url)
        if file_size is None:
            print("Can not get file size, cancel download\r\n")
            return None

        # 创建本地文件，如果已经存在，则检查其大小
        if os.path.exists(local_filename):
            first_byte = os.path.getsize(local_filename)
        else:
            first_byte = 0

        print(f"File Size:  {file_size}, { first_byte }")

        # 如果文件已经完全下载，则返回
        if first_byte >= file_size:
            print(f"File {local_filename} already downloaded.\r\n")
            return local_filename

        # 开始下载文件，支持断点续传
        # headers = {'Range': 'bytes=%d-' % first_byte,
        #             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
        headers = {"Range": f"bytes={first_byte}-"}
        with session.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, "ab") as f:
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)
                        print(f"\rDownloaded size { f.tell() }  ,  {f.tell() / file_size:.2%}", end="")

        print("Download complete.\r\n")
        return local_filename
    except requests.RequestException as e:
        print("Downloads Error\r\n", e)
        # 记录下载错误日志
        return None


def verify_file(local_filename, expected_hash, hash_algorithm="md5"):
    hash_func = hashlib.new(hash_algorithm)
    with open(local_filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    file_hash = hash_func.hexdigest()
    if file_hash == expected_hash:
        print(f"File {local_filename} is verified successfully.\r\n")
        return True
    else:
        print(f"File {local_filename} verification failed: expected {expected_hash}, got {file_hash}.", end="\r\n")
        return False


# 示例使用
if __name__ == "__main__":
    url = "https://example.com/path/to/large/file.tif"
    local_filename = "file.tif"
    expected_hash = "your_expected_hash_here"

    # 下载文件
    download_file(url, local_filename)

    # 校验文件完整性
    if verify_file(local_filename, expected_hash):
        print("File downloaded and verified successfully.")
    else:
        print("File verification failed.")
