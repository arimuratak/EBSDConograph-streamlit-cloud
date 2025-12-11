import os
import time
import shutil
import streamlit as st
from dataIO import zip_folder
from init_session_state import build_session_state
from classEBSD import EBSDClass
from classConograph import Conograph

build_session_state ()
if st.session_state['uploaded'] is None:
    st.session_state['uploaded'] = False
if st.session_state['doneEBSD'] is None:
    st.session_state['doneEBSD'] = False
if st.session_state['doneCono'] is None:
    st.session_state['doneCono'] = False
#if st.session_state['file_name'] is None:
#    st.session_state['file_name'] = ''
if st.session_state['jobs_side'] is None:
    st.session_state['jobs_side'] = []
if st.session_state['add_band'] is None:
    st.session_state['add_band'] = False
if st.session_state['radio_index'] is None:
    st.session_state['radio_index'] = 0
if st.session_state['enable_added_band'] is None:
    st.session_state['enable_added_band'] = True
if st.session_state['just_after_bandsearch'] is None:
    st.session_state['just_after_bandsearch'] = False
if st.session_state['unix_time'] is None:
    st.session_state['unix_time'] = ''
#if st.session_state['param_name'] is None:
#    st.session_state['param_name'] = ''

class MainClass:
    def __init__(self,):
        self.input = './input'
        self.filePath = './file.py'
        self.paramsPath = './params.py'
        self.path_sample = './sample'
        self.path_result = './result'
        self.path_line_visual = './result/out.shapes.json'
        self.H = None
        self.W = None
        
        os.makedirs (self.input, exist_ok = True)
        os.makedirs (self.path_result, exist_ok = True)

    def select_langage (self,):
        lang_sel = st.radio (
            'Select', ['English', 'Japanese'],
                             horizontal = True)
        if lang_sel == 'English': lang = 'eng'
        else: lang = 'jpn'
        st.session_state['lang'] = lang

    #-------------------------------------------------------
    # サンプルデータのzipファイルダウンロード
    #-------------------------------------------------------
    def down_load_sample (self,):
        lang = st.session_state['lang']
        zip_bytes = zip_folder (self.path_sample)
        st.download_button (
            label = {
                'eng':'Download sample data\n(zip format)', 
                'jpn' : 'サンプルデータ ダウンロード\n(zip形式)'}[lang],
            data = zip_bytes,
            file_name = 'sample.zip', key = 'sample_download')

    #-------------------------------------------------------
    # file.pyの生成
    #-------------------------------------------------------
    def make_file_py (self, fname):
        text = 'path = "input/{}"'.format (fname)
        with open (self.filePath, 'w', encoding = 'utf-8') as f:
            f.write (text)
        st.session_state['imgPath'] = os.path.join ('input', fname)

    #-------------------------------------------------------
    # ファイルのアップロード（EBSD画像、パラメータ）
    #-------------------------------------------------------
    def upload_files (self,):
        uploaded = False
        lang = st.session_state['lang']

        img_file = st.file_uploader (
            {'eng' : 'Upload EBSD image file',
             'jpn' : 'EBSD画像ファイル アップロード'}[lang],
            type = ['jpg', 'jpeg', 'png', 'tif'], key = 'img')
        
        if img_file is None: key = 'param'
        else: key = 'param_' + img_file.name
        param_file = st.file_uploader (
                {'eng' : 'Upload parameter file (py)',
                'jpn' : 'パラメータファイル アップロード (py)'}[lang],
                type = ['py'], key = key)
        
        flg_new_file = False
        if img_file is not None:
            if st.session_state['file_name'] is not None:
                flg_new_file = st.session_state['file_name'] != img_file.name
            else: flg_new_file = True
        
        flg_new_param = False
        if param_file is not None:
            flg_new_param = True
     
        
        if flg_new_file & flg_new_param:
            shutil.rmtree (self.input); os.makedirs (self.input)
            # EBSD画像は、inputフォルダへ保存
            fname = img_file.name
            st.session_state['file_name'] = fname
            savePath = os.path.join (self.input, fname)
            with open (savePath, 'wb') as f:
                f.write (img_file.getbuffer())

            # params.pyは、同じフォルダへ保存
            if os.path.exists (self.paramsPath):
                os.remove (self.paramsPath)
            with open (self.paramsPath, 'wb') as f:
                f.write (param_file.getbuffer())
            
            # file.pyは、同じフォルダへ保存
            self.make_file_py (fname)
            uploaded = True
            st.session_state['param_name'] = param_file.name
            st.session_state['file_name'] = img_file.name

        if uploaded:
            st.session_state['uploaded'] = True
            st.session_state['doneEBSD'] = False
            st.session_state['doneCono'] = False
    
    def menu_display_result_ebsd (self,):
        lang = st.session_state['lang']
        menu0 = {'eng':'EBSD orignal image',
                'jpn' : 'EBSD元画像'}[lang]
        menu3 = {'eng' : 'Bandsearch result',
                'jpn' : 'バンドサーチ結果'}[lang]
        menu4 = {'eng' : 'Conograph result',
                 'jpn' : 'Conograph結果表示'}[lang]
        ebsdlog = 'EBSD log'
        conographlog = 'Conograph log'
        menuList = []
        if st.session_state['doneCono']:
            menuList = [menu4, conographlog, menu3, ebsdlog, menu0]
        elif st.session_state['doneEBSD']:
            menuList +=  [menu3, ebsdlog, menu0]
        elif st.session_state['uploaded']:
            menuList.append (menu0)
        
        return menuList
    
    def menu_side_jobs (self,):
        lang = st.session_state['lang']
        menu1 = {'eng' : 'Bandsearch',
                 'jpn' : 'バンドサーチ'}[lang]
        menu2 = 'Conograph'
        menuList = [menu1, menu2]
        return menuList    

