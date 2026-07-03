import random
import matplotlib.pyplot as plt
import numpy as np

from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from PIL import Image, ImageFilter

from style_config import (
    FACE_PALETTES,
    LINE_COLORS,
    FILL_CATEGORIES,
    STYLE_WEIGHTS
)

# ========================== 工具函数 =========================
def random_valid_stack(row, col, height):
    """生成无浮空无孤立的立方体阵列"""
    h = np.zeros((row, col), dtype=int)
    start_i = random.randint(0, row-1)
    start_j = random.randint(0, col-1)
    h[start_i, start_j] = 1
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    connected = [(start_i, start_j)]
    expand_times = random.randint(2, row * col - 1)

    for _ in range(expand_times):
        i, j = random.choice(connected)
        random.shuffle(directions)
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < row and 0 <= nj < col and h[ni, nj] == 0:
                h[ni, nj] = 1
                connected.append((ni, nj))  
                break  

    for i, j in connected:
        h[i, j] = random.randint(1, height)

    return h

def move_xy_all0(mat):
    """去除矩阵中全为0的整行、整列"""
    return mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]

def lst2mat(lst):
    """一维堆叠序列立体化"""
    n = lst.max()
    i = np.arange(n-1, -1, -1)[:, None]
    return (lst > i).astype(int)

def view_mat(array):
    """返回f r l t的视图矩阵"""
    mat = move_xy_all0(np.array(array))
    if mat.ndim != 2:
        raise ValueError("input error")
    
    res = [lst2mat(np.max(mat, axis=0)),
           lst2mat(np.max(mat, axis=1)[::-1]),
           lst2mat(np.max(mat, axis=1)),
           (mat>0).astype(int)
        ]

    return [mati.tolist() for mati in res]

def mat2pic(ax, mat, max_x, max_y, style:CubeStyle, scale = 0.7, line_w = 0.6):
    """二维分布图绘制"""
    valid = np.array(mat[::-1]).T
    # print(valid)
    row, col = valid.shape
    ax.set_aspect("equal")
    ax.axis("off")

    deltax = 0.1
    offsetx = (max_x-row)*scale/2 + deltax
    offsety = scale/2
    ax.set_xlim(0, max_x*scale+2*deltax)
    ax.set_ylim(0, (max_y+1)*scale)
    
    for i in range(row):
        for j in range(col):
            if valid[i, j] > 0:
                x0 = offsetx + i * scale
                y0 = offsety + j * scale
                rect = plt.Rectangle(
                    (x0, y0),
                    scale, scale,
                    alpha=style.alpha/2,
                    facecolor=style.face_color_2d(),
                    edgecolor=style.edge_color,
                    linewidth=line_w
                    )
                ax.add_patch(rect)

