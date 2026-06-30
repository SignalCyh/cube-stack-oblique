import numpy as np
import random
import os
import json
import ast
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

DEFAULT_FILL = "#E5E5E5"
DEFAULT_EDGE = "black"
MAX_LAYER = 3
MAX_LEN = 3
NUM_QUESTIONS = 1

# ===================== 区域记录器 =====================
class VisibleArea:
    def __init__(self):
        self.polygon_objs = []   # 存 Shapely 多边形对象
        self.merged_region = None  

    def add_polygon(self, polygon_coords):
        """传入多边形坐标 → 自动转 Shapely 对象"""
        poly = Polygon(polygon_coords)
        self.polygon_objs.append(poly)
        # 合并区域
        self.merged_region = unary_union(self.polygon_objs)

    def clear(self):
        self.polygon_objs.clear()
        self.merged_region = None
    
    def get_line_outside_region(self, line_coords):
        """
        计算线段在区域外的部分
        :param line_coords: 线段AB坐标 → [(x1,y1), (x2,y2)]
        :return: 区域外的线段列表(可能0/1/多条线段)
        """
        if len(line_coords) < 2:
            raise ValueError("线段坐标必须包含至少两个点")  

        if self.merged_region is None:
            # 没有任何区域 → 整条线段都在外面
            return [line_coords]

        line = LineString(line_coords)
        outside_line = line.difference(self.merged_region)
        
        if outside_line.is_empty:
            # 完全在区域内 → 不绘制
            return []  
        elif hasattr(outside_line, 'geoms'):
            # 多段外线（被切成多段）
            return [list(geom.coords) for geom in outside_line.geoms]
        else:
            # 单段外线
            return [list(outside_line.coords)]

# ===================== 斜二测投影 =====================
def oblique_projection(x, y, z):
    """原三维坐标系 横x 垂直向里y 竖z"""
    x_new = x + y * 0.5 * np.cos(np.pi / 4)
    y_new = z + y * 0.5 * np.sin(np.pi / 4)
    return x_new, y_new

def draw_oblique_cube(ax, varea:VisibleArea, x0, y0, z0, size=1):
    """绘制单个正方体"""
    d = size / 2
    # 俯视下层从原点0-1-2-3 俯视上层4-5-6-7
    vertices = [
        [x0-d, y0-d, z0-d], [x0+d, y0-d, z0-d],
        [x0+d, y0+d, z0-d], [x0-d, y0+d, z0-d],
        [x0-d, y0-d, z0+d], [x0+d, y0-d, z0+d],
        [x0+d, y0+d, z0+d], [x0-d, y0+d, z0+d],
    ]
    # 坐标转换2D顶点列表
    verts2d = [oblique_projection(x, y, z) for x, y, z in vertices]
    xs, ys = zip(*verts2d)
    points_2d = [(xs[i], ys[i]) for i in range(8)] 

    # 可视部分(除去点3) 7顶点 9边
    edges = [
        [0,1],[4,5],[6,7],
        [0,4],[1,5],[2,6],
        [1,2],[5,6],[4,7]
    ]
    faces = [
        [0,1,5,4],
        [1,2,6,5],
        [4,5,6,7]
    ]

    # 棱绘制
    for a, b in edges:
        line_coords = [points_2d[a], points_2d[b]]
        lines = varea.get_line_outside_region(line_coords)
        if lines:
            for line in lines:
                (x1, y1), (x2, y2) = line
                ax.plot([x1, x2], [y1, y2], color=DEFAULT_EDGE, lw=0.6)

    # 面绘制
    for face in faces:
        polygon_coords = [points_2d[i] for i in face]
        varea.add_polygon(polygon_coords)
        ax.fill([p[0] for p in polygon_coords], [p[1] for p in polygon_coords], color=DEFAULT_FILL, alpha=0.9)