if __name__ == '__main__':
    title = 'EBSD Conograph'
    objMain = MainClass ()
    objEBSD = EBSDClass ()
    objCono = Conograph ()

    # メイン側のレイアウト
    title_place = st.title (title)
    img_disp = st.empty() # 画像表示エリア

    #サイドバー側のレイアウト＆処理
    with st.sidebar:
        # 言語選択＆サンプルデータダウンロード
        col1, col2 = st.columns (2)
        with col1: objMain.select_langage()
        lang = st.session_state['lang']
        with col2: objMain.down_load_sample()

        #　ファイルアップロード
        with st.container (border = True):
            _ = objMain.upload_files()
            
        #--------------------------------------------------------
        #  サイドバーのjobメニュータブ
        #--------------------------------------------------------
        side_jobs = objMain.menu_side_jobs ()
        if len (side_jobs) > 0:
            tabs = st.tabs (side_jobs)
            for tab, job_name in zip (tabs, side_jobs):
                with tab: # バンドサーチ
                    if (job_name in ['Bandsearch','バンドサーチ']) & st.session_state['uploaded']:
                        objEBSD.params_menu ()
                        objEBSD.run_band_search ()

                    elif (job_name == 'Conograph') & st.session_state['doneEBSD']:
                        objCono.params_menu ()
                        result = objCono.conograph_exec ()
                        flg_res = objCono.get_result (result)
           
        edit_area = st.empty ()
        conf_area = st.empty () # バンド座標編集エリア    


    # メイン表示部
    menuList = objMain.menu_display_result_ebsd ()
    if len (menuList) > 0:
        with img_disp.container():
            menu_tabs = st.tabs (menuList)

        for tab, tab_name in zip (menu_tabs, menuList):
            with tab:
                if tab_name in ['EBSD orignal image','EBSD元画像']: # EBSD元画像表示
                        objEBSD.display_ebsd ()
                elif tab_name in ['Bandsearch result', 'バンドサーチ結果']:
                    with st.container (border = True):
                        st.write ({'eng' : '＜＜EBSD image (w/bands)＞＞',
                                    'jpn' : '＜＜EBSD画像(バンド付き)＞＞'}[lang])
                        objEBSD.display_ebsd_with_band ()
                    with st.container (border = True):    
                        st.write ({'eng' : '＜＜2nd Derivative＞＞',
                                    'jpn' : '＜＜2次微分画像＞＞'}[lang])
                        xydata, is_clicked, res = objEBSD.display_clicked_point ()
                        st.session_state['xydata'] = xydata
                        st.session_state['res_clicked'] = res
                    if is_clicked & (xydata is None):
                        st.write ('クリックは範囲外です')

                    with edit_area.container(border = True):
                        st.write ({
                            'eng' : '＜＜Band date editor＞＞',
                            'jpn' : '＜＜バンドデータ編集＞＞'}[lang])
                        xydata = st.session_state['xydata']
                        res = st.session_state['res_clicked']
                        edited = objEBSD.manage_data_editor (xydata, res)
                        if edited:
                            with conf_area.container (border = True):
                                st.write ({
                                    'eng' : '＜＜For confirmation after edit＞＞',
                                    'jpn' : '＜＜編集後の確認用＞＞'}[lang])
                                objEBSD.df_for_monitor ()

                elif tab_name == 'EBSD log':
                    objEBSD.display_log ()

                elif tab_name == 'Conograph log':
                    flg_log = objCono.request_log ()
                    objCono.display_log ()

                elif tab_name in ['Conograph result', 'Conograph結果表示']:
                    objCono.display_result ()
                
