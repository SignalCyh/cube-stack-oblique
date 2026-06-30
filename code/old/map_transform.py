import numpy as np
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

def map_transform(mat):
    n = mat.shape[0]
    new_mat = np.zeros_like(mat)
    
    for i in range(n):
        for j in range(n):
            new_mat[i][j] = mat[j][n-1-i]
    
    return new_mat

if __name__ == "__main__":

    file_name = '200.txt'
    file_path = os.path.join(current_dir, file_name)
    save_1 = f'matrix.txt'
    save_2 = f'caption示例.txt'

    with open(file_path, 'r', encoding='utf-8') as f, \
        open(save_1, 'w', encoding='utf-8') as s1, \
        open(save_2, 'w', encoding='utf-8') as s2:

        for i, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            mat = np.array(eval(line))
            new_mat = map_transform(mat)

            mat_list = new_mat.tolist()
            s1.write(str(mat_list) + "\n")

            new_line = f'{str(mat_list)}是一个3*3的矩阵，数字代表试题图片中立体图俯视角下各个位置上的正方体个数，据此解题。'
            s2.write(new_line + "\n")