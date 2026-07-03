import json
import re
import os
from pathlib import Path
from tqdm import tqdm 

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)

# ===================== 配置项 =====================
TXT_FOLDER = r"C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\第二类选择题_正面\txt"
IMAGE_FOLDER = r"C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\第二类选择题_正面\ques_images"
OUTPUT_JSONL = "第二类选择题_正面_100000.jsonl"     # 输出文件名
QUESTION = '第二类选择题_正面'
# ==================================================

def txt_to_jsonl(txt_folder, output_path):
    # 确保文件夹存在
    folder = Path(txt_folder)
    if not folder.exists():
        print(f"ERROR: {txt_folder} not found")
        return

    total = 0
    skip = 0
    error = 0
    with open(output_path, "w", encoding="utf-8") as out_f:
        for id in tqdm(range(1, 100001)):
            txt_path = os.path.join(TXT_FOLDER, f'{QUESTION}_{id}_解析.txt' )
            img = f'{QUESTION}_{id}.png'
            img_path = os.path.join(IMAGE_FOLDER, f'{QUESTION}_{id}.png')
            if not os.path.exists(txt_path) and not os.path.exists(img_path):
                skip += 1
                continue
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    answer_str = f.read()
                match = re.search(r'【答案】\s*(.*)', answer_str)
                answer = match.group(1).strip()
                item = {
                    "img": img,
                    "img_path": os.path.join('ques_images', img),
                    "analysis": answer_str,
                    "answer": answer
                }
                out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                total += 1

            except Exception as e:
                error += 1
                print(f"skip {txt_path} for reason: {str(e)}")

    print(f"skip: {skip} | total: {total} | error: {error} | save to {output_path}")

if __name__ == "__main__":
    txt_to_jsonl(TXT_FOLDER, OUTPUT_JSONL)