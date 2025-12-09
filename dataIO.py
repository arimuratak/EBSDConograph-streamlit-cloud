import os
import io
import re
import zipfile
from PIL import Image
import pandas as pd

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

def read_params (names = [
            'PC0', 'Circle', 'RescaleParam', 'deg', 'num_points',
            'thred', 'MinCorrelation',
            'BAND_WIDTH_MIN', 'BAND_WIDTH_MAX', 'dtheta'], path = 'params.py'):
    ans = {}
    with open (path, 'r', encoding = 'utf-8') as f:
        for line in f.readlines ():
            if ('=' in line) & (line.split ('=')[0].strip() in names):
                line = line.split('#')[0].split ('=')
                name = line[0].strip()
                vstr = line[1].strip().strip ("'")

                if name in ['PC0', 'ref_shift_dXdYdZ']:
                    vstr = vstr.strip('[').strip(']').split (',')
                    vstr = [v.strip() for v in vstr]
                    
                ans[name] = vstr

    return ans

def update_params (params : dict, path = 'params.py'):
    ans = []
    names = list (params.keys())
    with open (path, 'r', encoding = 'utf-8') as f:
        for line in f.readlines ():
            if ('PC0' in line ) & ('=' in line):
                vstr = '[' + ', '.join (params['PC0']) + ']'
                ans.append ('PC0 = ' + vstr + '\n')
            elif ('=' in line) & (line.split ('=')[0].strip() in names):
                name = line.split ('=')[0].strip()
                ans.append (name + ' = ' + params[name] + '\n')
            else:
                ans.append (line)

    ans = ''.join (ans)
    with open (path, 'w', encoding = 'utf-8') as f:
        f.write (ans)

def read_params_import_bandsearch ():
    import params
    #importlib.reload (params)

    ans = {'PC0' : params.PC0, 'Circle' : params.Circle,
           'RescaleParam' : params.RescaleParam, 'deg' : params.deg,
           'num_points' : params.num_points, 'thred' : params.thred,
           'MinCorrelation' : params.MinCorrelation,
           'BAND_WIDTH_MIN' : params.BAND_WIDTH_MIN,
           'BAND_WIDTH_MAX' : params.BAND_WIDTH_MAX,
           'dtheta' : params.dtheta}

    return ans

def to_params_conograph (readPath = None,
                    savePath = 'input/input.txt', params = None):
    namesDict  = {
        'use_band_width' : '# use only band centers : 0, use band width : 1 ',
        'searchLevel' : '# 0:quick search, 1:exhaustive search',
        'range_deg' : '# The input phi, sigma are supposed to contain errors within this range (degree).',
        'tolerance_unit_cell' : '# The unit-cell scales s1, s2 computed from band widths are supposed to equal,\n# if both of s1 <= s2*(this.value) and s2 <= s1*(this.value) hold.',
        'tolerance_vector_length_gain' : '# (Used only for Bravais lattice determination and selection of output solutions when there are very similar solutions)\n# if both of s1 <= s2*(this.value) and s2 <= s1*(this.value) hold.',
        'tolerance_vector_length' : '# (Used only for selecting output solutions when there are very similar ones)\n#  lattice-vector lengths d1, d2 are considered to equal, if d1 <= d2*(1+ this.value) and d2 <= d1*(1+ this.value) hold.',
        'num_miller_idx' : '# The number of the Miller indices generated for computation of the figure of merit M.',
        'th_hkl' : '# The upper threshold for the absolute values |h|, |k|, |l| of the Miller indices generated for computation of the figure of merit M.',
        'ref_shift_dXdYdZ' : '# Refine the pattern center shift DeltaX, DeltaY, DeltaZ? (Z: the direction perpendicular to the screen)\n# (No: 0, Yes: 1)',
        'th_fm' : '# Only the solution with the figure of merit larger than this value is output.',
        'axisRhombohedralSym' : '# Axis for rhombohedral symmetry (“Rhombohedral” or “Hexagonal”)',
        'axisMonoclinicSym' : '# Axis for monoclinic symmetry ("A", "B", or "C")',
        'latexStyle' : '# Output in latex style (0:no, 1:yes (for journal writing))'}
    
    if params is None:
        names = list (namesDict.keys())
        params = read_params (names, readPath)
    
    use_band_width = None
    ans = []
    for k, v in params.items():
        comment = namesDict[k]
        if k == 'use_band_width':
            use_band_width = int (v == '1')
        elif k == 'ref_shift_dXdYdZ':
            v = '          '.join (v)
            ans.append (comment + '\n' + v + '\n')
        elif k == 'axisRhombohedralSym':
            v = '      ' + v.strip("'")
            ans.append (comment + '\n' + v + '\n')
        elif k in ['axisMonoclinicSym', 'latexStyle']:
            v = '              ' + v
            ans.append (comment + '\n' + v + '\n')
        else:
            ans.append (comment + '\n' + v + '\n')
    ans = '\n'.join (ans)
    with open (savePath, 'w', encoding = 'utf-8') as f:
        f.write (ans)
    return params, use_band_width

def read_kikuchi_radius (path):
    f = open (path, 'r', encoding = 'utf-8')
    line = list (f.readlines())[1]
    f.close()
    value = re.findall(r"\d+\.\d+", line)[0]
    return value

