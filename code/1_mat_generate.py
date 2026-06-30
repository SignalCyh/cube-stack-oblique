import os
import itertools
import numpy as np

from collections import deque, defaultdict

current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir)

# 方向：四连通
DIRS = [(-1,0), (1,0), (0,-1), (0,1)]
MAX_COLS = 4
MAX_ROWS = 4
MAX_HEIGHT = 3 

def normalize(cells):
    """归一化：贴左上角"""
    min_x = min(x for x, y in cells)
    min_y = min(y for x, y in cells)
    return tuple(sorted((x-min_x, y-min_y) for x, y in cells))

def four_connected(cells):
    """BFS判断四连通"""
    s = set(cells)                # 转成集合，方便快速查找
    start = cells[0]              # 随便选一个起点
    visited = {start}             # 记录访问过的格子
    q = deque([start])            # BFS 队列

    while q:                      # 开始广度优先搜索
        x, y = q.popleft()        # 取出队首
        for dx, dy in DIRS:       # 遍历上下左右四个方向
            nx = x + dx
            ny = y + dy
            # 如果邻居在选中集合里，且没访问过
            if (nx, ny) in s and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny))

    # 访问到的数量 = 总数量 → 全部连通
    return len(visited) == len(cells)

def rc_limit(cells, r, c, old_r = 3, old_c = 3):
    # 限制得到差集部分
    xs, ys = zip(*cells)
    h, l = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1

    result = []
    for x in range(1, r + 1):
        for y in range(1, c + 1):
            if x > old_r or y > old_c:
                result.append((x, y))
    return (h,l) in result
    
def count_and_group(m, n):
    """主函数：统计所有平移等价连通块，并按大小分组"""
    total_cells = m * n          # 总格子数量 n²
    shape_map = {}               # key：归一化的形状 value：格子大小

    # 二进制建立 数到坐标 的映射关系
    # 示例 5 - 0101 - idx=1,3 - (1//n, 1%n), (3//n, 3%n)
    for mask in range(1, 1 << total_cells):
        cells = []
        
        for idx in range(total_cells):
            # 是否选择 第idx 个格子
            if mask & (1 << idx):
                x = idx // n       # 行号
                y = idx % n        # 列号
                cells.append((x, y))

        if not four_connected(cells):  # 不连通直接跳过
            continue

        if not rc_limit(cells, MAX_ROWS, MAX_COLS):
            continue

        norm = normalize(cells)      # 平移归一化
        size = len(cells)            # 连通块大小
        shape_map[norm] = size       # 存入字典（自动去重）

    # 按大小分组：key=大小，value=形状列表 无序字典
    groups = defaultdict(list)
    for shape, s in shape_map.items():
        groups[s].append(shape)

    return groups

def print_shape(shape):
    """打印一个形状的示意图"""
    if not shape:
        return
    max_x = max(x for x, y in shape)
    max_y = max(y for x, y in shape)
    grid = [['□']*(max_y+1) for _ in range(max_x+1)]
    for x, y in shape:
        grid[x][y] = '■'
    for row in grid:
        print(''.join(row))
    print('---')

def output_save(groups, save_dir):
    """记录所有生成矩阵"""
    with open(save_dir, "w") as f:
        for size in groups:
            shapes = groups[size]
            for shape in shapes:
                for vals in itertools.product(range(1,MAX_HEIGHT+1), repeat=len(shape)):
                    mat = np.zeros((MAX_ROWS, MAX_COLS), dtype=int)
                    for (x, y), v in zip(shape, vals):
                        mat[x][y] = v
                    mat_list = mat.tolist()
                    f.write(str(mat_list) + "\n")
    

# ==================== 运行 ====================
if __name__ == '__main__':
    groups = count_and_group(MAX_ROWS, MAX_COLS)
    print(f"===== {MAX_ROWS}x{MAX_COLS}x{MAX_HEIGHT} 平移等价四连通组 统计 =====\n")
    kind = 0
    total = 0

    for size in sorted(groups):
        shapes = groups[size]
        cnt = len(shapes)
        kind += cnt
        total += cnt*(MAX_HEIGHT**size)
        print(f"【大小 = {size}】 → 共 {cnt} 种 {cnt*(MAX_HEIGHT**size)} 个")

    save_name = os.path.join(current_dir, f'mat_{MAX_ROWS}x{MAX_COLS}x{MAX_HEIGHT}_{total}.txt')
    output_save(groups, save_name)
    print(f"\n✅ 总计：{kind} 种 {total} 个")