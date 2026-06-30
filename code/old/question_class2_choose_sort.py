import json
import random
import math
import mmh3

from itertools import combinations
from collections import Counter
from tqdm import tqdm

# ====================== 配置 ======================
INPUT_JSONL = r"C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\test_200.jsonl"
OUTPUT_JSONL = "result.jsonl"
GROUP_SIZE = 4
MAX_DIFF = 3
FULL_COMBI_MAX = 15
RANDOM_SAMPLE_CNT = 50000  # 每个大窗口抽样数量uhhassg
QUESTION_NUM = 200000 # 最终试题至少数量
VIEW = 'front_1dim'
# ====================================================

# ====================== 布隆过滤器（全局去重，零内存） ======================
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
        import math
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

    def __len__(self):
        """返回已存入数据"""
        return self.count

# 全局唯一布隆过滤器
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
    mats = [tuple(g["view_mat"][f'{VIEW}']) for g in group]
    return len(set(mats)) != 1

def build_output(group):
    """输出唯一矩阵"""
    all_lists = []
    for elem in group:
        lst = elem["view_mat"][f'{VIEW}']
        all_lists.append(lst)
    cnt = Counter(tuple(lst) for lst in all_lists)
    unique_lists = [list(k) for k, v in cnt.items() if v == 1]

    return {
        "id": [g["id"] for g in group],
        "unique_mat": unique_lists
    }

def get_group_key(group):
    """生成组唯一key(排序id) 用于全局去重"""
    return ",".join(map(str, sorted(g["id"] for g in group)))

# ====================== 核心处理 ======================
def process_final():

    data = load_jsonl(INPUT_JSONL)
    sorted_data = sorted(data, key=lambda x: x["num"])
    n = len(sorted_data)
    i = 0

    pbar = tqdm(total=28)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        while i < n:
            current_num = sorted_data[i]["num"]
            max_allow = current_num + MAX_DIFF

            # 定位合法窗口
            j = i
            while j < n and sorted_data[j]["num"] <= max_allow:
                j += 1
            window = sorted_data[i:j]
            w_len = len(window)

            if w_len < 4:
                i = j
                continue

            # --------------------
            # 小窗口：全组合
            # --------------------
            if w_len <= FULL_COMBI_MAX:
                for g in combinations(window, 4):
                    key = get_group_key(g)
                    if not bloom.exists(key):
                        if is_group_valid(g):
                            bloom.add(key)
                            f.write(json.dumps(build_output(g), ensure_ascii=False) + "\n")

            # --------------------
            # 大窗口：随机5w条
            # --------------------
            else:
                count = 0
                while count < RANDOM_SAMPLE_CNT:
                    # 随机取4个不重复元素
                    indices = sorted(random.sample(range(w_len), 4))
                    g = [window[k] for k in indices]
                    key = get_group_key(g)

                    if not bloom.exists(key):
                        bloom.add(key)
                        if is_group_valid(g):
                            f.write(json.dumps(build_output(g), ensure_ascii=False) + "\n")
                            count += 1
            i = j
            pbar.update(j-i)
            # if len(bloom) > QUESTION_NUM:
            #     break

    print(f"count: {len(bloom)}")

# ====================== 执行 ======================
if __name__ == "__main__":
    process_final()