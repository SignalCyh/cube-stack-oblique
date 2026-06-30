import numpy as np
import random
import os
import matplotlib.pyplot as plt

from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

default_fill = "#E5E5E5"
default_edge = "black"
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
                ax.plot([x1, x2], [y1, y2], color=default_edge, lw=0.8)

    # 面绘制
    for face in faces:
        polygon_coords = [points_2d[i] for i in face]
        varea.add_polygon(polygon_coords)
        ax.fill([p[0] for p in polygon_coords], [p[1] for p in polygon_coords], color=default_fill, alpha=0.9)

# ===================== 堆叠矩阵生成 =====================
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

# ===================== 试题图绘制 =====================
def draw_oblique_with_title(height_mat, save_name="oblique_clipped.png"):
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

# ===================== 解析图绘制 =====================
def generate_analysis(height_mat):
    max_h = height_mat.max()
    layer_counts = []
    total = 0
    for layer in range(1, max_h + 1):
        cnt = np.sum(height_mat >= layer)
        layer_counts.append(cnt)
        total += cnt
    
    analysis = ['【分析】\n',
                ' 考查点：本题考察学生对立体图形的观察能力和空间构想能力，学会正确清点图片中小正方体的数量。',
                ' 解题思路：在清点此类图形时，为了避免遗漏或重复，通常采用“分层计数法”。\n',
                '【解答】\n',
                ' 解：使用分层计数法统计个数：'
    ]
    for i, num in enumerate(layer_counts):
        analysis.append(f"  第{i+1}层：如图所示，共有{num}个小正方体。")

    # analysis.append(f"  从上面看面：共有{i}列，每列正方形个数为[]")
    analysis.extend([f'  综上所述，这个图形由{" + ".join(map(str, layer_counts))} = {total}个小正方体摆成。',
                     f'  分别画出从前面（正视）、右面（侧视）、上面（俯视）三个方向看得到的图形\n',
                     f'【答案】 {total}个 图形如图所示\n'
    ])
    return '\n'.join(analysis)

def plot_single_view(ax, mat, view_type, layer=None):
    n = max(mat.shape[0], mat.shape[1])
    fill = default_fill
    edge = default_edge
    line_w = 0.8
    ax.set_aspect("equal")
    ax.axis("off")

    # 缩放系数
    scale = 0.5
    # 居中偏移，让缩小后的图形在子图正中间
    offset = n * (1 - scale) / 2

    # 固定所有视图坐标轴范围不变，只缩放内部图形
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)

    if view_type == "top":
        # ax.set_ylim(0, MAX_LEN)
        for i in range(n):
            for j in range(n):
                if mat[i, j] > 0:
                    # 坐标+边长同比例缩放
                    x0 = offset + i * scale
                    y0 = offset + j * scale
                    rect = plt.Rectangle((x0, y0), scale, scale, 
                                         facecolor=fill, edgecolor=edge, linewidth=line_w)
                    ax.add_patch(rect)
        ax.set_title("上面（俯视）", fontsize=9)

    elif view_type == "layer_top":
        # ax.set_ylim(0, MAX_LEN)
        for i in range(n):
            for j in range(n):
                if mat[i, j] >= layer:
                    x0 = offset + i * scale
                    y0 = offset + j * scale
                    rect = plt.Rectangle((x0, y0), scale, scale, 
                                         facecolor=fill, edgecolor=edge, linewidth=line_w)
                    ax.add_patch(rect)
        ax.set_title(f"第{layer}层", fontsize=9)

    elif view_type == "front":
        # ax.set_ylim(0, MAX_LAYER)
        front = np.max(mat, axis=1)
        off_y = MAX_LAYER * (1 - scale) / 2
        for row in range(n):
            h = front[row]
            for k in range(h):
                x0 = offset + row * scale
                y0 = off_y + k * scale
                rect = plt.Rectangle((x0, y0), scale, scale, 
                                     facecolor=fill, edgecolor=edge, linewidth=line_w)
                ax.add_patch(rect)
        ax.set_title("前面（正面）", fontsize=9)

    elif view_type == "right":
        # ax.set_ylim(0, MAX_LAYER)
        right = np.max(mat, axis=0)
        off_y = MAX_LAYER * (1 - scale) / 2
        for col in range(n):
            h = right[col]
            for k in range(h):
                x0 = offset + col * scale
                y0 = off_y + k * scale
                rect = plt.Rectangle((x0, y0), scale, scale, 
                                     facecolor=fill, edgecolor=edge, linewidth=line_w)
                ax.add_patch(rect)
        ax.set_title("右面（侧面）", fontsize=9)

