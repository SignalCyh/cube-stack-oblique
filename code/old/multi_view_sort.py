import os
import numpy as np
import json

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

mat_file = os.path.join(current_dir, 'mat_3x3x3_legal_47529.txt')
save_dir = os.path.join(current_dir, 'output')
os.makedirs(save_dir, exist_ok=True)
o1f = os.path.join(save_dir, f'same.jsonl')
o2f = os.path.join(save_dir, f'diff.jsonl')
files = [open(o1f, 'w', encoding='utf-8'),
         open(o2f, 'w', encoding='utf-8')
]       

def move_xy_all0(mat):
    """去除整行(列)为空的行(列)"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

same = 0
diff = 0
with open(mat_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f,start=1):
        line = line.strip()
        if not line:
            continue
        mat = np.array(eval(line))
        valid = move_xy_all0(np.rot90(mat))

        data = {
            'id':i,
            'mat':mat
        }
        front = np.max(valid, axis=0)
        right = np.max(valid, axis=1)[::-1]

        if np.array_equal(front, right):
            files[0].write(json.dumps(data, ensure_ascii=False) + '\n')
            same += 1
        else:
            files[1].write(json.dumps(data, ensure_ascii=False) + '\n')
            diff += 1

same_file = os.path.join(save_dir, f'same_{same}.jsonl')
os.rename(o1f, same_file)
diff_file = os.path.join(save_dir, f'diff_{diff}.jsonl')
os.rename(o2f, diff_file)
print(f"same:{same} | diff:{diff}")