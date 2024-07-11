import tensorflow as tf
import torch


def main():
    print("tensorflow 版本：", tf.__version__)
    print("tensorflow GPU 是否可用：", tf.test.is_gpu_available())
    print("tensorflow GPU 是否可用", tf.config.list_physical_devices("GPU"))

    print("pytorch 版本：", torch.__version__)
    print("pytorch cuda 版本：", torch.version.cuda)
    print("pytorch GPU 是否可用", torch.cuda.is_available())
    print("pytorch GPU 可用数据", torch.cuda.device_count())
    print("pytorch GPU 0号名字", torch.cuda.get_device_name(0))


if __name__ == "__main__":
    main()
