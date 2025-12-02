PC0 = [0.5, 0.2, 0.6]
# PCx,PCy,PCz (pixel)

Circle = False
# True: EBSD image is a circle, False: rectangular

RescaleParam = 400
# 画像のスケール変換

deg = 3
# 平滑化の次元

num_points = 3
# 2以上。
# 2*num_points+1点を用いて3次多項式をフィッティングする。

thred = 5.0
# ラドン変換の誤差値の計算
# (誤差値とピーク高さの比較によりバンド抽出を行う。)

MinCorrelation = 0.6
# Hough変換の2次微分のモデル値との相関は理論上[-1, 1]の範囲を取るが、
# 相関値がMinCorrelationより大きい場合にバンドとして検出する。
# Hough画像より検出したオブジェクトがバンドかどうか判定する際に使用する。

BAND_WIDTH_MIN = 0.02
BAND_WIDTH_MAX = 0.2
# バンド幅の下限と上限 (px)

dtheta = 5.0
# これより小さい角度で交わるバンドは、同一のバンドとみなす。
# Hough変換の座標(rho, theta)が近いバンドの中から最良のバンドを選定する際に使用する。

use_band_width = 0
# use only band centers : 0, use band width : 1 

searchLevel = 0
# 0:quick search, 1:exhaustive search

range_deg = 1.0
# The input phi, sigma are supposed to contain errors within this range (degree).

tolerance_unit_cell = 3.0
# The unit-cell scales s1, s2 computed from band widths are supposed to equal,
# if both of s1 <= s2*(this.value) and s2 <= s1*(this.value) hold.

tolerance_vector_length_gain = 0.02
# The unit-cell scales s1, s2 computed from band widths are supposed to equal,
# if both of s1 <= s2*(this.value) and s2 <= s1*(this.value) hold.

tolerance_vector_length = 0.01
# (Used only for selecting output solutions when there are very similar ones)
#  lattice-vector lengths d1, d2 are considered to equal, if d1 <= d2*(1+ this.value) and d2 <= d1*(1+ this.value) hold.

num_miller_idx = 400
# The number of the Miller indices generated for computation of the figure of merit M.

th_hkl = 7
# The upper threshold for the absolute values |h|, |k|, |l| of the Miller indices generated for computation of the figure of merit M.

ref_shift_dXdYdZ = [1, 1, 1]
# Refine the pattern center shift DeltaX, DeltaY, DeltaZ? (Z: the direction perpendicular to the screen)
# (No: 0, Yes: 1)

th_fm = 3.0
# Only the solution with the figure of merit larger than this value is output.

axisRhombohedralSym = 'Rhombohedral'
# Axis for rhombohedral symmetry (“Rhombohedral” or “Hexagonal”)

axisMonoclinicSym = 'B'
# Axis for monoclinic symmetry ("A", "B", or "C")

latexStyle = 0
# Output in latex style (0:no, 1:yes (for journal writing))
