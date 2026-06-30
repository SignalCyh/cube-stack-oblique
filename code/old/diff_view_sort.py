# 筛选正视图、右视图、俯视图各不相同的图形

import os
import numpy as np
import json

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

mat_file = os.path.join(current_dir, 'mat_3x3x3_legal_47529.txt')
save_dir = os.path.join(current_dir, 'output')
os.makedirs(save_dir, exist_ok=True)
opp = os.path.join(save_dir, f'same.jsonl')   

def move_xy_all0(mat):
    """去除整行(列)为空的行(列)"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

def lst2mat(lst):
    n = lst.max()

    i = np.arange(n-1, -1, -1)[:, None]
    mat = (lst > i).astype(int)
    return mat

result = 0
with open(mat_file, 'r', encoding='utf-8') as f,\
    open(opp, 'w', encoding='utf-8') as opf:
    for i, line in enumerate(f,start=1):
        line = line.strip()
        if not line:
            continue
        mat = np.array(eval(line))
        valid = move_xy_all0(np.rot90(mat))

        data = {
            'id':i,
            'mat':mat.tolist()
        }
        front = lst2mat(np.max(valid, axis=0))
        right = lst2mat(np.max(valid, axis=1)[::-1])
        top = (valid>0).astype(int)

        if (not np.array_equal(front,top) and
            not np.array_equal(front,right) and
            not np.array_equal(right,top)):
            opf.write(json.dumps(data, ensure_ascii=False) + '\n')
            result += 1

same_file = os.path.join(save_dir, f'diff3view_{result}.jsonl')
os.rename(opp, same_file)
print(f"result:{result}")