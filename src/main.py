from googleapiclient.discovery import build
import psycopg2
import pandas as pd
import streamlit as st

# API key connection
def Api_connect():
    Api_Id = "AIzaSyDS5WmgQf10XnGh2n5Cu3AtA-g75m_SYVU"
    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name, api_version, developerKey=Api_Id)
    return youtube

youtube = Api_connect()

# Get channel information
def get_channel_info(channel_id):
    request = youtube.channels().list(
        part="snippet,ContentDetails,statistics",
        id=channel_id
    )
    response = request.execute()

    for i in response['items']:
        data = dict(Channel_Name=i["snippet"]["title"],
                    Channel_Id=i["id"],
                    Subscribers=i['statistics']['subscriberCount'],
                    Title=i['snippet']['title'],
                    Views=i["statistics"]["viewCount"],
                    Total_Videos=i["statistics"]["videoCount"],
                    Channel_Description=i["snippet"]["description"],
                    Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
    return data

# Get video ids
def get_videos_ids(channel_id):
    video_ids = []
    response = youtube.channels().list(id=channel_id,
                                       part='contentDetails').execute()
    Playlist_Id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token = None

    while True:
        response1 = youtube.playlistItems().list(
            part='snippet',
            playlistId=Playlist_Id,
            maxResults=50,
            pageToken=next_page_token).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = response1.get('nextPageToken')

        if next_page_token is None:
            break
    return video_ids

# Get video information
def get_video_info(video_ids):
    video_data = []
    for video_id in video_ids:
        request = youtube.videos().list(
            part="snippet,ContentDetails,statistics",
            id=video_id
        )
        response = request.execute()

        for item in response["items"]:
            data = dict(Channel_Name=item['snippet']['channelTitle'],
                        Channel_Id=item['snippet']['channelId'],
                        Video_Id=item['id'],
                        Title=item['snippet']['title'],
                        Tags=item['snippet'].get('tags'),
                        Thumbnail=item['snippet']['thumbnails']['default']['url'],
                        Description=item['snippet'].get('description'),
                        Published_Date=item['snippet']['publishedAt'],
                        Duration=item['contentDetails']['duration'],
                        Views=item['statistics'].get('viewCount'),
                        Likes=item['statistics'].get('likeCount'),
                        Comments=item['statistics'].get('commentCount'),
                        Favorite_Count=item['statistics']['favoriteCount'],
                        Definition=item['contentDetails']['definition'],
                        Caption_Status=item['contentDetails']['caption']
                        )
            video_data.append(data)
    return video_data

# Get comment information
def get_comment_info(video_ids):
    Comment_data = []
    try:
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
            )
            response = request.execute()

            for item in response['items']:
                data = dict(Comment_Id=item['snippet']['topLevelComment']['id'],
                            Video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],
                            Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_Published=item['snippet']['topLevelComment']['snippet']['publishedAt'])

                Comment_data.append(data)

    except:
        pass
    return Comment_data