def read_cono_summary (path = 'result/out.txt'):
    ans = {}
    nums = ['({})'.format(i) for i in range (1,15)]
    with open (path, 'r', encoding = 'utf-8') as f:
        for line in f.readlines():
            if any ([num in line for num in nums]):
                line = line.strip()
                lattice = line.split (' ')[1]
                ans[lattice] = line.strip()
            if len (ans) == 14: break
    return ans

def put_separate (text):
    return re.sub(r'(?<=\d)\s+(?=[\-\d])', ', ', text)

def read_out_file(path):
    lattice = None
    candNo = None
    ans = {}
    ans['rad_kikuchi'] = read_kikuchi_radius (path)
    ans['summary'] = read_cono_summary (path)
    
    with open(path, 'r' ,encoding = 'utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    while len (lines) > 0:
        line = lines.pop (0)
        if '### Candidates for' in line:
            lattice = line.split()[-2]
            ans[lattice] = {}
        elif ('###' in line) & ('No.' in line):
            candNo = 'Candidate No. ' + re.findall (r'\d+', line)[0]
            ans[lattice][candNo] = {}
        elif '# a : b : c  alpha  beta  gamma (degree) scale_factor (before refinement)' in line:
            ans[lattice][candNo]['lattice_const_before_refinement'] = put_separate (lines.pop(0))
        elif '# a : b : c  alpha  beta  gamma (degree) scale_factor, a/c, b/c (after refinement)' in line:
            ans[lattice][candNo]['lattice_const_after_refinement'] = put_separate (lines.pop(0))
        elif '# a : b : c  alpha  beta  gamma (degree) scale_factor, a/c, b/c, a, b, c (after refinement)' in line:
            ans[lattice][candNo]['lattice_const_after_refinement'] = put_separate (lines.pop(0))
        elif '# propagation errors when the errors of the input angles are assumed to be within 1 deg.' in line:
            ans[lattice][candNo]['propagation_errors'] = put_separate (lines.pop (0))
        elif '# Buerger-reduced reciprocal_lattice basis (before refinement)' in line:
            v1 = put_separate (lines.pop(0))
            v2 = put_separate (lines.pop(0))
            v3 = put_separate (lines.pop(0))
            ans[lattice][candNo]['Buerger_lattice_basis_before_refinement'] = [v1, v2, v3]
        elif '# Buerger-reduced reciprocal_lattice basis, propagation errors  (after refinement)' in line:
            v1 = put_separate (lines.pop(0))
            v2 = put_separate (lines.pop(0))
            v3 = put_separate (lines.pop(0))
            ans[lattice][candNo]['Buerger_lattice_basis_after_refinement'] = [v1, v2, v3]
        elif '# Euler angles: theta1, theta2, theta3, Error_theta1, Error_theta2, Error_theta3 (deg) (after refinement)' in line:
            ans[lattice][candNo]['euler_angles'] = put_separate (lines.pop(0))
        elif '# Projection center shifts: Delta_x, Delta_y, Delta_z, Error_Delta_x, Error_Delta_y, Error_Delta_z,' in line:
            ans[lattice][candNo]['projection_center_shifts'] = put_separate (lines.pop (0))
        elif '# Number of computed bands' in line:
            ans[lattice][candNo]['num_bands'] = put_separate (lines.pop(0))
        elif '# Figure of merit at the beginning and the end of the refinement' in line:
            ans[lattice][candNo]['figure_of_merit'] = put_separate (lines.pop(0))
        elif '# Chi-squares at the beginning and the end of the refinement' in line:
            ans[lattice][candNo]['chi_squares'] = put_separate (lines.pop(0))
        elif '# Indexing with the parameters before refinement' in line:
            _ = lines.pop(0)
            vsList = []
            while True:
                if ('#' in lines[0]) | (lines[0] == ''):
                    break
                vsList.append (put_separate (lines.pop(0)))
            ans[lattice][candNo]['indexing_before_refinement'] = vsList
        elif '# Indexing with the parameters after refinement' in line:
            _ = lines.pop(0)
            vsList = []
            while True:
                if ('#' in lines[0]) | (lines[0] == ''):
                    break
                vsList.append (put_separate (lines.pop(0)))
            ans[lattice][candNo]['indexing_after_refinement'] = vsList

    return ans

def read_input_txt (names, path = 'input/input.txt'):
    with open (path, 'r', encoding = 'utf-8') as f:
        lines = list (f.readlines())
    ans = {}
    for line in lines:
        line = line.strip()
        if ('#' in line) | (len (line) == 0):
            continue
        name = names.pop (0)
        ans[name] = line.strip()
        if len (names) == 0: break
    return ans

def is_numeric (value):
    try:
        float (value)
        return True
    except ValueError:
        return False

if __name__ == '__main__':
    names = [
            'use_band_width', 'searchLevel', 'range_deg',
            'tolerance_unit_cell',
            'tolerance_vector_length_gain',
            'tolerance_vector_length', 'num_miller_idx',
            'th_hkl', 'ref_shift_dXdYdZ', 'th_fm',
            'axisRhombohedralSym', 'axisMonoclinicSym',
            'latexStyle']
    ans = read_input_txt (names = names[1:])
    print (ans)