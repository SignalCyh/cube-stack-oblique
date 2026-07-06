import time
import os
import multiprocessing as mp
from functools import partial
import math
from tqdm import tqdm
import tarfile


def _extract_image(task):
    tar_file_path, img_output_path = task
    # start_time = time.time()
    with tarfile.open(tar_file_path, "r") as tar:
        members = tar.getmembers()
        print(f"find {len(members)} images")
        for member in tqdm(members, desc="extract_file"):
            tar.extract(member, path=img_output_path)
    # end_time = time.time()
    # print(f"extract tar {tar_file_path} finished. time cost {end_time-start_time}")


def extract_tar_dir(
    input_path: str,
    output_path: str,
    parallel_num=64,
):
    tar_file_list = sorted([i.name for i in os.scandir(input_path) if i.name.endswith(".tar")])
    print(f"list {len(tar_file_list)} tars")

    tasks = []
    for tar_file_name in tar_file_list:
        tar_file_path = os.path.join(input_path, tar_file_name)
        img_output_path = os.path.join(output_path, os.path.splitext(tar_file_name)[0])
        tasks.append((tar_file_path, img_output_path))

    with mp.Pool(parallel_num) as pool:
        ress = pool.imap_unordered(_extract_image, tasks)
        for res in ress:
            pass
    pool.close()
    pool.join()


def extract_tar(
    output_path: str,
    input_path: str,
):
    # output = os.path.join(output_path, os.path.splitext(os.path.basename(input_path))[0])
    output = output_path
    os.makedirs(output, exist_ok=True)
    with tarfile.open(input_path, "r") as tar:
        try:
            members = tar.getmembers()
            for member in tqdm(members, desc="extract_file"):
                tar.extract(member, path=output)
        except Exception as e:
            print(f"failed | {e}")


if __name__ == "__main__":
    input_path = r"/xb-mix02/cv10/permanent/yyliu70/data/math/prim_math_part5/images-138542_tar"
    output_path = r"/xb-mix02/cv10/permanent/yyliu70/data/math/prim_math_part5/images"

    print(input_path)
    parallel_num = 64
    input_lst = [i.path for i in os.scandir(input_path) if i.name.endswith(".tar")]
    with mp.Pool(parallel_num) as pol:
        pol.map(partial(extract_tar, output_path), tqdm(input_lst, desc="_multi"))
    pol.close()
    pol.join()

    # extract_tar(input_path, output_path, parallel_num)
    # extract_tar_dir(input_path, output_path, parallel_num)