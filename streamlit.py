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

    # Add model distribution chart
    st.write("### Model Distribution")
    
    # Get current year's model distribution
    model_counts = current_year_data['default_model_slug'].value_counts().reset_index()
    model_counts.columns = ['model', 'count']
    
    # Calculate percentages
    total = model_counts['count'].sum()
    model_counts['percentage'] = (model_counts['count'] / total * 100).round(1)
    
    # Create the donut chart
    donut = alt.Chart(model_counts).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="count", type="quantitative"),
        color=alt.Color(
            field="model",
            type="nominal",
            scale=alt.Scale(scheme='blues'),
            legend=alt.Legend(title="Model")
        ),
        tooltip=[
            alt.Tooltip("model:N", title="Model"),
            alt.Tooltip("count:Q", title="Conversations"),
            alt.Tooltip("percentage:Q", title="Percentage", format=".1f")
        ]
    ).properties(
        width=400,
        height=400,
        title="Distribution of Conversations by Model"
    )
    
    st.altair_chart(donut, use_container_width=True)

    # Create word frequency visualization
    st.write("### Most Common Conversation Topics")
    
    # Process titles to get word frequencies
    def get_word_frequencies(titles, min_length=3):
        # Combine all titles and split into words
        words = ' '.join(titles.dropna().astype(str)).lower().split()
        # Filter out short words and count frequencies
        word_freq = pd.Series([w for w in words if len(w) >= min_length]).value_counts()
        return pd.DataFrame({'word': word_freq.index, 'frequency': word_freq.values})
    
    # Get word frequencies for current year
    word_freq_df = get_word_frequencies(current_year_data['title'])
    # Take top 30 words
    top_words = word_freq_df.head(30)
    
    # Create word frequency chart
    word_chart = alt.Chart(top_words).mark_bar().encode(
        x=alt.X('frequency:Q', title='Frequency'),
        y=alt.Y('word:N', 
                title=None,
                sort='-x'),  # Sort by frequency descending
        color=alt.Color('frequency:Q',
                       scale=alt.Scale(scheme='blues'),
                       legend=None),
        tooltip=[
            alt.Tooltip('word:N', title='Word'),
            alt.Tooltip('frequency:Q', title='Frequency')
        ]
    ).properties(
        width=600,
        height=400,
        title='Most Common Words in Conversation Titles'
    )
    
    st.altair_chart(word_chart, use_container_width=True)
    
    # Paginated table display
    st.write("Paginated Table:")
    st.dataframe(df)