def draw_three_view_with_analysis(mat, analysis_text, save_name):

    max_layer = mat.max()
    total_cols = 3 + max_layer

    plt.figure(figsize=(total_cols, 7), dpi=150)
    plt.figtext(
        0.02, 0.95, 
        analysis_text, 
        ha="left", va="top", 
        fontsize=9, 
        linespacing=1.3
    )

    # 中间标准三视图
    ax1 = plt.subplot(1, total_cols, 1)
    ax2 = plt.subplot(1, total_cols, 2)
    ax3 = plt.subplot(1, total_cols, 3)
    plot_single_view(ax1, mat, "front")
    plot_single_view(ax2, mat, "right")
    plot_single_view(ax3, mat, "top")

    for layer in range(1, max_layer + 1):
        ax = plt.subplot(1, total_cols, layer+3)
        plot_single_view(ax, mat, "layer_top", layer=layer)

    # 布局设定
    plt.tight_layout()
    plt.savefig(
        save_name, 
        dpi=150, 
        bbox_inches="tight"
    )
    plt.close()

# ===================== 参考图绘制 =====================
def generate_mat_grid(mat, save_name=None):
    rows, cols = mat.shape
    plt.figure(figsize=(3, 3), dpi=150)
    ax = plt.gca()

    # 1. 画水平网格线：只在 0~cols 之间，不延伸
    for i in range(rows + 1):
        ax.plot([0, cols], [i, i], color=default_edge, linewidth=0.8)
    # 2. 画竖直网格线：只在 0~rows 之间，不延伸
    for j in range(cols + 1):
        ax.plot([j, j], [0, rows], color=default_edge, linewidth=0.8)

    # 3. 每个格子中心写数值
    for i in range(rows):
        for j in range(cols):
            val = mat[j, rows - i - 1]
            if val > 0:
                # 绘制矩形色块（j列，i行，宽度1，高度1）
                rect = plt.Rectangle((j, i), 1, 1, color=default_fill, alpha=0.6)
                ax.add_patch(rect)
                ax.text(
                    j + 0.5, i + 0.5, str(val),
                    ha="center", va="center",
                    fontsize=11, color =default_edge)

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

if __name__ == "__main__":
        
    # 随机生成
    # save_dir = None
    # for i in range(1, NUM_QUESTIONS + 1):
    #     mat = generate_valid_stack()
    #     analysis = generate_analysis(mat)
    #     if save_dir is None:
    #         save_dir = current_dir

    #     draw_oblique_with_title(mat, os.path.join(save_dir,f"{i}_question.png"))
    #     draw_three_view_with_analysis(mat, analysis, os.path.join(save_dir,f"{i}_answer.png"))
    #     generate_mat_grid(mat, os.path.join(save_dir,f"{i}_matrix.png"))

    #     print(f"✅ 第{i}题 已生成")

    # 文件生成
    mat_file = os.path.join(current_dir,'200.txt')
    save_dir = os.path.join(current_dir,'200')
    os.makedirs(save_dir, exist_ok=True)
    with open(mat_file, 'r', encoding='utf-8') as f:

        for i, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            mat = np.array(eval(line))

            analysis = generate_analysis(mat)

            draw_oblique_with_title(mat, os.path.join(save_dir,f"{i}_question.png"))
            draw_three_view_with_analysis(mat, analysis, os.path.join(save_dir,f"{i}_answer.png"))
            generate_mat_grid(mat, os.path.join(save_dir,f"{i}_matrix.png"))

            print(f"✅ 第{i}题 已生成")
