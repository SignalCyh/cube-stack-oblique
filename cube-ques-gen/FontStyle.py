import os
import glob
import random
import platform
import matplotlib.pyplot as plt

from matplotlib import font_manager

# ====================== 常量定义 ======================
FONT_EXTS = ("*.ttf", "*.ttc", "*.otf")
FALLBACK_FONTS = ["SimHei", "Microsoft YaHei"] if platform.system() == "Windows" else ["DejaVu Sans"]
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font")
_FONT_CACHE={}


# ====================== 工具函数 ======================
def list_fonts(font_dir=_FONT_DIR):
    """列出字体目录下所有字体文件"""
    font_dir = font_dir or _FONT_DIR
    files = []
    for ext in ("*.ttf", "*.ttc", "*.otf"):
        files.extend(glob.glob(os.path.join(font_dir, ext)))
    return sorted(files)


def get_fonts_info(font_dir=_FONT_DIR):
    """提取字体信息
    Args:
        font_dir: 字体文件夹路径
    Returns:
        字体文件信息
    """
    font_files = list_fonts(font_dir)
    font_dict = {}
    for path in font_files:
        font_manager.fontManager.addfont(path)
        font_prop = font_manager.FontProperties(fname=path)
        if font_prop.get_name() not in font_dict:
            font_dict[font_prop.get_name()] = []
        font_dict[font_prop.get_name()].append(path)

    return font_dict
        

def _register_fonts(font_dir=_FONT_DIR,verbose=True):
    """注册指定目录全部字体并缓存(重名无法解决)
    Args:
        font_dir: 字体文件夹路径
    Returns:
        注册成功字体文件
    """
    fonts_dict = get_fonts_info(font_dir)
    fonts_reg = {k: min(v, key=lambda s: len(os.path.basename(s))) for k, v in fonts_dict.items()}

    for name, path in fonts_reg.items():
        file_basename = os.path.basename(path)
        if file_basename in _FONT_CACHE.values():
            continue
        try:
            font_manager.fontManager.addfont(path)
            _FONT_CACHE[name] = file_basename
        except Exception:
            continue
    fnames = list(_FONT_CACHE.keys())
    if verbose:
        print(f"[INFO] Registered fonts: {fnames}")
    return fnames


def clear_font_cache():
    global _FONT_CACHE
    _FONT_CACHE.clear()


def set_all_fonts(font_list):
    """统一设置 family / sans-serif / serif"""
    plt.rcParams["font.family"] = font_list
    plt.rcParams["font.sans-serif"] = font_list
    plt.rcParams["font.serif"] = font_list


# ====================== 全局字体 ======================
def plt_use_global_font(name=None,rng=random,font_dir=_FONT_DIR,verbose=True):
    """配置 Matplotlib 绘图中文字体，支持指定字体/随机自定义字体/系统默认字体
    Args:
        name: 期望使用的字体名，存在则优先加载
        rng: 随机数生成器，用于随机选取字体
        font_dir: 自定义字体文件夹路径
        verbose: 是否打印日志信息，关闭后无控制台输出
    Returns:
        当前生效的自定义字体名；无可用自定义字体返回 None
    """
    plt.rcParams["axes.unicode_minus"] = False
    font_names = _register_fonts(font_dir)

    lower_name_map = {fn.lower(): fn for fn in font_names}

    if name is not None:
        name_lower = name.lower()
        if name_lower in lower_name_map:
            real_font = lower_name_map[name_lower]
            set_all_fonts([real_font] + FALLBACK_FONTS)
            if verbose:
                print(f"[INFO] Using font: {real_font}")
            return real_font

    if name is not None and verbose:
        print(f"[WARNING] Font '{name}' not found in {font_dir}, will pick random font.")

    if font_names:
        random_font = rng.choice(font_names)
        set_all_fonts([random_font] + FALLBACK_FONTS)
        if verbose:
            print(f"[INFO] Using random font: {random_font}")
        return random_font

    set_all_fonts(FALLBACK_FONTS)
    if verbose:
        print(f"[INFO] No custom fonts found in {font_dir}, using system fallback fonts.")
    return None


def plt_use_random_font(rng=random, font_dir=_FONT_DIR, verbose=True):
    """随机选择一个字体并设置为全局字体"""
    plt.rcParams["axes.unicode_minus"] = False
    flist = list_fonts(font_dir)

    if not flist:
        if verbose:
            print(f"[INFO] No fonts found in {font_dir}, using system fallback fonts.")
        set_all_fonts(FALLBACK_FONTS)
        return None
    
    path = rng.choice(flist)
    font_manager.fontManager.addfont(path)
    font_prop = font_manager.FontProperties(fname=path)
    random_font = font_prop.get_name()
    set_all_fonts([random_font] + FALLBACK_FONTS)
    if verbose:
        print(f"[INFO] Using random font: {random_font}")
        return random_font


# ====================== 自检测试 ======================
if __name__ == "__main__":
    # 自检逻辑
    font_file_list = get_fonts_info(_FONT_DIR)
    print(f"[INFO] Detected font files: {[os.path.basename(p) for plist in font_file_list.values() for p in plist]}")
    # 测试随机字体
    font_used = plt_use_global_font()
    print(f"[INFO] Active font: {font_used}")
    # 清空缓存重新加载
    clear_font_cache()
