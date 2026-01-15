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
    if 'ArrayDeriv2' not in st.session_state:
        st.session_state['ArrayDeriv2'] = None
    if 'file_name' not in st.session_state:
        st.session_state['file_name'] = None
    if 'unix_time' not in st.session_state:
        st.session_state['unix_time'] = None
    if 'xydata' not in st.session_state:
        st.session_state['xydata'] = None
    if 'res_clicked' not in st.session_state:
        st.session_state['res_clicked'] = None
    if 'use_band_width' not in st.session_state:
        st.session_state['use_band_width'] = None
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = None
    if 'num_trial' not in st.session_state:
        st.session_state['num_trial'] = None
    if 'BAND_WIDTH_MIN' not in st.session_state:
        st.session_state['BAND_WIDTH_MIN'] = None
    if 'BAND_WIDTH_MAX' not in st.session_state:
        st.session_state['BAND_WIDTH_MAX'] = None
    if 'PC' not in st.session_state:
        st.session_state['PC'] = None
    if 'rhos' not in st.session_state:
        st.session_state['rhos'] = None
    if 'thetas' not in st.session_state:
        st.session_state['thetas'] = None
    if 'ArraySinogramErrors' not in st.session_state:
        st.session_state['ArraySinogramErrors'] = None
    if 'bdata_uploaded' not in st.session_state:
        st.session_state['bdata_uploaded'] = None

def reset_session_state ():
    if st.session_state['uploaded'] is None:
        st.session_state['uploaded'] = False
    if st.session_state['doneEBSD'] is None:
        st.session_state['doneEBSD'] = False
    if st.session_state['doneCono'] is None:
        st.session_state['doneCono'] = False
    if st.session_state['unix_time'] is None:
        st.session_state['unix_time'] = ''
    if st.session_state['edit_mode'] is None:
        st.session_state['edit_mode'] = ''
    if st.session_state['num_trial'] is None:
        st.session_state['num_trial'] = ''
    if st.session_state['BandKukans'] is None:
        st.session_state['BandKukans'] = []
    if st.session_state['bdata_uploaded'] is None:
        st.session_state['bdata_uploaded'] = False
