# src/data/youtube_api.py

from googleapiclient.discovery import build
import psycopg2
import pandas as pd

def api_connect(api_key):
    """Connect to the YouTube API using the provided API key."""
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        return youtube
    except Exception as e:
        print("Error connecting to the YouTube API:", e)
        return None

def get_channel_info(youtube, channel_id):
    """Retrieve information about a YouTube channel."""
    try:
        request = youtube.channels().list(
            part="snippet, contentDetails, statistics",
            id=channel_id
        )
        response = request.execute()
        return response.get('items', [])
    except Exception as e:
        print("Error retrieving channel information:", e)
        return []

def get_playlist_details(youtube, channel_id):
    """Retrieve details of playlists associated with a YouTube channel."""
    try:
        next_page_token = None
        all_playlists = []
        while True:
            request = youtube.playlists().list(
                part='snippet, contentDetails',
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            all_playlists.extend(response.get('items', []))
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        return all_playlists
    except Exception as e:
        print("Error retrieving playlist details:", e)
        return []

def get_videos_ids(youtube, channel_id):
    """Retrieve video IDs of videos uploaded to a channel."""
    video_ids = []
    try:
        response = youtube.channels().list(id=channel_id, part='contentDetails').execute()
        playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        next_page_token = None
        while True:
            request = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            for item in response['items']:
                video_ids.append(item['snippet']['resourceId']['videoId'])
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
    except Exception as e:
        print("Error retrieving video IDs:", e)
    return video_ids

def get_video_info(youtube, video_ids):
    """Retrieve information about videos."""
    video_data = []
    try:
        for video_id in video_ids:
            request = youtube.videos().list(
                part="snippet, contentDetails, statistics",
                id=video_id
            )
            response = request.execute()

            for item in response["items"]:
                data = {
                    'Channel_Name': item['snippet']['channelTitle'],
                    'Channel_Id': item['snippet']['channelId'],
                    'Video_Id': item['id'],
                    'Title': item['snippet']['title'],
                    'Tags': item['snippet'].get('tags'),
                    'Thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'Description': item['snippet'].get('description'),
                    'Published_Date': item['snippet']['publishedAt'],
                    'Duration': item['contentDetails']['duration'],
                    'Views': item['statistics'].get('viewCount'),
                    'Likes': item['statistics'].get('likeCount'),
                    'Comments': item['statistics'].get('commentCount'),
                    'Favorite_Count': item['statistics']['favoriteCount'],
                    'Definition': item['contentDetails']['definition'],
                    'Caption_Status': item['contentDetails']['caption']
                }
                video_data.append(data)
    except Exception as e:
        print("Error retrieving video information:", e)
    return video_data

def get_comment_info(youtube, video_ids):
    """Retrieve information about comments on videos."""
    comment_data = []
    try:
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
            )
            response = request.execute()

            for item in response['items']:
                data = {
                    'Comment_Id': item['snippet']['topLevelComment']['id'],
                    'Video_Id': item['snippet']['topLevelComment']['snippet']['videoId'],
                    'Comment_Text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'Comment_Author': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'Comment_Published': item['snippet']['topLevelComment']['snippet']['publishedAt']
                }
                comment_data.append(data)
    except Exception as e:
        print("Error retrieving comment information:", e)
    return comment_data

# Additional functions for interacting with the YouTube API can be added as needed
