# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 19:34:19 2024

@author: Abinash.m
"""

import pandas as pd
import requests
import io
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
from datetime import datetime
import pytz
url ="https://home-c45.nice-incontact.com/ReportService/DataDownloadHandler.ashx?CDST=C3JXgBEguvxxk7vTBugMOa258ohbohd20s%2fVo46V9QYM71x9zXk%2f9YOcTGZQ%2bDNG0DcqfqmmckZjjwQK%2b9mFpRbSD%2bT370c5mwLiPOTbHU02R%2bzc%2fUOMXaWR%2fQkpWn%2beTE6hyRUpyCyjZ%2fzUkeZb6BZd5UJr8ZiqGFUspzF2e7pP8J6rNp29sRB2%2b%2bx1oC0S3usc02iljryQ9rIGvsyMgeNMbk43lyK1haCqz9aZpMxi8MNAb8x7&PresetDate=1&Format=CSV&IncludeHeaders=True&AppendDate=False"
my_urls = [url]
final_df = pd.DataFrame()
for my_url in my_urls:
    response = requests.get(my_url, stream=True)
    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text))
        df = df.sort_values(by=['agent_no', 'start_date'])
        final_df = pd.concat([final_df, df], ignore_index=True)
    else:
        print(f"Failed to fetch data from {my_url}")
agent_id_list=[34622818,34622820,34670597,34670594,34787623
,34624631,34624633,34624635,34670605,39184600,39555533,39442978,34715083,39555566,39583073,39442979
,34622819,39292418,34670601,34624640,39336086,30124481,30124483,30124484,30297577,34472267,39583074,38829615,34472270
,34787620,34814295,39555565,39582488,34787621,34670606,34622822,34670590,34670592,39184599
,34670593,25992864,38829589,25992854,30124482,26010029,26025857,30220239,34472268,38830108
,38830109,26109218,39292723,39292724,30373026,38830110,30220803,34787625,30124145,34472269
,30220240,34472266,34622821,30123930,30124543,39036196,34472465,39036702,39104298,30124146
,20033534,34751882,38830374,30220238,39582489,39582485,39582487,39582486,38874691,38874690
]

mask =final_df['agent_no'].isin(agent_id_list)
final_ldl_df = final_df[mask] 
agent_shift = pd.read_excel("./Agent_Schedule.xlsx")

agent_shift1 =agent_shift.copy()
melted_df = pd.melt(agent_shift, id_vars=['VN ID', 'Name', 'WM Role', 'Location', 'agent_no'], 
                    var_name='Shift_Date', value_name='Value')
final_ldl_df['start_date']= pd.to_datetime(final_ldl_df['start_date']).dt.strftime('%d-%m-%Y')
mnth = datetime.today().month
if mnth<10:
    mnth = "0"+str(mnth)
current_day = str(datetime.today().day)+"-"+str(mnth)+"-"+str(datetime.today().year)
final_ldl_df = final_ldl_df[final_ldl_df['start_date']==current_day]
merge_agent_shift = pd.merge(melted_df,final_ldl_df,on='agent_no',how='left')
merge_agent_shift.fillna('N/A',inplace=True)
merge_agent_shift_for_current = merge_agent_shift[(merge_agent_shift['Shift_Date']==current_day) &( (merge_agent_shift['start_date']==current_day) | (merge_agent_shift['start_date']=='N/A'))]
merge_agent_shift_for_current[['Start_Time', 'End_Time']] = merge_agent_shift_for_current['Value'].str.split(' - ', expand=True)

merge_agent_shift_for_current['End_Time'] = np.where(merge_agent_shift_for_current['Start_Time'].isin(['OFF', 'N/A', 'PL']), 
                                                     merge_agent_shift_for_current['Start_Time'], 
                                                     merge_agent_shift_for_current['End_Time'])


merge_agent_shift_for_current1=merge_agent_shift_for_current.copy()
ist_timezone = pytz.timezone('Asia/Kolkata')
cst_timezone = pytz.timezone('US/Central')

current_time_ist = datetime.now(ist_timezone)
current_time_cst = current_time_ist.astimezone(cst_timezone)
current_time_cst_str = current_time_cst.strftime('%I:%M %p')

def is_working(row):
    if row['Start_Time'] in ['OFF', 'N/A', 'PL'] or row['End_Time'] in ['OFF', 'N/A', 'PL']:
        return False
    start_time = datetime.strptime(row['Start_Time'], '%I:%M %p')
    end_time = datetime.strptime(row['End_Time'], '%I:%M %p')
    return start_time.time() <= current_time_cst.time() <= end_time.time()
df_filtered = merge_agent_shift_for_current[~merge_agent_shift_for_current['Value'].isin(['OFF', 'N/A', 'PL'])]
df_filtered['Currently_Working'] = df_filtered.apply(is_working, axis=1)


total_agents = len(merge_agent_shift_for_current['agent_no'].unique())
scheduled_agents = len(merge_agent_shift_for_current[~merge_agent_shift_for_current['Value'].isin(['OFF', 'N/A', 'PL'])]['agent_no'].unique())
off_agents = len(merge_agent_shift_for_current[merge_agent_shift_for_current['Value'] == 'OFF']['agent_no'].unique())
pl_agents = len(merge_agent_shift_for_current[merge_agent_shift_for_current['Value'] == 'PL']['agent_no'].unique())
working_agents = len(df_filtered[(df_filtered['Currently_Working']) ]['agent_no'].unique())
current_time_scheduled_agents = len(df_filtered[df_filtered.apply(is_working, axis=1)]['agent_no'].unique())

agents_worked_until_now = df_filtered[df_filtered['Start_Time'].apply(lambda x: datetime.strptime(x, '%I:%M %p').time()) <= current_time_cst.time()]
total_hours_scheduled =scheduled_agents*8
total_hours_clocked_until_now = len(agents_worked_until_now['agent_no'].unique()) * 9
difference = total_hours_scheduled - total_hours_clocked_until_now

overall_info_df = pd.DataFrame({
    'Total_Agents': [total_agents],
    'Scheduled_Agents': [scheduled_agents],
    'Off_Agents': [off_agents],
    'Pl_Agents': [pl_agents],
    'Working_Agents': [working_agents],
    'Scheduled_At_Current_Time': [current_time_scheduled_agents]
})

location_info_df = df_filtered.groupby('Location').apply(lambda x: pd.Series({
    'Total_Agents': len(x['agent_no'].unique()),
    'Scheduled_Agents': len(x[~x['Value'].isin(['OFF', 'N/A', 'PL'])]['agent_no'].unique()),
    'Off_Agents': len(x[x['Value'] == 'OFF']['agent_no'].unique()),
    'Pl_Agents': len(x[x['Value'] == 'PL']['agent_no'].unique()),
    'Working_Agents': len(x[x.apply(is_working, axis=1)]['agent_no'].unique())
    ,'Scheduled_At_Current_Time': len(x[x.apply(is_working, axis=1)]['agent_no'].unique())

})).reset_index()


import streamlit as st
st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)
import pandas as pd
import plotly.express as px
import pytz
from datetime import datetime


def convert_to_ist(current_time_cst):
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time_ist = current_time_cst.astimezone(ist_timezone)
    return current_time_ist.strftime('%Y-%m-%d %H:%M:%S')



# Sidebar
current_time_cst = datetime.now(pytz.timezone('US/Central'))
current_time_ist = convert_to_ist(current_time_cst)
st.sidebar.header('Current Time')
st.sidebar.subheader('CST Time')
st.sidebar.write(current_time_cst.strftime('%Y-%m-%d %H:%M:%S'))
st.sidebar.subheader('IST Time')
st.sidebar.write(current_time_ist)
st.markdown("<h1 style='text-align: center; color: red;'>Overall Information</h1>", unsafe_allow_html=True)

# Pivot the data for location-wise information
# df_transformed = pd.DataFrame({'Information': overall_info_df.columns, 'Value': overall_info_df.iloc[0]})
# location_info_pivot = pd.pivot_table(location_info_df, index='Location', values=['Total_Agents', 'Scheduled_Agents', 'Off_Agents', 'Pl_Agents', 'Working_Agents', 'Scheduled_At_Current_Time'])
# df_transformed.reset_index(drop=True, inplace=True)
# st.write(df_transformed)
# Display location-wise distribution in two pie charts side by side

col1, col2, col3,col6, col4, col5 = st.columns(6)
col1.metric("Total Agents", overall_info_df['Total_Agents'][0])
col2.metric("Scheduled Agents",overall_info_df['Scheduled_Agents'][0])
col3.metric("Weekly Off Agents",overall_info_df['Off_Agents'][0])
col4.metric("On Leave", overall_info_df['Pl_Agents'][0])
col5.metric("Currently Working",overall_info_df['Working_Agents'][0])
col6.metric("Scheduled for Today",overall_info_df['Scheduled_At_Current_Time'][0])
st.header('Location-wise Distribution')
import plotly.graph_objects as go



import streamlit as st
import plotly.graph_objects as go

# Assuming location_info_df contains your DataFrame
if len(location_info_df) >= 2:
    col1, col2 = st.beta_columns(2)

    with col1:
        st.markdown("<h2 style='position: absolute; left: 140px; color: red;'>Chennai</h2>", unsafe_allow_html=True)
        st.subheader('')
        row1_data = location_info_df.iloc[0]
        fig1 = go.Figure(data=[go.Pie(labels=row1_data.index, values=row1_data.values)])
        fig1.update_layout(showlegend=False, width=400, height=400)  # Set width and height
        st.plotly_chart(fig1)

    with col2:
        st.markdown("<h2 style='position: absolute; left: 125px; color: red;'>Mumbai</h2>", unsafe_allow_html=True)
        st.subheader('')

        row2_data = location_info_df.iloc[1]
        fig2 = go.Figure(data=[go.Pie(labels=row2_data.index, values=row2_data.values)])
        fig2.update_layout(width=400, height=400)  # Set width and height
        st.plotly_chart(fig2)
else:
    st.warning("Insufficient data to generate two pie charts. At least two rows are required.")
