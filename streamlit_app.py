import streamlit as st
import pandas as pd
from excel_modification import FileUpdate

# Page title

st.set_page_config(page_title='West-Fork Data Explorer', page_icon='📊')
st.title('West-Fork Data Exploration')
st.markdown('## Single File Processing')
st.markdown('### Steps to use:\n\n1. Select and load single tabbed Excel file\n2. Enter the facility name\n3. Click "Process File"')

file_update = FileUpdate()

uploaded_file = st.file_uploader("Upload a single Excel file", type=["xls", "xlsx"])

single_facility_name = st.text_input('Enter the name of the facility')

single_df = pd.DataFrame()
if st.button('Process Single File'):
    if not single_facility_name:
        st.markdown('Please add a file name')
    if uploaded_file and single_facility_name:
        single_df = file_update.update_single_facility(uploaded_file, single_facility_name)
st.divider()
st.markdown('\n\n## Multiple File Processing')
st.markdown('### Steps to use:\n\n1. Select and load single zipped file of the main folder containing the facilities in the sub folders (i.e., Example 1)\n2. Click "Process File"')
zip_file = st.file_uploader("Upload a single Zip file", type=["zip"])
if st.button('Process Zip File'):
    if zip_file:
        single_df = file_update.update_facilities(zip_file)

# Display DataFrame
# Un-pivot dataframe
udf = single_df.reset_index()
df_editor = st.data_editor(udf, height=300, use_container_width=True, num_rows="dynamic")

# df_chart = pd.melt(df_editor.reset_index(), id_vars='year', var_name='genre', value_name='gross')

# # Display chart
# chart = alt.Chart(df_chart).mark_line().encode(
#             x=alt.X('year:N', title='Year'),
#             y=alt.Y('gross:Q', title='Gross earnings ($)'),
#             color='genre:N'
#             ).properties(height=320)
# st.altair_chart(chart, use_container_width=True)
