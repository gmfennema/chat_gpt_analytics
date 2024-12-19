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
    
    # Fill null model slugs with 'Unknown'
    df['default_model_slug'] = df['default_model_slug'].fillna('Unknown')
    
    # Count unique conversation_ids by month-year and default_model_slug
    monthly_counts = df.groupby(['month_year', 'default_model_slug'])['conversation_id'].nunique().reset_index()
    
    # Create the Altair bar chart
    chart = alt.Chart(monthly_counts).mark_bar().encode(
        x='month_year:O',
        y='conversation_id:Q',
        color='default_model_slug:N',
        tooltip=['month_year', 'default_model_slug', 'conversation_id']
    ).properties(
        title='Monthly Conversation Counts by Model Slug'
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
    
    # Calculate total number of unique conversation IDs
    total_chats = df['conversation_id'].nunique()
    
    # Calculate average messages per conversation
    avg_messages = df['message_count'].mean()
    
    # Calculate total audio messages (count when voice is not null)
    total_audio_messages = df['voice'].notnull().sum()
    
    # Create three columns for KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<h2 style='text-align: center; font-weight: bold;'>Total Conversations</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{total_chats}</h1>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h2 style='text-align: center; font-weight: bold;'>Avg Messages</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{avg_messages:.2f}</h1>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<h2 style='text-align: center; font-weight: bold;'>Total Audio Messages</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{total_audio_messages}</h1>", unsafe_allow_html=True)

    # Plot the bar chart
    plot_conversation_counts_by_month(df)

    # Paginated table display
    st.write("Paginated Table:")
    st.dataframe(df)
