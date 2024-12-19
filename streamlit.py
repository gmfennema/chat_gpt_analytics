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
    # Convert create_time to datetime format
    df['create_time'] = pd.to_datetime(df['create_time'], errors='coerce')
    
    # Get current and previous year
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    # Filter for only current and previous year
    df_filtered = df[df['create_time'].dt.year.isin([current_year, previous_year])]
    
    # Extract month name and year
    df_filtered['month'] = df_filtered['create_time'].dt.strftime('%B')
    df_filtered['year'] = df_filtered['create_time'].dt.year.astype(str)  # Convert year to string
    
    # Count conversations by month and year
    monthly_counts = df_filtered.groupby(['month', 'year']).size().reset_index(name='count')
    
    # Create the Altair bar chart
    chart = alt.Chart(monthly_counts).mark_bar(opacity=0.8).encode(
        x=alt.X('month:N', 
                title='Month',
                sort=['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']),
        y='count:Q',
        xOffset='year:N',
        color=alt.Color('year:N',
                       scale=alt.Scale(domain=[str(current_year), str(previous_year)],
                                     range=['#0284c7', '#bae6fd']))
    ).properties(
        width=600,
        height=400,
        title='Number of Conversations by Month vs Previous Year'
    )
    
    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)

def plot_activity_heatmap(df, year):
    # Filter data for the specified year
    year_data = df[df['create_time'].dt.year == year]
    
    # Create daily counts
    daily_counts = year_data.groupby(year_data['create_time'].dt.date).size().reset_index()
    daily_counts.columns = ['date', 'count']
    
    # Add weekday and week number
    daily_counts['weekday'] = pd.to_datetime(daily_counts['date']).dt.strftime('%a')
    daily_counts['week'] = pd.to_datetime(daily_counts['date']).dt.strftime('%V')
    
    # Create the heatmap
    heatmap = alt.Chart(daily_counts).mark_rect().encode(
        x=alt.X('week:O', 
                title=None,
                axis=None),
        y=alt.Y('weekday:O', 
                title=None,
                axis=None,
                sort=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
        color=alt.Color('count:Q',
                       scale=alt.Scale(scheme='blues'),
                       legend=None),
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip('count:Q', title='Conversations')
        ]
    ).properties(
        title=f'Conversation Activity in {year}',
        width=600,
        height=200
    )
    
    return heatmap

# File uploader
uploaded_file = st.file_uploader("Choose a JSON file", type="json")

# Streamlit app
st.title("ChatGPT Year in Review")

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
        st.markdown("<h6 style='text-align: center;'>Total Conversations</h6>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>{total_chats}</h2>", unsafe_allow_html=True)
        if total_chats_prev > 0:  # Avoid division by zero
            total_chats_change = ((total_chats - total_chats_prev) / total_chats_prev * 100)
            if total_chats_change > 0:
                st.markdown(f"<p style='color: green; text-align: center;'>+{total_chats_change:.1f}%</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color: red; text-align: center;'>{total_chats_change:.1f}%</p>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h6 style='text-align: center;'>Avg Messages/Conversation</h6>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>{avg_messages:.1f}</h2>", unsafe_allow_html=True)
        if avg_messages_prev > 0:  # Avoid division by zero
            avg_messages_change = ((avg_messages - avg_messages_prev) / avg_messages_prev * 100)
            if avg_messages_change > 0:
                st.markdown(f"<p style='color: green; text-align: center;'>+{avg_messages_change:.1f}%</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color: red; text-align: center;'>{avg_messages_change:.1f}%</p>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<h6 style='text-align: center;'>Total Audio Messages</h6>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>{total_audio_messages}</h2>", unsafe_allow_html=True)
        if total_audio_messages_prev > 0:  # Avoid division by zero
            audio_change = ((total_audio_messages - total_audio_messages_prev) / total_audio_messages_prev * 100)
            if audio_change > 0:
                st.markdown(f"<p style='color: green; text-align: center;'>+{audio_change:.1f}%</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color: red; text-align: center;'>{audio_change:.1f}%</p>", unsafe_allow_html=True)


    st.write("### Daily Activity")
    activity_heatmap = plot_activity_heatmap(df, current_year)
    st.altair_chart(activity_heatmap, use_container_width=True)
    
    st.write("### Monthly Activity")
    plot_conversation_counts_by_month(df)

    # New section for Conversation Types
    st.write("### Conversation Types")

    # Calculate text vs audio conversations
    text_conversations = df[df['voice'].isnull()]['conversation_id'].nunique()
    audio_conversations = df[df['voice'].notnull()]['conversation_id'].nunique()

    # Create a DataFrame for the doughnut chart
    conversation_types = pd.DataFrame({
        'Type': ['Text', 'Audio'],
        'Count': [text_conversations, audio_conversations]
    })

    # Create the doughnut chart for text vs audio conversations
    text_audio_chart = alt.Chart(conversation_types).mark_arc(innerRadius=30).encode(
        theta=alt.Theta(field='Count', type='quantitative'),
        color=alt.Color(field='Type', type='nominal', scale=alt.Scale(domain=['Text', 'Audio'], range=['#1f77b4', '#ff7f0e'])),
        tooltip=['Type', 'Count']
    ).properties(title='Text vs Audio Conversations')

    # Calculate conversations by model slug
    model_slug_counts = df['default_model_slug'].value_counts().reset_index()
    model_slug_counts.columns = ['Model Slug', 'Count']

    # Create the doughnut chart for conversations by model slug
    model_slug_chart = alt.Chart(model_slug_counts).mark_arc(innerRadius=30).encode(
        theta=alt.Theta(field='Count', type='quantitative'),
        color=alt.Color(field='Model Slug', type='nominal', scale=alt.Scale(scheme='category10')),
        tooltip=['Model Slug', 'Count']
    ).properties(title='Conversations by Model Slug')

    # Display the charts side by side
    st.altair_chart(text_audio_chart | model_slug_chart, use_container_width=True)

    # Paginated table display
    st.write("Paginated Table:")
    st.dataframe(df)
