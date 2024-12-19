import streamlit as st
import pandas as pd
import json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

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
    monthly_counts = df.groupby(['month_year', 'default_model_slug'])['conversation_id'].nunique().unstack(fill_value=0)
    
    # Create a complete date range from January 2023 to the current month
    all_months = pd.date_range(start='2023-01-01', end=pd.Timestamp.now(), freq='MS').strftime('%Y-%m').tolist()
    
    # Reindex to ensure all months are included
    monthly_counts = monthly_counts.reindex(all_months, fill_value=0)
    
    # Create the bar chart using matplotlib
    plt.figure(figsize=(10, 6))
    monthly_counts.plot(kind='bar', stacked=True, colormap='tab10')  # Use a colormap for different colors
    plt.title('Monthly Conversation Counts by Model Slug')
    plt.xlabel('Month-Year')
    plt.ylabel('Number of Conversations')
    plt.legend(title='Model Slug', bbox_to_anchor=(1.05, 1), loc='upper left')  # Legend outside the plot
    plt.xticks(rotation=45)
    
    # Display the plot in Streamlit
    st.pyplot(plt)  # Use Streamlit's function to display the matplotlib figure

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
        st.markdown("<span style='font-size: 16px; font-weight: bold;'>Total Conversations</span>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{total_chats}</h1>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<span style='font-size: 16px; font-weight: bold;'>Avg Messages</span>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{avg_messages:.2f}</h1>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<span style='font-size: 16px; font-weight: bold;'>Total Audio Messages</span>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-weight: bold;'>{total_audio_messages}</h1>", unsafe_allow_html=True)

    # Plot the bar chart
    plot_conversation_counts_by_month(df)

    # Paginated table display
    st.write("Paginated Table:")
    st.dataframe(df)
