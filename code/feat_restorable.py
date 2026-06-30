import json
from collections import defaultdict

input = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x2x4_548\mat_224_data_fix.jsonl'
output = r'C:\Users\yhcheng24\Desktop\yhcheng24\Code\cube-stack-oblique\data\mat_2x2x4_548\mat_224_data_final.jsonl'

def add_restorable_keep_order(input_path: str, output_path: str):
    group_id_list = defaultdict(list)

    # 第一次遍历：统计每个分组
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                uid = obj["id"]
                # 序列化二维数组作为分组key
                key_a = json.dumps(obj["f_mat"], sort_keys=True)
                key_b = json.dumps(obj["r_mat"], sort_keys=True)
                key_c = json.dumps(obj["t_mat"], sort_keys=True)
                group_key = (key_a, key_b, key_c)
                group_id_list[group_key].append(uid)
            except (KeyError, json.JSONDecodeError):
                continue

    # 第二次遍历：追加restorable
    with open(input_path, "r", encoding="utf-8") as f_in,\
        open(output_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            raw_line = line.strip()
            if not raw_line:
                continue
            try:
                data = json.loads(raw_line)
                key_a = json.dumps(data["f_mat"], sort_keys=True)
                key_b = json.dumps(data["r_mat"], sort_keys=True)
                key_c = json.dumps(data["t_mat"], sort_keys=True)
                gk = (key_a, key_b, key_c)
                # 绑定本组所有id
                data["restorable"] = group_id_list[gk]
                f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
            except (KeyError, json.JSONDecodeError):
                # 损坏/缺字段行直接跳过，不输出
                continue

if __name__ == "__main__":
    add_restorable_keep_order(input, output)