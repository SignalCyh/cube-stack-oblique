# 多线程生成第二类选择题 step1

import json
import os
import random
import textwrap
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)

VIEW = '正面'           # 正面 右面


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

def choose_2_question_analysis(mat333, idlst, answer):

    text = ''
    if VIEW == '右面':
        x = 'r_text'
    elif VIEW == '正面':
        x = 'f_text'
        
    for i, id in enumerate(idlst):
        text += f"  选项{chr(65+i)}: {textwrap.indent(mat333[id-1]['view_text'][x], '  ')}\n"

    analysis = [
        '【分析】',
        f' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，正确获得{VIEW}观察到的图形。',
        f' 解题思路：依次从对各个选项从{VIEW}观察图形特征，与右图进行比对。\n',
        '【解答】',
        f' 解：{text}',
        f"  所以，选项{answer}能够从{VIEW}观察到正确的图像。",
        f"\n【答案】 {answer}"
    ]
        
    return '\n'.join(analysis)

# ===================== 主程序 =====================
if __name__ == "__main__":
    
    mat333 = load_jsonl(r'C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\output\mat_333_data.jsonl')

    jsonl_path = r'C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\front_100000.jsonl'

    save_dir = os.path.join(current_dir, 'output')
    os.makedirs(save_dir, exist_ok=True)
    output_file = os.path.join(save_dir, f'front_100000.jsonl')

    total = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
        
    with open(jsonl_path, "r", encoding="utf-8") as f,\
        open(output_file, 'w', encoding='utf-8') as opf:
        for idx, line in tqdm(enumerate(f,1), total=total_lines):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            idlst = item["id"]
            mat = item["unique_mat"][0]

            indices = list(range(len(idlst)))
            random.shuffle(indices)
            shuffled = [idlst[i] for i in indices]

            answer = ''
            if VIEW == '右面':
                x = 'right_1dim'
            elif VIEW == '正面':
                x = 'front_1dim'
            for id in shuffled:
                if mat333[id-1]["view_mat"][x] == mat:
                    answer = chr(shuffled.index(id)+65)

            images = []
            for id in shuffled:
                images.append(f"mat_333_{id}.png")

            analysis = choose_2_question_analysis(mat333, shuffled, answer)

            data = {
                "img": images,
                "lst": mat,
                "analysis": analysis,
                "answer": answer
            }

            opf.write(json.dumps(data, ensure_ascii=False) + '\n')
            total += 1

    print(f"total: {total}")
