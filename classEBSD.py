import os
import shutil
import numpy as np
import random
import pandas as pd
import cv2
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from dataIO import fig2img, cvtPos, update_params, \
    read_params, is_numeric, save_logsList
from EBSD import run, getLinesForDisplay,\
    addBandsFrom4Bands, removeBands, editBandCenter,\
        addBand_theta_edges, addBand_theta_rho
random.seed (2025)

class EBSDClass:
    def __init__(self,):
        self.input = './input'
        self.filePath = './file.py'
        self.paramsPath = './params.py'
        self.path_sample = './sample'
        self.path_result = './result'
        #self.path_line_visual = './result/out.shapes.json'
        self.H = None
        self.W = None
        self.cols = ['idx', 'score', 'θ', 'ρ_center', 'ρ_begin', 'ρ_end']
        self.cols_tr = self.cols[2:]
        self.param_names = [
            'PC0', 'Circle', 'RescaleParam', 'deg', 'num_points',
            'thred', 'MinCorrelation',
            'BAND_WIDTH_MIN', 'BAND_WIDTH_MAX', 'dtheta']
        self.logPath = 'result/LOG_EBSD.txt'
        
        os.makedirs (self.input, exist_ok = True)
        os.makedirs (self.path_result, exist_ok = True)

    #-------------------------------------------------------
    # EBSD.run()により出力された結果ファイルをresultフォルダへ移動
    #-------------------------------------------------------
    def to_result_folder (self,):
        for path in os.listdir ('.'):
            if any ([suffix in path for suffix in [
                'txt','tif', 'json', 'png', 'pickle']]):
                dst = os.path.join (self.path_result, path)
                shutil.move (path, dst)
            
    #-------------------------------------------------------
    # バンドサーチの実行、結果ファイルの格納
    #-------------------------------------------------------
    def run_band_search (self,):
        lang = st.session_state['lang']
        exec = st.button ({
            'eng' : 'Band search Run',
            'jpn' : 'バンドサーチ実行'}[lang])
        if exec:
            logs = run ()
            #st.session_state['uploaded'] = False
            st.session_state['doneEBSD'] = True
            st.session_state['doneCono'] = False
            df = self.get_lines_for_display ()
            st.session_state['lines_for_display'] = df
            st.session_state['just_after_bandsearch'] = True
            st.session_state['prev_idx'] = -100
            st.session_state['prev_col'] = ''
            save_logsList (logs, self.logPath)
            st.session_state['num_trial'] = str (random.randint (0, 1000))
    
    #-------------------------------------------------------
    # バンドサーチの結果（BandKukans）から、
    # 相関値,θ,ρ_center,ρ_begin,ρ_endのデータフレームを生成
    #-------------------------------------------------------
    def getBandDataFrame (self,):
        bands = st.session_state['BandKukans']
        df = {'idx' : [], 'score' : [], 'theta' : [],
              'rho_center' : [], 'rho_begin' : [], 'rho_end' : []}
        for i, band in enumerate (bands, 1):
            df['idx'].append (i)
            df['score'].append (band.convolution)
            df['theta'].append (band.center_rt[1])
            df['rho_center'].append (band.center_rt[0])
            df['rho_begin'].append (band.edge_rhos[0])
            df['rho_end'].append (band.edge_rhos[1])

        return pd.DataFrame (df)



    #-------------------------------------------------------
    # バンドサーチの結果（BandKukans）から、
    # バンドを描画するためのデータフレームを生成
    # EBSD画像上のedge1, edge2, center　(x1,y1),(x2,y2)
    # 2次微分画像上の (x1,y1),(x2,y2)
    #-------------------------------------------------------
    def get_lines_for_display (self,):
        bands = st.session_state['BandKukans']
        shape = st.session_state['shape']
        df = {'idx' : [], 'score' : [],
              'edge1_xy1' : [], 'edge1_xy2' : [],
              'edge2_xy1' : [], 'edge2_xy2' : [],
              'center_xy1'  : [], 'center_xy2' : [],
              '2nd_xy1' : [], '2nd_xy2' : []}
        
        scores = []
        BandEdges_rhotheta  = []
        BandCenters_rhotheta = []
        for band in bands:
            scores.append (band.putConvolution())
            BandEdges_rhotheta.append([band.edge_rhos[0], band.center_rt[1]])
            BandEdges_rhotheta.append([band.edge_rhos[1], band.center_rt[1]])
            BandCenters_rhotheta.append(band.center_rt)

        edges = []
        centers = []
        getLinesForDisplay(shape, BandEdges_rhotheta, edges)
        getLinesForDisplay(shape, BandCenters_rhotheta, centers)

        for i, (score, edge1, edge2, center, b2nd1, b2nd2) in enumerate (
                    zip (scores, edges[::2], edges[1::2], centers,
                        BandEdges_rhotheta[::2],
                        BandEdges_rhotheta[1::2]), 1):
            df['idx'].append (i)
            df['score'].append (score)
            df['edge1_xy1'].append ([edge1[0][0], edge1[1][0]])
            df['edge1_xy2'].append ([edge1[0][1], edge1[1][1]])
            df['edge2_xy1'].append ([edge2[0][0], edge2[1][0]])
            df['edge2_xy2'].append ([edge2[0][1], edge2[1][1]])
            df['center_xy1'].append ([center[0][0], center[1][0]])
            df['center_xy2'].append ([center[0][1], center[1][1]])
            df['2nd_xy1'].append ([b2nd1[1], b2nd1[0]])
            df['2nd_xy2'].append ([b2nd2[1], b2nd2[0]])

        df = pd.DataFrame (df).sort_values ('score', ascending = False)
        df['idx'] = list (range (1, len (df) + 1))
        df['θ'] = df['2nd_xy1'].apply (lambda x: x[0])
        df['ρ_begin'] = df['2nd_xy1'].apply (lambda x: x[1])
        df['ρ_end'] = df['2nd_xy2'].apply (lambda x: x[1])
        df['ρ_center'] = (df['ρ_begin'] + df['ρ_end']) / 2
        
        return df

    #---------------------------------------------------------
    # EBSD画像へのバンド番号挿入
    # img : 画像, xys : バンド線の座標（x1, y1）, (x2, y2)
    # idx : 番号
    # imgのinstanceで、st.plot or st.imageを判断
    #---------------------------------------------------------    
    def display_ebsd (self, img = None):       
        if img is None:
            path = st.session_state['imgPath']
            
            while img is None:
                img = cv2.imread (path)
            
            img = cv2.cvtColor (img, cv2.COLOR_BGR2RGB)
        
        with st.container(border = True):
            if isinstance (img, Figure):
                st.pyplot (img)
            else:
                st.image (img)

    #---------------------------------------------------------
    # EBSD画像へのバンド番号挿入
    # img : 画像, xys : バンド線の座標（x1, y1）, (x2, y2)
    # idx : 番号
    #---------------------------------------------------------
    def put_line_index (self, img, xys, idx):
        H, W, _ = img.shape
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        font_color = (255, 255, 0)
        idx = str (idx)
        textSize = cv2.getTextSize (
            idx, font, font_scale, font_thickness)[0]
        for x, y in xys:
            x = int (x); y = int (y)
            dx = abs (W - x)
            dy = abs (H - y)
            dxy = np.array ([x, y, dx, dy])
            tbl = [(0, y + int (textSize[1] / 2)),
                   (x - int (textSize[0] / 2), textSize[1]),
                   (W - textSize[0], y + int (textSize[1] / 2)), 
                   (x - int (textSize[0] / 2), H - 2)]
            xys = tbl[dxy.argmin()]

            cv2.putText (img, idx, xys, font,
                    font_scale, font_color, font_thickness,
                    lineType = cv2.LINE_AA)

    #---------------------------------------------------------
    # EBSD画像へのバンド線描画 (edge, center, 番号)
    # selsの入力で選択
    #---------------------------------------------------------
    def draw_lines_ebsd (self, img, sels = ['edge', 'center']):
        H, W, _ = img.shape
        if st.session_state['lines_for_display'] is None:
            df = self.get_lines_for_display ()
        else:
            df = st.session_state['lines_for_display']
        fig = plt.figure ()
        ax = fig.add_subplot (1,1,1)
        for _, row in df.iterrows():
            if 'edge' in sels:
                plt.plot (
                    [row['edge1_xy1'][0],row['edge1_xy2'][0]],
                    [row['edge1_xy1'][1],row['edge1_xy2'][1]],
                    c = 'y')
                plt.plot (
                    [row['edge2_xy1'][0],row['edge2_xy2'][0]],
                    [row['edge2_xy1'][1],row['edge2_xy2'][1]],
                    c = 'y')
            if 'center' in sels:
                plt.plot (
                    [row['center_xy1'][0],row['center_xy2'][0]],
                    [row['center_xy1'][1],row['center_xy2'][1]],
                    c = 'y')
            if 'number' in sels:
                idx = row['idx']
                xys_center = [row['center_xy1'], row['center_xy2']]
                self.put_line_index (img, xys_center, idx)
            ax.imshow (img)
            step = 50
            ax.set_xticks (np.arange (0, W + 1, step))
            ax.set_yticks (np.arange (0, H + 1, step))
            plt.tight_layout ()
        return fig
    
    #---------------------------------------------------------
    # バンド線付きEBSD画像の表示（center, edges, 番号）
    #---------------------------------------------------------
    def display_ebsd_with_band (self,):
        lang = st.session_state['lang']
        col1, col2 = st.columns (2)
        with col1:
            st.write ({'eng' : '＜＜EBSD image (w/bands)＞＞',
                        'jpn' : '＜＜EBSD画像(バンド付き)＞＞'}[lang])
        with col2:   
            sels = self.ebsd_line_display_menu ()
        path = 'result/out.rescaled.png'
        img = cv2.imread (path)
        img = cv2.cvtColor (img, cv2.COLOR_BGR2RGB)
        fig = self.draw_lines_ebsd (img, sels) # EBSD画像バンド線追加
        self.display_ebsd (fig)
    
    #---------------------------------------------------------
    # 2次微分画像へのバンド番号の挿入
    #---------------------------------------------------------
    def put_line_index_2nd (self, img, xy, idx):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        font_color = (255, 255, 0)
        idx = str (idx)
        textSize = cv2.getTextSize (
            idx, font, font_scale, font_thickness)[0]
        xy[0] = int (xy[0]) + 1 # int (textSize[0] / 2)
        xy[1] = int (xy[1]) - int (textSize[1] / 2) - 1
        cv2.putText (img, idx, xy, font, font_scale,
                     font_color, font_thickness,
                     lineType = cv2.LINE_AA)

    #---------------------------------------------------------
    # バンド線付き2次微分画像の生成
    #---------------------------------------------------------
    def image_2nd_der_with_line (self,):
        img = cv2.imread ('result/out.2nd_derivative.png')
        img = cv2.cvtColor (img, cv2.COLOR_BGR2RGB)
        H, W, _ = img.shape
        if st.session_state['lines_for_display'] is None:
            df = self.get_lines_for_display ()
        else:
            df = st.session_state['lines_for_display']
        
        fig = plt.figure (figsize = (6,6))
        ax = fig.add_subplot (1,1,1)
        for _, row in df.iterrows():
            idx = row['idx']
            xy1 = row['2nd_xy1'].copy(); xy2 = row['2nd_xy2'].copy()
            plt.plot ([xy1[0], xy2[0]],[xy1[1],xy2[1]], c = 'y', linewidth = 3)
            
            xy1[0] *= W / 180
            xy2[0] *= W / 180
            xy1[1] += H / 2
            xy2[1] += H / 2
            xy1[0] = int (xy1[0]); xy1[1] = int (xy1[1])
            
            # ライン番号付与
            self.put_line_index_2nd (img, xy1, idx)
        
        # 縦横の目盛り付き2次元微分画像(matplotlibのfig形式)
        ax.imshow (img, cmap = plt.cm.Greys_r,
            extent = (0, 180, H / 2, - H / 2))
        ax.set_aspect ('auto', adjustable = 'box')
        ax.set_xlim ((0, 180))
        ax.set_ylim ((H // 2, - H // 2))
        
        plt.tight_layout ()
        #plt.savefig ('test.png')
        return fig, ax

    #---------------------------------------------------------
    # バンド線付き2次微分画像の表示＆クリック情報出力
    # 
    #---------------------------------------------------------
    def display_2nd_der (self, key = '2ndDerivative'):
        fig, ax = self.image_2nd_der_with_line ()
        with st.container(border = True):
            #st.image (img, use_container_width = True)
            #st.pyplot (fig)
            img, ax_px = fig2img (fig, ax)
            res = streamlit_image_coordinates (img, key = key)
            st.session_state['last_coords'] = res
        
        return res, ax_px, img, ax

    #---------------------------------------------------------
    # バンド線付き2次微分画像の表示＆クリック情報出力
    # 
    #---------------------------------------------------------
    def display_clicked_point (self, key = '2ndDerivative'):
        res, ax_px, img, ax = self.display_2nd_der(key)
        xydata = None
        is_clicked = False
        if res is not None:
            is_clicked = True
            _, img_h = img.size
            xydata = cvtPos (res, ax_px, ax, img_h)
            #クリックされても範囲外であれば、xydataはNone
        return xydata, is_clicked, res

    #---------------------------------------------------------
    # バンド線付きEBSD画像の描画選択
    # （center, edges, index）
    #---------------------------------------------------------
    def ebsd_line_display_menu (self,):
        edge, center, number = st.columns (3)
        sels = []
        with edge:
            if st.checkbox ('Edge', key = 'edge', value = True):
                sels.append ('edge')
            
        with center:
            if st.checkbox ('Center', key = 'center'):
                sels.append ('center')

        with number:
            if st.checkbox ('Number', key = 'number', value = True):
                sels.append ('number')
        
        return sels

    #---------------------------------------------------------
    # 交点からのバンド生成
    #---------------------------------------------------------
    def add_bands_intersection (self,):
        lang = st.session_state['lang']
        flg = st.button (
            {'eng' : 'Add bands by intersections',
            'jpn' : '交点からバンド生成'}[lang],
                            key = 'add_bands_intersec')
        if flg:
            logs = addBandsFrom4Bands ()
            save_logsList (logs, self.logPath)
            st.session_state['lines_for_display'] =\
                        self.get_lines_for_display ()
        return flg

    #---------------------------------------------------------
    # バンドデータ表の表示と編集
    # df：編集前, newDf : 編集後
    #---------------------------------------------------------
    def to_str (self, df):
        df['score'] = df['score'].apply (lambda x: '{:4f}'.format(x))
        df['θ'] = df['θ'].apply (lambda x: '{:.4f}'.format(x))
        df['ρ_begin'] = df['ρ_begin'].apply (lambda x: '{:.4f}'.format(x))
        df['ρ_end'] = df['ρ_end'].apply (lambda x: '{:.4f}'.format(x))
        df['ρ_center'] = df['ρ_center'].apply (lambda x: '{:.4f}'.format(x))
        return df
    
    def to_float (self, df):
        df['score'] = df['score'].apply (float)
        df['θ'] = df['θ'].apply (float)
        df['ρ_begin'] = df['ρ_begin'].apply (float)
        df['ρ_end'] = df['ρ_end'].apply (float)
        df['ρ_center'] = df['ρ_center'].apply (float)
        return df

    def numerical_check (self, df):
        flg = True
        for col in self.cols_tr:
            flg &= all ([is_numeric (v) for v in df[col].tolist()])
        return flg

    def df_for_edit (self, mode = ''):
        df = st.session_state['lines_for_display']
        df = df.loc[:, self.cols]
        df = self.to_str (df)
        key = 'edit' + st.session_state['num_trial'] + mode
        newDf = st.data_editor (df, hide_index = True,
                            num_rows = 'dynamic',
                            key = key,
                            #disabled = self.cols
                            disabled = ['idx', 'score'])

        if not self.numerical_check (newDf):
            st.write ('Please input numerical value!!!')
            newDf = df

        df = self.to_float (df)
        newDf = self.to_float (newDf)
        return df, newDf

    #---------------------------------------------------------
    # バンドデータ表の表示（編集不可）
    #---------------------------------------------------------
    def df_for_monitor (self,):
        df = st.session_state['lines_for_display']
        df = df.loc[:, self.cols]
        df = self.to_str (df)
        
        _ = st.data_editor (df, hide_index = True,
                            num_rows = 'fixed',
                            key = 'monitor',
                            disabled = self.cols)
        
    #---------------------------------------------------------
    # バンドデータ表の行削除検知
    #---------------------------------------------------------
    def search_deleted_rows (self, df, newDf):
        indices = []
        if len (newDf) < len (df):
            new_indices = newDf['idx'].tolist()
            for idx in df['idx'].tolist():
                if idx not in new_indices:
                    indices.append (idx - 1)
        return indices

    #----------------------------------------------------
    # 表示されているデータ表変更検知（index, 相関値, θ, ρ_center, ρ_begin, ρ_end）
    # df : 表示データ表, newDf : data_editorの出力
    #----------------------------------------------------
    def judge_changed_df (self, df, newDf):
        flg_len = len (df) < len (newDf)
        # 行の追加
        if flg_len:
            newDf = newDf.loc[:len (df)]
            return None, None, [], flg_len
        
        # 行の削除
        indices = self.search_deleted_rows (df, newDf)
        if len (indices) > 0:
            return None, None, indices, flg_len

        # 行の変更
        idx_changed = None; col_changed = None
        for col in df.columns:
            olds = np.array (df[col].tolist())
            news = np.array (newDf[col].tolist())
            flgs = (olds != news).astype (int)
            if flgs.sum () > 0:
                idx_changed = np.argmax (flgs)
                col_changed = col
                break

        return idx_changed, col_changed, indices, flg_len

    #----------------------------------------------------
    # バンド追加処理（xydata: 2次微分画像のクリック座標）
    # 
    #----------------------------------------------------
    def addBandThetaRho (self, xydata):
        res = ''
        if xydata is not None:
            theta, rho = xydata
            res = addBand_theta_rho (theta, rho)
            st.session_state['lines_for_display'] = self.get_lines_for_display ()
        return res
    
    #----------------------------------------------------
    # データ表関連処理（index, 相関値, θ, ρ_center, ρ_begin, ρ_end）
    # 追加、行削除、数値変更 (θ, ρ_begin, ρ_end, ρ_center)
    #----------------------------------------------------
    def manage_data_editor (self, xydata = None, res = None):
        added = False
        if (res is not None) and (
            st.session_state['unix_time'] != str (res['unix_time'])):
            is_found = self.addBandThetaRho (xydata)
            if is_found == 'Found':
                st.session_state['unix_time'] = str (res['unix_time'])
                added = True

        lang = st.session_state['lang']
        col1, col2 = st.columns (2)
        with col1:
            doneIntsec = self.add_bands_intersection ()
        
        old_df, new_df = self.df_for_edit (st.session_state['edit_mode'])
        # idx, col : 変更された行番号とカラム名
        # indices : 削除された行番, flg : 行が追加された(True)        
        idx, col, indices, flg_expanded = self.judge_changed_df(old_df, new_df)
        
        if flg_expanded:
            with col2:
                st.write (
                    {'eng' : 'Delete added row. Impossible to add new row in editor...',
                     'jpn' : 'エディタ内での新しい行は追加できませんので削除してください...'}[lang])
        
        elif len (indices) > 0:
            removeBands (indices)
            st.session_state['lines_for_display'] = self.get_lines_for_display()
            st.session_state['edit_mode'] = 'deleted'
            
        elif (idx is not None) & (col is not None):
            if col == 'ρ_center':
                rho = new_df.loc [idx, col]
                res = editBandCenter (rho, idx)
            if col in ['θ', 'ρ_begin', 'ρ_end']:
                #idx -= 1
                theta = new_df.at[idx, 'θ'],
                rhomin = new_df.at[idx, 'ρ_begin']
                rhomax = new_df.at[idx, 'ρ_end']
                removeBands ([idx])
                logs = addBand_theta_edges (theta, rhomin, rhomax)
                save_logsList(logs, self.logPath)
            st.session_state['lines_for_display'] = self.get_lines_for_display()
            st.session_state['edit_mode'] = 'changed' + str (idx) + col + str (random.choice(list(range(1,1000))))
        
        if (idx is not None) & (col is not None):
            with col2:
                st.button ({
                    'eng' : 'Click to fix data change',
                    'jpn' : 'データ変更確定のためクリック'}[lang])
              
        return (idx is not None) | (col is not None)
    
    def read_params (self,):
        params = read_params ()
        st.session_state['params'] = params

    def param_PC0 (self, params):
        param_name = st.session_state['file_name']
        PC0 = params['PC0']
        col0, col1, col2, col3 = st.columns (4)
        with col0: st.write ('PC0')
        ans = []
        for i, (pc, col) in enumerate (
                                zip (PC0, [col1, col2, col3])):
            with col:
                key = 'PC0_{}_{}'.format(i, param_name) 
                pc = st.text_input (
                        key, PC0[i], key = key,
                        label_visibility = 'hidden')
                if not is_numeric (pc):
                    st.write ('Please input numeric value!!')
                ans.append (pc)
        
        return ans

    def param_uniq (self, params, name = 'Circle'):
        param_name = st.session_state['file_name']
        vstr = str (params[name])
        if name == 'Circle':
            options = ['False', 'True']
            ans = st.selectbox (name,
                    options, index = options.index(vstr),
                    key = name + param_name)
        else:
            ans = st.text_input (name, vstr, key = name + param_name)
            if not is_numeric(ans):
                st.write ('Please input numeric value!!')

        return ans
    
    def params_menu (self,):
        lang = st.session_state['lang']
        params = read_params (self.param_names,
                            path = self.paramsPath)

        ans = {}
        with st.expander (
            {'eng' : 'Parameter menu',
             'jpn' : 'パラメータメニュー'}[lang]):
            ans['PC0'] = self.param_PC0 (params)
            col1, col2 = st.columns (2)
            for i, name in enumerate (self.param_names[1:]):
                if i % 2 == 0:
                    with col1:
                        ans[name] = self.param_uniq (params, name)
                else:
                    with col2:
                        ans[name] = self.param_uniq (params, name)
        
        if len (ans) > 0:
            update_params (params = ans, path = self.paramsPath)

    def display_log (self,):
        lang = st.session_state['lang']
        if os.path.exists (self.logPath):
            with open (self.logPath, 'r', encoding = 'utf-8') as f:
                st.download_button (
                    {'eng' : 'Download log file',
                     'jpn' : 'logファイルダウンロード'}[lang],
                     data = f,
                     file_name = 'log_ebsd.txt',
                     mime = 'text/plain', key = 'ebsd_log')
        
            with open (self.logPath, 'r', encoding = 'utf-8') as f:
                text = f.read ()
            st.text_area ('log', text, height = 400,
                    label_visibility = 'hidden')
