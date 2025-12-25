import streamlit as st
from init_session_state import build_session_state, reset_session_state
from classMain import MainClass
from classEBSD import EBSDClass
from classConograph import Conograph

build_session_state ()
reset_session_state ()
    
if __name__ == '__main__':
    title = 'EBSD Conograph'
    objMain = MainClass ()
    objEBSD = EBSDClass ()
    objCono = Conograph ()

    # メイン側のレイアウト
    title_place = st.title (title)
    img_disp = st.empty() # 画像表示エリア
    result_disp = st.empty () 

    #サイドバー側のレイアウト＆処理
    with st.sidebar:
        # 言語選択＆サンプルデータダウンロード
        col1, col2 = st.columns (2)
        with col1: objMain.select_langage()
        lang = st.session_state['lang']
        with col2: objMain.down_load_sample()
            
        #--------------------------------------------------------
        #  サイドバーのjobメニュータブ
        #--------------------------------------------------------
        side_jobs = objMain.menu_side_jobs ()
        if len (side_jobs) > 0:
            tabs = st.tabs (side_jobs)
            for tab, job_name in zip (tabs, side_jobs):
                with tab:
                    if job_name in ['Upload', 'アップロード']:
                        _ = objMain.upload_files ()

                    # バンドサーチ
                    elif (job_name in ['Bandsearch','バンドサーチ']) & st.session_state['uploaded']:
                        space_bs_exec = st.empty ()
                        objEBSD.params_menu ()
                        with space_bs_exec: objEBSD.run_band_search ()

                    elif (job_name in ['Band data', 'バンドデータ']) & st.session_state['doneEBSD']:
                        st.write ({
                                'eng' : '＜＜Band date editor＞＞',
                                'jpn' : '＜＜バンドデータ編集＞＞'}[lang])
                        xydata = st.session_state['xydata']
                        res = st.session_state['res_clicked']
                        edited = objEBSD.manage_data_editor (xydata, res)
                        if edited:
                            st.write ({
                                    'eng' : '＜＜For confirmation after edit＞＞',
                                    'jpn' : '＜＜編集後の確認用＞＞'}[lang])
                            objEBSD.df_for_monitor ()

                    # COnograph
                    elif (job_name == 'Conograph') & st.session_state['doneEBSD']:
                        space_cono_exec = st.empty ()
                        objCono.params_menu ()
                        with space_cono_exec:
                            result = objCono.conograph_exec ()
                        flg_res = objCono.get_result (result)

    # メイン表示部
    genMenus = objMain.general_disp_menus ()
    if len(genMenus) > 0:
        name_radio = st.radio (
            'mainMenu', genMenus, key = 'general_menu',
            horizontal = True, label_visibility = 'hidden')
        
        if name_radio in ['EBSD orignal image', 'EBSD元画像']:
            objEBSD.display_ebsd ()

        elif name_radio in ['Bandsearch', 'バンドサーチ']:
            menus = objMain.menus_disp['Bandsearch'][lang]
            tabs = st.tabs (menus)
            for tab, tab_name in zip (tabs, menus):
                with tab:
                    if tab_name in [
                                    'Bandsearch result (EBSD img)',
                                    'バンドサーチ結果 (EBSD画像)']:
                        objEBSD.display_ebsd_with_band ()
                    elif tab_name in [
                                'Bandsearch result (2nd Derivate img)',
                                'バンドサーチ結果 (2次微分画像)']:
                        col1, col2 = st.columns (2)
                        with col1:  
                            st.write ({'eng' : '＜＜2nd Derivative＞＞',
                                    'jpn' : '＜＜2次微分画像＞＞'}[lang])
                        xydata, is_clicked, res = objEBSD.display_clicked_point ()
                        st.session_state['xydata'] = xydata
                        st.session_state['res_clicked'] = res
                        if is_clicked & (xydata is None):
                            with col2:
                                st.write ('クリックは範囲外です')
                        elif is_clicked & (xydata is not None) & (res is not None) and (
                            st.session_state['unix_time'] != str (res['unix_time'])):
                            with col2:
                                _ = st.button (
                                    {'eng' : 'Click to fix band adding',
                                     'jpn' : 'バンド追加確定のためクリック'}[lang],
                                     key = 'conf_add_band')

                    elif tab_name in ['Bandsearch result', 'バンドサーチ結果']:
                        objEBSD.display_ebsd_with_band ()

                        col1, col2 = st.columns (2)
                        with col1:  
                            st.write ({'eng' : '＜＜2nd Derivative＞＞',
                                    'jpn' : '＜＜2次微分画像＞＞'}[lang])
                        xydata, is_clicked, res = objEBSD.display_clicked_point ()
                        st.session_state['xydata'] = xydata
                        st.session_state['res_clicked'] = res
                        if is_clicked & (xydata is None):
                            with col2:
                                st.write ('クリックは範囲外です')
                        elif is_clicked & (xydata is not None) & (res is not None) and (
                            st.session_state['unix_time'] != str (res['unix_time'])):
                            with col2:
                                _ = st.button (
                                    {'eng' : 'Click to fix band adding',
                                     'jpn' : 'バンド追加確定のためクリック'}[lang],
                                     key = 'conf_add_band')


                    elif tab_name == 'EBSD log':
                        objEBSD.display_log ()

        elif name_radio == 'Conograph':
            menus = objMain.menus_disp['Conograph'][lang]
            tabs = st.tabs (menus)
            for tab, tab_name in zip (tabs, menus):
                with tab:
                    if tab_name in ['Conograph result', 'Conograph結果']:
                        objCono.display_result ()
                    elif tab_name == 'Conograph log':
                        objCono.request_log ()
                        objCono.display_log ()
