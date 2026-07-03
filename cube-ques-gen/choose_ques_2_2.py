# 第二类选择题 step2

import json
import os
import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('Agg')

from tqdm import tqdm 

from CubeStyle import CubeStyle, CubeStacking, mat2pic
from FontStyle import plt_use_random_font

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


def choose_2_question_step2(item,view, save_path, figsize=(5, 2), dpi=200):
    plt_use_random_font(verbose=False)
    plt.figure(figsize=figsize, dpi=dpi)
    ques_text = f'右图图形是由（  ） 中立体堆叠图从{view}观察得到。'
    plt.figtext(0.02, 0.80, ques_text, ha="left", va="top", fontsize=9, linespacing=1.3)

    option = item['img3d']
    answer_2d = item['img2d']

    gs = plt.GridSpec(1, 5, width_ratios=[1,1,1,1,1.2], wspace=0.3)
    style = CubeStyle.random()

    for i in range(4):
        ax = plt.subplot(gs[i])
        cubes = CubeStacking(option[i],style = style)
        cubes.draw_3D(ax)
        ax.text(-0.12, 0.1, f'{chr(65+i)}.', fontsize=9, transform=ax.transAxes, va='bottom', ha='left')

    ax2 = plt.subplot(gs[4])
    mat2pic(ax2, answer_2d, len(answer_2d[0]), len(answer_2d), style)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    plt.savefig(
        save_path, 
        dpi=dpi, 
        bbox_inches="tight"
    )
    plt.close()


def ques_task(jsonl_path,view):

    save_dir = os.path.join(current_dir,f'第二类选择题_{view}')
    os.makedirs(save_dir, exist_ok=True)

    output_path = os.path.join(save_dir,f'第二类选择题_{view}.jsonl')
    img_dir = os.path.join(save_dir, 'ques_images')
    os.makedirs(img_dir, exist_ok=True)

    total = sum(1 for _ in open(jsonl_path, 'r', encoding='utf-8'))
    success = 0
    error= 0
    with tqdm(total=total) as pbar, \
        open(jsonl_path, 'r', encoding='utf-8') as f,\
        open(output_path, 'w', encoding='utf-8') as opf:
        for idx, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            if idx > 10: break
            try:
                item = json.loads(line)
                img_name = f"第二类选择题_{view}_{idx}.png"

                choose_2_question_step2(item,view, os.path.join(img_dir, img_name))

                solid_mats = collect_solid_mats(item['img3d'])
                item = {
                    "img": img_name,
                    "img_path": os.path.join('ques_images', img_name),
                    "analysis": item['analysis'],
                    "answer": item['answer'],
                    "solid_mats": solid_mats
                }
                opf.write(json.dumps(item, ensure_ascii=False) + "\n")
                success+=1

            except Exception as e:
                error += 1
                print(f"error: {type(e).__name__} | {str(e)}")
                
            pbar.update(1)
    
    print(f'total:{total} | success:{success} | error:{error}')

if __name__ == "__main__":

    jsonl_path = './front_100000.jsonl'
    view = '正面'           # 正面 右面
    ques_task(jsonl_path, view)
