# 第一类判断题生成

import os
import json
import textwrap
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)
image_dir = os.path.join(current_dir,'legal_images')

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

def tof_question(item,save_path,figsize=(3,3),dpi=150):
    """判断题"""
    title_text="下面立体图由小正方体堆叠形成，其从正面和右面看到的图形是否相同____（填“是”或“否”）"
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_aspect('equal')
    ax.set_axis_off()

    img_path = os.path.join(image_dir,item["img"])
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

if __name__ == "__main__":
    # 文件生成
    save_dir = os.path.join(current_dir,'test')

    img_dir = os.path.join(save_dir, 'ques_images')
    os.makedirs(img_dir, exist_ok=True)
    txt_dir = os.path.join(save_dir, 'txt')
    os.makedirs(txt_dir, exist_ok=True)
    image_dir = os.path.join(current_dir,'legal_images')
    os.makedirs(save_dir, exist_ok=True)

    
    opf_path = os.path.join(save_dir,f'第一类填空题.jsonl')
    json_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\test_200.jsonl'
    question = 0
    error= 0
    with open(json_file, 'r', encoding='utf-8') as f,\
        open(opf_path, 'w', encoding='utf-8') as opf:
        for i, line in enumerate(f,start=1):
            if i > 1:
                break
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                img_name = f"第一类判断题_{i}.png"
                tof_question(item, os.path.join(img_dir,f"第一类判断题_{i}.png"))
                answer_str, answer = tof_question_analysis(item, os.path.join(txt_dir,f"第一类判断题_{i}_解析.txt"))
                question += 1

                item = {
                    "img": img_name,
                    "img_path": os.path.join('ques_images', img_name),
                    "analysis": answer_str,
                    "answer": answer
                }
                opf.write(json.dumps(item, ensure_ascii=False) + "\n")
                print(f"✅ 第{i}题 已生成")
            except:
                error += 1

    print(f'question:{question} | error:{error}')