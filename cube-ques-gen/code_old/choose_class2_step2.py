# 多线程生成第二类选择题 step2

import json
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from multiprocessing import Pool
from tqdm import tqdm 

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)

VIEW = '右面'           # 正面 右面
DATA_DIR = os.path.join(current_dir,'legal_images')
SAVE_DIR = os.path.join(current_dir,f'第二类选择题_{VIEW}')

IMAGE_DIR = os.path.join(SAVE_DIR,'ques_images')
TXT_DIR = os.path.join(SAVE_DIR,'txt')
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

DEFAULT_FILL = "#E5E5E5"
DEFAULT_EDGE = "black"
MAX_LEN = 3


def load_img(ax, img_path, size = 348):
    """原比例载入图片"""
    img = mpimg.imread(img_path)
    h, w = img.shape[:2]
    max_size = size
    scale = min(max_size / w, max_size / h)
    new_w = w * scale
    new_h = h * scale

    offset_x = (max_size - new_w) / 2
    offset_y = (max_size - new_h) / 2

    ax.set_xlim(0, max_size)
    ax.set_ylim(0, max_size)
    ax.axis("off")
    ax.set_aspect("equal")
    ax.imshow(
        img,
        extent=[offset_x, offset_x+new_w, offset_y, offset_y+new_h],
        origin="upper"
    )

def list2pic(ax,lst,scale = 0.7, line_w = 0.7, offsety = 0.5):
    """一维堆叠图绘制"""
    n = len(lst)
    ax.set_aspect("equal")
    ax.axis("off")

    offsetx = (MAX_LEN - n*scale)/2
    ax.set_xlim(0, MAX_LEN)
    ax.set_ylim(0, MAX_LEN)

    for i in range(n):
        h = lst[i]
        for k in range(h):
            x0 = offsetx + i * scale
            y0 = offsety + k * scale
            rect = plt.Rectangle(
                (x0, y0), 
                scale, scale, 
                facecolor=DEFAULT_FILL, 
                edgecolor=DEFAULT_EDGE, 
                linewidth=line_w
            )
            ax.add_patch(rect)

def choose_2_question_step2(piclst, lst, analysis, ques_path, analysis_path, figsize=(4, 2), dpi=200):
    ques_text = f'右图图形是由（  ） 中立体堆叠图从{VIEW}观察得到。'
    plt.figure(figsize=figsize, dpi=dpi)
    plt.figtext(
        0.02, 0.80, 
        ques_text, 
        ha="left", va="top", 
        fontsize=9, 
        linespacing=1.3
    )

    gs = plt.GridSpec(1, 5, width_ratios=[1,1,1,1,1.2], wspace=0.3)

    for i in range(4):
        ax = plt.subplot(gs[i])
        load_img(ax, os.path.join(DATA_DIR, piclst[i]))
        ax.text(-0.1, 0.15, f'{chr(65+i)}.', fontsize=9, transform=ax.transAxes, va='bottom', ha='left')

    ax2 = plt.subplot(gs[4])
    list2pic(ax2, lst)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    plt.savefig(
        ques_path, 
        dpi=dpi, 
        bbox_inches="tight"
    )
    plt.close()

    with open(analysis_path, 'w', encoding='utf-8') as f:
        f.write(analysis)

def process_task(args):
    idx, line= args
    try:
        item = json.loads(line)
        piclst = item["img"]
        analysis = item["analysis"]
        lst = item["lst"]
        img_name = f"第二类选择题_{VIEW}_{idx}.png"
        choose_2_question_step2(piclst, lst, analysis, os.path.join(IMAGE_DIR,img_name), os.path.join(TXT_DIR,f"第二类选择题_{VIEW}_{idx}_解析.txt"))
        return True
    except Exception as e:
        print(f" 第{idx}题 失败: {str(e)}")
        return False

if __name__ == "__main__":

    jsonl_path = r'C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\output\第二类选择题\step1_right_100000.jsonl'

    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    # tasks = [(i+1, line) for i, line in enumerate(lines) if i < 100]
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
