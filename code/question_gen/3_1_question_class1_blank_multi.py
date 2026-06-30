# 多线程生成第一类填空题

import json
import os
import random
import textwrap

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from multiprocessing import Pool
from tqdm import tqdm  # 进度条（可选）

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)

DATA_DIR = os.path.join(current_dir,'legal_images')
SAVE_DIR = os.path.join(current_dir,'第一类填空题')

IMAGE_DIR = os.path.join(SAVE_DIR,'ques_images')
TXT_DIR = os.path.join(SAVE_DIR,'txt')
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

DEFAULT_FILL = "#E5E5E5"
DEFAULT_EDGE = "black"
MAX_LEN = 3

def move_xy_all0(mat):
    """去除整行(列)为空的行(列)"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

def mat2pic(ax, mat, scale = 0.7, line_w = 0.7, offsety = 0.5):
    """二维分布图绘制"""
    valid = move_xy_all0(mat[::-1].T)
    row, col = valid.shape
    ax.set_aspect("equal")
    ax.axis("off")

    offsetx = (MAX_LEN - row*scale)/2
    ax.set_xlim(0, MAX_LEN)
    ax.set_ylim(0, MAX_LEN)
    
    for i in range(row):
        for j in range(col):
            if valid[i, j] > 0:
                x0 = offsetx + i * scale
                y0 = offsety + j * scale
                rect = plt.Rectangle(
                    (x0, y0), 
                    scale, scale, 
                    facecolor=DEFAULT_FILL, 
                    edgecolor=DEFAULT_EDGE, 
                    linewidth=line_w
                    )
                ax.add_patch(rect)

def blank_1_question(item, save_path, figsize=(6, 3), dpi=200):
    ques_text = f'右图立体图形由若干小正方体堆叠而成，从“正面”、“上面”、“右面”中选择正确答案填入对应括号。'
    plt.figure(figsize=figsize, dpi=dpi)
    plt.figtext(
        0.02, 0.80, 
        ques_text, 
        ha="left", va="top", 
        fontsize=9, 
        linespacing=1.3
    )

    order = ['正面','右面','上面']
    shuffled = order.copy()
    random.shuffle(shuffled)

    def drawview(ax,view:str):
        if view == '正面':
            mat2pic(ax, np.array(item['view_mat']['front_2dim']))
        elif view == '右面':
            mat2pic(ax, np.array(item['view_mat']['right_2dim']))
        elif view == '上面':
            mat2pic(ax, np.array(item['view_mat']['top_2dim']))


    gs = plt.GridSpec(1, 4, width_ratios=[1,1,1,1.2], wspace=0.3)

    ax1 = plt.subplot(gs[0])
    drawview(ax1, shuffled[0])
    ax1.text(0.5, -0.1, '（     ）', fontsize=9, transform=ax1.transAxes, va='bottom', ha='center')

    ax2 = plt.subplot(gs[1])
    drawview(ax2, shuffled[1])
    ax2.text(0.5, -0.1, '（     ）', fontsize=9, transform=ax2.transAxes, va='bottom', ha='center')

    ax3 = plt.subplot(gs[2])
    drawview(ax3, shuffled[2])
    ax3.text(0.5, -0.1, '（     ）', fontsize=9, transform=ax3.transAxes, va='bottom', ha='center')

    ax4 = plt.subplot(gs[3])
    img_path = os.path.join(DATA_DIR, item["img"])
    img = mpimg.imread(img_path)

    h, w = img.shape[:2]
    max_size = 348
    scale = min(max_size / w, max_size / h)
    new_w = w * scale
    new_h = h * scale

    offset_x = (max_size - new_w) / 2
    offset_y = (max_size - new_h) / 2

    ax4.set_xlim(0, max_size)
    ax4.set_ylim(0, max_size)
    ax4.axis("off")
    ax4.set_aspect("equal")

    ax4.imshow(
        img,
        extent=[offset_x, offset_x+new_w, offset_y, offset_y+new_h],
        origin="upper"
    )

    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    plt.savefig(
        save_path, 
        dpi=dpi, 
        bbox_inches="tight"
    )
    plt.close()

    return shuffled

def blank_1_question_analysis(item, answer, save_path):

    top = textwrap.indent(item['view_text']['t_text'], ' ')
    front = textwrap.indent(item['view_text']['f_text'], ' ')
    right = textwrap.indent(item['view_text']['r_text'], ' ')
    
    ans_str = ' '.join([f'（{view}）' for view in answer])

    analysis = [
        '【分析】',
        ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，从不同方向观察立体图形。',
        f' 解题思路：依次从正面，右面，上面观察图形特征，与选项进行比对，填入正确答案。\n',
        '【解答】',
        f' 解：从正面看：{front}\n 与第{answer.index('正面') + 1}个图形相符合。',
        f'  从右面看：{right}\n 与第{answer.index('右面') + 1}个图形相符合。',
        f'  从上面看：{top}\n 与第{answer.index('上面') + 1}个图形相符合。',
        f"  所以，在括号中依次填入{'，'.join(answer)}。",
        f"\n【答案】 {ans_str}"
    ]
    
    analysis_str = '\n'.join(analysis)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)
        
    return analysis_str 

def process_task(args):
    idx, line = args
    try:
        item = json.loads(line)
        if item['frt_diff']:
            img_name = f"第一类填空题_{idx}.png"
            answer = blank_1_question(item,os.path.join(IMAGE_DIR,img_name))
            blank_1_question_analysis(item, answer, os.path.join(TXT_DIR,f"第一类填空题_{idx}_解析.txt"))
            return True
        else:
            return False
    except Exception as e:
        print(f" 第{idx}题 失败: {str(e)}")
        return False

# ===================== 主程序 =====================
if __name__ == "__main__":

    jsonl_path = r'C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\output\mat_333_data.jsonl'

    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    tasks = [(i+1, line) for i, line in enumerate(lines)]

    total = len(tasks)
    print(f"total: {total}")

    # processes=os.cpu_count()
    with Pool(processes=8) as pool:
        results = list(tqdm(
            pool.imap(process_task, tasks),
            total=total
        ))

    success = sum(results)
    print(f"\nsuccess = {success}")