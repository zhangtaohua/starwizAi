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
    print("pytorch GPU name", torch.cuda.get_device_name(0))

    tf.debugging.set_log_device_placement(True)
    gpus = tf.config.list_logical_devices("GPU")
    if gpus:
        # Replicate your computation on multiple GPUs
        c = []
        for gpu in gpus:
            with tf.device(gpu.name):
                a = tf.constant([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
                b = tf.constant([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
                c.append(tf.matmul(a, b))

    with tf.device("/CPU:0"):
        matmul_sum = tf.add_n(c)

    print(matmul_sum)


if __name__ == "__main__":
    main()
