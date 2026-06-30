import json
import time
import os
import argparse
import math
import tarfile

from multiprocessing import Pool  # 多进程并行处理
from tqdm import tqdm 


def _pack_image(task):
    """
    单个任务：将一批图片打包成 tar 文件
    :param task: 元组，包含 (原始图片根路径, 该任务要打包的图片列表, 输出tar文件路径)
    """
    raw_image_path, image_names, tar_file_path = task
    start_time = time.time()  # 记录开始时间

    # 创建 tar 文件并写入
    with tarfile.open(tar_file_path, "w") as tar:
        # 遍历当前任务的所有图片，展示打包进度
        for image_name in tqdm(image_names, desc="pack_image"):
            # 把文件加入 tar，arcname 控制压缩包内的目录结构
            tar.add(image_name, arcname=os.path.join(
                os.path.basename(os.path.dirname(image_name)),  # 取父目录名
                os.path.basename(image_name)                   # 取文件名
            ))

    end_time = time.time()
    # 打印当前 tar 包完成信息 + 耗时
    print(f"create tar {tar_file_path} finised. time cost {end_time - start_time}")


def compress_parts(
        raw_image_path: str,          # 原始图片文件夹路径
        image_cnt_per_part: int = 1000000,  # 每个 tar 包包含多少张图片
        parallel_num=32,              # 并行进程数
):
    """
    主逻辑：遍历图片目录 → 分片 → 多进程并行打包成多个 tar
    """
    start_time = time.time()

    # 扫描目录下所有文件，生成文件路径列表，带进度条
    all_file_list = [i.path for i in tqdm(list(os.scandir(raw_image_path)))]
    print(len(all_file_list))  # 打印总文件数量
    end_time = time.time()

    image_cnt = len(all_file_list)  # 总图片数量

    # 定义输出 tar 包的根目录（网络共享路径）
    # output_path = r"\\172.30.209.40Z\yyliu70\yhcheng24_三视图数据\data\images-{str(image_cnt)}_tar"
    output_path = r"C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\Data\images_tar"
    os.makedirs(output_path, exist_ok=True)  # 不存在则创建目录

    # 打印扫描总耗时
    print(f"list {image_cnt} images, time cost {end_time - start_time}")

    # 计算需要分成多少个 tar 包（向上取整）
    part_cnt = math.ceil(len(all_file_list) / image_cnt_per_part)

    tasks = []  # 多进程任务列表
    for idx in range(part_cnt):
        # 每个 tar 包的保存路径，命名为 part000000.tar 格式
        tar_file_path = os.path.join(output_path, f"part{idx:06d}.tar")

        # 截取当前分片对应的图片列表
        image_names = all_file_list[image_cnt_per_part * idx:image_cnt_per_part * (idx + 1)]

        # 把任务参数加入任务列表
        tasks.append((raw_image_path, image_names, tar_file_path))

    # 启动多进程池，并行执行打包任务
    with Pool(parallel_num) as pool:
        # 无序映射执行，提高效率
        ress = pool.imap_unordered(_pack_image, tasks)
        # 遍历等待所有进程完成
        for res in ress:
            pass


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='tar切片压缩')  # 工具描述
    # 原始图片目录
    parser.add_argument('--raw_image_path', type=str, default=r"C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\legal_images", help='压缩文件夹')
    # 每个切片多少张图
    parser.add_argument('--image_cnt_per_part', type=int, default=50000, help='每个切片包含的文件数')
    # 并行进程数
    parser.add_argument('--parallel_num', type=int, default=40, help='压缩进程数')
    return parser.parse_args()


if __name__ == "__main__":
    # 主入口：解析参数 → 执行压缩 → 打印总耗时
    args = parse_arguments()
    print(args.raw_image_path)  # 打印输入路径

    start_time = time.time()
    compress_parts(args.raw_image_path, args.image_cnt_per_part, args.parallel_num)
    end_time = time.time()

    # 打印总耗时和处理的文件夹
    print(f"totoal time cost :{end_time - start_time}, \nfile: {args.raw_image_path}")
