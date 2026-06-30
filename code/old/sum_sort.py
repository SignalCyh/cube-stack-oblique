import os
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

mat_file = os.path.join(current_dir, 'mat_3x3x3_legal_47529.txt')
save_dir = os.path.join(current_dir, 'output')
os.makedirs(save_dir, exist_ok=True)
files = [open(os.path.join(save_dir, f'mat_sum_{s}.txt'), 'w', encoding='utf-8') for s in range(28)]

with open(mat_file, 'r', encoding='utf-8') as f:
    cnt = np.zeros(3*3*3+1, dtype=int)
    for i, line in enumerate(f,start=1):
        line = line.strip()
        if not line:
            continue
        mat = np.array(eval(line))
        s = mat.sum()
        cnt[s] += 1
        files[s].write(line + '\n')

for f in files:
    f.close()

for s in range(28):
    old_path = os.path.join(save_dir, f'mat_sum_{s}.txt')
    new_path = os.path.join(save_dir, f"mat_sum_{s}_{cnt[s]}.txt")
    
    if os.path.exists(old_path):
        os.rename(old_path, new_path)

print(cnt)