import streamlit as st
from googleapiclient.discovery import build
import psycopg2
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set your API Key and Database Password here
os.environ['YOUTUBE_API_KEY'] = 'AIzaSyDS5WmgQf10XnGh2n5Cu3AtA-g75m_SYVU'
os.environ['DB_PASSWORD'] = 'mani@94'

# Function to connect to the YouTube API
def api_connect():
    api_id = os.getenv("YOUTUBE_API_KEY")
    if not api_id:
        st.error("YouTube API Key not found. Please set the environment variable YOUTUBE_API_KEY.")
        return None
    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name, api_version, developerKey=api_id)
    return youtube

youtube = api_connect()

# Function to get channel information
def get_channel_info(channel_id):
    try:
        request = youtube.channels().list(part="snippet,contentDetails,statistics", id=channel_id)
        response = request.execute()
        for item in response['items']:
            data = {
                "channel_name": item["snippet"]["title"],
                "channel_id": item["id"],
                "subscribers": int(item['statistics']['subscriberCount']),
                "views": int(item["statistics"]["viewCount"]),
                "total_videos": int(item["statistics"]["videoCount"]),
                "channel_description": item["snippet"]["description"],
                "playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"]
            }
        return data
    except Exception as e:
        st.error(f"Error fetching channel info: {e}")
        return None

# Function to get video IDs
def get_videos_ids(channel_id):
    video_ids = []
    try:
        response = youtube.channels().list(id=channel_id, part='contentDetails').execute()
        playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        next_page_token = None
        while True:
            response1 = youtube.playlistItems().list(part='snippet', playlistId=playlist_id, maxResults=50, pageToken=next_page_token).execute()
            for item in response1['items']:
                video_ids.append(item['snippet']['resourceId']['videoId'])
            next_page_token = response1.get('nextPageToken')
            if next_page_token is None:
                break
    except Exception as e:
        st.error(f"Error fetching video IDs: {e}")
    return video_ids

# Function to get video information
def get_video_info(video_ids):
    video_data = []
    for video_id in video_ids:
        try:
            request = youtube.videos().list(part="snippet,contentDetails,statistics", id=video_id)
            response = request.execute()
            for item in response["items"]:
                data = {
                    "channel_name": item['snippet']['channelTitle'],
                    "channel_id": item['snippet']['channelId'],
                    "video_id": item['id'],
                    "title": item['snippet']['title'],
                    "tags": item['snippet'].get('tags'),
                    "thumbnail": item['snippet']['thumbnails']['default']['url'],
                    "description": item['snippet'].get('description'),
                    "published_date": item['snippet']['publishedAt'],
                    "duration": item['contentDetails']['duration'],
                    "views": int(item['statistics'].get('viewCount', 0)),
                    "likes": int(item['statistics'].get('likeCount', 0)),
                    "comments": int(item['statistics'].get('commentCount', 0)),
                    "favorite_count": int(item['statistics']['favoriteCount']),
                    "definition": item['contentDetails']['definition'],
                    "caption_status": item['contentDetails']['caption']
                }
                video_data.append(data)
        except Exception as e:
            st.error(f"Error fetching video info: {e}")
    return video_data

# Function to get comment information
def get_comment_info(video_ids):
    comment_data = []
    for video_id in video_ids:
        try:
            request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=50)
            response = request.execute()
            for item in response['items']:
                data = {
                    "comment_id": item['snippet']['topLevelComment']['id'],
                    "video_id": item['snippet']['topLevelComment']['snippet']['videoId'],
                    "comment_text": item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    "comment_author": item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    "comment_published": item['snippet']['topLevelComment']['snippet']['publishedAt']
                }
                comment_data.append(data)
        except Exception as e:
            st.error(f"Error fetching comment info: {e}")
    return comment_data

