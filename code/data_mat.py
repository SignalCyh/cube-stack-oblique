# 基础信息生成

import numpy as np
import json

mat_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x4x3_40176\mat_2x4x3_40176.txt'
output_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\restorable\mat_243.jsonl'


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


if __name__ == "__main__":

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