# Get playlist details
def get_playlist_details(channel_id):
    next_page_token = None
    All_data = []
    while True:
        request = youtube.playlists().list(
            part='snippet,contentDetails',
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            data = dict(Playlist_Id=item['id'],
                        Title=item['snippet']['title'],
                        Channel_Id=item['snippet']['channelId'],
                        Channel_Name=item['snippet']['channelTitle'],
                        PublishedAt=item['snippet']['publishedAt'],
                        Video_Count=item['contentDetails']['itemCount'])
            All_data.append(data)

        next_page_token = response.get('nextPageToken')
        if next_page_token is None:
            break
    return All_data

# Table creation for channels, playlists, videos, comments
def channels_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        port="5432",
        database="youtube",
        password="mani94"
    )
    cursor = mydb.cursor()

    try:
        create_query = '''create table if not exists channels(Channel_Name varchar(100),
                                                            Channel_Id varchar(80) primary key,
                                                            Subscribers bigint,
                                                            Views bigint,
                                                            Total_Videos int,
                                                            Channel_Description text,
                                                            Playlist_Id varchar(80))'''
        cursor.execute(create_query)
        mydb.commit()

    except:
        print("Channels table already created")

    # Fetching all data
    query_1 = "SELECT * FROM channels"
    cursor.execute(query_1)
    table = cursor.fetchall()
    mydb.commit()

    chann_list = []
    chann_list2 = []
    df_all_channels = pd.DataFrame(table)

    chann_list.append(df_all_channels[0])
    for i in chann_list[0]:
        chann_list2.append(i)

    if channel_name_s in chann_list2:
        news = f"Your Provided Channel {channel_name_s} is Already exists"
        return news

    else:
        single_channel_details = get_channel_info(channel_id)

        insert_query = '''insert into channels(Channel_Name ,
                                                Channel_Id,
                                                Subscribers,
                                                Views,
                                                Total_Videos,
                                                Channel_Description,
                                                Playlist_Id)
                                                values(%s,%s,%s,%s,%s,%s,%s)'''
        values = (single_channel_details['Channel_Name'],
                  single_channel_details['Channel_Id'],
                  single_channel_details['Subscribers'],
                  single_channel_details['Views'],
                  single_channel_details['Total_Videos'],
                  single_channel_details['Channel_Description'],
                  single_channel_details['Playlist_Id'])

        try:
            cursor.execute(insert_query, values)
            mydb.commit()
            st.success("Channel data inserted successfully.")

        except Exception as e:
            st.error(f"Error inserting channel data: {e}")

def playlist_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        port="5432",
        database="youtube",
        password="mani94"
    )
    cursor = mydb.cursor()

    create_query = '''create table if not exists playlists(Playlist_Id varchar(100) primary key,
                                                        Title varchar(100),
                                                        Channel_Id varchar(100),
                                                        Channel_Name varchar(100),
                                                        PublishedAt timestamp,
                                                        Video_Count int
                                                        )'''

    cursor.execute(create_query)
    mydb.commit()

    playlist_details = get_playlist_details(channel_id)
    df_playlist = pd.DataFrame(playlist_details)

    for index, row in df_playlist.iterrows():
        insert_query = '''insert into playlists(Playlist_Id,
                                            Title,
                                            Channel_Id,
                                            Channel_Name,
                                            PublishedAt,
                                            Video_Count
                                            )
                                            values(%s,%s,%s,%s,%s,%s)'''

        values = (row['Playlist_Id'],
                  row['Title'],
                  row['Channel_Id'],
                  row['Channel_Name'],
                  row['PublishedAt'],
                  row['Video_Count']
                  )

        