# ===================== 堆叠矩阵随机生成 =====================
def generate_valid_stack():
    """生成无浮空无孤立的立方体阵列"""
    # 初始化高度矩阵
    h = np.zeros((MAX_LEN, MAX_LEN), dtype=int)
    # 随机选择一个起点作为第一个方块的位置
    start_i = random.randint(0, MAX_LEN-1)
    start_j = random.randint(0, MAX_LEN-1)
    h[start_i, start_j] = 1

    # 四方向 用于扩展连通区域
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    # 记录所有已生成的连通方块坐标（保证整体连通）
    connected = [(start_i, start_j)]
    # 随机决定要生成多少个方块（最少2个，最多铺满整个区域）
    expand_times = random.randint(2, MAX_LEN * MAX_LEN - 1)

    # 扩展阶段：从已连通方块向外生长新方块
    for _ in range(expand_times):
        # 随机选一个已存在的方块作为扩展源
        i, j = random.choice(connected)
        # 打乱方向，保证随机扩展
        random.shuffle(directions)
        
        # 尝试向四个方向扩展
        for di, dj in directions:
            ni, nj = i + di, j + dj
            # 判断新位置是否在边界内 + 未被占用
            if 0 <= ni < MAX_LEN and 0 <= nj < MAX_LEN and h[ni, nj] == 0:
                h[ni, nj] = 1
                connected.append((ni, nj))  
                break  

    # 赋值阶段：给所有已生成的方块随机赋予高度（1 ~ MAX_LAYER）
    for i, j in connected:
        h[i, j] = random.randint(1, MAX_LAYER)

    return h

# ===================== 立体图绘制 =====================
def draw_oblique_with_title(height_mat, save_name="example.png"):
    """
    绘制带标题的斜二测立体图（正方体堆叠）
    :param height_mat: 高度矩阵，记录每个位置堆叠的正方体层数
    :param save_name: 保存的图片文件名
    """
    fig, ax = plt.subplots(figsize=(3,3), dpi=150) # 创建画布与坐标系，设置画布大小和分辨率
    ax.set_aspect('equal') # 设置坐标轴等比例，保证图形不变形
    
    rows, cols = height_mat.shape
    varea = VisibleArea()

    # y-从前往后 x-从右往左 h-从上到下
    for y in range(cols):
        for x in reversed(range(rows)):
            h = height_mat[x, y]
            for z in reversed(range(h)):
                draw_oblique_cube(ax, varea, x, y, z, 1)
    
    ax.set_axis_off() # 关闭坐标轴
    plt.figtext(
        0.5, 0.93,  # 标题位置：水平居中，垂直靠上
        "下面立体图中共有多少个正方体？统计图像中的正方体个数，并分别描述从前面、右面、上面三个方向看到的图形。",
        ha="center",  # 水平居中
        fontsize=12   # 字体大小
    )

    plt.subplots_adjust(top=0.88) # 顶部边距
    plt.savefig(save_name, dpi=200, bbox_inches="tight", pad_inches=0.1) # 紧凑布局，去除多余空白
    
    plt.close()

def draw_prb_pic(ax, height_mat):
    """绘制试题斜二测图像"""
    ax.set_aspect('equal')
    ax.axis("off")

    varea = VisibleArea()
    rows, cols = height_mat.shape
    # y-从前往后 x-从右往左 h-从上到下
    for y in range(cols):
        for x in reversed(range(rows)):
            h = height_mat[x, y]
            for z in reversed(range(h)):
                draw_oblique_cube(ax, varea, x, y, z, 1)

def save_prb_pic(height_mat,save_path,figsize=(2, 2),dpi=200):

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_aspect('equal')
    ax.set_axis_off()

    draw_prb_pic(ax, height_mat)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close()

