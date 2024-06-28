import os


def create_directory(file_path, permissions=0o777):
    """
    判断目录是否存在，如果不存在则创建目录，并创建一个空文件。

    :param file_path: 要创建的文件的完整路径
    """
    # 提取目录路径
    dir_path = os.path.dirname(file_path)

    # 检查目录是否存在
    if not os.path.exists(dir_path):
        # 如果目录不存在，则创建目录
        os.makedirs(dir_path, permissions)
        print(f"目录 {dir_path} 已创建")
    else:
        print(f"目录 {dir_path} 已存在")


def create_directory_and_file(file_path, permissions=0o777):
    """
    判断目录是否存在，如果不存在则创建目录，并创建一个空文件。

    :param file_path: 要创建的文件的完整路径
    """
    # 提取目录路径
    dir_path = os.path.dirname(file_path)

    # 检查目录是否存在
    if not os.path.exists(dir_path):
        # 如果目录不存在，则创建目录
        os.makedirs(dir_path, permissions)
        print(f"目录 {dir_path} 已创建")
    else:
        print(f"目录 {dir_path} 已存在")

    # 创建文件
    with open(file_path, "w") as f:
        f.write("")
    print(f"文件 {file_path} 已创建")


if __name__ == "__main__":
    file_path = r"D:\Work\project\Python\starwizAi\assets\ai\results\abc\handle.tif"
    create_directory_and_file(file_path)
