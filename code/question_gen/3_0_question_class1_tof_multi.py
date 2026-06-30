# 多线程生成第一类判断题

import os
import json
import textwrap
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from multiprocessing import Pool
from tqdm import tqdm 

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)

DATA_DIR = os.path.join(current_dir,'legal_images')
SAVE_DIR = os.path.join(current_dir,'第一类判断题')

IMAGE_DIR = os.path.join(SAVE_DIR,'ques_images')
TXT_DIR = os.path.join(SAVE_DIR,'txt')
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

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

def tof_question(item,save_path,figsize=(3, 3),dpi=150):
    """判断题"""
    title_text="下面立体图由小正方体堆叠形成，其从正面和右面看到的图形是否相同____（填“是”或“否”）"
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_aspect('equal')
    ax.set_axis_off()

    img_path = os.path.join(DATA_DIR,item["img"])
    load_img(ax, img_path)
    ax.axis("off")

    plt.figtext(0.5, 0.93, title_text, ha="center", fontsize=12)

    plt.subplots_adjust(top=0.88)
    plt.savefig(save_path, dpi=200, bbox_inches="tight", pad_inches=0.1)
    plt.close()

def tof_question_analysis(item, save_path):
    """判断题解析生成"""
    front = textwrap.indent(item['view_text']['f_text'], ' ')
    right = textwrap.indent(item['view_text']['r_text'], ' ')
    answer = item['fr_diff']
    
    tof = '相同' if answer else '不相同'
    ans_str = '是' if answer else '否'

    analysis = [
        '【分析】',
        ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，从不同方向观察立体图形。',
        ' 解题思路：依次从正面和右面观察图形特征，从行、列、个数多个角度比较图形是否相同。\n',
        '【解答】',
        f' 解：从正面看：\n{front}\n',
        f' 从右面看：\n{right}\n',
        f' 所以，该立体图从正面和右面观察到的图形{tof}。'
        f"\n【答案】 {ans_str}"
    ]
    
    analysis_str = '\n'.join(analysis)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)
        
    return analysis_str, ans_str

def process_task(args):
    idx, line = args
    try:
        item = json.loads(line)
        img_name = f"第一类判断题_{idx}.png"
        tof_question(item, os.path.join(IMAGE_DIR,img_name))
        tof_question_analysis(item, os.path.join(TXT_DIR,f"第一类判断题_{idx}_解析.txt"))
        return True
    
    except Exception as e:
        print(f" 第{idx}题 失败: {str(e)}")
        return False

# ===================== 主程序 =====================
if __name__ == "__main__":

    jsonl_path = r'C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\output\mat_333_data.jsonl'

    with open(jsonl_path, "r", encoding="utf-8") as f:
        # lines = [line.strip() for i,line in enumerate(f) if line.strip() and i < 1000]
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