def videos_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        port="5432",
        database="youtube",
        password="mani94"
    )
    cursor = mydb.cursor()

    create_query = '''create table if not exists videos(Channel_Name varchar(100),
                                                    Channel_Id varchar(100),
                                                    Video_Id varchar(30) primary key,
                                                    Title varchar(150),
                                                    Tags text,
                                                    Thumbnail varchar(200),
                                                    Description text,
                                                    Published_Date timestamp,
                                                    Duration interval,
                                                    Views bigint,
                                                    Likes bigint,
                                                    Comments int,
                                                    Favorite_Count int,
                                                    Definition varchar(10),
                                                    Caption_Status varchar(50)
                                                        )'''

    cursor.execute(create_query)
    mydb.commit()

    video_ids = get_videos_ids(channel_id)
    video_details = get_video_info(video_ids)
    df_videos = pd.DataFrame(video_details)

    for index, row in df_videos.iterrows():
        insert_query = '''insert into videos(Channel_Name,
                                                    Channel_Id,
                                                    Video_Id,
                                                    Title,
                                                    Tags,
                                                    Thumbnail,
                                                    Description,
                                                    Published_Date,
                                                    Duration,
                                                    Views,
                                                    Likes,
                                                    Comments,
                                                    Favorite_Count,
                                                    Definition,
                                                    Caption_Status
                                                )
                                                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

        values = (row['Channel_Name'],
                  row['Channel_Id'],
                  row['Video_Id'],
                  row['Title'],
                  str(row['Tags']),
                  row['Thumbnail'],
                  row['Description'],
                  row['Published_Date'],
                  row['Duration'],
                  row['Views'],
                  row['Likes'],
                  row['Comments'],
                  row['Favorite_Count'],
                  row['Definition'],
                  row['Caption_Status']
                  )

        
def comments_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        port="5432",
        database="youtube",
        password="mani94"
    )
    cursor = mydb.cursor()

    create_query = '''create table if not exists comments(Comment_Id varchar(100) primary key,
                                                        Video_Id varchar(50),
                                                        Comment_Text text,
                                                        Comment_Author varchar(150),
                                                        Comment_Published timestamp
                                                        )'''

    cursor.execute(create_query)
    mydb.commit()

    video_ids = get_videos_ids(channel_id)
    comment_details = get_comment_info(video_ids)
    df_comments = pd.DataFrame(comment_details)

    for index, row in df_comments.iterrows():
        insert_query = '''insert into comments(Comment_Id,
                                                    Video_Id,
                                                    Comment_Text,
                                                    Comment_Author,
                                                    Comment_Published
                                                )
                                                values(%s,%s,%s,%s,%s)'''

        values = (row['Comment_Id'],
                  row['Video_Id'],
                  row['Comment_Text'],
                  row['Comment_Author'],
                  row['Comment_Published']
                  )

        
            

def tables(channel_name):
    news = channels_table(channel_name)
    if news:
        st.write(news)
    else:
        playlist_table(channel_name)
        videos_table(channel_name)
        comments_table(channel_name)

    return "Tables Created Successfully"
def connect_to_sql():
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        port="5432",
        database="youtube",
        password="mani94"
    )
    return conn

# Define the function to display the channels table
def show_channels_table():
    try:
        conn = connect_to_sql()
        cursor = conn.cursor()
        query = "SELECT * FROM channels"
        cursor.execute(query)
        channels_data = cursor.fetchall()
        conn.close()
        df_channels = pd.DataFrame(channels_data, columns=["Channel Name", "Channel Id","Total Views" , "Total Videos", "Channel Description", "Playlist Id","Subscribers"])
        st.write(df_channels)
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"An error occurred: {error}")

# Define the function to display the playlists table

def show_playlists_table():
    try:
        conn = connect_to_sql()
        cursor = conn.cursor()
        query = "SELECT * FROM playlists"
        cursor.execute(query)
        playlists_data = cursor.fetchall()
        conn.close()
        df_playlists = pd.DataFrame(playlists_data, columns=["Playlist ID", "Channel ID","Channel Name", "Title", "Video Count", "Published At"])
        st.write(df_playlists)
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"An error occurred: {error}")

# Define the function to display the videos table
def show_videos_table():
    try:
        conn = connect_to_sql()
        cursor = conn.cursor()
        query = "SELECT video_id, channel_id, title, description, published_date, views, likes, comments, favorite_count, duration, thumbnail, definition, channel_name, caption_status, tags FROM videos"
        cursor.execute(query)
        videos_data = cursor.fetchall()
        conn.close()
        df_videos = pd.DataFrame(videos_data, columns=["Video ID", "Channel ID", "Title", "Description", "Published Date", "Views", "Likes", "Comments", "Favorite Count", "Duration", "Thumbnail", "Definition", "Channel Name", "Caption Status", "Tags"])
        st.write(df_videos)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)




# Define the function to display the comments table
def show_comments_table():
    try:
        conn = connect_to_sql()
        cursor = conn.cursor()
        query = "SELECT * FROM comments"
        cursor.execute(query)
        comments_data = cursor.fetchall()
        conn.close()
        df_comments = pd.DataFrame(comments_data, columns=["Comment ID", "Video ID", "Text", "Author", "Published At"])
        st.write(df_comments)
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"An error occurred: {error}")

# Streamlit part
with st.sidebar:
    st.title(":red[YOUTUBE DATA HAVERSTING AND WAREHOUSING]")
    st.header("Skill Take Away")
    st.caption("Python Scripting")
    st.caption("Data Collection")
    st.caption("API Integration")
    st.caption("Data Management using SQL")

channel_id = st.text_input("Enter the channel ID")

if st.button("Collect and Store Data"):
    tables(get_channel_info(channel_id)['Channel_Name'])

            

def get_all_channels():
    try:
        conn = connect_to_sql()
        cursor = conn.cursor()
        query = "SELECT channel_name FROM channels"  # Modify the table name here
        cursor.execute(query)
        channels = cursor.fetchall()
        conn.close()
        return [channel[0] for channel in channels]
    except (Exception, psycopg2.DatabaseError) as error:
        st.error("An error occurred while fetching channel names from the database.")
        st.error(error)
        return []

all_channels = get_all_channels()
unique_channel = st.selectbox("Select the Channel", all_channels)


show_table = st.radio("SELECT THE TABLE FOR VIEW", ("CHANNELS", "PLAYLISTS", "VIDEOS", "COMMENTS"))

if show_table == "CHANNELS":
    show_channels_table()
elif show_table == "PLAYLISTS":
    show_playlists_table()
elif show_table == "VIDEOS":
    show_videos_table()
elif show_table == "COMMENTS":
    show_comments_table()


# SQL Connection
mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        port="5432",
        database="youtube",
        password="mani94"
    )
cursor = mydb.cursor()


# Function to connect to the PostgreSQL database
def connect_to_sql():
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        port="5432",
        database="youtube",
        password="mani94"
    )
    return conn

# Function to execute SQL queries and display results
def execute_query(query, columns):
    try:
        conn = connect_to_sql()
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        df = pd.DataFrame(data, columns=columns)
        st.write(df)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

# Define questions
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

# Function to execute selected question
def execute_question(question):
    if question == "1. All the videos and the channel name":
        query = '''SELECT title AS "Video Title", channel_name AS "Channel Name" FROM videos'''
        columns = ["Video Title", "Channel Name"]
        execute_query(query, columns)
    elif question == "2. Channels with most number of videos":
        query = '''SELECT channel_name AS "Channel Name", COUNT(*) AS "No of Videos" FROM videos GROUP BY channel_name ORDER BY COUNT(*) DESC'''
        columns = ["Channel Name", "No of Videos"]
        execute_query(query, columns)
    elif question == "3. 10 most viewed videos":
        query = '''SELECT title AS "Video Title", views AS "Views" FROM videos ORDER BY views DESC LIMIT 10'''
        columns = ["Video Title", "Views"]
        execute_query(query, columns)
    elif question == "4. Comments in each videos":
        query = '''SELECT title AS "Video Title", comments AS "No of Comments" FROM videos WHERE comments IS NOT NULL'''
        columns = ["Video Title", "No of Comments"]
        execute_query(query, columns)
    elif question == "5. Videos with highest likes":
        query = '''SELECT title AS "Video Title", channel_name AS "Channel Name", likes AS "Like Count" FROM videos WHERE likes IS NOT NULL ORDER BY likes DESC'''
        columns = ["Video Title", "Channel Name", "Like Count"]
        execute_query(query, columns)
    elif question == "6. Likes of all videos":
        query = '''SELECT likes AS "Like Count", title AS "Video Title" FROM videos'''
        columns = ["Like Count", "Video Title"]
        execute_query(query, columns)
    elif question == "7. Views of each channel":
        query = '''SELECT channel_name AS "Channel Name", SUM(views) AS "Total Views" FROM videos GROUP BY channel_name'''
        columns = ["Channel Name", "Total Views"]
        execute_query(query, columns)
    elif question == "8. Videos published in the year of 2022":
        query = '''SELECT title AS "Video Title", published_date AS "Published Date", channel_name AS "Channel Name" FROM videos WHERE EXTRACT(YEAR FROM published_date) = 2022'''
        columns = ["Video Title", "Published Date", "Channel Name"]
        execute_query(query, columns)
    elif question == "9. Average duration of all videos in each channel":
        query = '''SELECT channel_name AS "Channel Name", AVG(duration) AS "Average Duration" FROM videos GROUP BY channel_name'''
        columns = ["Channel Name", "Average Duration"]
        execute_query(query, columns)
    elif question == "10. Videos with highest number of comments":
        query = '''SELECT title AS "Video Title", channel_name AS "Channel Name", comments AS "No of Comments" FROM videos WHERE comments IS NOT NULL ORDER BY comments DESC'''
        columns = ["Video Title", "Channel Name", "No of Comments"]
        execute_query(query, columns)

# Display questions and execute selected question
selected_question = st.selectbox("Select the question", questions)
if st.button("Execute"):
    execute_question(selected_question)
