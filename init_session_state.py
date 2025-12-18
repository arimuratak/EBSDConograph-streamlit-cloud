import streamlit as st

def build_session_state ():
    if 'lang' not in st.session_state:
        st.session_state['lang'] = None
    if 'BandKukans' not in st.session_state:
        st.session_state['BandKukans'] = None
    if 'shape' not in st.session_state:
        st.session_state['shape'] = None
    if 'Circle' not in st.session_state:
        st.session_state['Circle'] = None
    if 'uploaded' not in st.session_state:
        st.session_state['uploaded'] = None
    if 'doneEBSD' not in st.session_state:
        st.session_state['doneEBSD'] = None
    if 'doneCono' not in st.session_state:
        st.session_state['doneCono'] = None
    if 'imgPath' not in st.session_state:
        st.session_state['imgPath'] = None
    if 'ebsd_sels' not in st.session_state:
        st.session_state['ebsd_sels'] = None
    if 'ArrayDeriv2' not in st.session_state:
        st.session_state['ArrayDeriv2'] = None
    if 'file_name' not in st.session_state:
        st.session_state['file_name'] = None
    if 'point_clicked' not in st.session_state:
        st.session_state['point_clicked'] = None
    if 'origin_2ndDeriv' not in st.session_state:
        st.session_state['origin_2ndDeriv'] = None
    if 'jobs_side' not in st.session_state:
        st.session_state['jobs_side'] = None
    if 'img_2ndDeriv_disp' not in st.session_state:
        st.session_state['img_2ndDeriv_disp'] = None
    if 'ax' not in st.session_state:
        st.session_state['ax'] = None
    if 'lines_for_display' not in st.session_state:
        st.session_state['lines_for_display'] = None
    if 'active_tab_disp' not in st.session_state:
        st.session_state['active_tab_disp'] = None
    if 'add_band' not in st.session_state:
        st.session_state['add_band'] = None
    if 'radio_index' not in st.session_state:
        st.session_state['radio_index'] = None
    if 'last_coords' not in st.session_state:
        st.session_state['last_coords'] = None
    if 'enable_added_band' not in st.session_state:
        st.session_state['enable_added_band'] = None
    if 'just_after_bandsearch' not in st.session_state:
        st.session_state['just_after_bandsearch'] = None
    if 'unix_time' not in st.session_state:
        st.session_state['unix_time'] = None
    if 'param_name' not in st.session_state:
        st.session_state['param_name'] = None
    if 'xydata' not in st.session_state:
        st.session_state['xydata'] = None
    if 'res_clicked' not in st.session_state:
        st.session_state['res_clicked'] = None
    if 'use_band_width' not in st.session_state:
        st.session_state['use_band_width'] = None
    if 'menu_list_img' not in st.session_state:
        st.session_state['menu_list_img'] = None
    if 'menu_list_text' not in st.session_state:
        st.session_state['menu_list_text'] = None
    if 'prev_idx' not in st.session_state:
        st.session_state['prev_idx'] = None
    if 'prev_col' not in st.session_state:
        st.session_state['prev_col'] = None
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = None
    if 'num_trial' not in st.session_state:
        st.session_state['num_trial'] = None