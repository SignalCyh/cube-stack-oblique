# 第二类选择题试题组生成 正面 右面

import json
import random
import math
import mmh3
import time
import os

from collections import Counter
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)

# ====================== 配置 ======================
QUESTION_NUM = 500000               # 最终试题数量
VIEW = 'front'                      # front right
INPUT_JSONL = r"C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\output\mat_333_data.jsonl"
OUTPUT_JSONL = os.path.join(current_dir, f'choose_{VIEW}_{QUESTION_NUM}.jsonl')
GROUP_SIZE = 4
MAX_DIFF = 3
MAX_WAIT_SECONDS_PER_ATTEMPT = 10   # 单次尝试最大等待时间(s)
# ====================================================

# ====================== 布隆过滤器 ======================
class BloomFilter:
    def __init__(self, capacity=10000000, error_rate=0.00001):
        """
        布隆过滤器
        :param capacity: 预计存储元素数量
        :param error_rate: 期望误判率（如 0.00001 = 万分之一）
        """
        self.capacity = capacity
        self.error_rate = error_rate

        # 计算最优位数组大小 和 最优哈希函数个数
        self.bit_size = self.get_bit_size(capacity, error_rate)
        self.hash_count = self.get_hash_count(self.bit_size, capacity)

        # 用 int 数组存储 bit（每个 int 32位，节省内存）
        self.bits = [0] * ((self.bit_size + 31) // 32)

        self.count = 0

    def get_bit_size(self, n, p):
        """
        计算最优 bit 数
        公式：m = -n * ln(p) / (ln2)^2
        """
        return int(-n * math.log(p) / (math.log(2) ** 2))

    def get_hash_count(self, m, n):
        """
        计算最优哈希函数数量
        公式：k = m/n * ln2
        """
        return max(1, int((m / n) * math.log(2)))

    def add(self, key):
        """添加元素到布隆过滤器"""
        key = str(key).encode()  # 统一转 bytes
        for i in range(self.hash_count):
            h = mmh3.hash(key, i) % self.bit_size
            self.bits[h // 32] |= 1 << (h % 32)

    def exists(self, key):
        """判断元素是否存在（可能存在误判）"""
        key = str(key).encode()
        for i in range(self.hash_count):
            h = mmh3.hash(key, i) % self.bit_size
            if not (self.bits[h // 32] & (1 << (h % 32))):
                return False
        return True

bloom = BloomFilter(capacity=1500000)

# ====================== 工具函数 ======================
def load_jsonl(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            item = json.loads(line)
            if "id" in item and "num" in item and isinstance(item.get("mat"), list):
                data.append(item)
    print(f"{file_path} load successfully: {len(data)}")
    return data

def is_group_valid(group):
    """独立校验: mat 不能全相同"""
    n = len(group)
    diff = group[n-1]['num'] - group[0]['num']
    mats = [tuple(g["view_mat"][f'{VIEW}_1dim']) for g in group]
    return len(set(mats)) != 1 and diff <= MAX_DIFF

def build_output(group):
    """输出唯一矩阵"""
    all_lists = []
    for elem in group:
        lst = elem["view_mat"][f'{VIEW}_1dim']
        all_lists.append(lst)
    cnt = Counter(tuple(lst) for lst in all_lists)
    unique_lists = [list(k) for k, v in cnt.items() if v == 1]

    result = {
        "id": [g["id"] for g in group],
        "unique_mat": unique_lists
    }
    num = len(unique_lists)

    return result, num

def get_group_key(group):
    """生成组唯一key(排序id) 用于全局去重"""
    return ",".join(map(str, sorted(g["id"] for g in group)))

# ====================== 核心处理 ======================
def process_final():

    data = load_jsonl(INPUT_JSONL)
    sorted_data = sorted(data, key=lambda x: x["num"])
    n = len(sorted_data)

    i = 0
    ques = 0
    with tqdm(total=QUESTION_NUM) as pbar, \
        open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        
        attempt_start = time.time()
        while i < QUESTION_NUM:
            if time.time() - attempt_start > MAX_WAIT_SECONDS_PER_ATTEMPT:
                print(f"\n⚠️  单次尝试超过 {MAX_WAIT_SECONDS_PER_ATTEMPT}s 未找到有效组合，退出")
                break

            indices = sorted(random.sample(range(n), 4))
            g = [sorted_data[k] for k in indices]
            key = get_group_key(g)

            if not bloom.exists(key):
                bloom.add(key)

                if is_group_valid(g):
                    data, num = build_output(g)
                    if num != 0:
                        f.write(json.dumps(data, ensure_ascii=False) + "\n")
                        i += 1
                        ques += num
                        pbar.update(1)
                        attempt_start = time.time()

    print(f"Group {QUESTION_NUM} : Question {ques}")

# ====================== 执行 ======================
if __name__ == "__main__":
    process_final()