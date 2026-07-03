# 第二类选择题 step1

import json
import os
import random
import textwrap
import numpy as np
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)
EN_DIC ={
    '正面': 'front',
    '右面': 'right'
}

def lst2mat(arr):
    """一维堆叠序列立体化"""
    lst = np.array(arr)
    n = lst.max()
    i = np.arange(n-1, -1, -1)[:, None]
    return (lst > i).astype(int).tolist()

def load_jsonl(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            item = json.loads(line)
            data.append(item)   
    print(f"{file_path} load successfully: {len(data)}")
    return data

def choose_2_question_analysis(mat333, idlst, answer,view):

    text = ''
    if view == '右面':
        x = 'r_text'
    elif view == '正面':
        x = 'f_text'
        
    for i, id in enumerate(idlst):
        text += f"  选项{chr(65+i)}: {textwrap.indent(mat333[id-1]['view_text'][x], '  ')}\n"

    analysis = [
        '【分析】',
        f' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，正确获得{view}观察到的图形。',
        f' 解题思路：依次从对各个选项从{view}观察图形特征，与右图进行比对。\n',
        '【解答】',
        f' 解：{text}',
        f"  所以，选项{answer}能够从{view}观察到正确的图像。",
        f"\n【答案】 {answer}"
    ]
        
    return '\n'.join(analysis)

def ques_task(data_path, input_path, view):
    
    mat333 = load_jsonl(data_path)
    output_file = os.path.join(current_dir, f'{EN_DIC[view]}_100000.jsonl')

    total = 0

    with open(input_path, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
        
    with open(input_path, "r", encoding="utf-8") as f,\
        open(output_file, 'w', encoding='utf-8') as opf:
        for idx, line in tqdm(enumerate(f,1), total=total_lines):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            idlst = item["id"]
            mat = item["unique_mat"][-1]

            indices = list(range(len(idlst)))
            random.shuffle(indices)
            shuffled = [idlst[i] for i in indices]

            answer = ''
            for id in shuffled:
                if mat333[id-1]["view_mat"][f'{EN_DIC[view]}_1dim'] == mat:
                    answer = chr(shuffled.index(id)+65)

            img3d = []
            for id in shuffled:
                img3d.append(mat333[id-1]['mat'])

            analysis = choose_2_question_analysis(mat333, shuffled, answer, view)

            data = {
                "img3d": img3d,
                "img2d": lst2mat(mat),
                "analysis": analysis,
                "answer": answer
            }

            opf.write(json.dumps(data, ensure_ascii=False) + '\n')
            total += 1

    print(f"total: {total}")



# ===================== 主程序 =====================
if __name__ == "__main__":
    view = '正面'  # 正面 右面
    data_path = './mat_333_data.jsonl'
    input_path = f'./random_{EN_DIC[view]}_100000.jsonl'
    ques_task(data_path,input_path,view)