# ===================== 参考图绘制 =====================
def generate_mat_grid(mat, save_name=None):
    rows, cols = mat.shape
    plt.figure(figsize=(3, 3), dpi=150)
    ax = plt.gca()

    # 1. 画水平网格线：只在 0~cols 之间，不延伸
    for i in range(rows + 1):
        ax.plot([0, cols], [i, i], color=DEFAULT_EDGE, linewidth=0.8)
    # 2. 画竖直网格线：只在 0~rows 之间，不延伸
    for j in range(cols + 1):
        ax.plot([j, j], [0, rows], color=DEFAULT_EDGE, linewidth=0.8)

    # 3. 每个格子中心写数值
    for i in range(rows):
        for j in range(cols):
            val = mat[j, rows - i - 1]
            if val > 0:
                # 绘制矩形色块（j列，i行，宽度1，高度1）
                rect = plt.Rectangle((j, i), 1, 1, color=DEFAULT_FILL, alpha=0.6)
                ax.add_patch(rect)
                ax.text(
                    j + 0.5, i + 0.5, str(val),
                    ha="center", va="center",
                    fontsize=11, color =DEFAULT_EDGE)

    # 坐标约束 + 正方格子 + 倒置y轴(数组左上起点)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.invert_yaxis()
    ax.set_aspect("equal")   # 强制正方形格子
    ax.axis("off")           # 隐藏坐标轴刻度

    if save_name:
        plt.savefig(save_name, bbox_inches="tight", pad_inches=0.2)
    else:
        plt.show()
    plt.close()


