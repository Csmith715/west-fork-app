import pandas as pd
import openpyxl
import re
from datetime import datetime
import streamlit as st
import io
from io import BytesIO
import zipfile
from base64 import b64encode

class FileUpdate:
    def __init__(self):
        # self.base_directory = base_dir_
        self.workbook = openpyxl.load_workbook('data/FE Template - WFAS - CLIENT - BORROWER - Field Exam Report - Automation.xlsx')
        self.cols = ['Payer Type', 'Future Cash', 'Current', '30', '60', '90', '120', '150', '180', '210', 'As Of Date']
        self.num_payers = 1
        self.facility_cols = {
            1: ['N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U'],
            2: ['Y', 'Z', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF'],
            3: ['AJ', 'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ'],
            4: ['AU', 'AV', 'AW', 'AX', 'AY', 'AZ', 'BA', 'BB'],
            5: ['BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM']
        }
        self.facility_name_cells = {1: 'M14', 2: 'X14', 3: 'AI14', 4: 'AT14', 5: 'BE14', 6: 'BP14', 7: 'CA14', 8: 'CL14'}
        self.facility_cell = ''
        self.facility_cols_single_file = ['O', 'P', 'Q', 'R', 'S', 'T', 'U']
        self.sheet_cols = []
        self.ar_bucket_labels = ['30', '60', '90', '120', '150', '180']
        self.ar_bucket_ranges = [
            range(1, 31),
            range(31, 61),
            range(61, 91),
            range(91, 121),
            range(121, 151),
            range(151, 181)
        ]
        self.date_start_row = 81
        self.unique_payers = []
        self.payer_mappings = {'Medicare A': 'Medicare', 'Medicare B': 'Medicare'}
        self.max_date = None
        self.encoding_options = ['utf-8', 'latin1', 'ISO-8859-1']

    def decode_file(self, file) -> pd.DataFrame:
        for encoding in self.encoding_options:
            try:
                dframe = pd.read_csv(io.StringIO(file.decode(encoding))).fillna('')
                return dframe
            except UnicodeDecodeError:
                pass

    def update_facilities(self, zip_file):
        zip_dict = {}
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            csv_files = [file.filename for file in zip_ref.infolist() if file.filename.endswith('.csv')]
            for file in csv_files:
                key_name = file.split('/')[1]
                key_name = re.sub('\d - ', '', key_name)
                with zip_ref.open(file) as cfile:
                    content = cfile.read()
                    content_df = self.decode_file(content)
                if content_df.shape[1] > 10:
                    if key_name not in zip_dict.keys():
                        zip_dict[key_name] = [content_df]
                    else:
                        zip_dict[key_name].extend([content_df])
            final_dfs = []
            for i, (sub, facility_dfs) in enumerate(zip_dict.items(), start=1):
                self.sheet_cols = self.facility_cols[i]
                self.facility_cell = self.facility_name_cells[i]
                # Concatenate dataframes
                temp_df = pd.concat(facility_dfs)
                temp_df = temp_df[self.cols].fillna('')
                temp_df['30'] = temp_df['Current'] + temp_df['30']
                temp_df = temp_df.drop('Current', axis=1)
                temp_df = temp_df[temp_df['Payer Type'] != ''].rename(columns={'As Of Date': 'Date'})
                temp_df = temp_df.reset_index(drop=True)
                temp_df['Date'] = [datetime.strptime(w, '%m/%d/%Y') for w in temp_df.Date]
                temp_df['Payer Type'] = temp_df['Payer Type'].replace(self.payer_mappings)
                self.date_start_row = (24 - len(pd.unique(temp_df.Date))) + 81
                self.unique_payers = temp_df['Payer Type'].unique()
                self.num_payers = len(self.unique_payers)
                self.update_facility(temp_df, sub, False)
                final_dfs.append(temp_df)
            self.save_file()
            final_df = pd.concat(final_dfs)
            final_df = final_df.groupby(['Payer Type', 'Date']).sum()
            return final_df

    def update_facility(self, df, facility_name, single=False):
        if single:
            df_grouped = df
            self.sheet_cols = self.facility_cols_single_file
            self.unique_payers = pd.unique(df.index.get_level_values('Payer Type'))
            self.facility_cell = 'M14'
        else:
            df_grouped = df.groupby(['Payer Type', 'Date']).sum()
            self.max_date = max(df['Date'])
            self.unique_payers.sort()
        ar6 = self.workbook['AR6  AR Aging Trend']
        ar6['A39'] = self.max_date
        ar6[self.facility_cell] = facility_name
        ranges = [self.date_start_row+(x*33) for x in range(self.num_payers)]
        payer_name_start_cell = [f'A{(r*33)+79}' for r in range(self.num_payers)]
        for w, start_row_val, pcell in zip(self.unique_payers, ranges, payer_name_start_cell):
            payor_df = df_grouped[df_grouped.index.get_level_values('Payer Type') == w]
            ar6[pcell] = w
            row_sums = [row for row in payor_df.values]
            for r, row_add in zip(row_sums, range(len(row_sums))):
                for row_val, col in zip(r, self.sheet_cols):
                    ar6[f'{col}{start_row_val+row_add}'] = row_val

    def update_single_facility(self, facility_file, facility_name):
        single_df = self.process_single_file(facility_file)
        self.unique_payers = pd.unique(single_df.index.get_level_values('Payer Type'))
        self.num_payers = len(self.unique_payers)
        self.update_facility(single_df, facility_name, True)
        self.save_file()
        return single_df

    def save_file(self):
        output = BytesIO()
        self.workbook.save(output)
        xlsx_data = output.getvalue()
        output.seek(0)

        # Generate download link
        suffix = '<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,'
        href = f'{suffix}{b64encode(xlsx_data).decode()}" download="Modified.xlsx">Download Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)

    def label_ar_bucket(self, value: int):
        label = ''
        if value > 180:
            label = 'Over 180'
        else:
            for ar_range, lab in zip(self.ar_bucket_ranges, self.ar_bucket_labels):
                if value in ar_range:
                    label = lab
        return label

    def process_single_file(self, single_file: str):
        sdf = pd.ExcelFile(single_file)
        sheet_names = sdf.sheet_names
        sheet_dates = [s.strip('ATB ').replace('  ', ' ') for s in sheet_names]
        sheet_dates = [datetime.strptime(d, '%m %d %Y') for d in sheet_dates]
        self.max_date = max(sheet_dates)
        self.date_start_row = (24 - len(sheet_dates)) + 81
        all_dataframes = []
        for tab_name in sheet_names:
            tab_df = pd.read_excel(single_file, sheet_name=tab_name)
            tab_df = tab_df.rename(columns={
                'FIN CLASS': 'Financial Class',
                'FC': 'Financial Class',
                'DISCH DATE': 'DISCH DT',
                ' ACHGS ': 'ACHGS'
            })
            sdate = datetime.strptime(tab_name.strip('ATB ').replace('  ', ' '), '%m %d %Y')
            days_since_discharge = [(sdate - d).days for d in tab_df['DISCH DT']]
            ar_buckets = [self.label_ar_bucket(max(1, d)) for d in days_since_discharge]
            temp_df = pd.DataFrame({
                'Payer Type': tab_df['Financial Class'],
                'Charges': tab_df['ACHGS'],
                'AR Bucket': ar_buckets,
                'Date': sdate
            })
            all_dataframes.append(temp_df)
        all_tab_df = pd.concat(all_dataframes).reset_index(drop=True)
        pivot_df = all_tab_df.pivot_table(values='Charges', index=['Payer Type', 'Date'], columns='AR Bucket', aggfunc='sum')
        pivot_df = pivot_df[['30', '60', '90', '120', '150', '180', 'Over 180']].sort_index()
        return pivot_df
