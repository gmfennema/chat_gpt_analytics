import streamlit as st
import pandas as pd
import json
from datetime import datetime
import numpy as np
import altair as alt

def process_json_to_dataframe(json_file):
    # Open and load the JSON file
    json_data = json.load(json_file)
    
    # Extract required fields and parse the timestamp
    records = []
    for obj in json_data:
        create_time = obj.get("create_time")
        # Convert UNIX timestamp to readable datetime
        if create_time:
            readable_time = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            readable_time = None
        
        # Count the number of messages in the mapping object
        message_count = len(obj.get("mapping", {}))  # Count the keys in the mapping
        
        record = {
            "conversation_id": obj.get("conversation_id"),
            "title": obj.get("title"),
            "create_time": readable_time,
            "default_model_slug": obj.get("default_model_slug"),
            "voice": obj.get("voice"),
            "message_count": message_count  # Add message count to the record
        }
        records.append(record)
    
    # Create a DataFrame from the extracted records
    df = pd.DataFrame(records)
    return df

def plot_conversation_counts_by_month(df):
    # Convert create_time to datetime format and extract month-year
    df['create_time'] = pd.to_datetime(df['create_time'])
    df['month_year'] = df['create_time'].dt.strftime('%Y-%m')  # Format as 'YYYY-MM'
    df['year'] = df['create_time'].dt.year  # Extract year for comparison
    
    # Count unique conversation_ids by month and year
    monthly_counts = df.groupby(['month_year', 'year'])['conversation_id'].nunique().unstack(fill_value=0)
    
    # Create the Altair bar chart for side-by-side comparison
    chart = alt.Chart(monthly_counts.reset_index()).mark_bar().encode(
        x='month_year:O',
        y='conversation_id:Q',
        color='year:N',
        tooltip=['month_year', 'year', 'conversation_id']
    ).properties(
        title='ChatGPT Year in Review'
    ).configure_axis(
        labelAngle=45
    )
    
    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)

# Streamlit app
st.title("JSON to DataFrame and Bar Chart")

# File uploader
uploaded_file = st.file_uploader("Choose a JSON file", type="json")

if uploaded_file is not None:
    # Process the JSON file
    df = process_json_to_dataframe(uploaded_file)
    
    # Ensure create_time is in datetime format
    df['create_time'] = pd.to_datetime(df['create_time'], errors='coerce')  # Convert and coerce errors to NaT
    
    # Calculate total number of unique conversation IDs for the current year
    current_year = datetime.now().year
    current_year_data = df[df['create_time'].dt.year == current_year]
    
    # Check if current_year_data is empty
    if current_year_data.empty:
        st.warning("No data available for the current year.")
        st.stop()  # Stop execution if there's no data for the current year
    
    total_chats = current_year_data['conversation_id'].nunique()
    
    # Calculate average messages per conversation for the current year
    avg_messages = current_year_data['message_count'].mean()
    
    # Calculate total audio messages for the current year
    total_audio_messages = current_year_data['voice'].notnull().sum()
    
    # Calculate previous year data for comparison
    previous_year_data = df[df['create_time'].dt.year == current_year - 1]
    total_chats_prev = previous_year_data['conversation_id'].nunique()
    avg_messages_prev = previous_year_data['message_count'].mean() if not previous_year_data.empty else 0
    total_audio_messages_prev = previous_year_data['voice'].notnull().sum()
    
    # Calculate percentage changes
    total_chats_change = ((total_chats - total_chats_prev) / total_chats_prev * 100) if total_chats_prev else 0
    avg_messages_change = ((avg_messages - avg_messages_prev) / avg_messages_prev * 100) if avg_messages_prev else 0
    total_audio_messages_change = ((total_audio_messages - total_audio_messages_prev) / total_audio_messages_prev * 100) if total_audio_messages_prev else 0
    
    # Create three columns for KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<h4 style='text-align: center; font-weight: bold;'>Total Conversations</h4>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{total_chats}</h1>", unsafe_allow_html=True)
        if total_chats_change > 0:
            st.markdown(f"<h4 style='color: green;'>+{total_chats_change:.2f}%</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='color: red;'>{total_chats_change:.2f}%</h4>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h4 style='text-align: center; font-weight: bold;'>Avg Messages</h4>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{avg_messages:.2f}</h1>", unsafe_allow_html=True)
        if avg_messages_change > 0:
            st.markdown(f"<h4 style='color: green;'>+{avg_messages_change:.2f}%</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='color: red;'>{avg_messages_change:.2f}%</h4>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<h4 style='text-align: center; font-weight: bold;'>Total Audio Messages</h4>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{total_audio_messages}</h1>", unsafe_allow_html=True)
        if total_audio_messages_change > 0:
            st.markdown(f"<h4 style='color: green;'>+{total_audio_messages_change:.2f}%</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='color: red;'>{total_audio_messages_change:.2f}%</h4>", unsafe_allow_html=True)

    # Plot the bar chart
    plot_conversation_counts_by_month(df)

    # Paginated table display
    st.write("Paginated Table:")
    st.dataframe(df)