# Function to get playlist details
def get_playlist_details(channel_id):
    all_data = []
    next_page_token = None
    try:
        while True:
            request = youtube.playlists().list(part='snippet,contentDetails', channelId=channel_id, maxResults=50, pageToken=next_page_token)
            response = request.execute()
            for item in response['items']:
                data = {
                    "playlist_id": item['id'],
                    "title": item['snippet']['title'],
                    "channel_id": item['snippet']['channelId'],
                    "channel_name": item['snippet']['channelTitle'],
                    "published_at": item['snippet']['publishedAt'],
                    "video_count": item['contentDetails']['itemCount']
                }
                all_data.append(data)
            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break
    except Exception as e:
        st.error(f"Error fetching playlist details: {e}")
    return all_data

def create_and_insert_table(create_query, data, conflict_column):
    conn = None
    try:
        conn = psycopg2.connect(host="localhost", user="postgres", port="5432", database="youtube", password=os.getenv("DB_PASSWORD"))
        cursor = conn.cursor()
        cursor.execute(create_query)
        conn.commit()

        table_name = create_query.split()[5]
        columns = ', '.join(data[0].keys())
        values_placeholders = ', '.join(['%s'] * len(data[0]))
        insert_query = f"""
            INSERT INTO {table_name} ({columns}) 
            VALUES ({values_placeholders}) 
            ON CONFLICT ({conflict_column}) DO NOTHING
        """

        for values in data:
            cursor.execute(insert_query, tuple(values.values()))

        conn.commit()
    except Exception as e:
        st.error(f"Error creating/inserting table: {e}")
    finally:
        if conn:
            conn.close()

def channels_table(channel_name, channel_id):
    create_query = '''
        CREATE TABLE IF NOT EXISTS channels (
            channel_name VARCHAR(100),
            channel_id VARCHAR(80) PRIMARY KEY,
            subscribers BIGINT,
            views BIGINT,
            total_videos INT,
            channel_description TEXT,
            playlist_id VARCHAR(80)
        )
    '''
    single_channel_details = [get_channel_info(channel_id)]
    create_and_insert_table(create_query, single_channel_details, conflict_column="channel_id")
    st.success("Channel data inserted successfully.")

def playlist_table(channel_name, channel_id):
    create_query = '''
        CREATE TABLE IF NOT EXISTS playlists (
            playlist_id VARCHAR(100) PRIMARY KEY,
            title VARCHAR(100),
            channel_id VARCHAR(100),
            channel_name VARCHAR(100),
            published_at TIMESTAMP,
            video_count INT
        )
    '''
    playlist_details = get_playlist_details(channel_id)
    create_and_insert_table(create_query, playlist_details, conflict_column="playlist_id")
    st.success("Playlist data inserted successfully.")

def videos_table(channel_name, channel_id):
    create_query = '''
        CREATE TABLE IF NOT EXISTS videos (
            channel_name VARCHAR(100),
            channel_id VARCHAR(100),
            video_id VARCHAR(30) PRIMARY KEY,
            title VARCHAR(150),
            tags TEXT,
            thumbnail VARCHAR(200),
            description TEXT,
            published_date TIMESTAMP,
            duration VARCHAR(20),
            views BIGINT,
            likes BIGINT,
            comments INT,
            favorite_count INT,
            definition VARCHAR(10),
            caption_status VARCHAR(50)
        )
    '''
    video_ids = get_videos_ids(channel_id)
    video_details = get_video_info(video_ids)
    create_and_insert_table(create_query, video_details, conflict_column="video_id")
    st.success("Video data inserted successfully.")

def comments_table(channel_name, channel_id):
    create_query = '''
        CREATE TABLE IF NOT EXISTS comments (
            comment_id VARCHAR(100) PRIMARY KEY,
            video_id VARCHAR(50),
            comment_text TEXT,
            comment_author VARCHAR(150),
            comment_published TIMESTAMP
        )
    '''
    video_ids = get_videos_ids(channel_id)
    comment_details = get_comment_info(video_ids)
    create_and_insert_table(create_query, comment_details, conflict_column="comment_id")
    st.success("Comment data inserted successfully.")

def tables(channel_name, channel_id):
    channels_table(channel_name, channel_id)
    playlist_table(channel_name, channel_id)
    videos_table(channel_name, channel_id)
    comments_table(channel_name, channel_id)
    return "Tables Created Successfully"

