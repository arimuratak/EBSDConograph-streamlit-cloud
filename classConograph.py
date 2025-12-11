import os
import shutil
import pandas as pd
import requests
import streamlit as st
from dataIO import to_params_conograph, read_out_file,\
        read_input_txt, read_params, is_numeric

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

        self.cols_to_disp = {
            'lattice_const_before_refinement' : ['a', 'b', 'c', 'α', 'β', 'γ', 'sacle_factor'],
            'lattice_const_after_refinement' : [
                ['a', 'b', 'c', 'α', 'β', 'γ', 'sacle_factor', 'a/c', 'b/c'],
                ['a', 'b', 'c', 'α', 'β', 'γ', 'sacle_factor', 'a/c', 'b/c', "a'", "b'", "c'"]
                ],
            'euler_angles' : ['θ1', 'θ2', 'θ3', 'Err_θ1', 'Err_θ2', 'Err_θ3'],
            'projection_center_shifts' : ['Δx', 'Δy', 'Δz', 'Err_Δx', 'Err_Δy', 'Err_Δz'],
            'indexing_before_refinement' : [
                ['Band No.', 'h', 'k', 'l', 'X_cal', 'Y_cal', 'X_obs', 'Y_obs', 'distance', 'good_fit?'],
                ['Band No.', 'h', 'k', 'l', 'X_cal', 'Y_cal', 'X_obs', 'Y_obs', 'distance', 'good_fit?', 'band_width_cal', 'band_width_obs']
                ],
            'indexing_after_refinement' : [
                ['Band No.', 'h', 'k', 'l', 'X_cal', 'Y_cal', 'X_obs', 'Y_obs', 'distance', 'good_fit?'],
                ['Band No.', 'h', 'k', 'l', 'X_cal', 'Y_cal', 'X_obs', 'Y_obs', 'distance', 'good_fit?', 'band_width_cal', 'band_width_obs']
                ]
            }

        

        self.label2key = {v:k for k,v in self.key2label.items()}

        self.keys_lines = [
            'Buerger_lattice_basis_before_refinement',
            'Buerger_lattice_basis_after_refinement']
        
        self.paramNames = [
            'searchLevel',
            'range_deg', 
            'tolerance_unit_cell',
            'tolerance_vector_length_gain',
            'tolerance_vector_length', 'num_miller_idx',
            'th_hkl', 'ref_shift_dXdYdZ', 'th_fm',
            'axisRhombohedralSym', 'axisMonoclinicSym',
            'latexStyle']
        
        self.cvtTbl = {
            'searchLevel' : 'Quick search/exhaustive search',
            'range_deg' : 'Upper bound on errors in Φ, σ, σ_begin, σ_end',
            'tolerance_unit_cell' : 'Tolerance level for errors in the unit-cell scales',
            'tolerance_vector_length_gain' : 'Resolution for Bravais-type determination',
            'tolerance_vector_length' : 'Resolution for selecting output solutions',
            'num_miller_idx' : 'Number of hkl generated  for indexing',
            'th_hkl' : 'Max |h|,|k|,|l| used for indexing',
            'th_fm' : 'Lower threshold of FOM',
            'axisRhombohedralSym' : 'Axis for rhombohedral symmetry',
            'axisMonoclinicSym' : 'Axis for monoclinic symmetry',
            'latexStyle' : 'Output in latex style'}


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
        #self.prepare_data_params ()
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
        lang = st.session_state['lang']
        if os.path.exists (self.logPath):
            with open (self.logPath, 'r', encoding = 'utf-8') as f:
                st.download_button (
                    {'eng' : 'Download log file',
                     'jpn' : 'logファイルダウンロード'}[lang],
                     data = f,
                     file_name = 'log_conograph.txt',
                     mime = 'text/plain', key = 'conograph_log')
        
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

    def display_as_df (self, cols, texts):
        if not isinstance (texts, list):
            texts = texts.split ('\n')
        
        texts = [ts.split(',') for ts in texts]
        df = pd.DataFrame (texts, columns = cols)
        st.data_editor (df, num_rows = 'fixed',
                        disabled  =True, hide_index = True)


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
            elif labelKey in self.cols_to_disp:
                if ('indexing_' in labelKey) | (labelKey == 'lattice_const_after_refinement'):
                    if isinstance (resultKey, list):
                        n = int (len (resultKey[0].split(',')) == 12)
                    else:
                        n = int (len (resultKey.split(',')) == 12)
                    cols = self.cols_to_disp[labelKey][n]
                else:
                    cols = self.cols_to_disp[labelKey]
                self.display_as_df (cols, resultKey)
            else:
                st.write (resultKey)

    def set_data_0or1 (self, use_band_width):
        nums = ['0 : use band center', '1 : use band edges']
        v = st.selectbox (
            'Select use band center or edges',
            nums, index = int (use_band_width),
            key = 'use_band_edges')
        v = nums.index (v)
        dPath = self.data0_or_1 (v)
        if os.path.exists (self.dataPath):
            os.remove (self.dataPath)
        shutil.copyfile (dPath, self.dataPath)

    def select_search_level (self, v):
        vlist = ['0 : Quick', '1 : Exhaustive']
        label = self.cvtTbl['searchLevel']
        v = st.selectbox (
            label, vlist, index = int (v),
            key = 'search_level')
        v = vlist.index (v)
        return str (v)

    def centerShift_dxdydz (self, v):
        vs = v.split()
        options = ['0 : No', '1 : Yes']
        ans = []
        st.write ('Flags to fit the projection center shifts')
        for col, v, label in zip (st.columns (3), vs, ['ΔX', 'ΔY', 'ΔZ']):
            with col:
                v = st.selectbox (
                    label, options, index = int (v), key = label)
            v = options.index(v)
            ans.append (str (v))
        return ans

    def axisRhombohedralSym (self, v):
        options = ['Rhombohedral', 'Hexagonal']
        select = st.selectbox (
            self.cvtTbl['axisRhombohedralSym'],
            options, index = options.index(v),
            key = 'axisRhonmbohedral')
        return select
    
    def axisMonoclinicSym (self, v):
        options = ['A','B','C']
        select = st.selectbox (
            self.cvtTbl['axisMonoclinicSym'],
            options, index = options.index (v),
            key = 'axisMonoclinicSym')
        return select

    def latex_style (self, v):
        options = ['0 : No', '1 : Yes']
        select = st.selectbox (
            self.cvtTbl['latexStyle'],
            options, index = int (v),
            key = 'latex_style')
        select = options.index (select)
        return str (select)

    def params_menu (self,):
        lang = st.session_state['lang']
        self.prepare_data_params ()
        if st.session_state['use_band_width'] is None:
            use_band_width = read_params (names = ['use_band_width'])['use_band_width']
            st.session_state['use_band_width'] = int (use_band_width)
        else:
            use_band_width = st.session_state['use_band_width']
        
        params = {}        
        params['use_band_width'] = use_band_width
        for k,v in read_input_txt (self.paramNames,
                                path = self.paramsPath).items():
            params[k] = v
        
        ans = {}
        with st.expander ({'eng' : 'Parameter menu',
                    'jpn' : 'パラメータメニュー'}[lang]):
            for k, v in params.items():
                if k == 'use_band_width':
                    self.set_data_0or1 (v)
                elif k == 'searchLevel':
                    ans[k] = self.select_search_level (v)
                elif k == 'ref_shift_dXdYdZ':
                    ans[k] = self.centerShift_dxdydz (v)
                elif k == 'axisRhombohedralSym':
                    ans[k] = self.axisRhombohedralSym (v)
                elif k == 'axisMonoclinicSym':
                    ans[k] = self.axisMonoclinicSym (v)
                elif k == 'latexStyle':
                    ans[k] = self.latex_style (v)
                else:
                    label = self.cvtTbl[k]
                    tmp = st.text_input (
                        label, v, key = label)
                    if not is_numeric (tmp):
                        st.write ('Please input numeric value!!')
                        tmp = v
                    ans[k] = tmp
        
        to_params_conograph (params = ans)
