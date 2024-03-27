import streamlit as st
import pandas as pd
from excel_modification import FileUpdate

# Page title

st.set_page_config(page_title='West-Fork Data Explorer', page_icon='📊')
st.title('West-Fork Data Exploration')
st.markdown('## Steps to use:\n\n1. Select and load single tabbed Excel file\n2. Enter the facility name\n3. Click "Process File"')

file_update = FileUpdate()

uploaded_file = st.file_uploader("Upload a single Excel file", type=["xls", "xlsx"])

# directory_path = st.text_input('Enter directory path:')
# facility_names = st.text_input('List the names of the facilities/folders')
single_facility_name = st.text_input('Enter the name of the facility')

single_df = pd.DataFrame()
if st.button('Process File(s)'):
    if not single_facility_name:
        st.markdown('Please add a file name')
    if uploaded_file and single_facility_name:
        single_df = file_update.update_single_facility(uploaded_file, single_facility_name)
    # elif facility_names is not None and directory_path is not None:
    #     dir_names = facility_names.split(',')
    #     file_update.update_facilities(directory_path, dir_names)


# with st.expander('About this app'):
#   st.markdown('**What can this app do?**')
#   st.info('This app shows the use of Pandas for data wrangling, Altair for chart creation and editable dataframe for data interaction.')
#   st.markdown('**How to use the app?**')
#   st.warning('To engage with the app, 1. Select genres of your interest in the drop-down selection box and then 2. Select the year duration from the slider widget.
#   As a result, this should generate an updated editable DataFrame and line plot.')
  
# st.subheader('Which Movie Genre performs ($) best at the box office?')

# Load data
# df = pd.read_csv('data/movies_genres_summary.csv')
# df.year = df.year.astype('int')

# Input widgets
# Genres selection
# genres_list = df.genre.unique()
# genres_selection = st.multiselect('Select genres', genres_list, ['Action', 'Adventure', 'Biography', 'Comedy', 'Drama', 'Horror'])
#
# ## Year selection
# year_list = df.year.unique()
# year_selection = st.slider('Select year duration', 1986, 2006, (2000, 2016))
# year_selection_list = list(np.arange(year_selection[0], year_selection[1]+1))

# df_selection = df[df.genre.isin(genres_selection) & df['year'].isin(year_selection_list)]
# reshaped_df = df_selection.pivot_table(index='year', columns='genre', values='gross', aggfunc='sum', fill_value=0)
# reshaped_df = reshaped_df.sort_values(by='year', ascending=False)


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
