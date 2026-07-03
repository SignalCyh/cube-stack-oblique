# style_config.py 样式配色全局配置

import os

# 面可用颜色族
FACE_PALETTES = {
    "gray":   ["#E5E5E5", "#d9d9d9", "#cccccc", "#bfbfbf"],
    "blue":   ["#7aa7c3", "#5c8b9a", "#6d8091", "#66a0b8"],
    "yellow": ["#c8907b", "#c99991", "#fffec3"],
    "red":    ["#836773"],
}

# 线条可用颜色
LINE_COLORS = {
    "black":  "#000000",
    "gray":   "#808080",
    "blue":   "#5c8b9a",
    "yellow": "#c8907b",
    "red":    "#836773",
}

# 统一涂色类别 (3D, 2D)
FILL_CATEGORIES = {
    "none":       ("none",       "none"),
    "right_only": ("right_only", "all_same"),
    "all_same":   ("all_same",   "all_same"),
    "front_dark": ("front_dark", "all_same"),
    "side_dark":  ("side_dark",  "all_same"),
    "erase":      ("erase",      "erase"),
}

# 各类别采样权重
CATEGORY_WEIGHTS = {
    "none": 1.0, "right_only": 1.0, "all_same": 1.5,
    "front_dark": 1.0, "side_dark": 1.0, "erase": 1.0,
}

# 图片样式权重
DEFAULT_STYLE_WEIGHTS = {
    "white_black": 0.60,
    "none":        0.40 / 6,
    "right_only":  0.40 / 6,
    "all_same":    0.40 / 6,
    "front_dark":  0.40 / 6,
    "side_dark":   0.40 / 6,
    "erase":       0.40 / 6,
}

# 当前生效的权重表; 可通过 set_style_weights() / parse_style_weights() 调整
STYLE_WEIGHTS = dict(DEFAULT_STYLE_WEIGHTS)

def set_style_weights(weights):
    """标准归一化"""
    s = float(sum(weights.values()))
    if s <= 0:
        raise ValueError("style weights must sum > 0")
    STYLE_WEIGHTS.clear()
    STYLE_WEIGHTS.update({k: float(v) / s for k, v in weights.items()})
    return dict(STYLE_WEIGHTS)

def parse_style_weights(spec):
    """解析权重逗号分隔字符串（用于环境变量），未列出的 preset 设为 0。"""
    if not spec:
        return dict(STYLE_WEIGHTS)
    w = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        k, v = part.split("=", 1)
        w[k.strip()] = float(v.strip())
    # 未列出的补 0
    for k in DEFAULT_STYLE_WEIGHTS:
        w.setdefault(k, 0.0)
    return set_style_weights(w)

if os.environ.get("STYLE_WEIGHTS"):
    try:
        parse_style_weights(os.environ["STYLE_WEIGHTS"])
    except Exception as _e:  # 解析失败保留默认
        pass
