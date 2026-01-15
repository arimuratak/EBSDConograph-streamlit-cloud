import os
import time
import shutil
import streamlit as st
from dataIO import zip_folder,\
    bdata_check, update_use_band_width

class MainClass:
    def __init__(self,):
        self.input = './input'
        self.filePath = './file.py'
        self.paramsPath = './params.py'
        self.path_sample = './sample'
        self.path_result = './result'
        self.path_line_visual = './result/out.shapes.json'
        self.dataPath0 = 'result/data0.txt'
        self.dataPath1 = 'result/data1.txt'
        self.dataPath_uploaded = 'input/data_uploaded.txt'
        self.H = None
        self.W = None

        self.gen_disp = [
            {   'eng' : ['EBSD orignal image'],
                'jpn' : ['EBSD元画像']},
            {   'eng' : ['Bandsearch', 'EBSD orignal image'],
                'jpn' : ['バンドサーチ', 'EBSD元画像']},
            {   'eng' : [
                        'Conograph', 'Bandsearch',
                        'EBSD orignal image'],
                'jpn' : [
                        'Conograph', 'バンドサーチ',
                        'EBSD元画像']},
            {   'eng' : ['Conograph'], 'jpn' : ['COnograph']}
            ]
        
        self.disp_ebsd = {'eng' : 'EBSD orignal image', 'jpn' : 'EBSD元画像'}
        self.disp_band = {'eng' : 'Bandsearch', 'jpn' : 'バンドサーチ'}
        self.disp_cono = {'eng' : 'Conograph', 'jpn' : 'Conograph'}

        self.menus_disp = {
            'Bandsearch' : {
                'eng' : ['Bandsearch result', 'EBSD log'],
                'jpn' : ['バンドサーチ結果', 'EBSD log']},
            'Conograph' : {
                'eng' : ['Conograph result', 'Conograph log'],
                'jpn' : ['Conograph結果', 'Conograph log']}    
            }
        
        os.makedirs (self.input, exist_ok = True)
        os.makedirs (self.path_result, exist_ok = True)

    #-------------------------------------------------------
    # 言語選択
    #-------------------------------------------------------
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
            {'eng' : 'EBSD image file',
             'jpn' : 'EBSD画像ファイル'}[lang],
            type = ['jpg', 'jpeg', 'png', 'tif'], key = 'img')
        
        if img_file is None: key = 'param'
        else: key = 'param_' + img_file.name
        param_file = st.file_uploader (
                {'eng' : 'Parameter file (py)',
                'jpn' : 'パラメータファイル (py)'}[lang],
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
            #st.session_state['param_name'] = param_file.name
            st.session_state['file_name'] = img_file.name

        if uploaded:
            st.session_state['uploaded'] = True
            st.session_state['doneEBSD'] = False
            st.session_state['doneCono'] = False
            st.session_state['bdata_uploaded'] = False

        if flg_new_param:
            self.upload_banddata_file ()
    
    def upload_banddata_file (self,):
        lang = st.session_state['lang']

        bdata_file = st.file_uploader (
            {'eng' : 'Band data',
             'jpn' : 'バンドデータ'}[lang],
             type = ['txt'], key = 'band_data')
        
        if bdata_file is not None:
            savePath = self.dataPath_uploaded
            if os.path.exists (savePath): os.remove (savePath)
            with open (savePath, 'wb') as f:
                f.write (bdata_file.getbuffer ())

            flg, _ = bdata_check (savePath)
            if flg:
                update_use_band_width (
                    use_band_width = 0,
                    readPath = savePath,
                    savePath = self.dataPath0)
                update_use_band_width (
                    use_band_width = 1,
                    readPath = savePath,
                    savePath = self.dataPath1)
                st.session_state['bdata_uploaded'] = True
                #st.session_state['doneEBSD'] = False
                st.session_state['doneCono'] = False

            else:
                st.session_state['bdata_uploaded'] = False
                st.write (
                    {'eng' : 'Please upload correct data!!',
                    'jpn' : '正しいデータをアップロードして下さい!!'}[lang])

    def general_disp_menus (self,):
        lang = st.session_state['lang']
        menus = []

        if st.session_state['doneCono']:
            menus = self.gen_disp[2][lang]
        elif st.session_state['doneEBSD']:
            menus = self.gen_disp[1][lang]
        elif st.session_state['uploaded']:
            menus = self.gen_disp[0][lang]
        
        return menus

    # ----------------------------------------------------
    # 結果表示のタブ設定
    # （EBSD元画像、バンドサーチ結果＆log、Conograph結果&log）
    # ----------------------------------------------------
    def menu_display_result_ebsd (self, gen = 'bandsearch'):
        lang = st.session_state['lang']
        menuList = self.menus_disp[gen][lang]
        return menuList
    
    def menu_display_text_result (self,):
        lang = st.session_state['lang']
        menu0 = {'eng' : 'Table of band data',
                 'jpn' : 'バンドデータ表'}[lang]
        menu1 = {'eng' : 'Conograph result',
                 'jpn' : 'Conograph結果表示'}[lang]
        #ebsdlog = 'EBSD log'
        #conographlog = 'Conograph log'
        menuList = []
        if st.session_state['doneCono']:
            menuList = [menu1, menu0]
        elif st.session_state['doneEBSD']:
            menuList = [menu0]
        return menuList

    # ----------------------------------------------------
    # サイドバーのタブ設定 （バンドサーチ、Conograph結果）
    # ----------------------------------------------------
    def menu_side_jobs (self,):
        lang = st.session_state['lang']
        menu0 = {'eng': 'Upload',
                 'jpn' : 'アップロード'}[lang]
        menu1 = {'eng' : 'Bandsearch',
                 'jpn' : 'バンドサーチ'}[lang]
        menu_edit = {'eng' : 'Band data',
                     'jpn' : 'バンドデータ'}[lang]
        menu2 = 'Conograph'
        menuList = [menu0, menu1, menu_edit, menu2]
        return menuList
