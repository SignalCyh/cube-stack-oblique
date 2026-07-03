# 计数题生成（运行时绘图）- 多线程版本
import os
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import matplotlib.pyplot as plt
import numpy as np

from tqdm import tqdm

plt.switch_backend('Agg')

from CubeStyle import CubeStacking, CubeStyle
from FontStyle import plt_use_random_font


current_dir = os.path.dirname(os.path.abspath(__file__))  # 当前py脚本目录
os.chdir(current_dir)

# 全局锁：解决文件写入和matplotlib可能的资源竞争
file_lock = threading.Lock()
plot_lock = threading.Lock()


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
        for idx, cnt in enumerate(counts, start=1):
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
    for i in range(1, h + 1):
        if counts[i] != 0:
            total += i * counts[i]
            exp.append(f'{i} × {counts[i]}')
            analysis += f'，高度为{i}的正方体堆叠有{counts[i]}个'
    analysis += f'。\n  所以共有{" + ".join(exp)} = {total}个小正方体。'
    return analysis


def cnt_question(height_mat, save_path, figsize=(3, 3), dpi=200):
    """计数题绘图（加锁避免多线程绘图冲突）"""
    with plot_lock:
        title_text="下面立体图由小正方体堆叠形成，请统计图像中的正方体个数。"
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        style = CubeStyle.random()
        cubes = CubeStacking(height_mat, style=style)
        fig = cubes.draw_3D(ax)

        plt.figtext(0.5, 0.93, title_text, ha="center", fontsize=12)
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
    # 写入文件加锁，避免多线程同时写文件
    with file_lock:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(analysis_str)
    return analysis_str


def process_single_item(line, idx, img_dir, txt_dir):
    """处理单个数据项（供线程池调用）"""
    try:
        line = line.strip()
        if not line:
            return None, False
        
        plt_use_random_font(verbose=False)
        item = json.loads(line)
        id = item["id"]
        mat = np.array(item["mat"])

        # 生成图片和解析文件
        img_name = f"计数题_{id}.png"
        cnt_question(mat, os.path.join(img_dir, img_name))
        answer_str = cnt_question_analysis(mat, os.path.join(txt_dir, f"计数题_{id}_解析.txt"))

        # 提取答案
        match = re.search(r'【答案】\s*(.*)', answer_str)
        answer = match.group(1).strip()
        result_item = {
            "img": img_name,
            "img_path": os.path.join('ques_images', img_name),
            "analysis": answer_str,
            "answer": answer,
            "solid_mats": collect_solid_mats([np.array(item['mat'])])
        }
        return result_item, True
    except Exception as e:
        print(f"Error processing item {idx}: {type(e).__name__} | {str(e)}")
        return None, False


def cnt_task(file_path, task_thread=4):
    """多线程版本的计数题生成任务"""
    save_dir = os.path.join(current_dir, '计数题')
    os.makedirs(save_dir, exist_ok=True)

    jsonl_path = os.path.join(save_dir, f'计数题.jsonl')
    img_dir = os.path.join(save_dir, 'ques_images')
    os.makedirs(img_dir, exist_ok=True)
    txt_dir = os.path.join(save_dir, 'txt')
    os.makedirs(txt_dir, exist_ok=True)

    # 先读取所有行，避免多线程读取文件冲突
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    total = len(lines)
    success = 0
    error = 0

    # 创建线程池并处理任务
    with ThreadPoolExecutor(max_workers=task_thread) as executor, \
            open(jsonl_path, 'w', encoding='utf-8') as opf, \
            tqdm(total=total) as pbar:

        # 提交所有任务
        future_to_idx = {
            executor.submit(process_single_item, line, idx, img_dir, txt_dir): idx
            for idx, line in enumerate(lines, start=1)
        }

        # 处理完成的任务
        for future in as_completed(future_to_idx):
            result_item, is_success = future.result()
            if is_success and result_item:
                # 写入JSONL加锁，避免多线程写入冲突
                with file_lock:
                    opf.write(json.dumps(result_item, ensure_ascii=False) + "\n")
                success += 1
            else:
                error += 1
            pbar.update(1)

    print(f"Total: {total} | Success: {success} | Error: {error}")


if __name__ == "__main__":
    json_file = r'./test_data.jsonl'
    cnt_task(json_file, task_thread=4)