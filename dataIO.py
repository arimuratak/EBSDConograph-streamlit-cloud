import os
import io
import zipfile
from PIL import Image

def zip_folder(folder_path):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                zipf.write(file_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer

def fig2img (fig, ax):
    fig.canvas.draw()                              # レンダリング
    renderer = fig.canvas.get_renderer()
    bbox = ax.get_window_extent(renderer)          # Axes の表示座標系（左下原点, 単位: ピクセル）
    ax_bbox_canvas = dict (
        x0 = bbox.x0, y0 = bbox.y0,
        w = bbox.width, h = bbox.height)  
        
    buf = io.BytesIO()
    fig.savefig(buf, format = "png", dpi = fig.dpi)
    buf.seek(0)
    img = Image.open(buf)
    img_w, img_h = img.size

    canvas_w, canvas_h = fig.canvas.get_width_height()
    sx = img_w / canvas_w
    sy = img_h / canvas_h

    ax_px = {
    "x0": ax_bbox_canvas["x0"] * sx,
    "y0": ax_bbox_canvas["y0"] * sy,
    "w":  ax_bbox_canvas["w"]  * sx,
    "h":  ax_bbox_canvas["h"]  * sy}
    return img, ax_px

# クリックされた２次微分画像の座標を(θ,ρ)に変換
# クリックされた地点が範囲外であればNoneを返す
def cvtPos (res, ax_px, ax, img_h):
    cx, cy_top = res["x"], res["y"]
    cy = img_h - cy_top  # 左下原点に反転

    # 画像内Ax領域へのオフセット補正
    rx = cx - ax_px["x0"]
    ry = cy - ax_px["y0"]
    inside = (0 <= rx <= ax_px["w"]) and (0 <= ry <= ax_px["h"])
    if not inside:
        return None
    else:
        fx = rx / ax_px["w"]
        fy = ry / ax_px["h"]
        xmin, xmax = ax.get_xbound()
        ymin, ymax = ax.get_ybound()
        xdata = xmin + fx * (xmax - xmin)
        ydata = ymin + fy * (ymax - ymin)
        ydata *= -1
        return xdata, ydata