# Define the function to connect to SQL database
def connect_to_sql():
    try:
        conn = psycopg2.connect(host="localhost", user="postgres", port="5432", database="youtube", password=os.getenv("DB_PASSWORD"))
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Define the function to display the channels table
def show_channels_table():
    conn = connect_to_sql()
    if not conn:
        return pd.DataFrame()
    cursor = conn.cursor()
    query = "SELECT * FROM channels"
    cursor.execute(query)
    channels_data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(channels_data, columns=["channel_name", "channel_id", "subscribers", "views", "total_videos", "channel_description", "playlist_id"])

# Define the function to display the playlists table
def show_playlists_table():
    conn = connect_to_sql()
    if not conn:
        return pd.DataFrame()
    cursor = conn.cursor()
    query = "SELECT * FROM playlists"
    cursor.execute(query)
    playlists_data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(playlists_data, columns=["playlist_id", "title", "channel_id", "channel_name", "published_at", "video_count"])

# Define the function to display the videos table
def show_videos_table():
    conn = connect_to_sql()
    if not conn:
        return pd.DataFrame()
    cursor = conn.cursor()
    query = "SELECT * FROM videos"
    cursor.execute(query)
    videos_data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(videos_data, columns=["channel_name", "channel_id", "video_id", "title", "tags", "thumbnail", "description", "published_date", "duration", "views", "likes", "comments", "favorite_count", "definition", "caption_status"])

# Define the function to display the comments table
def show_comments_table():
    conn = connect_to_sql()
    if not conn:
        return pd.DataFrame()
    cursor = conn.cursor()
    query = "SELECT * FROM comments"
    cursor.execute(query)
    comments_data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(comments_data, columns=["comment_id", "video_id", "comment_text", "comment_author", "comment_published"])

# Function to visualize subscriber count over time
def visualize_subscribers(df_channels):
    fig = px.line(df_channels, x='channel_name', y='subscribers', title='Subscribers Over Time')
    st.plotly_chart(fig)
    st.write(f"The channel with the highest subscribers is {df_channels.loc[df_channels['subscribers'].idxmax()]['channel_name']} with {df_channels['subscribers'].max()} subscribers.")
    st.write(f"The channel with the lowest subscribers is {df_channels.loc[df_channels['subscribers'].idxmin()]['channel_name']} with {df_channels['subscribers'].min()} subscribers.")
    st.write(f"The total number of subscribers across all channels is {df_channels['subscribers'].sum()}.")

# Function to visualize top videos by views
def visualize_top_videos(df_videos):
    df_videos_sorted = df_videos.sort_values(by='views', ascending=False).head(10)
    fig = px.bar(df_videos_sorted, x='title', y='views', title='Top 10 Videos by Views')
    st.plotly_chart(fig)
    st.write(f"The video with the highest views is '{df_videos_sorted.iloc[0]['title']}' with {df_videos_sorted.iloc[0]['views']} views.")
    st.write(f"The video with the lowest views among the top 10 is '{df_videos_sorted.iloc[-1]['title']}' with {df_videos_sorted.iloc[-1]['views']} views.")
    st.write(f"The total number of views across the top 10 videos is {df_videos_sorted['views'].sum()}.")

# Function to visualize video duration distribution
def visualize_video_duration(df_videos):
    df_videos['duration'] = pd.to_timedelta(df_videos['duration'])
    fig, ax = plt.subplots()
    sns.histplot(df_videos['duration'].dt.total_seconds() / 60, bins=20, ax=ax)
    ax.set_title('Video Duration Distribution')
    ax.set_xlabel('Duration (minutes)')
    st.pyplot(fig)
    st.write(f"The longest video is {df_videos.loc[df_videos['duration'].idxmax()]['title']} with a duration of {df_videos['duration'].max()}.")
    st.write(f"The shortest video is {df_videos.loc[df_videos['duration'].idxmin()]['title']} with a duration of {df_videos['duration'].min()}.")
    st.write(f"The average video duration is {df_videos['duration'].mean()}.")

