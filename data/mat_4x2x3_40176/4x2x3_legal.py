import numpy as np
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 
  
   
def hide4(h, x1, x2, x3, x4):
    pairs = [(x1, x2), (x1, x4), (x2, x3), (x3, x4)]
    return any(a >= h and b >= h for a, b in pairs)

def visible_check(mat)->bool:
    row, col = mat.shape
    h = mat.max()
    if row == 1 or col == 1 or h == 1:
        return True

    def check_422(mat):
        y = 0
        for x in range(3):
            if mat[x][y] < 2:
                if x == 0 and mat[3][1] >= 3 and mat[0][1] >= 2:
                    return False
                # 前 右 遮挡不确定
                if mat[x+1][y] >= 2 and mat[x][y+1] >= 2:
                    return False

                if x == 1 or x == 2:
                    #前 前右 遮挡不确定
                    if mat[x+1][y] >= 2 and mat[x+1][y+1] >= 2:
                        return False

                    #前 右 后 遮挡不确定
                    if mat[x+1][y] >= 2 and mat[x][y+1] == 1 and mat[x-1][y] != 0:
                        return False
                
                if x in (0, 1) and hide4(2, mat[x+1][y], mat[x+1][y+1], mat[x+2][y], mat[x+2][y+1]):
                        return False
        return True
    
    mat_1 = np.where(mat >= 1, mat - 1, 0)
    return check_422(mat) and check_422(mat_1)
    

if __name__ == "__main__":

    file_name = 'mat_4x2x3_40176.txt'
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