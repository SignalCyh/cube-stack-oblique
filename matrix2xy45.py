import random
import matplotlib.pyplot as plt
import numpy as np

from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely.plotting import plot_polygon

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

DEFAULT_FILL = "#E5E5E5"
DEFAULT_EDGE = "black"

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

def move_xy_all0(array, return_list: bool = False):
    """
    去除矩阵中全为0的整行、整列
    :param array: input list[list] / np.ndarray
    :param return_list: True返回嵌套list False返回np.ndarray
    :return: 剔除全零行列后的矩阵
    """
    mat = np.array(array)
    if mat.ndim != 2:
        raise ValueError("input error")
    
    res = mat[~np.all(mat == 0, axis=1)][:, ~np.all(mat == 0, axis=0)]
    if return_list:
        return res.tolist()
    return res

def view_mat(array, return_list: bool = False):
    mat = move_xy_all0(np.array(array))
    if mat.ndim != 2:
        raise ValueError("input error")
    
    res = []
    res.append(lst2mat(np.max(mat, axis=0)))
    res.append(lst2mat(np.max(mat, axis=1)[::-1]))
    res.append(lst2mat(np.max(mat, axis=1)))
    res.append((mat>0).astype(int))

    if return_list:
        return [i.tolist() for i in res]
    return res

def lst2mat(array, return_list: bool = False):
    """一维堆叠序列立体化"""
    lst = np.array(array)
    n = lst.max()
    i = np.arange(n-1, -1, -1)[:, None]
    res = (lst > i).astype(int)
    if return_list:
        return res.tolist()
    return res

class CubeStacking:
    def __init__(self, mat, size=1, fill=DEFAULT_FILL):
        self._matrix = mat
        self._size = size
        self._fill = fill
        self._level_polys = {}
        self._lines = []
        self._union_all = Polygon([])

    def add_polygon(self, polygon_coords, level = None) -> None:
        try:
            poly = Polygon(polygon_coords)
        except Exception:
            return
        if poly.is_empty or not poly.is_valid:
            return

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

            for a, b in edges:
                line_coords = [points_2d[a], points_2d[b]]
                self.add_lines(line_coords)

            for face in faces:
                polygon_coords = [points_2d[i] for i in face]
                self.add_polygon(polygon_coords)

        rows, cols = mat.shape
        # x-从前往后 y-从右往左 h-从上到下
        for y in reversed(range(cols)):
            for x in reversed(range(rows)):
                h = mat[x, y]
                for z in reversed(range(h)):
                     dim2_dim3(y, rows - x, z, self._size)

    def mat2pic(self, ax, mat, max_x, max_y, scale = 0.7, line_w = 0.6):
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
                        alpha=0.8, 
                        facecolor=self._fill, 
                        edgecolor=DEFAULT_EDGE, 
                        linewidth=line_w
                        )
                    ax.add_patch(rect)

    def grid(self, save_name=None):
        mat = move_xy_all0(self._matrix)
        rows, cols = mat.shape
        plt.figure(figsize=(rows, cols), dpi=150)
        ax = plt.gca()
        ax.set_aspect("equal")   
        ax.axis("off")  

        for i in range(rows + 1):
            ax.plot([0, cols], [i, i], color=DEFAULT_EDGE, linewidth=0.8)
        for j in range(cols + 1):
            ax.plot([j, j], [0, rows], color=DEFAULT_EDGE, linewidth=0.8)

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

    def draw_3D(self,ax=None,figsize=(2,2),dpi=200):
        fig = None
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        else:
            fig = ax.figure
        ax.set_aspect('equal') 
        ax.set_axis_off()
        
        self.matrix2poly()
        for line in self._lines:
            x, y = line
            ax.plot(x, y, color=DEFAULT_EDGE, linewidth=0.6)

        plot_polygon(self._union_all,ax,facecolor=self._fill,edgecolor="none",alpha=0.6,add_points=False)
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
        

        def view_draw(self, ax, view, max_x, max_y):
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
            self.mat2pic(ax, mat, max_x, max_y)
            ax.text(0.5, -0.05, language, fontsize=9, transform=ax.transAxes, va='bottom', ha='center')

        for i in range(length):
            view_draw(self, ax_list[i], view_list[i], max_x, max_y)

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
        ax2.set_axis_off()

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
    # cubes = CubeStacking(random_valid_stack(3,3,3))

    cubes = CubeStacking([[2, 0, 3], [1, 1, 1], [1, 1, 0]],fill='white')
    cubes.c23D('flrtf')