# Other visualization functions
def visualize_video_duration_scatter(df_videos):
    fig = px.scatter(df_videos, x='title', y='duration', title='Video Duration Scatter')
    st.plotly_chart(fig)
    st.write(f"The longest video is {df_videos.loc[df_videos['duration'].idxmax()]['title']} with a duration of {df_videos['duration'].max()}.")
    st.write(f"The shortest video is {df_videos.loc[df_videos['duration'].idxmin()]['title']} with a duration of {df_videos['duration'].min()}.")

def visualize_videos_per_channel(df_videos):
    df_videos_grouped = df_videos.groupby('channel_name').size().reset_index(name='video_count')
    fig = px.bar(df_videos_grouped, x='channel_name', y='video_count', title='Videos per Channel')
    st.plotly_chart(fig)
    st.write(f"The channel with the most videos is {df_videos_grouped.loc[df_videos_grouped['video_count'].idxmax()]['channel_name']} with {df_videos_grouped['video_count'].max()} videos.")
    st.write(f"The channel with the least videos is {df_videos_grouped.loc[df_videos_grouped['video_count'].idxmin()]['channel_name']} with {df_videos_grouped['video_count'].min()} videos.")
    st.write(f"The total number of videos across all channels is {df_videos_grouped['video_count'].sum()}.")

def visualize_avg_views_per_channel(df_videos):
    df_videos_grouped = df_videos.groupby('channel_name')['views'].mean().reset_index(name='avg_views')
    fig = px.bar(df_videos_grouped, x='channel_name', y='avg_views', title='Average Views per Channel')
    st.plotly_chart(fig)
    st.write(f"The channel with the highest average views is {df_videos_grouped.loc[df_videos_grouped['avg_views'].idxmax()]['channel_name']} with an average of {df_videos_grouped['avg_views'].max()} views per video.")
    st.write(f"The channel with the lowest average views is {df_videos_grouped.loc[df_videos_grouped['avg_views'].idxmin()]['channel_name']} with an average of {df_videos_grouped['avg_views'].min()} views per video.")
    st.write(f"The overall average views per video across all channels is {df_videos_grouped['avg_views'].mean()}.")

def visualize_video_definitions(df_videos):
    fig = px.pie(df_videos, names='definition', title='Video Definitions')
    st.plotly_chart(fig)
    definition_counts = df_videos['definition'].value_counts()
    for definition, count in definition_counts.items():
        st.write(f"Definition: {definition}, Count: {count}")

# Function to execute selected question
def execute_question(question):
    conn = connect_to_sql()
    if not conn:
        return
    try:
        if question == "1. All the videos and the channel name":
            query = '''SELECT title AS "video_title", channel_name AS "channel_name" FROM videos'''
        elif question == "2. Channels with most number of videos":
            query = '''SELECT channel_name AS "channel_name", COUNT(*) AS "no_of_videos" FROM videos GROUP BY channel_name ORDER BY COUNT(*) DESC'''
        elif question == "3. 10 most viewed videos":
            query = '''SELECT title AS "video_title", views AS "views" FROM videos ORDER BY views DESC LIMIT 10'''
        elif question == "4. Comments in each videos":
            query = '''SELECT title AS "video_title", comments AS "no_of_comments" FROM videos WHERE comments IS NOT NULL'''
        elif question == "5. Videos with highest likes":
            query = '''SELECT title AS "video_title", channel_name AS "channel_name", likes AS "like_count" FROM videos WHERE likes IS NOT NULL ORDER BY likes DESC'''
        elif question == "6. Likes of all videos":
            query = '''SELECT likes AS "like_count", title AS "video_title" FROM videos'''
        elif question == "7. Views of each channel":
            query = '''SELECT channel_name AS "channel_name", SUM(views) AS "total_views" FROM videos GROUP BY channel_name'''
        elif question == "8. Videos published in the year of 2022":
            query = '''SELECT title AS "video_title", published_date AS "published_date", channel_name AS "channel_name" FROM videos WHERE EXTRACT(YEAR FROM published_date) = 2022'''
        elif question == "9. Average duration of all videos in each channel":
            query = '''SELECT channel_name AS "channel_name", AVG(duration) AS "average_duration" FROM videos GROUP BY channel_name'''
        elif question == "10. Videos with highest number of comments":
            query = '''SELECT title AS "video_title", channel_name AS "channel_name", comments AS "no_of_comments" FROM videos WHERE comments IS NOT NULL ORDER BY comments DESC'''

        df = pd.read_sql(query, conn)
        conn.close()
        st.write(df)
    except Exception as e:
        st.error(f"Error executing query: {e}")
    finally:
        if conn:
            conn.close()

