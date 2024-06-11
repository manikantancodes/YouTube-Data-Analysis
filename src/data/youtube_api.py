# src/data/youtube_api.py
import os
import streamlit as st
from googleapiclient.discovery import build

# Function to connect to the YouTube API
def api_connect():
    """
    Connects to the YouTube API using the API key from environment variables.
    
    Returns:
        youtube: The YouTube API client object.
    """
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
    """
    Retrieves channel details such as name, ID, subscribers, views, total videos, description, and playlist ID.
    
    Args:
        channel_id (str): The ID of the YouTube channel.
    
    Returns:
        dict: A dictionary containing channel details.
    """
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
    """
    Retrieves video IDs from the channel's uploads playlist.
    
    Args:
        channel_id (str): The ID of the YouTube channel.
    
    Returns:
        list: A list of video IDs.
    """
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
    """
    Retrieves detailed information for each video, including title, tags, description, publish date, duration, views, likes, comments, etc.
    
    Args:
        video_ids (list): A list of video IDs.
    
    Returns:
        list: A list of dictionaries containing video details.
    """
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
    """
    Retrieves comment details for each video, including comment text, author, and publish date.
    
    Args:
        video_ids (list): A list of video IDs.
    
    Returns:
        list: A list of dictionaries containing comment details.
    """
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
    """
    Retrieves details for each playlist, including title, channel ID, channel name, publish date, and video count.
    
    Args:
        channel_id (str): The ID of the YouTube channel.
    
    Returns:
        list: A list of dictionaries containing playlist details.
    """
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

