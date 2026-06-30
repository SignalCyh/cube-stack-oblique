# 基础信息生成

import numpy as np
import json
import os
import uuid
import sys
sys.path.append(r"C:\Users\yhcheng24\Desktop\yhcheng24\Code\FileTools\Code")
from jsonTools_stream import json_filter_json
from collections import defaultdict
from tqdm import tqdm


current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

def move_xy_all0(array):
    """去除整行(列)为空的行(列)"""
    mat = np.array(array)
    res = mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]
    return res

def lst2mat(lst):
    """一维堆叠序列立体化"""
    n = lst.max()
    i = np.arange(n-1, -1, -1)[:, None]
    mat = (lst > i).astype(int)
    return mat

def baseinf(mat_file):

    output_file = os.path.join(current_dir,f'1_{uuid.uuid4()}.jsonl')
    with open(mat_file, 'r', encoding='utf-8') as inf,\
        open(output_file, 'w', encoding='utf-8') as opf:
        for i, line in enumerate(inf,start=1):
            line = line.strip()
            if not line:
                continue
            mat = np.array(eval(line))
            num = mat.sum()
            height = mat.max()

            valid = move_xy_all0(mat)
            front_1 = np.max(valid, axis=0)
            front_2 = lst2mat(front_1)
            right_1 = np.max(valid, axis=1)[::-1]
            right_2 = lst2mat(right_1)
            left_1 = np.max(valid, axis=1)
            left_2 = lst2mat(left_1)
            # left_2 = np.fliplr(right_2)
            top_2 = (valid>0).astype(int)

            data = {
                'id': i,
                'num': int(num),
                'height': int(height),
                'mat': valid.tolist(),

                'f_mat': front_2.tolist(),
                'l_mat': left_2.tolist(),
                'r_mat': right_2.tolist(),
                't_mat': top_2.tolist(),
            }

            opf.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    return output_file

def add_restorable_keep_order(input_path: str):
    group_id_list = defaultdict(list)
    output_path = os.path.join(current_dir,f'2_{uuid.uuid4()}.jsonl')
    # 第一次遍历：统计每个分组
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                uid = obj["id"]
                # 序列化二维数组作为分组key
                key_a = json.dumps(obj["f_mat"], sort_keys=True)
                key_b = json.dumps(obj["r_mat"], sort_keys=True)
                key_c = json.dumps(obj["t_mat"], sort_keys=True)
                group_key = (key_a, key_b, key_c)
                group_id_list[group_key].append(uid)
            except (KeyError, json.JSONDecodeError):
                continue

    # 第二次遍历：追加restorable
    with open(input_path, "r", encoding="utf-8") as f_in,\
        open(output_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            raw_line = line.strip()
            if not raw_line:
                continue
            try:
                data = json.loads(raw_line)
                key_a = json.dumps(data["f_mat"], sort_keys=True)
                key_b = json.dumps(data["r_mat"], sort_keys=True)
                key_c = json.dumps(data["t_mat"], sort_keys=True)
                gk = (key_a, key_b, key_c)
                # 绑定本组所有id
                data["restorable"] = group_id_list[gk]
                f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
            except (KeyError, json.JSONDecodeError):
                # 损坏/缺字段行直接跳过，不输出
                continue

    return output_path

def json_extract(file_path):

    output_path = os.path.join(current_dir,f'3_{uuid.uuid4()}.jsonl')
    total = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))

    num = 0
    error = 0
    with tqdm(total=total) as pbar, \
        open(file_path, "r", encoding="utf-8") as f,\
        open(output_path, "w", encoding="utf-8") as opf:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line: continue
            try:
                item = json.loads(line)
                if len(item['restorable']) == 1:
                    opf.write(json.dumps(item, ensure_ascii=False) + "\n")
                    num += 1
            except Exception as e:
                print(f'{idx} error: {e}')
                error += 1
            pbar.update(1)

    print(f"total: {total} | num: {num} | error: {error}")
    return output_path

if __name__ == '__main__':
    file1 = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x2x4_548\mat_224_data_final.jsonl'
    mat_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x2x4_548\legal_236.txt'

    # file1 = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x4x3_40176\mat_243_data_final.jsonl'
    # mat_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x4x3_40176\mat_2x4x3_40176.txt'
    
    # file1 = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_4x2x3_40176\mat_423_data_final.jsonl'
    # mat_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_4x2x3_40176\mat_4x2x3_40176.txt'


    path1 = baseinf(mat_file)
    path2 = add_restorable_keep_order(path1)
    path3 = json_extract(path2)
    json_filter_json(file1,path3,'mat')