# ===================== 辅助函数 =====================
def move_xy_all0(mat):
    """去除整行(列)为空的行(列)"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

def row2square(lst):
    """0->白正方形 1->黑正方形"""
    return ''.join([chr(0x2B1C) if p == 0 else chr(0x2B1B) for p in lst])

def lst2mat(lst):
    """一维堆叠序列立体化"""
    n = lst.max()

    i = np.arange(n-1, -1, -1)[:, None]
    mat = (lst > i).astype(int)
    return mat

def generate_wrong_pic_list(lst1):
    """根据正确选项生成错误选项"""
    len1 = len(lst1)
    is_palindrome = np.array_equal(lst1, lst1[::-1])

    len3 = random.randint(2,3)
    if len1 == 3:
        len4 = random.randint(2, len1)
    else:
        len4 = random.randint(1, len1+1)

    h = 2 if lst1.max() == 1 and len1 != 1 else MAX_LAYER

    def random_list(length):
        return [random.randint(1, h) for _ in range(length)]
    
    while True:
        if not is_palindrome:
            lst2 = lst1[::-1]
        else:
            lst2 = random_list(len1)
        lst3 = random_list(len3)
        lst4 = random_list(len4)
        
        # 4个列表全部互不相同
        if (not np.array_equal(lst2,lst3) and
            not np.array_equal(lst2,lst4) and
            not np.array_equal(lst3,lst4) and
            not np.array_equal(lst1,lst2) and
            not np.array_equal(lst1,lst3) and
            not np.array_equal(lst1,lst4)):
            break

    return [lst1, lst2, lst3, lst4]

def list2pic(ax,lst,scale = 0.7):
    """一维堆叠图绘制"""
    n = len(lst)
    ax.set_aspect("equal")
    ax.axis("off")

    offset = n * (1 - scale) / 2
    ax.set_xlim(0, MAX_LAYER)
    ax.set_ylim(0, MAX_LAYER)
    line_w = 0.8

    off_y = MAX_LAYER * (1 - scale) / 2
    for row in range(n):
        h = lst[row]
        for k in range(h):
            x0 = offset + row * scale
            y0 = off_y + k * scale
            rect = plt.Rectangle((x0, y0), scale, scale, 
                                    facecolor=DEFAULT_FILL, edgecolor=DEFAULT_EDGE, linewidth=line_w)
            ax.add_patch(rect)

def generate_wrong_pic_mat(mat):
    """根据正确选项生成错误选项"""
    row, col = mat.shape
    if row == 1: row = 2
    if col == 1: col = 2
    m1 = (mat>0).astype(int)
    front = np.rot90(lst2mat(np.max(mat, axis=1)), k=3)
    right = lst2mat(np.max(mat, axis=0))[::-1].T

    s1 = m1.sum()
    s2 = s1 if s1 != 1 else 2

    def random_binary_matrix(row, col, n):
    
        total = row * col
        arr = np.array([1] * n + [0] * (total - n))
        np.random.shuffle(arr)
    
        return move_xy_all0(arr.reshape(row, col))
    
    while True:
        if not np.array_equal(front,m1):
            m2 = front
        else:
            s2 = random.randint(max(1,s1-1),min(row*col, s1+1))
            m2 = random_binary_matrix(row, col, s2)
        
        if (not np.array_equal(right,m1) and
            not np.array_equal(right,m2)):
            m3 = right
        else:
            s3 = random.randint(max(1,s1-1),min(row*col, s1+1))
            m3 = random_binary_matrix(row, col, s3)

        s4 = random.randint(max(1,s1-2),min(row*col, s1+2))
        m4 = random_binary_matrix(row, col, s4)
        
        # 4个列表全部互不相同
        if (not np.array_equal(m2,m3) and
            not np.array_equal(m2,m4) and
            not np.array_equal(m3,m4) and
            not np.array_equal(m1,m2) and
            not np.array_equal(m1,m3) and
            not np.array_equal(m1,m4)):
            break

    return [m1, m2, m3, m4]

def mat2pic(ax, mat, scale = 0.7, line_w = 0.7, offsety = 0.5):
    """二维分布图绘制"""
    valid = move_xy_all0(mat[::-1].T)
    row, col = valid.shape
    ax.set_aspect("equal")
    ax.axis("off")

    offsetx = (MAX_LEN - row*scale)/2
    ax.set_xlim(0, MAX_LEN)
    ax.set_ylim(0, MAX_LEN)
    
    for i in range(row):
        for j in range(col):
            if valid[i, j] > 0:
                x0 = offsetx + i * scale
                y0 = offsety + j * scale
                rect = plt.Rectangle(
                    (x0, y0), 
                    scale, scale, 
                    facecolor=DEFAULT_FILL, 
                    edgecolor=DEFAULT_EDGE, 
                    linewidth=line_w
                    )
                ax.add_patch(rect)



# ===================== 视图描述 =====================
def layer_analysis(mat):
    height_mat = np.rot90(mat)
    valid = move_xy_all0(height_mat) 
    max_h = height_mat.max()
    
    total = 0
    cnt_text = []
    layer_counts = []
    analysis = []
    
    for layer in range(1, max_h + 1):
        # 统计每一列 ≥ 当前层的数量
        counts = np.sum(valid >= layer, axis=0)
        # 当前层总数量
        count = counts.sum()
        layer_counts.append(count)
        total += count

        col_num = len(counts)
        col_texts = []
        col_nums = []
        for idx, cnt in counts:
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
    analysis = f' 最大堆叠高度为{h}'
    exp = []
    total = 0
    for i in range(1, h+1):
        if counts[i] != 0:
            total += i*counts[i]
            exp.append(f'{i} \u00d7 {counts[i]}')
            analysis += f'，高度为{i}的立体堆叠有{counts[i]}个'
    analysis += f'。\n  所以共有{" + ".join(exp)} = {total}个小正方体。'
    return analysis
         
def front_analysis(mat):
    height_mat = np.rot90(mat)
    valid = move_xy_all0(height_mat)
    front = np.max(valid, axis=0)

    analysis = [f'共有{len(front)}列']
    
    for i, num in enumerate(front,1):
        analysis.append(f'第{i}列有{num}个小正方形')
    
    analysis.append(f'共计能看到{front.sum()}个小正方形。')
    analysis_str = '，'.join(analysis)
    return analysis_str

def right_analysis(mat):
    height_mat = np.rot90(mat)
    valid = move_xy_all0(height_mat)
    right = np.max(valid, axis=1)[::-1]

    analysis = [f'共有{len(right)}列']
    
    for i, num in enumerate(right,1):
        analysis.append(f'第{i}列有{num}个小正方形')
    
    analysis.append(f'共计能看到{right.sum()}个小正方形。')
    analysis_str = '，'.join(analysis)
    return analysis_str

def left_analysis(mat):
    height_mat = np.rot90(mat)
    valid = move_xy_all0(height_mat)
    left = np.max(valid, axis=1)

    analysis = [f'共有{len(left)}列']
    for i, num in enumerate(left,1):
        analysis.append(f'第{i}列有{num}个')
    
    analysis.append(f'共计能看到{left.sum()}个小正方形。')
    analysis_str = '，'.join(analysis)
    return analysis_str

def fr_analysis(height_mat):
    mat = move_xy_all0(height_mat)

    front = lst2mat(np.max(mat, axis=1))
    h1, l1 = front.shape
    rows1 = np.sum(front, axis=1)
    analysis_f = f'呈{h1}行{l1}列的布局：\n'
    
    for i, num in enumerate(rows1,0):
        analysis_f += f'  第{i+1}行有{num}个正方形，呈现{row2square(front[i])}；\n'
    analysis_f += f'  共计能看到{rows1.sum()}个小正方形。'

    right = lst2mat(np.max(mat, axis=0))
    h2, l2 = right.shape
    rows2 = np.sum(right, axis=1)
    analysis_r = f'呈{h2}行{l2}列的布局：\n'
    
    for i, num in enumerate(rows2,0):
        analysis_r += f'  第{i+1}行有{num}个正方形，呈现{row2square(right[i])}；\n'
    analysis_r += f'  共计能看到{rows2.sum()}个小正方形。'

    return analysis_f, analysis_r

def top_analysis(height_mat):
    mat = np.rot90(height_mat)
    top = (move_xy_all0(mat)>0).astype(int)
    hang, lie = top.shape
    rows = np.sum(top, axis=1)

    analysis = f'呈{hang}行{lie}列的布局：\n'
    
    for i, num in enumerate(rows,0):
        analysis += f'  第{i+1}行有{num}个正方形，呈现{row2square(top[i])}；\n'
    
    analysis += f'  共计能看到{rows.sum()}个小正方形。'
    return analysis


# ===================== 试题设计 =====================
def cnt_question(height_mat,save_path,figsize=(3, 3),dpi=150):
    """计数题"""

    title_text="下面立体图由小正方体堆叠形成，请统计图像中的正方体个数。"
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_aspect('equal')
    ax.set_axis_off()

    draw_prb_pic(ax, height_mat)

    plt.figtext(0.5, 0.93, title_text, ha="center", fontsize=12)

    plt.subplots_adjust(top=0.88)
    plt.savefig(save_path, dpi=200, bbox_inches="tight", pad_inches=0.1)
    plt.close()

def choose_question(height_mat,view,img_path,save_path,figsize=(5, 2),dpi=200):
    
    prb_text = f'右图立体图形由若干小正方体堆叠而成，从{view}看到的图像是（）'
    plt.figure(figsize=figsize, dpi=dpi)
    plt.figtext(
        0.02, 0.80, 
        prb_text, 
        ha="left", va="top", 
        fontsize=9, 
        linespacing=1.3
    )

    mat = np.rot90(height_mat)
    valid = move_xy_all0(mat)
    if view == '正面':
        f1 = np.max(valid, axis=0)
    elif view == '右面':
        f1 = np.max(valid, axis=1)[::-1]
    order = generate_wrong_pic_list(f1)
    
    indices = list(range(len(order)))
    random.shuffle(indices)
    shuffled = [order[i] for i in indices]
    pos = indices.index(0)
    answer = chr(pos + 65)

    # shuffled = order.copy()
    # random.shuffle(shuffled)
    # def find_index(lst, target):
    #     for i, arr in enumerate(lst):
    #         if np.array_equal(arr, target):
    #             return i
    #     return -1
    # answer = chr(find_index(shuffled, f1) + 65)

    gs = plt.GridSpec(1, 5, width_ratios=[1,1,1,1,1.2], wspace=0.3)

    ax1 = plt.subplot(gs[0])
    list2pic(ax1, shuffled[0])
    ax1.text(-0.1, 0.15, 'A.', fontsize=9, transform=ax1.transAxes, va='bottom', ha='left')

    ax2 = plt.subplot(gs[1])
    list2pic(ax2, shuffled[1])
    ax2.text(-0.1, 0.15, 'B.', fontsize=9, transform=ax2.transAxes, va='bottom', ha='left')

    ax3 = plt.subplot(gs[2])
    list2pic(ax3, shuffled[2])
    ax3.text(-0.1, 0.15, 'C.', fontsize=9, transform=ax3.transAxes, va='bottom', ha='left')

    ax4 = plt.subplot(gs[3])
    list2pic(ax4, shuffled[3])
    ax4.text(-0.1, 0.15, 'D.', fontsize=9, transform=ax4.transAxes, va='bottom', ha='left')

    ax5 = plt.subplot(gs[4])
    img = mpimg.imread(img_path)
    ax5.imshow(img)
    ax5.axis("off")
    # draw_prb_pic(ax5,height_mat)
    
    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    plt.savefig(
        save_path, 
        dpi=dpi, 
        bbox_inches="tight"
    )
    plt.close()

    return answer

def choose_question_top(height_mat,img_path,save_path,figsize=(5, 2),dpi=200):
    
    prb_text = f'右图立体图形由若干小正方体堆叠而成，从顶部看到的图像是（）'
    plt.figure(figsize=figsize, dpi=dpi)
    plt.figtext(
        0.02, 0.80, 
        prb_text, 
        ha="left", va="top", 
        fontsize=9, 
        linespacing=1.3
    )

    # m1 = np.rot90(height_mat)
    valid = move_xy_all0(height_mat)
    order = generate_wrong_pic_mat(valid)
    
    indices = list(range(len(order)))
    random.shuffle(indices)
    shuffled = [order[i] for i in indices]
    pos = indices.index(0)
    answer = chr(pos + 65)

    gs = plt.GridSpec(1, 5, width_ratios=[1,1,1,1,1.2], wspace=0.3)

    ax1 = plt.subplot(gs[0])
    mat2pic(ax1, shuffled[0])
    ax1.text(-0.1, 0.15, 'A.', fontsize=9, transform=ax1.transAxes, va='bottom', ha='left')

    ax2 = plt.subplot(gs[1])
    mat2pic(ax2, shuffled[1])
    ax2.text(-0.1, 0.15, 'B.', fontsize=9, transform=ax2.transAxes, va='bottom', ha='left')

    ax3 = plt.subplot(gs[2])
    mat2pic(ax3, shuffled[2])
    ax3.text(-0.1, 0.15, 'C.', fontsize=9, transform=ax3.transAxes, va='bottom', ha='left')

    ax4 = plt.subplot(gs[3])
    mat2pic(ax4, shuffled[3])
    ax4.text(-0.1, 0.15, 'D.', fontsize=9, transform=ax4.transAxes, va='bottom', ha='left')

    ax5 = plt.subplot(gs[4])
    img = mpimg.imread(img_path)
    ax5.imshow(img)
    ax5.axis("off")
    # draw_prb_pic(ax5,height_mat)
    
    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    plt.savefig(
        save_path, 
        dpi=dpi, 
        bbox_inches="tight"
    )
    plt.close()

    return answer

def tof_question(img_path,save_path,figsize=(3, 3),dpi=150):
    """判断题"""
    title_text="下面立体图由小正方体堆叠形成，其从正面和右面看到的图形是否相同____（填“是”或“否”）"
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_aspect('equal')
    ax.set_axis_off()

    img = mpimg.imread(img_path)
    ax.imshow(img)
    ax.axis("off")

    plt.figtext(0.5, 0.93, title_text, ha="center", fontsize=12)

    plt.subplots_adjust(top=0.88)
    plt.savefig(save_path, dpi=200, bbox_inches="tight", pad_inches=0.1)
    plt.close()

def blank_1_question(height_mat,img_path,save_path,figsize=(6,3),dpi=200):
     
    prb_text = f'右图立体图形由若干小正方体堆叠而成，从“正面”、“上面”、“右面”中选择正确答案填入对应括号。'
    plt.figure(figsize=figsize, dpi=dpi)
    plt.figtext(
        0.02, 0.80, 
        prb_text, 
        ha="left", va="top", 
        fontsize=9, 
        linespacing=1.3
    )

    order = ['正面','右面','上面']
    shuffled = order.copy()
    random.shuffle(shuffled)

    mat = np.rot90(height_mat)
    front = np.max(mat, axis=0)
    right = np.max(mat, axis=1)[::-1]

    def drawview(ax,view:str):
        if view == '正面':
            list2pic(ax,front)
        elif view == '右面':
            list2pic(ax,right)
        elif view == '上面':
            mat2pic(ax,mat)


    shuffled = order.copy()
    random.shuffle(shuffled)

    gs = plt.GridSpec(1, 4, width_ratios=[1,1,1,1.2], wspace=0.3)

    ax1 = plt.subplot(gs[0])
    drawview(ax1, shuffled[0])
    ax1.text(0.5, -0.1, '（     ）', fontsize=9, transform=ax1.transAxes, va='bottom', ha='center')

    ax2 = plt.subplot(gs[1])
    drawview(ax2, shuffled[1])
    ax2.text(0.5, -0.1, '（     ）', fontsize=9, transform=ax2.transAxes, va='bottom', ha='center')

    ax3 = plt.subplot(gs[2])
    drawview(ax3, shuffled[2])
    ax3.text(0.5, -0.1, '（     ）', fontsize=9, transform=ax3.transAxes, va='bottom', ha='center')

    ax4 = plt.subplot(gs[3])
    img = mpimg.imread(img_path)
    ax4.imshow(img)
    ax4.axis("off")
    # draw_prb_pic(ax5,height_mat)
    
    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    plt.savefig(
        save_path, 
        dpi=dpi, 
        bbox_inches="tight"
    )
    plt.close()

    return shuffled


# ===================== 解析文本预设 =====================
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
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)

def choose_question_analysis(height_mat, view, answer, save_path):
    """
    选择题解析生成
    :param height_mat: 高度矩阵，记录每个位置堆叠的正方体层数
    :param save_path: 保存的图片路径
    """
    if view == '正面':
        step = front_analysis(height_mat)
    elif view == '右面':
        step = right_analysis(height_mat)
    
    analysis = [
        '【分析】',
        ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，从不同方向观察立体图形。',
        f' 解题思路：为找出立体图形从{view}观察得到的平面图形，解题时先确定从{view}看的列数，再分别数出每一列的正方体个数，最后与选项进行比对。\n',
        '【解答】',
        f' 解：从{view}看：{step}',
        f"  所以，选项{answer}符合描述。",
        f"\n【答案】 {answer}"
    ]
    
    analysis_str = '\n'.join(analysis)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)

def choose_question_top_analysis(height_mat, answer, save_path):
    """
    选择题解析生成
    :param height_mat: 高度矩阵，记录每个位置堆叠的正方体层数
    :param save_path: 保存的图片路径
    """
    step = top_analysis(height_mat)
    
    analysis = [
        '【分析】',
        ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，从不同方向观察立体图形。',
        f' 解题思路：为找出立体图形从上面观察得到的平面图形，解题时先确定从上面看的行数，再分别寻找每一行的正方体位置分布，最后与选项进行比对。\n',
        '【解答】',
        f' 解：从上面看：{step}',
        f"  所以，选项{answer}符合描述。",
        f"\n【答案】 {answer}"
    ]
    
    analysis_str = '\n'.join(analysis)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)

def tof_question_analysis(height_mat, save_path):
    """
    判断题解析生成
    :param height_mat: 高度矩阵，记录每个位置堆叠的正方体层数
    :param save_path: 保存的图片路径
    """
    front = front_analysis(height_mat)
    right = right_analysis(height_mat)

    mat = move_xy_all0(height_mat)
    answer = np.array_equal(np.max(mat, axis=0), np.max(mat, axis=1))
    
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

def blank_1_question_analysis(height_mat, answer, save_path):

    top = top_analysis(height_mat)
    front, right = fr_analysis(height_mat)
    
    ans_str = ' '.join([f'（{view}）' for view in answer])

    analysis = [
        '【分析】',
        ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，从不同方向观察立体图形。',
        f' 解题思路：依次从正面，右面，上面观察图形特征，与选项进行比对，填入正确答案。\n',
        '【解答】',
        f' 解：从正面看：{front}\n  与第{answer.index('正面') + 1}个图形相符合。\n',
        f'  从右面看：{right}\n  与第{answer.index('右面') + 1}个图形相符合。\n',
        f'  从上面看：{top}\n  与第{answer.index('上面') + 1}个图形相符合。',
        f"  所以，在括号中依次填入{'，'.join(answer)}。",
        f"\n【答案】 {ans_str}"
    ]
    
    analysis_str = '\n'.join(analysis)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(analysis_str)

    return 



# if __name__ == "__main__":
#     # 随机生成
#     # save_dir = None
#     # for i in range(1, NUM_QUESTIONS + 1):
#     #     mat = generate_valid_stack()
#     #     analysis = generate_analysis(mat)
#     #     save_dir = os.path.join(current_dir,'random')
#     #     os.makedirs(save_dir, exist_ok=True)
#     #     if save_dir is None:
#     #         save_dir = current_dir
        
#     #     # cnt_problem(mat, os.path.join(save_dir,f"计数题_{i}.png"))
#     #     # cnt_problem_analysis(mat, os.path.join(save_dir,f"计数题_{i}_解析.txt"))

#     #     # print(top_analysis(mat))
#     #     print(f"✅ 第{i}题 已生成")

#     # 文件生成
#     mat_file = os.path.join(current_dir,'mat_3x3x3_legal_47529.txt')
#     save_dir = os.path.join(current_dir,'选择题_上面')
#     image_dir = os.path.join(current_dir,'legal_images')
#     os.makedirs(save_dir, exist_ok=True)

#     with open(mat_file, 'r', encoding='utf-8') as f:

#         for i, line in enumerate(f,start=1):
#             line = line.strip()
#             if not line:
#                 continue
#             mat = np.array(ast.literal_eval(line))
    
#             # if i > 100:
#             #     break

#             answer = choose_question_top(mat, os.path.join(image_dir,f"mat_333_{i}.png"), os.path.join(save_dir,f"选择题_上面_{i}.png"))
#             choose_question_top_analysis(mat, answer, os.path.join(save_dir,f"选择题_上面_{i}_解析.txt"))
            
#             # view = '右面'
#             # answer = choose_question(mat, view, os.path.join(image_dir,f"mat_333_{i}.png"), os.path.join(save_dir,f"选择题_{view}_{i}.png"))
#             # choose_question_analysis(mat, view, answer, os.path.join(save_dir,f"选择题_{view}_{i}_解析.txt"))

#             # view = '正面'
#             # answer = choose_question(mat, view, os.path.join(image_dir,f"mat_333_{i}.png"), os.path.join(save_dir,f"选择题_{view}_{i}.png"))
#             # choose_question_analysis(mat, view, answer, os.path.join(save_dir,f"选择题_{view}_{i}_解析.txt"))

#             # save_prb_pic(mat,os.path.join(save_dir,f"mat_333_{i}.png"))

#             # cnt_question(mat, os.path.join(save_dir,f"计数题_{i}.png"))
#             # cnt_question_analysis(mat, os.path.join(save_dir,f"计数题_{i}_解析.txt"))

#             print(f"✅ 第{i}题 已生成")


if __name__ == "__main__":
    # 文件生成
    save_dir = os.path.join(current_dir,'第一类填空题')
    image_dir = os.path.join(current_dir,'legal_images')
    os.makedirs(save_dir, exist_ok=True)
    json_file = r'C:\Users\yhcheng24\Desktop\yhcheng24\Work\260511\output\diff3view_39305.jsonl'
    success = 0
    error= 0
    with open(json_file, 'r', encoding='utf-8') as f:

        for i, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            if i > 4:
                break
            try:
                item = json.loads(line)
                id = item["id"]
                mat = np.array(item["mat"])

                answer = blank_1_question(mat, os.path.join(image_dir,f"mat_333_{id}.png"), os.path.join(save_dir,f"第一类填空题_{i}.png"))
                blank_1_question_analysis(mat, answer, os.path.join(save_dir,f"第一类填空题_{i}_解析.txt"))

                print(f"✅ 第{i}题 已生成")
                success += 1
            except:
                error += 1

#     print(f'success:{success} | error:{error}')

    

