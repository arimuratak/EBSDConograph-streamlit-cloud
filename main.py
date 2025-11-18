import os
import shutil
import streamlit as st
from dataIO import zip_folder
from init_session_state import build_session_state
from classEBSD import EBSDClass

build_session_state ()
if st.session_state['uploaded'] is None:
    st.session_state['uploaded'] = False
if st.session_state['doneEBSD'] is None:
    st.session_state['doneEBSD'] = False
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
        self.input = 'input'
        self.filePath = 'file.py'
        self.paramsPath = 'params.py'
        self.path_sample = 'sample'
        self.path_result = 'result'
        self.path_line_visual = 'result/out.shapes.json'
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
            file_name = 'sample.zip')

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
        flg_new_file = False
        if img_file is not None:
            if st.session_state['file_name'] is not None:
                flg_new_file = st.session_state['file_name'] != img_file.name
            else: flg_new_file = True
        
        if img_file is not None:
            st.write ('img file upload status {}, {}, {}'.format (img_file is not None, st.session_state['file_name'], img_file.name))
        param_file = None
        flg_new_param = False
        if (img_file is not None) and (st.session_state['file_name'] != img_file.name):
            param_file = None
            st.write (
                {'eng' : 'Uploade new parameter file...',
                 'jpn' : '新しいパラメータファイルをUploadしてください'
                 }[lang])
        
            param_file = st.file_uploader (
                {'eng' : 'Upload parameter file (py)',
                'jpn' : 'パラメータファイル アップロード (py)'}[lang],
                type = ['py'], key = 'param')
            if param_file is not None:
                if st.session_state['param_name'] is not None:
                    flg_new_param = st.session_state['param_name'] != param_file.name
                else: flg_new_param = True
        
        st.write ('img file upload status {}, param file upload status {}'.format(
            img_file is not None, param_file is not None))

        if (img_file is not None) and (
            param_file is not None) and flg_new_file and flg_new_param:
            st.write ('old img file {}, new img file {}, old param file {}, new param file {}'.format(
                st.session_state['file_name'], img_file.name, st.session_state['param_name'], param_file.name))
            #print (st.session_state['file_name'], img_file.name, st.session_state['param_name'], param_file.name)
            shutil.rmtree (self.input); os.makedirs (self.input)
            # EBSD画像は、inputフォルダへ保存
            fname = img_file.name
            st.session_state['file_name'] = fname
            savePath = os.path.join (self.input, fname)
            with open (savePath, 'wb') as f:
                f.write (img_file.getbuffer())

            # params.pyは、同じフォルダへ保存
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


    
    def menu_display_result_ebsd (self,):
        lang = st.session_state['lang']
        menu0 = {'eng':'EBSD orignal image',
                'jpn' : 'EBSD元画像'}[lang]
        #menu1 = {'eng' : 'EBSD image (w/ bands)',
        #             'jpn' : 'EBSD画像 (バンド付)'}[lang]
        #menu2 = {'eng' : '2nd derivative image',
        #             'jpn' : '2次微分画像'}[lang]
        menu3 = {'eng' : 'Bandsearch result',
                'jpn' : 'バンドサーチ結果'}[lang]
        menuList = []
        if st.session_state['uploaded']:
            menuList.append (menu0)
        elif st.session_state['doneEBSD']:
            menuList +=  [menu3, menu0]
        return menuList
    
    def menu_side_jobs (self,):
        lang = st.session_state['lang']
        menu0 = {'eng' : 'Upload files',
                 'jpn' : 'ファイルアップロード'}[lang]
        menu1 = {'eng' : 'Bandsearch',
                 'jpn' : 'バンドサーチ'}[lang]
        #menu2 = {'eng' : 'Band data editor',
        #         'jpn' : 'バンドデータ編集'}[lang]
        menu2 = 'indexing'
        menuList = []
        #if not st.session_state['uploaded']:
        #    menuList = [menu0]
        if st.session_state['uploaded']:
            menuList = [menu1]
        elif st.session_state['doneEBSD']:
            menuList = [menu1, menu2]
        
        return menuList    

if __name__ == '__main__':
    title = 'EBSD Conograph'
    objMain = MainClass ()
    objEBSD = EBSDClass ()

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
            #    st.session_state['uploaded'] = True
            #    st.session_state['doneEBSD'] = False
                    
        #if st.session_state['doneEBSD']:
        #    if 'Conograph' not in jobs_side: 
        #        jobs_side.append ('Conograph')

        if st.session_state['uploaded']:
            st.session_state['radio_index'] = 0
            job_bandsearch = {'eng' : 'Band Search','jpn' : 'バンドサーチ'}[lang]
            if job_bandsearch not in st.session_state['jobs_side']:
                st.session_state['jobs_side'].append (job_bandsearch)
            
        #--------------------------------------------------------
        #  サイドバーのjobメニュータブ
        #--------------------------------------------------------
        side_jobs = objMain.menu_side_jobs ()
        if len (side_jobs) > 0:
            tabs = st.tabs (side_jobs)
            for tab, job_name in zip (tabs, side_jobs):
            #with jobs[0]:
            #    objMain.upload_files ()
                with tab: # バンドサーチ
                    #if job_name in ['Upload files','ファイルアップロード']:
                    #    _ = objMain.upload_files ()
                    if job_name in ['Bandsearch','バンドサーチ']:
                        objEBSD.params_menu ()
                        objEBSD.run_band_search ()

                        edit_area = st.empty ()
                        conf_area = st.empty () # バンド座標編集エリア    

                        
                #if exec:
                #    st.session_state['uploaded'] = False
                #    st.session_state['doneEBSD'] = True

        #if st.session_state['doneEBSD']:
        #    _ = objEBSD.add_bands_intersection ()

    # メイン表示部
    menuList = objMain.menu_display_result_ebsd ()
    if len (menuList) > 0:

        with img_disp.container():
            #menu = st.radio (
            #    {'eng' : 'Select display', 'jpn' : '表示画像選択'}[lang],
            #    menuList, horizontal = True,
            #    index = st.session_state['radio_index'])
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
                        if is_clicked & (xydata is None):
                            st.write ('クリックは範囲外です')

                        with edit_area.container(border = True):
                            st.write ({
                            'eng' : '＜＜Band date editor＞＞',
                            'jpn' : '＜＜バンドデータ編集＞＞'}[lang])
                            edited = objEBSD.manage_data_editor (xydata, res)
                    
                        if edited:
                            with conf_area.container (border = True):
                                st.write ({
                                    'eng' : '＜＜For confirmation after edit＞＞',
                                    'jpn' : '＜＜編集後の確認用＞＞'}[lang])
                                objEBSD.df_for_monitor ()
                
