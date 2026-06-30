import numpy as np
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 
  
   
def hide4(h, x1, x2, x3, x4):
    pairs = [(x1, x2), (x1, x4), (x2, x3), (x3, x4)]
    return any(a >= h and b >= h for a, b in pairs)

def visible_check(mat)->bool:
    if mat.max() <= 3:
        return False

    def check_222(mat):
        if mat[0][0] < 2 and mat[1][0] >= 2 and (mat[0][1] >= 2 or mat[1][1] >= 2):
            return False
        return True
    
    mat_1 = np.where(mat >= 1, mat - 1, 0)
    mat_2 = np.where(mat_1 >= 1, mat_1 - 1, 0)
    return check_222(mat) and check_222(mat_1) and check_222(mat_2)
    

if __name__ == "__main__":

    file_name = 'mat_2x2x4_548.txt'
    file_path = os.path.join(current_dir, file_name)
    save_1 = f'{os.path.splitext(file_path)[0]}_legal.txt'
    save_2 = f'{os.path.splitext(file_path)[0]}_illegal.txt'

    num1 = 0 
    num2 = 0

    with open(file_path, 'r', encoding='utf-8') as f, \
        open(save_1, 'w', encoding='utf-8') as s1, \
        open(save_2, 'w', encoding='utf-8') as s2:

        for i, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            mat = np.array(eval(line))

            if visible_check(mat):
                s1.write(line + "\n")
                num1 += 1
            else:
                s2.write(line + "\n")
                num2 += 1

    new_path_1 = os.path.join(current_dir, f"legal_{num1}.txt")
    os.rename(save_1, new_path_1)
    new_path_2 = os.path.join(current_dir, f"illegal_{num2}.txt")
    os.rename(save_2, new_path_2)
    print(f"legal: {num1} | illegal: {num2}")