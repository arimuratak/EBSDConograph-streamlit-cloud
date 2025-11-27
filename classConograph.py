import os
import shutil
import numpy as np
import json
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import requests
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from dataIO import to_params_conograph, read_out_file

class Conograph:
    def __init__ (self,):
        #self.api_url = "http://localhost:9000"
        self.api_url = 'https://ebsdconograph-api.onrender.com'
        self.dataPath0 = 'result/data0.txt'
        self.dataPath1 = 'result/data1.txt'
        self.paramsPathPy = 'params.py'
        self.paramsPath = 'input/input.txt'
        self.dataPath = 'input/data.txt'
        self.outPath = 'result/out.txt'
        self.logPath = 'result/LOG_CONOGRAPH.txt'

        self.key2label = {
            'lattice_const_before_refinement' : 'Lattice constant (a,b,c,α,β,γ), scale_factor (before refinement)',
            'lattice_const_after_refinement' : 'Lattice constant (a,b,c,α,β,γ), scale_factor, a/c, b/c, (after refinement)',
            'propagation_errors' : 'Propagation errors when the errors of the input angles are assumed to be within 1 deg.',
            'Buerger_lattice_basis_before_refinement' : 'Buerger-reduced reciprocal_lattice basis (before refinement)',
            'Buerger_lattice_basis_after_refinement' : 'Buerger-reduced reciprocal_lattice basis, propagation errors (after refinement)',
            'euler_angles' : 'Euler angles: θ1, θ2, θ3, Err_θ1, Err_θ2, Err_θ3 (deg) (after refinement)',
            'projection_center_shifts' : 'Projection center shifts: Δx, Δy, Δz, Err_Δx, Err_Δy, Err_Δz',
            'num_bands' : 'Number of computed bands',
            'figure_of_merit' : 'Figure of merit at the beginning and the end of the refinement',
            'chi_squares' : 'χ squares at the beginning and the end of the refinement',
            'indexing_before_refinement' : 'Indexing with the parameters before refinement',
            'indexing_after_refinement' : 'Indexing with the parameters after refinement'}
        self.label2key = {v:k for k,v in self.key2label.items()}

        self.keys_lines = [
            'Buerger_lattice_basis_before_refinement',
            'Buerger_lattice_basis_after_refinement',
            'indexing_before_refinement',
            'indexing_after_refinement']

    def data0_or_1 (self, use_band_width):
        return {
            0 : self.dataPath0, 1 : self.dataPath1
                                }[use_band_width]
    def prepare_data_params (self,):
        _, use_band_width = to_params_conograph (
                    self.paramsPathPy, self.paramsPath)
        dPath = self.data0_or_1 (use_band_width)
        if os.path.exists (self.dataPath):
            os.remove (self.dataPath)
        shutil.copyfile (dPath, self.dataPath)

    def load_files (self,):
        self.prepare_data_params ()
        uploaded_map = {}
        with open (self.paramsPath, 'rb') as f:
            uploaded_map['input.txt'] = f.read()
        with open (self.dataPath, 'rb') as f:
            uploaded_map['data.txt'] = f.read()
        return uploaded_map

    def conograph_exec (self,):
        uploaded_map = self.load_files ()
        lang = st.session_state['lang']
        if st.button ({'eng' : 'Conograph Run',
                       'jpn':'Conograph実行'}[lang]):
            files = {}
            for fname, fobj in uploaded_map.items():
                files[fname] = (fname, fobj,
                                'application/octet-stream')
            
            res = requests.post (
                self.api_url + '/run_cpp', files = files)
            
            return res
        return None

    def get_result (self, res):
        if res is None: ans = None
        else:
            if res.status_code == 200:
                if os.path.exists (self.outPath):
                    os.remove (self.outPath)
                with open (self.outPath, 'wb') as f:
                    f.write (res.content)
                ans = True
                st.session_state['doneCono'] = True

            elif res.status_code == 500:
                ans = 'Error 500'

        return ans
    
    def request_log (self,):
        res = requests.post (
            self.api_url + '/log_file')
        
        if res is None: ans = False
        else:
            if res.status_code == 200:
                if os.path.exists (self.logPath):
                    os.remove (self.logPath)
                content = res.content.decode ('utf-8')
                with open (self.logPath, 'w', encoding = 'utf-8') as f:
                    f.write (content)
                ans = True
            else:
                ans = False

        return ans
    
    def display_log (self,):
        text = ''
        if os.path.exists (self.logPath):
            with open (self.logPath, 'r', encoding = 'utf-8') as f:
                text = f.read ()
        
        st.text_area ('log', text, height = 400,
                    label_visibility='hidden')

    def download_result (self,):
        lang = st.session_state['lang']
        path = 'result/out.txt'
        with open (path, 'rb') as f:
            st.download_button (
                {'eng' : 'Download conograph result file',
                'jpn' : 'Conograh結果ファイルのダウンロード'}[lang],
                data = f,
                file_name = 'result.txt',
                mime="text/plain")

    def display_result (self,):
        result = read_out_file (self.outPath)

        radius = result['rad_kikuchi']
        col_left, col_right = st.columns (2)
        with col_left:
            st.write (
                'Radius of Kikuchi pattern R = {}'.format (radius))
        with col_right:
            self.download_result ()

        summary = result['summary']
        sel2lat = {v:k for k,v in summary.items()}
        selList = list (sel2lat.keys())
        col11, col12 = st.columns (2)
        with col11:
            selected = st.selectbox (
                    'Select lattice pattern',
                    ['-----'] + selList, key = 'select_lattice')
    
        if selected in selList:
            lat = sel2lat[selected]
            resultLat = result[lat]
            numbers = list (resultLat.keys())
            with col12:
                numSel = st.selectbox (
                    'Select candidate No.',
                    numbers, key = 'select_num')
                
            resultNum = resultLat[numSel]
            labels = list (self.label2key.keys())

            labelSel = st.selectbox (
                    'Select item to display',
                    labels, key = 'select_label')
                
            labelKey = self.label2key[labelSel]
            resultKey = resultNum[labelKey]
            if labelKey in self.keys_lines:
                text = '  \n'.join (resultKey)
                st.markdown (text)
            else:
                st.write (resultKey)



        