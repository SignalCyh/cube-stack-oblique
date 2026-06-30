import json
import os

from tqdm import tqdm
from matrix2xy45 import CubeStacking

DEFAULT_FILL = "#E5E5E5"
DEFAULT_EDGE = "black"

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir) 

def txt_png(file,dim3:str,save_dir=current_dir):
    save_dir_1 = os.path.join(save_dir, '2D')
    os.makedirs(save_dir_1,exist_ok=True)
    save_dir_2 = os.path.join(save_dir, '3D')
    os.makedirs(save_dir_2,exist_ok=True)
    save_dir_3 = os.path.join(save_dir, '23D')
    os.makedirs(save_dir_3,exist_ok=True)

    num = sum(1 for _ in open(file, 'r', encoding='utf-8'))
    with tqdm(total=num) as pbar, \
        open(file, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line: continue

            name = f'mat{dim3}_{idx}.png'
            save_path_1 = os.path.join(save_dir_1, name)
            save_path_2 = os.path.join(save_dir_2, name)
            save_path_3 = os.path.join(save_dir_3, name)
            cubes = CubeStacking(eval(line))

            cubes.save_2D(save_path_1)
            cubes.save_3D(save_path_2)
            cubes.save_23D(save_path_3)
            pbar.update(1)

def json_png(file,save_dir=current_dir):
    save_dir_1 = os.path.join(save_dir, '2D')
    os.makedirs(save_dir_1,exist_ok=True)
    save_dir_2 = os.path.join(save_dir, '3D')
    os.makedirs(save_dir_2,exist_ok=True)
    save_dir_3 = os.path.join(save_dir, '23D')
    os.makedirs(save_dir_3,exist_ok=True)

    num = sum(1 for _ in open(file, 'r', encoding='utf-8'))
    with tqdm(total=num) as pbar, \
        open(file, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line: continue

            item = json.loads(line)
            name = item["img"]
            save_path_1 = os.path.join(save_dir_1, name)
            save_path_2 = os.path.join(save_dir_2, name)
            save_path_3 = os.path.join(save_dir_3, name)
            cubes = CubeStacking(item['mat'])

            cubes.save_2D(save_path_1)
            cubes.save_3D(save_path_2)
            cubes.save_23D(save_path_3)
            pbar.update(1)

if __name__ == "__main__":
    
    # txt_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\legal_100.txt'
    # txt_png(txt_file,'333',os.path.join(current_dir, 'output_333'))

    # json_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x4x3_40176\mat_243_data_final.jsonl'
    # json_png(json_file,os.path.join(current_dir, 'output/output_243'))

    # json_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_4x2x3_40176\mat_423_data_final.jsonl'
    # json_png(json_file,os.path.join(current_dir, 'output/output_423'))

    json_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x2x4_548\mat_224_data_final.jsonl'
    json_png(json_file,os.path.join(current_dir, 'output/output_224'))