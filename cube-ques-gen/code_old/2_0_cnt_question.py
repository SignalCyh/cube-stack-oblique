# 计数题生成（运行时绘图）

import os
import json

import matplotlib.pyplot as plt
import numpy as np

from tqdm import tqdm
import sys
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)
from matrix2xy45 import CubeStacking

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

def move_xy_all0(mat):
    """去除整行(列)为空的行(列)"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

def layer_analysis(height_mat):
    valid = move_xy_all0(height_mat) 
    max_h = height_mat.max()
    
    total = 0
    cnt_text = []
    layer_counts = []
    analysis = []
    
    for layer in range(1, max_h + 1):
        # 统计每一列 ≥ 当前层的数量
        cols = np.sum(valid >= layer, axis=0)
        counts = cols[cols != 0]
        # 当前层总数量
        count = counts.sum()
        layer_counts.append(count)
        total += count

        col_num = len(counts)
        col_texts = []
        col_nums = []
        for idx, cnt in enumerate(counts,start=1):
            col_texts.append(f"第{idx}列{cnt}个")
            col_nums.append(str(cnt))

        if col_num > 1:
            cnt_text.append(
                f"共有{col_num}列：{'，'.join(col_texts)}，"
                f"总计{' + '.join(col_nums)} = {count}个；"
            )
        else:
            cnt_text.append(
                f"共有{col_num}列：{'，'.join(col_texts)}，"
                f"总计{count}个；"
            )

    for i, text in enumerate(cnt_text):
        analysis.append(f"  第{i+1}层，{text}")

    layer_str = " + ".join(map(str, layer_counts))
    analysis.append(f"  所以，立体图中共有{layer_str} = {total}个小正方体。")
    analysis_str = '\n'.join(analysis)

    return analysis_str, total

def height_sort_analysis(mat):
    h = mat.max()
    counts = np.bincount(mat.ravel())
    analysis = f' 单个正方体最大堆叠高度为{h}'
    exp = []
    total = 0
    for i in range(1, h+1):
        if counts[i] != 0:
            total += i*counts[i]
            exp.append(f'{i} \u00d7 {counts[i]}')
            analysis += f'，高度为{i}的正方体堆叠有{counts[i]}个'
    analysis += f'。\n  所以共有{" + ".join(exp)} = {total}个小正方体。'
    return analysis

def cnt_question(height_mat,save_path,figsize=(3, 3),dpi=200):
    """计数题"""

    title_text="下面立体图由小正方体堆叠形成，请统计图像中的正方体个数。"
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    plt.figtext(0.5, 0.93, title_text, ha="center", fontsize=12)

    cubes = CubeStacking(height_mat)
    cubes.draw_3D(ax)

    plt.savefig(save_path, dpi=200, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)

def cnt_question_analysis(height_mat, save_path):
    """
    计数题解析生成
    :param height_mat: 高度矩阵，记录每个位置堆叠的正方体层数
    :param save_path: 保存的图片路径
    """
    # 生成分析文本
    step1, total = layer_analysis(height_mat)
    step2 = height_sort_analysis(height_mat)
    
    analysis = [
        '【分析】',
        ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，学会正确清点图片中小正方体的数量。',
        ' 解题思路：在清点此类图形时，为了避免遗漏或重复，通常采用分类计数法。\n',
        '【解答】',
        ' 方法一',
        ' 解：使用分层计数法统计个数（底层到顶层顺序）：',
        f'{step1}',
        ' 方法二',
        ' 解：根据竖直方向上正方体堆叠的高度进分类计数，从高度上来看：',
        f' {step2}',
        f"\n【答案】 {total}个"
    ]
    
    analysis_str = '\n'.join(analysis)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)

def cnt_task(file_path):
    save_dir = os.path.join(current_dir,'计数题')
    os.makedirs(save_dir, exist_ok=True)

    total = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
    success = 0
    error= 0
    with tqdm(total=total) as pbar, \
        open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            # if idx < 1000: continue
            # if idx > 1001: break
            try:
                item = json.loads(line)
                id = item["id"]
                mat = np.array(item["mat"])

                cnt_question(mat, os.path.join(save_dir,f"计数题_{id}.png"))
                cnt_question_analysis(mat, os.path.join(save_dir,f"计数题_{id}_解析.txt"))
                success += 1

            except Exception as e:
                print(f"{idx} error: {e}")
                error += 1
                
            pbar.update(1)

    print(f"total: {total} | success:{success} | error:{error}")

if __name__ == "__main__":
    json_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_3x3x3_192801\mat_333_data.jsonl'
    cnt_task(json_file)
    