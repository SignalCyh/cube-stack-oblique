# jsonl文件内容修改框架

import os
import json
import numpy as np
from tqdm import tqdm

file_path = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_4x2x3_40176\mat_423_data.jsonl'
output_path = os.path.splitext(file_path)[0] + '_fix.jsonl'

def difficult(array):
    mat = np.array(array)
    row, col = mat.shape
    h = mat.max()
    if row == 1 or col == 1 or h == 1:
        return '易'
    if h == 2:
        return '中'
    if any(3 in row[1:] for row in mat[1:]):
        return "极难"
    return '难'

def move_xy_all0(array):
    """去除整行(列)为空的行(列)"""
    mat = np.array(array)
    res = mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]
    return res.tolist()

def fix_func(idx,item):
    mat = item["mat"]
    data = {
        "id": item["id"],
        "num": item["num"],
        "height": item["height"],
        "img": item["img"],
        "mat": move_xy_all0(mat),
        "f_mat": move_xy_all0(item["view_mat"]["front_2dim"]),
        "r_mat": move_xy_all0(item["view_mat"]["right_2dim"]),
        "t_mat": move_xy_all0(item["view_mat"]["top_2dim"]),
        "diff": difficult(move_xy_all0(mat))
    }
    return data

if __name__ == "__main__":

    num = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))

    with tqdm(total=num) as pbar, \
        open(file_path, "r", encoding="utf-8") as f,\
        open(output_path, "w", encoding="utf-8") as opf:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line: continue
            try:
                item = json.loads(line)
                data = fix_func(idx,item)
                opf.write(json.dumps(data, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f'error: {e}')
            pbar.update(1)