def _smooth_noise(h, w, rng, scale=8):
    sh = max(2, h // scale)
    sw = max(2, w // scale)
    low = np.array([[rng.random() for _ in range(sw)] for _ in range(sh)],
                   dtype=np.float32)
    field = Image.fromarray((low * 255).astype(np.uint8)).resize(
        (w, h), Image.BICUBIC)
    return np.asarray(field).astype(np.float32) / 255.0

def apply_erase(ax, rng=None, strength=None):

    rng = rng or random
    if strength is None:
        strength = rng.uniform(0.35, 0.7)

    fig = ax.figure
    fig.canvas.draw()
    rgba_buf = np.array(fig.canvas.buffer_rgba())
    full_img = Image.fromarray(rgba_buf[..., :3])
    arr = np.asarray(full_img).astype(np.float32)
    h, w = arr.shape[:2]

    fig_w, fig_h = w, h

    ax_pos = ax.get_position()
    x1 = int(ax_pos.x0 * fig_w)
    x2 = int(ax_pos.x1 * fig_w)
    y1 = int((1 - ax_pos.y1) * fig_h)
    y2 = int((1 - ax_pos.y0) * fig_h)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(fig_w, x2), min(fig_h, y2)
    ax_mask = np.zeros((h, w), dtype=np.float32)
    ax_mask[y1:y2, x1:x2] = 1.0

    lum = arr.mean(axis=2) / 255.0
    face_mask = np.clip((lum - 0.25) / 0.6, 0, 1)
    is_colored = (arr.max(axis=2) - arr.min(axis=2) > 12) | (lum < 0.96)
    face_mask = face_mask * is_colored
    final_mask = face_mask * ax_mask

    field = _smooth_noise(h, w, rng, scale=rng.choice([6, 8, 10, 12]))
    field = field ** rng.uniform(1.0, 2.0)
    erase = (1 - field)[:, :, None] * final_mask[:, :, None] * strength
    arr = arr + (255.0 - arr) * erase
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    blur_radius = rng.uniform(0.4, 1.0)
    out = out.filter(ImageFilter.GaussianBlur(radius=blur_radius))


    # 新建画布承载处理后的图片
    new_fig, new_ax = plt.subplots(figsize=(fig_w / fig.dpi, fig_h / fig.dpi), dpi=fig.dpi)
    new_ax.imshow(out, extent=[0, w, h, 0])
    new_ax.set_axis_off()
    new_ax.set_aspect("equal")

    plt.close(fig)
    return new_fig

# ===================== 颜色工具 =====================
class ColorUtil:
    @staticmethod
    def _hex_to_rgb(c: str) -> tuple[float, float, float]:
        """十六进制颜色转归一化RGB(0~1)"""
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
        """归一化RGB(0~1)转回十六进制色值"""
        return "#{:02x}{:02x}{:02x}".format(
            *[max(0, min(255, int(round(v * 255)))) for v in rgb]
        )

    @staticmethod
    def darken(color: str, factor: float = 0.65) -> str:
        """加深颜色: 向黑色插值, factor 越小越深。"""
        r, g, b = ColorUtil._hex_to_rgb(color)
        return ColorUtil._rgb_to_hex((r * factor, g * factor, b * factor))

    @staticmethod
    def lighten(color: str, factor: float = 0.5) -> str:
        """提亮颜色: 向白色插值, factor 为保留原色比例。"""
        r, g, b = ColorUtil._hex_to_rgb(color)
        return ColorUtil._rgb_to_hex((
            r + (1 - r) * (1 - factor),
            g + (1 - g) * (1 - factor),
            b + (1 - b) * (1 - factor),
        ))

# ===================== 颜色风格 =====================
class CubeStyle:
    """ 颜色风格 """
    def __init__(self, colors, category, fill_color, edge_color, fill_alpha=1.0, seed=None):
        """
        实例初始化

        Args:
            colors      : 颜色族
            category    : 涂色类别
            mode3d      : 3D 涂色模式
            mode2d      : 2D 涂色模式
            fill_color  : 面基础颜色
            edge_color  : 线条颜色
            seed        : 随机数生成器

        Raises:
        """
        self.colors = colors
        self.category = category
        self.mode3d, self.mode2d = FILL_CATEGORIES[category]
        self.fill_color = fill_color
        self.edge_color = edge_color
        self.alpha = fill_alpha
        self._rng = random.Random(seed if seed is not None else random.randrange(1 << 30))

    @classmethod
    def random(cls, rng=None, allow_families=None, allow_categories=None, weights=None):
        """
        随机生成一个颜色风格。

        Args:
            rng              : 随机数生成器, 用于固定随机种子复现结果, 默认标准库random
            allow_families   : 限制 color_family 候选（白面黑线时被忽略）
            allow_categories : 若指定, 则仅在该集合内按 STYLE_WEIGHTS 子采样
            weights          : 覆盖默认 STYLE_WEIGHTS; 不传则用模块当前值

        Raises:
        """
        rng = rng or random
        wmap = dict(weights) if weights else dict(STYLE_WEIGHTS)

        # 若调用方限制了 categories, 则只在限制集合 + 它们对应的权重内采样
        if allow_categories is not None:
            wmap = {k: v for k, v in wmap.items() if k in allow_categories}
            if not wmap or sum(wmap.values()) <= 0:
                # 退化: 均匀采样
                wmap = {k: 1.0 for k in allow_categories}

        presets = list(wmap.keys())
        weights_v = [wmap[k] for k in presets]
        preset = rng.choices(presets, weights=weights_v, k=1)[0]

        # 白面黑线 white_black
        if preset == "white_black":
            return cls("gray", "none", "#ffffff", "#000000", seed=rng.randrange(1 << 30))

        # 其余 6 种 category
        category = preset
        families = allow_families or list(FACE_PALETTES.keys())
        family = rng.choice(families)
        mode3d, _ = FILL_CATEGORIES[category]

        # 面颜色: 未涂色时为白色, 否则从该族调色板取一色
        if mode3d == "none":
            fill_color = "#ffffff"
        else:
            fill_color = rng.choice(FACE_PALETTES[family])

        # 线条颜色: 
        #  - 未涂色（category=none, 非白面黑线 preset）: 从该族 + 灰色中选彩线
        #  - 已涂色: 黑色 或 加深的面颜色
        if mode3d == "none":
            line_key = rng.choice([k for k in LINE_COLORS if k in (family, "gray")])
            edge_color = LINE_COLORS[line_key]
        else:
            edge_color = rng.choice(["#000000", ColorUtil.darken(fill_color, 0.55)])

        return cls(family, category, fill_color, edge_color, seed=rng.randrange(1 << 30))

    def face_color_2d(self):
        """2D 填充色"""
        if self.mode2d == "none":
            return "#ffffff"
        return self.fill_color

    def face_color_3d(self, face_kind):
        """3D 面颜色

        :param 面类型:'front'(正面), 'side'(侧面), 'top'(顶面)
        """
        mode = self.mode3d
        if mode == "none":
            return "#ffffff"
        if mode == "right_only":
            # 只有右侧面涂色, 其余白色
            return self.fill_color if face_kind == "side" else "#ffffff"
        if mode == "all_same":
            return self.fill_color
        if mode == "front_dark":
            # 正面深、其余浅
            if face_kind == "front":
                return ColorUtil.darken(self.fill_color, 0.7)
            return ColorUtil.lighten(self.fill_color, 0.75)
        if mode == "side_dark":
            if face_kind == "side":
                return ColorUtil.darken(self.fill_color, 0.7)
            return ColorUtil.lighten(self.fill_color, 0.75)
        if mode == "erase":
            return self.fill_color
        return self.fill_color
    
    @property
    def is_erase(self):
        # return self.category == "erase"
        return False
    
    def __repr__(self):
        return (f"ColorStyle(family={self.colors}, "
                f"category={self.category}, "
                f"fill={self.fill_color}, "
                f"edge={self.edge_color})")


# ===================== 立体堆叠 =====================
DEFAULT_STYLE = CubeStyle("gray", "all_same", "#E5E5E5", "black")
class CubeStacking:
    def __init__(self, mat, size=1, style=DEFAULT_STYLE):
        self._matrix = mat
        self._size = size
        self._style = style
        self._level_polys = {}
        self._lines = []
        self._faces = []
        self._union_all = Polygon([])

    def set_style(self, style):
        self._style = style
        return self
    
    def reset(self):
        """重置缓存几何"""
        self._level_polys = {}
        self._lines = []
        self._faces = []
        self._union_all = Polygon([])

    def add_polygon(self, polygon_coords, level = None, kind=None):
        try:
            poly = Polygon(polygon_coords)
        except Exception:
            return
        if poly.is_empty or not poly.is_valid:
            return
        
        visible = poly.difference(self._union_all)
        if not visible.is_empty and kind is not None:
            self._faces.append((visible, kind))

        if level not in self._level_polys:
            self._level_polys[level] = []
        self._level_polys[level].append(poly)
        self._union_all = unary_union([self._union_all, poly])
    
    def add_lines(self, line_coords):
        if len(line_coords) < 2:
            raise ValueError("线段坐标必须包含至少两个点")  
        line = LineString(line_coords)

        res = line.difference(self._union_all)
        if res.is_empty:
            return
        elif res.geom_type == "LineString":
            x, y = res.xy
            self._lines.append([x,y])
        elif res.geom_type == "MultiLineString":
            for line in res:
                x, y = line.xy
                self._lines.append([x,y])
        
    def matrix2poly(self):
        """俯视角矩阵转变多边形坐标集"""
        mat = np.array(self._matrix)

        def projection(x, y, z):
            """原三维坐标系 横x 垂直向里y 竖z"""
            x_new = x + y * 0.5 * np.cos(np.pi / 4)
            y_new = z + y * 0.5 * np.sin(np.pi / 4)
            return x_new, y_new

        def dim2_dim3(x0, y0, z0, size):
            x0 = x0*size
            y0 = y0*size
            z0 = z0*size
            d = size / 2
            # 俯视下层从原点0-1-2-3 俯视上层4-5-6-7
            vertices = [
                [x0-d, y0-d, z0-d], [x0+d, y0-d, z0-d],
                [x0+d, y0+d, z0-d], [x0-d, y0+d, z0-d],
                [x0-d, y0-d, z0+d], [x0+d, y0-d, z0+d],
                [x0+d, y0+d, z0+d], [x0-d, y0+d, z0+d],
            ]
            # 坐标转换2D顶点列表
            verts2d = [projection(x, y, z) for x, y, z in vertices]
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
            faces = [
                [0,1,5,4],
                [1,2,6,5],
                [4,5,6,7]
            ]
            face_kinds = ["front", "side", "top"]

            for a, b in edges:
                line_coords = [points_2d[a], points_2d[b]]
                self.add_lines(line_coords)

            for face, kind in zip(faces, face_kinds):
                polygon_coords = [points_2d[i] for i in face]
                self.add_polygon(polygon_coords, kind=kind)

        rows, cols = mat.shape
        # x-从前往后 y-从右往左 h-从上到下
        for y in reversed(range(cols)):
            for x in reversed(range(rows)):
                h = mat[x, y]
                for z in reversed(range(h)):
                     dim2_dim3(y, rows - x, z, self._size)

    def grid(self, save_name=None):
        mat = move_xy_all0(self._matrix)
        rows, cols = mat.shape
        plt.figure(figsize=(rows, cols), dpi=150)
        ax = plt.gca()
        ax.set_aspect("equal")   
        ax.axis("off")  
        style = self._style

        for i in range(rows + 1):
            ax.plot([0, cols], [i, i], color=style.fill_color, linewidth=0.8)
        for j in range(cols + 1):
            ax.plot([j, j], [0, rows], color=style.fill_color, linewidth=0.8)

        for i in range(rows):
            for j in range(cols):
                val = mat[i,j]
                if val > 0:
                    rect = plt.Rectangle((j,i), 1, 1, color=self._fill, alpha=0.6)
                    ax.add_patch(rect)
                    ax.text(j + 0.5,i + 0.5, str(val),ha="center", va="center",fontsize=15)

        ax.invert_yaxis()         
        if save_name:
            plt.savefig(save_name, bbox_inches="tight", pad_inches=0.2)
        else:
            plt.show()
        plt.close()

    def geom_fill(self, ax, geom, color, alpha=0.85, zorder=1):
        """不同种类面染色"""
        if geom.is_empty:
            return
        geoms = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for g in geoms:
            xs, ys = g.exterior.xy
            ax.fill(xs, ys, facecolor=color, edgecolor="none",
                    alpha=alpha, zorder=zorder)

    def draw_3D(self,ax=None,figsize=(2,2),dpi=200):
        fig = None
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        else:
            fig = ax.figure
        ax.set_aspect('equal')
        ax.set_axis_off()
        ax.set_xlim(-0.7,4)
        ax.set_ylim(-0.7,4)

        style = self._style
        self.reset()
        self.matrix2poly()
        

        if style.mode3d != "none":
            for visible, kind in self._faces:
                color = style.face_color_3d(kind)
                if color == "#ffffff":
                    self.geom_fill(ax, visible, "#ffffff", alpha=1.0, zorder=1)
                else:
                    self.geom_fill(ax, visible, color, alpha=style.alpha, zorder=1)
        else:
            self.geom_fill(ax, self._union_all, "#ffffff", alpha=1.0, zorder=1)

        for line in self._lines:
            x, y = line
            ax.plot(x, y, color=style.edge_color, linewidth=0.6, zorder=4)

        if style.is_erase:
            return apply_erase(ax)    
        return fig

    def c3D(self,save_path=None,dpi=200):
        fig = self.draw_3D()
        if save_path:
            plt.savefig(save_path, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
        else:
            plt.show()
        plt.close(fig)

    def draw_2D(self,view,ax=None,dpi=200):
        f_mat, r_mat, l_mat, t_mat = view_mat(self._matrix)

        view_list = list(view)
        length = len(view_list)

        max_x = max(len(f_mat[0]),len(r_mat[0]),len(t_mat[0]))
        max_y = max(len(f_mat),len(r_mat),len(t_mat))
        fig = None
        if ax is None:
            fig = plt.figure(figsize=(2*length,2), dpi=dpi)
            gs = plt.GridSpec(1, length, width_ratios= [1.0 for _ in range(length)], wspace=0.3)
            ax_list = [plt.subplot(gs[i]) for i in range(length)]
        else:
            fig = ax.figure
            width_unit = 1 / length
            ax_list = [ax.inset_axes([i*width_unit, 0.0, width_unit, 1.0]) for i in range(length)]
            ax.set_axis_off()
        

        def view_draw(ax, view, max_x, max_y):
            if view == 'f':
                mat = f_mat
                language = '正面'
            elif view == 'r':
                mat = r_mat
                language = '右面'
            elif view == 'l':
                mat = l_mat
                language = '左面'
            elif view == 't':
                mat = t_mat
                language = '上面'
            else:
                raise TypeError("error: view must in [f,r,l,t]")
            mat2pic(ax, mat, max_x, max_y, self._style)
            ax.text(0.5, -0.05, language, fontsize=9, transform=ax.transAxes, va='bottom', ha='center')

        for i in range(length):
            view_draw(ax_list[i], view_list[i], max_x, max_y)

        return fig
    
    def c2D(self,view:str='frt',save_path=None,dpi=200):
        fig = self.draw_2D(view)
        if save_path:
            plt.savefig(save_path, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
        else:
            plt.show()
        plt.close(fig)

    def draw_23D(self,view,dpi=200):
        
        view_list = list(view)
        length = len(view_list)
        fig = plt.figure(figsize=(2+2*length,2), dpi=dpi)

        gs = plt.GridSpec(1, 2, width_ratios=[1,3], wspace=0.1)

        ax1 = plt.subplot(gs[0])
        self.draw_3D(ax1)
        ax1.text(0.5, -0.1, '立体图', fontsize=9, transform=ax1.transAxes, va='bottom', ha='center')

        ax2 = plt.subplot(gs[1])
        self.draw_2D(view,ax2)

        plt.subplots_adjust(left=0.05, right=0.95, top=0.98, bottom=0.1)

        return fig

    def c23D(self,view:str='frt',save_path=None,dpi=200):
        fig = self.draw_23D(view)
        if save_path:
            plt.savefig(save_path, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
        else:
            plt.show()
        plt.close(fig)

if __name__ == "__main__":
    from FontStyle import plt_use_global_font
    plt_use_global_font(verbose=False)

    # cubes = CubeStacking(random_valid_stack(3,3,3))
    style=CubeStyle.random()
    print(style)
    cubes = CubeStacking([[3, 1, 0], [1, 2, 1], [1, 0, 1]],style=style)
    cubes.c23D('tflr')
