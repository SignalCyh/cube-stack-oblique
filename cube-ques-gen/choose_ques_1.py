# 第一类选择题生成（运行时绘图）

import os
import json
import random
import re

import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('Agg')

from collections import deque
from tqdm import tqdm

from CubeStyle import CubeStacking, CubeStyle, mat2pic
from FontStyle import plt_use_global_font, plt_use_random_font

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 


def collect_solid_mats(mats):
    """
    按阅读顺序汇总若干 3D 立体图的高度矩阵
    """
    res = []
    for mat in mats:
        arr = np.array(mat)
        if arr.ndim == 2:
            res.append(arr[::-1, ::-1].astype(int).tolist())
    return res

def move_xy_all0(mat):
    """去除整行(列)为空的行(列)"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

def row2square(lst):
    """0->白正方形 1->黑正方形"""
    return ''.join([chr(0x2B1C) if p == 0 else chr(0x2B1B) for p in lst])

def is_4connected(mat):
    """判断矩阵中所有值为1的格子是否四向连通"""
    rows, cols = mat.shape
    dirs = [(-1,0), (1,0), (0,-1), (0,1)]

    start = None
    for i in range(rows):
        for j in range(cols):
            if mat[i, j] == 1:
                start = (i, j)
                break
        if start is not None:
            break
    if start is None:
        return True
    
    # BFS遍历连通区域
    visited = np.zeros_like(mat, dtype=bool)
    q = deque([start])
    visited[start[0], start[1]] = True
    cnt = 1
    
    while q:
        x, y = q.popleft()
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols:
                if mat[nx, ny] == 1 and not visited[nx, ny]:
                    visited[nx, ny] = True
                    cnt += 1
                    q.append((nx, ny))
    
    total_one = np.sum(mat)
    return cnt == total_one

def random_binary_matrix(row, col, n):
    row += (row == 1)
    col += (col == 1)
    total = row * col
    assert 1 <= n <= total, f"error: n must in [1,{total}]"
    
    arr = np.array([1] * n + [0] * (total - n))
    while True:
        np.random.shuffle(arr)
        mat = arr.reshape(row, col)
        if is_4connected(mat):
            break

    return move_xy_all0(mat)

def generate_wrong_pic(item, view):

    mat_map = {
        "正面": "front_2dim",
        "右面": "right_2dim",
        "上面": "top_2dim"
    }

    base_key = mat_map[view]
    mat1 = np.array(item["view_mat"][base_key])
    res = [mat1]
    seen = {mat1.tobytes()}

    for mat_name in mat_map.values():
        if mat_name == base_key:
            continue  
        mat = np.array(item["view_mat"][mat_name])
        bts = mat.tobytes()
        if bts not in seen:
            seen.add(bts)
            res.append(mat)
    
    mat2 = np.fliplr(mat1)
    if not any(np.array_equal(mat2, m) for m in res):
        res.append(mat2)
    
    s1 = mat1.sum()
    row, col = mat1.shape

    while len(res) < 4:
        s2 = random.randint(max(1,s1-1),min(row*col, s1+1)) if s1 not in [1,2] else random.randint(2,3)
        m2 = random_binary_matrix(row, col, s2)

        if not any(np.array_equal(m2, m) for m in res):
            res.append(m2)

    return res
      
def view_analysis(mat):

    hang, lie = mat.shape
    rows = np.sum(mat, axis=1)
    analysis = f'呈{hang}行{lie}列的布局：\n'

    for i, num in enumerate(rows,0):
        analysis += f'  第{i+1}行有{num}个正方形，呈现{row2square(mat[i])}；\n'
    
    analysis += f'  共计能看到{rows.sum()}个小正方形。'

    return analysis

def choose_question(item,view,save_path,figsize=(5, 2),dpi=200):
    plt.figure(figsize=figsize, dpi=dpi)

    order = generate_wrong_pic(item, view)
    indices = list(range(len(order)))
    random.shuffle(indices)
    shuffled = [order[i] for i in indices]
    pos = indices.index(0)
    answer = chr(pos + 65)

    max_x = max(len(x[0]) for x in order)
    max_y = max(len(x) for x in order)

    gs = plt.GridSpec(1, 5, width_ratios=[1,1,1,1,1], wspace=0.3)

    style = CubeStyle.random()
    for option in range(4):
        ax = plt.subplot(gs[option])
        mat2pic(ax, shuffled[option], max_x, max_y, style)
        ax.text(-0.12, 0.1, f'{chr(option + 65)}.', fontsize=9, transform=ax.transAxes, va='bottom', ha='left')

    ax_3d = plt.subplot(gs[4])
    mat = np.array(item['mat'])
    cubes = CubeStacking(mat, style=style)
    cubes.draw_3D(ax_3d)
    
    prb_text = f'右图立体图形由若干小正方体堆叠而成，从{view}看到的图像是（）'
    plt.figtext(0.02,0.90,prb_text,ha="left",va="top",fontsize=9,linespacing=1.3)
    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
    plt.savefig(save_path,dpi=dpi,bbox_inches="tight")
    plt.close()    

    return answer

def choose_question_analysis(item, view, answer, save_path):
    """选择题解析生成

    :param item: 矩阵信息
    :param save_path: 保存的图片路径
    """
    view_key_map = {
        "正面": "front_2dim",
        "右面": "right_2dim",
        "上面": "top_2dim"
    }
    step = view_analysis(np.array(item["view_mat"][view_key_map[view]]))
    
    analysis = [
        '【分析】',
        ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，从不同方向观察立体图形。',
        f' 解题思路：为找出立体图形从{view}观察得到的平面图形，解题时先确定从{view}看的列数，再分别数出每一列的正方体个数，最后与选项进行比对。\n',
        '【解答】',
        f' 解：从{view}看：{step}',
        f"  所以，选项{answer}符合描述。",
        f"\n【答案】 {answer}"
    ]
    
    analysis_str = '\n'.join(analysis)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)

    return analysis_str


def choose_task(file_path,view):
    save_dir = os.path.join(current_dir,f'第一类选择题_{view}')
    os.makedirs(save_dir, exist_ok=True)

    jsonl_path = os.path.join(save_dir,f'第一类选择题_{view}.jsonl')
    img_dir = os.path.join(save_dir, 'ques_images')
    os.makedirs(img_dir, exist_ok=True)
    txt_dir = os.path.join(save_dir, 'txt')
    os.makedirs(txt_dir, exist_ok=True)

    total = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
    success = 0
    error= 0
    with tqdm(total=total) as pbar, \
        open(file_path, 'r', encoding='utf-8') as f,\
        open(jsonl_path, 'w', encoding='utf-8') as opf:
        for idx, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            # if idx < 40: continue
            # if idx > 50: break
            try:
                plt_use_random_font(verbose=False)
                item = json.loads(line)
                id = item["id"]
                img_name = f"第一类选择题_{view}_{id}.png"
                answer = choose_question(item, view, os.path.join(img_dir,img_name))
                answer_str = choose_question_analysis(item, view, answer, os.path.join(txt_dir,f"第一类选择题_{view}_{id}_解析.txt"))

                match = re.search(r'【答案】\s*(.*)', answer_str)
                answer = match.group(1).strip()
                item = {
                    "img": img_name,
                    "img_path": os.path.join('ques_images', img_name),
                    "analysis": answer_str,
                    "answer": answer,
                    "solid_mats": collect_solid_mats([np.array(item['mat'])])
                }
                opf.write(json.dumps(item, ensure_ascii=False) + "\n")
                
                success += 1

            except Exception as e:
                print(f"error: {type(e).__name__} | {str(e)}")
                error += 1
                
            pbar.update(1)

    print(f"total: {total} | success:{success} | error:{error}")

if __name__ == "__main__":
    json_file = './test_data.jsonl'
    view = '上面'
    choose_task(json_file,view)

    

