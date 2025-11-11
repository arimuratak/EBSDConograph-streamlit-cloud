import os
import shutil
import numpy as np
import json
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from dataIO import fig2img, cvtPos
from EBSD import run, getLinesForDisplay,\
    addBandsFrom4Bands, removeBands, editBandCenter,\
        addBand_theta_edges, addBand_theta_rho

class EBSDClass:
    def __init__(self,):
        self.input = 'input'
        self.filePath = 'file.py'
        self.paramsPath = 'params.py'
        self.path_sample = 'sample'
        self.path_result = 'result'
        self.path_line_visual = 'result/out.shapes.json'
        self.H = None
        self.W = None
        self.cols = ['idx', 'score', 'θ', 'ρ_center', 'ρ_begin', 'ρ_end']

        
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
            run ()
            st.session_state['doneEBSD'] = True
            self.to_result_folder ()
            st.session_state['uploaded'] = False
            st.session_state['doneEBSD'] = True
            df = self.get_lines_for_display ()
            st.session_state['lines_for_display'] = df
            st.session_state['just_after_bandsearch'] = True
        

    def get_lines (self,):
        with open (self.path_line_visual, 'r', encoding = 'utf-8') as f:
            linesDict = json.load (f)

        return linesDict
    
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
    
    def display_ebsd (self, img = None, needScale = False):       
        if img is None:
            path = st.session_state['imgPath']
            img = cv2.imread (path)
            img = cv2.cvtColor (img, cv2.COLOR_BGR2RGB)
        
        with st.container(border = True):
            if needScale:
                st.pyplot (img)
            else:
                st.image (img)

    #def put_line (self, img, xys, color = (0,0,255)):
    #    xy1, xy2 = xys
    #    cv2.line (img, tuple (xy1), tuple (xy2),
    #              thickness = 1, color = color,
    #              lineType = cv2.LINE_AA)

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
    # EBSD画像へのバンド線描画 (edge, center)
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
            idx = row['idx']
            xys_center = (row['center_xy1'],row['center_xy2'])
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
                self.put_line_index (img, list (xys_center), idx)
            ax.imshow (img)
            step = 50
            ax.set_xticks (np.arange (0, W + 1, step))
            ax.set_yticks (np.arange (0, H + 1, step))
            plt.tight_layout ()
        return fig
    
    def display_ebsd_with_band (self,):
        sels = self.ebsd_line_display_menu ()
        path = 'result/out.rescaled.png'
        img = cv2.imread (path)
        img = cv2.cvtColor (img, cv2.COLOR_BGR2RGB)
        fig = self.draw_lines_ebsd (img, sels) # EBSD画像バンド線追加
        self.display_ebsd (fig, needScale = True)
    
    def add_scale_2nd (self, img):
        H, W, _ = img.shape
        fig, ax = plt.subplots ()
        ax.imshow (img)
        #ax.set_xlabel("X (pixels)", fontsize=12)
        #ax.set_ylabel("Y (pixels)", fontsize=12)

        step_X = 25
        step_y = 50
        ax.set_xticks (np.arange (0, 180 + 1, step_X))
        ax.set_yticks (np.arange (int (- H / 2), int (H / 2) + 1, step_y))
        plt.tight_layout ()

        return fig


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

    def pix2scale_y (self, pix):
            return '{:.0f}'.format (pix - int (self.H / 2))
        
    def pix2scale_x (self, pix):
            return '{:.0f}'.format (pix * 180 / self.W)

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

    def display_2nd_der (self, key = '2ndDerivative'):
        fig, ax = self.image_2nd_der_with_line ()
        with st.container(border = True):
            #st.image (img, use_container_width = True)
            #st.pyplot (fig)
            img, ax_px = fig2img (fig, ax)
            res = streamlit_image_coordinates (img, key = key)
            st.session_state['last_coords'] = res
        
        return res, ax_px, img, ax

    def display_clicked_point (self, key = '2ndDerivative'):
        res, ax_px, img, ax = self.display_2nd_der(key)
        xydata = None
        is_clicked = False
        if res is not None:
            is_clicked = True
            _, img_h = img.size
            xydata = cvtPos (res, ax_px, ax, img_h)
            #クリックされても範囲外であれば、xydataはNone
        return xydata, is_clicked

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
    
    def add_bands_intersection (self,):
        lang = st.session_state['lang']
        flg = st.button (
            {'eng' : 'Add bands by intersections',
            'jpn' : '交点からバンド生成'}[lang],
                            key = 'add_bands_intersec')
        if flg:
            addBandsFrom4Bands ()
            st.session_state['lines_for_display'] =\
                        self.get_lines_for_display ()
        return flg

    def df_for_edit (self,):
        df = st.session_state['lines_for_display']
        df = df.loc[:, self.cols]
        
        newDf = st.data_editor (df, hide_index = True,
                            num_rows = 'dynamic',
                            key = 'edit',
                            #disabled = self.cols
                            disabled = ['idx', 'score'])
        return df, newDf

    def df_for_monitor (self,):
        df = st.session_state['lines_for_display']
        df = df.loc[:, self.cols]
        
        _ = st.data_editor (df, hide_index = True,
                            num_rows = 'fixed',
                            key = 'monitor',
                            disabled = self.cols,
                            #height = 45 * len (df)
                            )
        
    def search_deleted_rows (self, df, newDf):
        indices = []
        if len (newDf) < len (df):
            new_indices = newDf['idx'].tolist()
            for idx in df['idx'].tolist():
                if idx not in new_indices:
                    indices.append (idx - 1)
        return indices

    def judge_changed_df (self, df, newDf):
        flg_len = len (df) < len (newDf)
        if flg_len:
            newDf = newDf.loc[:len (df)]
            return None, None, None, flg_len
        
        indices = self.search_deleted_rows (df, newDf)
        if len (indices) > 0:
            return None, None, indices, flg_len

        idx_changed = None; col_changed = None
        for col in df.columns:
            olds = np.array (df[col].tolist()) #; print (olds)
            news = np.array (newDf[col].tolist()) #; print (news)
            flgs = (olds != news).astype (int) #; print (flgs)
            if flgs.sum () > 0:
                idx_changed = np.argmax (flgs)
                col_changed = col
                break

        return idx_changed, col_changed, indices, flg_len

    def addBandThetaRho (self, xydata):
        res = ''
        if xydata is not None:
            theta, rho = xydata #; print (xydata)
            res = addBand_theta_rho (theta, rho)
            st.session_state['lines_for_display'] = self.get_lines_for_display ()
        return res
    #----------------------------------------------------
    # データ表関連処理（index, 相関値, θ, ρ_center, ρ_begin, ρ_end）
    # 追加、行削除、数値変更 (θ, ρ_begin, ρ_end, ρ_center)
    #----------------------------------------------------
    def manage_data_editor (self, xydata = None):
        added = False
        res = self.addBandThetaRho (xydata)
        if res == 'Found': added = True

        lang = st.session_state['lang']
        #col1, col2 = st.columns (2)
        doneIntsec = self.add_bands_intersection ()
        
        old_df, new_df = self.df_for_edit ()
        # idx, col : 変更された行番号とカラム名
        # indices : 削除された行番, flg : 行が追加された(True)        
        idx, col, indices, flg = self.judge_changed_df(old_df, new_df)
        #print ('#1-------', idx, col)
        if flg:
            st.write (
                {'eng' : 'Impossible to add new row...',
                 'jpn' : '新しい行は追加できません...'}[lang])
            
        if len (indices) > 0:
            removeBands (indices)
            st.session_state['lines_for_display'] = self.get_lines_for_display()
            
        if (idx is not None) & (col is not None):
            if col == 'ρ_center':
                rho = new_df.loc [idx, col]
                res = editBandCenter (rho, idx)
            if col in ['θ', 'ρ_begin', 'ρ_end']:
                #idx -= 1
                theta = new_df.at[idx, 'θ'],
                rhomin = new_df.at[idx, 'ρ_begin']
                rhomax = new_df.at[idx, 'ρ_end']
                removeBands ([idx])
                addBand_theta_edges (theta, rhomin, rhomax)
            st.session_state['lines_for_display'] = self.get_lines_for_display()
            #print (st.session_state['lines_for_display'])
        #print (added, xydata, idx, col, indices)
        if added | doneIntsec:
            if st.button ({
                'eng' : 'Band id added. Feedback to image??',
                'jpn' : 'バンドが追加されています。画像へ反映させますか？'}[lang]):
                st.write ({'eng' : 'Feedback complete!!',
                               'jpn' : '反映完了!!'}[lang])

        if (idx is not None) | (col is not None) | (len (indices) > 0):
            if st.button ({'eng' : 'Fix data change??',
                               'jpn' : 'データ変更を確定しますか？'}[lang]):
                st.write ({'eng' : 'Complete!!',
                               'jpn' : '確定しました!!'}[lang])      
        return (idx is not None) | (col is not None)