def show_individual_channel_details(channel_name):
    conn = connect_to_sql()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        # Display channel details
        query = "SELECT * FROM channels WHERE channel_name = %s"
        cursor.execute(query, (channel_name,))
        channel_details = cursor.fetchall()
        df_channel_details = pd.DataFrame(channel_details, columns=["channel_name", "channel_id", "subscribers", "views", "total_videos", "channel_description", "playlist_id"])
        st.write("Channel Details:")
        st.write(df_channel_details)

        # Display playlists for the selected channel
        query = "SELECT * FROM playlists WHERE channel_name = %s"
        cursor.execute(query, (channel_name,))
        playlist_details = cursor.fetchall()
        df_playlist_details = pd.DataFrame(playlist_details, columns=["playlist_id", "title", "channel_id", "channel_name", "published_at", "video_count"])
        st.write("Playlists:")
        st.write(df_playlist_details)

        # Display videos for the selected channel
        query = "SELECT * FROM videos WHERE channel_name = %s"
        cursor.execute(query, (channel_name,))
        video_details = cursor.fetchall()
        df_video_details = pd.DataFrame(video_details, columns=["channel_name", "channel_id", "video_id", "title", "tags", "thumbnail", "description", "published_date", "duration", "views", "likes", "comments", "favorite_count", "definition", "caption_status"])
        st.write("Videos:")
        st.write(df_video_details)

        # Display comments for the selected channel
        query = "SELECT * FROM comments WHERE video_id IN (SELECT video_id FROM videos WHERE channel_name = %s)"
        cursor.execute(query, (channel_name,))
        comment_details = cursor.fetchall()
        df_comment_details = pd.DataFrame(comment_details, columns=["comment_id", "video_id", "comment_text", "comment_author", "comment_published"])
        st.write("Comments:")
        st.write(df_comment_details)
    except Exception as e:
        st.error(f"Error displaying individual channel details: {e}")
    finally:
        if conn:
            conn.close()

