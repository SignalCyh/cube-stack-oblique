# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(FONT_DIR, "font_preview.png")

# preview sample text
SAMPLE = "正方体堆叠 三视图 ABCabc 0123"
LABEL_SIZE = 22
SAMPLE_SIZE = 40

# plot layout
PAD = 24
ROW_GAP = 26
LINE_GAP = 6
ROW_HEIGHT = LABEL_SIZE + SAMPLE_SIZE + ROW_GAP

def get_label_font(size: int):
    """标签字体"""
    simhei_path = os.path.join(FONT_DIR, "simhei.ttf")
    if os.path.exists(simhei_path):
        try:
            return ImageFont.truetype(simhei_path, size)
        except:
            pass
    # 系统默认字体兜底
    return ImageFont.load_default(size=size)


def get_dir_font_files(font_dir=FONT_DIR):
    """获取指定目录下的字体文件列表"""
    try:
        all_files = os.listdir(font_dir)
    except Exception as e:
        print(f"[error] loading directory {font_dir} failed: {str(e)}")
        exit(1)

    font_files = sorted(
        f for f in all_files
        if f.lower().endswith((".ttf", ".ttc"))
    )
    return font_files


def get_label_info(font_dir=FONT_DIR):
    """获取字体标签信息"""
    entries = []  # (label_text, sample_font, label_font)
    font_files = get_dir_font_files(font_dir)
    for fname in font_files:
        font_path = os.path.join(font_dir, fname)
        idx = 0
        
        while True:
            try:
                base_font = ImageFont.truetype(font_path, SAMPLE_SIZE, index=idx)
            except Exception as e:
                print(f"[INFO] {fname} font index {set(range(idx))}")
                break
            
            try:
                family, style = base_font.getname()
            except Exception as e:
                print(f"[error] failed to get font name for {fname} index {idx}: {str(e)}")
                family, style = fname, "未知样式"
            
            label_text = f"{fname} [idx {idx}]  ->  {family} / {style}"
            label_font = ImageFont.truetype(font_path, LABEL_SIZE, index=idx)
            entries.append((label_text, base_font, label_font))
            idx += 1
            if not font_path.lower().endswith(".ttc"):
                print(f"[INFO] {fname} font index {{0}}")
                break
    return entries


def render_font_preview(font_dir=FONT_DIR, out_path=OUT_PATH):
    entries = get_label_info(font_dir)

    img_w = 1200
    img_h = PAD * 2 + ROW_HEIGHT * len(entries)

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)
    global_label_font = get_label_font(LABEL_SIZE)

    y_offset = PAD
    for label_txt, sample_font, _ in entries:
        # 绘制字体信息标签
        draw.text((PAD, y_offset), label_txt, fill="#444444", font=global_label_font)
        # 绘制样例文字
        sample_y = y_offset + LABEL_SIZE + LINE_GAP
        draw.text((PAD, sample_y), SAMPLE, fill="#000000", font=sample_font)
        # 行分割线
        line_y = y_offset + ROW_HEIGHT - LINE_GAP
        draw.line([(PAD, line_y), (img_w - PAD, line_y)], fill="#e2e2e2", width=1)
        y_offset += ROW_HEIGHT

    # 保存输出
    img.save(out_path)
    print(f"预览图已保存：{out_path}")
    print(f"共渲染字体变体数量：{len(entries)}")


if __name__ == "__main__":
    render_font_preview()