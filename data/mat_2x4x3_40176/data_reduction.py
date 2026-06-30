# mat243数据整合

import os
import numpy as np
import json

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

def move_xy_all0(mat):
    """去除整行(列)为空的行(列)"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

def lst2mat(lst):
    """一维堆叠序列立体化"""
    n = lst.max()
    i = np.arange(n-1, -1, -1)[:, None]
    mat = (lst > i).astype(int)
    return mat

def row2square(lst):
    """0->白正方形 1->黑正方形"""
    return ''.join([chr(0x2B1C) if p == 0 else chr(0x2B1B) for p in lst])

def numpy_diff3(a, b, c):
    """判断三个numpy数组两两互不相同"""
    return (not np.array_equal(a, b) and 
            not np.array_equal(a, c) and 
            not np.array_equal(b, c))

def mat2text(mat):
    """01矩阵可视化分析文本"""
    row, col = mat.shape
    total = mat.sum()
    rows = np.sum(mat, axis=1)
    analysis = f'呈{row}行{col}列的布局，其中从上向下数：\n'
    for i, num in enumerate(rows,0):
        analysis += f'第{i+1}行有{num}个正方形，呈现{row2square(mat[i])}；\n'
    analysis += f'共计能看到{total}个小正方形。'

    return analysis

def frt_analysis(mat):
    """三视图分析文本"""
    valid = move_xy_all0(mat)

    front = lst2mat(np.max(valid, axis=0))
    h1, l1 = front.shape
    rows1 = np.sum(front, axis=1)
    analysis_f = f'呈{h1}行{l1}列的布局，其中从上向下数：\n'
    for i, num in enumerate(rows1,0):
        analysis_f += f'第{i+1}行有{num}个正方形，呈现{row2square(front[i])}；\n'
    analysis_f += f'共计能看到{rows1.sum()}个小正方形。'

    right = lst2mat(np.max(mat, axis=1))[::-1]
    h2, l2 = right.shape
    rows2 = np.sum(right, axis=1)
    analysis_r = f'呈{h2}行{l2}列的布局，其中从上向下数：\n'  
    for i, num in enumerate(rows2,0):
        analysis_r += f'第{i+1}行有{num}个正方形，呈现{row2square(right[i])}；\n'
    analysis_r += f'共计能看到{rows2.sum()}个小正方形。'

    top = (valid>0).astype(int)
    h3, l3 = top.shape
    rows3 = np.sum(top, axis=1)
    analysis_t = f'呈{h3}行{l3}列的布局，其中从上向下数：\n'
    for i, num in enumerate(rows3,0):
        analysis_t += f'第{i+1}行有{num}个正方形，呈现{row2square(top[i])}；\n'
    analysis_t += f'共计能看到{rows3.sum()}个小正方形。'

    return analysis_f, analysis_r, analysis_t


if __name__ == "__main__":
    mat_file = os.path.join(current_dir, 'mat_2x4x3_legal_18295.txt')
    output_file = os.path.join(current_dir, f'mat_243_data.jsonl')

    with open(mat_file, 'r', encoding='utf-8') as inf,\
        open(output_file, 'w', encoding='utf-8') as opf:
        for i, line in enumerate(inf,start=1):
            line = line.strip()
            if not line:
                continue
            mat = np.array(eval(line))
            num = mat.sum()
            height = mat.max()
            # f_text, r_text, t_text = frt_analysis(mat)
            valid = move_xy_all0(mat)
            front_1 = np.max(valid, axis=0)
            front_2 = lst2mat(front_1)
            right_1 = np.max(valid, axis=1)[::-1]
            right_2 = lst2mat(right_1)
            top_2 = (valid>0).astype(int)

            data = {
                'id': i,
                'num': int(num),
                'height': int(height),
                'img': f'mat_243_{i}.png',
                'mat': mat.tolist(),

                'view_mat':{
                    'front_1dim': front_1.tolist(),
                    'front_2dim': front_2.tolist(),
                    'right_1dim': right_1.tolist(),
                    'right_2dim': right_2.tolist(),
                    'top_2dim': top_2.tolist(),
                },

                'view_text':{
                    'f_text': mat2text(front_2),
                    'f_num': int(front_2.sum()),
                    'r_text': mat2text(right_2),
                    'r_num': int(right_2.sum()),
                    't_text': mat2text(top_2),
                    't_num': int(top_2.sum())
                },   

                'is_fr_diff': not np.array_equal(front_1, right_1),
                'is_frt_diff': numpy_diff3(front_2, right_2, top_2)
            }

            opf.write(json.dumps(data, ensure_ascii=False) + '\n')