# Main function
def main():
    st.sidebar.title("YouTube Data Analyzer")

    # Custom CSS for fonts, backgrounds, and buttons
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Roboto', sans-serif;
        }

        .stButton button {
            background: linear-gradient(to right, #1e90ff, #00d4ff);
            border: none;
            color: white;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            transition-duration: 0.4s;
            cursor: pointer;
        }

        .stButton button:hover {
            background: linear-gradient(to right, #00d4ff, #1e90ff);
        }
        
        .css-10trblm {
            background: url('https://www.example.com/background-image.jpg');
            background-size: cover;
        }
        
        .radio-group {
            display: flex;
            flex-direction: column;
        }

        .radio-label {
            display: flex;
            align-items: center;
            padding: 0.5em;
            margin-bottom: 0.5em;
            background-color: #fff;
            border: 1px solid #ccc;
            border-radius: 4px;
            transition: background-color 0.2s, border-color 0.2s;
        }

        .radio-label:hover {
            background-color: #e6e6e6;
        }

        .radio-input {
            position: absolute;
            opacity: 0;
        }

        .radio-input:checked + .radio-label {
            background-color: #c3c3ff;
            border-color: #1111ff;
        }

        .radio-input:focus + .radio-label {
            outline: 2px solid #1111ff;
        }

        .radio-inner-circle {
            display: inline-block;
            width: 1em;
            height: 1em;
            border: 2px solid #888;
            border-radius: 50%;
            margin-right: 0.5em;
            transition: border-color 0.2s;
            position: relative;
        }

        .radio-label:hover .radio-inner-circle {
            border-color: #555;
        }

        .radio-input:checked + .radio-label .radio-inner-circle {
            border-color: #1111ff;
        }

        .radio-input:checked + .radio-label .radio-inner-circle::after {
            content: '';
            display: block;
            width: 0.5em;
            height: 0.5em;
            background-color: #1111ff;
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }

        .input {
            width: 200px;
            padding: 12px;
            border: 2px solid #3498db;
            border-radius: 8px;
            outline: none;
            font-size: 18px;
            transition: border-color 0.3s, box-shadow 0.3s, transform 0.3s;
            background-color: #fff;
            color: #333;
            box-sizing: border-box;
        }

        .input:focus {
            border-color: #2980b9;
            box-shadow: 0 0 15px rgba(52, 152, 219, 0.5);
            transform: scale(1.02);
        }

        .input::placeholder {
            color: #aaa;
            font-style: italic;
        }

        .input:hover {
            background-color: #f0f8ff;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Main navigation options
    main_page = st.sidebar.radio("Choose a section", ["Home", "YouTube Analysis",])

    if main_page == "Home":
        st.title("Welcome to the YouTube Data Harvesting and Warehousing")
        st.write("Use this app to analyze YouTube channel data.")

    elif main_page == "YouTube Analysis":
        st.title("YouTube Analysis")

        # Sub-navigation for YouTube Analysis
        sub_page = st.sidebar.radio("Choose a sub-section", ["Data Display", "Individual Channel Details", "Analysis Questions", "Visualizations"])

        if sub_page == "Data Display":
            st.header("Data Display")
            display_option = st.selectbox("Choose a table to display", ["Channels", "Playlists", "Videos", "Comments"])
            if display_option == "Channels":
                st.dataframe(show_channels_table())
            elif display_option == "Playlists":
                st.dataframe(show_playlists_table())
            elif display_option == "Videos":
                st.dataframe(show_videos_table())
            elif display_option == "Comments":
                st.dataframe(show_comments_table())

        elif sub_page == "Individual Channel Details":
            st.header("Individual Channel Details")
            df_channels = show_channels_table()
            channel_name_selected = st.selectbox("Select a channel to view individual data", df_channels['channel_name'].tolist() if not df_channels.empty else [])
            if channel_name_selected:
                show_individual_channel_details(channel_name_selected)

        elif sub_page == "Visualizations":
            st.header("Visualizations")
            df_channels = show_channels_table()
            df_videos = show_videos_table()

            visualization_option = st.selectbox("Choose a visualization", [
                "Subscribers Over Time", "Top Videos by Views", "Video Duration Distribution",
                "Video Duration Scatter", "Videos per Channel", "Average Views per Channel",
                "Video Definitions"
            ])

            if visualization_option == "Subscribers Over Time":
                visualize_subscribers(df_channels)
            elif visualization_option == "Top Videos by Views":
                visualize_top_videos(df_videos)
            elif visualization_option == "Video Duration Distribution":
                visualize_video_duration(df_videos)
            elif visualization_option == "Video Duration Scatter":
                visualize_video_duration_scatter(df_videos)
            elif visualization_option == "Videos per Channel":
                visualize_videos_per_channel(df_videos)
            elif visualization_option == "Average Views per Channel":
                visualize_avg_views_per_channel(df_videos)
            elif visualization_option == "Video Definitions":
                visualize_video_definitions(df_videos)

        elif sub_page == "Analysis Questions":
            st.title("Q&A (Questions & Answers)")
            st.header("Analysis Questions")
            questions = [
                "1. All the videos and the channel name",
                "2. Channels with most number of videos",
                "3. 10 most viewed videos",
                "4. Comments in each videos",
                "5. Videos with highest likes",
                "6. Likes of all videos",
                "7. Views of each channel",
                "8. Videos published in the year of 2022",
                "9. Average duration of all videos in each channel",
                "10. Videos with highest number of comments"
            ]
            selected_question = st.selectbox("Select the question", questions)
            if st.button("Execute"):
                execute_question(selected_question)

    st.sidebar.header("Enter YouTube Channel ID")
    channel_id = st.sidebar.text_input("Channel ID")
    if st.sidebar.button("Fetch and Store Data"):
        channel_info = get_channel_info(channel_id)
        if channel_info:
            channel_name = channel_info['channel_name']
            st.write(f"Fetching data for channel: {channel_name}")
            tables(channel_name, channel_id)

if __name__ == "__main__":
    main()
