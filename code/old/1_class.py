import matplotlib.pyplot as plt
import numpy as np
import random
import os

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
current_dir = os.path.dirname(os.path.abspath(__file__)) # 当前py脚本目录
os.chdir(current_dir) 

# 全局画布基准，统一所有视图网格大小
default_fill = "#E5E5E5"
default_edge = "black"
MAX_LAYER = 3
MAX_LEN = 3
NUM_QUESTIONS = 1
save_dir = None


# 1. 生成无浮空 + 底层联通合法堆叠
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

# 2. 正交投影
def set_ortho_equal_aspect(ax):
    # 设为正交投影，消除透视变形
    ax.set_proj_type('ortho')
    # 严格XYZ等比例
    x_lim = ax.get_xlim()
    y_lim = ax.get_ylim()
    z_lim = ax.get_zlim()
    max_range = max(x_lim[1]-x_lim[0], y_lim[1]-y_lim[0], z_lim[1]-z_lim[0]) / 2.0
    mid_x = (x_lim[0] + x_lim[1]) * 0.5
    mid_y = (y_lim[0] + y_lim[1]) * 0.5
    mid_z = (z_lim[0] + z_lim[1]) * 0.5
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

# 3. 题图生成
def draw_3d_with_title(height_mat, save_name):
    fig = plt.figure(figsize=(4,4), dpi=150)
    ax = fig.add_subplot(111, projection='3d')
    rows, cols = height_mat.shape

    dx = dy = dz = 1
    fill_color = default_fill
    edge_color = default_edge
    line_w = 0.8

    for x in range(rows):
        for y in range(cols):
            h = height_mat[x, y]
            for z in range(h):
                ax.bar3d(x, y, z, dx, dy, dz,
                         color=fill_color, edgecolor=edge_color,
                         linewidth=line_w, shade=False)

    
    # 垂直 YOZ 平面 → 指向 X 轴负方向
    x0, y0, z0 = rows + 1.3, cols/2, 0
    dx, dy, dz = -1, 0, 0 

    # 绘制箭头
    ax.quiver(
        x0, y0, z0,
        dx, dy, dz,
        color=edge_color,
        linewidth=1,    # 箭头粗细
        arrow_length_ratio=0.3, # 箭头张开程度
        label='front'
    )
    # 箭头文字标注
    ax.text(x0+dx/2, y0, z0 - 0.8, '正面', color="#000000FF", fontsize=11, ha='center')

    ax.view_init(elev=32, azim=48)
    set_ortho_equal_aspect(ax)
    
    ax.set_axis_off()
    ax.grid(False)

    plt.figtext(0.5, 0.93,
                "下面立体图中共有多少个正方体？统计图像中的正方体个数，并分别描述从前面、右面、上面三个方向看到的图形。",
                ha="center", fontsize=12)

    plt.subplots_adjust(top=0.88)
    plt.savefig(save_name, dpi=200, bbox_inches="tight", pad_inches=0.1)
    plt.close()

# 4. 解析文字
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

# 5. 视图生成
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
                    x0 = offset + j * scale
                    y0 = offset + (n - 1 - i) * scale
                    rect = plt.Rectangle((x0, y0), scale, scale, 
                                         facecolor=fill, edgecolor=edge, linewidth=line_w)
                    ax.add_patch(rect)

    elif view_type == "layer_top":
        # ax.set_ylim(0, MAX_LEN)
        for i in range(n):
            for j in range(n):
                if mat[i, j] >= layer:
                    x0 = offset + j * scale
                    y0 = offset + (n - 1 - i) * scale
                    rect = plt.Rectangle((x0, y0), scale, scale, 
                                         facecolor=fill, edgecolor=edge, linewidth=line_w)
                    ax.add_patch(rect)
        ax.set_title(f"第{layer}层", fontsize=9)

    elif view_type == "front":
        # ax.set_ylim(0, MAX_LAYER)
        front = np.max(mat, axis=0)
        off_y = MAX_LAYER * (1 - scale) / 2
        for col in range(n):
            h = front[col]
            for k in range(h):
                x0 = offset + col * scale
                y0 = off_y + k * scale
                rect = plt.Rectangle((x0, y0), scale, scale, 
                                     facecolor=fill, edgecolor=edge, linewidth=line_w)
                ax.add_patch(rect)

    elif view_type == "right":
        # ax.set_ylim(0, MAX_LAYER)
        right = np.max(mat, axis=1)[::-1]
        off_y = MAX_LAYER * (1 - scale) / 2
        for row in range(n):
            h = right[row]
            for k in range(h):
                x0 = offset + row * scale
                y0 = off_y + k * scale
                rect = plt.Rectangle((x0, y0), scale, scale, 
                                     facecolor=fill, edgecolor=edge, linewidth=line_w)
                ax.add_patch(rect)

# 6. 解析图生成
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
    ax1.set_title("前面（正面）", fontsize=9)
    ax2.set_title("右面（侧面）", fontsize=9)
    ax3.set_title("上面（俯视）", fontsize=9)

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

# 7. 参考图绘制 
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
            val = mat[i, j]
            if val > 0:
                # 绘制矩形色块（j列，i行，宽度1，高度1）
                rect = plt.Rectangle((j, i), 1, 1, color=default_fill, alpha=0.6)
                ax.add_patch(rect)
                ax.text(j + 0.5, i + 0.5, str(val),
                    ha="center", va="center", fontsize=11)

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
    # for i in range(1, NUM_QUESTIONS + 1):
    #     mat = generate_valid_stack()
    #     analysis = generate_analysis(mat)
    #     if save_dir is None:
    #         save_dir = current_dir
    #     draw_3d_with_title(mat, os.path.join(save_dir,f"第{i}题_题目图.png"))
    #     draw_three_view_with_analysis(mat, analysis, os.path.join(save_dir,f"第{i}题_答案解析图.png"))
    #     generate_mat_grid(mat, os.path.join(save_dir,f"第{i}题_生成矩阵.png"))

    #     print(f"✅ 第{i}题 已生成")

    # 文件生成
    mat_file = os.path.join(current_dir,'20.txt')
    save_dir = os.path.join(current_dir,'20')
    os.makedirs(save_dir, exist_ok=True)
    with open(mat_file, 'r', encoding='utf-8') as f:

        for i, line in enumerate(f,start=1):
            line = line.strip()
            if not line:
                continue
            mat = np.array(eval(line))

            analysis = generate_analysis(mat)

            draw_3d_with_title(mat, os.path.join(save_dir,f"{i}_question.png"))
            draw_three_view_with_analysis(mat, analysis, os.path.join(save_dir,f"{i}_answer.png"))
            generate_mat_grid(mat, os.path.join(save_dir,f"{i}_matrix.png"))

            print(f"✅ 第{i}题 已生成")