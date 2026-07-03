from shapely.geometry import Point, LineString
from typing import Set

import numpy as np

class LPoint:
    """带标签点类"""
    def __init__(self, x: float, y: float, label: str):
        self.geom = Point(x, y)  
        self.label = label      

    @property
    def x(self) -> float:
        return self.geom.x

    @property
    def y(self) -> float:
        return self.geom.y

    def distance(self, other: "LPoint") -> float:
        return self.geom.distance(other.geom)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LPoint):
            return False
        return self.geom.equals(other.geom)
    
    def __hash__(self):
        return self.label

    def __repr__(self):
        return f"LabeledPoint(label={self.label}, coord=({self.x},{self.y}))"


class LLine:
    """带标签线段类"""
    def __init__(self, p1: LPoint, p2: LPoint, label: str=''):
        pts = sorted([p1, p2], key=lambda p: p.label)
        self.p1: LPoint = pts[0]
        self.p2: LPoint = pts[1]

        self.labels:list = [f"{pts[0].label}{pts[1].label}"]
        if label.strip():
            self.labels.append(label)
            
        self.geom = LineString([(pts[0].x, pts[0].y), (pts[1].x, pts[1].y)])

    @property
    def length(self) -> float:
        """线段长度"""
        return self.geom.length
    def intersection(self, other: "LLine"):
        """获取交点"""
        return self.geom.intersection(other.geom)

    def __eq__(self, other: object) -> bool:
        """== 判断：坐标完全一致即相等"""
        if not isinstance(other, LLine):
            return False
        return self.geom.equals(other.geom)
    
    def __hash__(self):
        """哈希函数"""
        return self.labels[0]

    def __repr__(self):
        return (
            f"LLine(labels={self.labels}, "
            f"end1={self.p1.label}, end2={self.p2.label}, "
            f"length={round(self.length, 2)})"
        )


class GeoGraphMat:
    """几何图矩阵"""
    def __init__(self):
        self.point_list: list[LPoint] = []       # 点集
        self.line_set: Set[LLine] = set()       # 线段集
        self.dist_mat = np.zeros((0, 0), dtype=np.float64) # 距离邻接矩阵

    @property
    def pnum(self) -> int:
        return len(self.point_list)
    
    def get_point_index(self, pt: LPoint) -> int:
        """获取点下标，用于距离矩阵"""
        return self.point_list.index(pt)
    
    def newplabel(self, label:str=''):
        if label.strip():
            return label
        
        idx = 65+self.pnum
        labels = [p.label for p in self.point_list]
        while chr(idx) in labels:
            idx += 1
        return chr(idx)

    def add_point(self, pt: LPoint):
        """添加单个点并更新矩阵"""
        if pt in self.point_list:
            return
        self.point_list.append(pt)
        # n_old = self.dist_mat[0] if len(self.dist_mat) != 0 else 0
        n_old = self.dist_mat[0]
        new_mat = np.zeros((n_old + 1, n_old + 1), dtype=np.float64)
        new_mat[:n_old, :n_old] = self.dist_mat

    def add_point_line(self, pt1:LPoint, pt2:LPoint, label:str):
        """添加线段并更新交点和距离矩阵"""
        # 1. 线段两个端点个加入点集
        self.add_point(pt1)
        self.add_point(pt2)
        line = LLine(pt1,pt2,label)
        
        # 2. 交点加入点集,并更新线段
        newlines = set()
        for ls in self.line_set:
            inter = line.intersection(ls)
            if inter.geom_type == "Point" and not inter.is_empty:
                linter = LPoint(inter.x, inter.y, self.newplabel())

                points = [pt1, pt2, ls.p1, ls.p2]
                new_lines = [LLine(p, linter) for p in points]
                newlines.update(new_lines)
                self.line_set.update(new_lines)
                self.add_point(linter)

        # 3. 更新邻接矩阵
        for new_line in new_lines:
            pts = [new_line.p1, new_line.p2]
            idx = [self.get_point_index(pt) for pt in pts]
            
            dist = pts[0].distance(pts[1])
            self.dist_mat[idx[0], idx[1]] = dist
            self.dist_mat[idx[1], idx[0]] = dist




