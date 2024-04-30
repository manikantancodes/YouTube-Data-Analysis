-- Create table for channels
CREATE TABLE IF NOT EXISTS CHANNEL (
    Channel_Name VARCHAR(100),
    Channel_Id VARCHAR(80) PRIMARY KEY,
    Subscribers BIGINT,
    Views BIGINT,
    Total_Videos INT,
    Channel_Description TEXT,
    Playlist_Id VARCHAR(80)
);

-- Create table for playlists
CREATE TABLE IF NOT EXISTS PLAYLIST (
    Playlist_Id VARCHAR(100) PRIMARY KEY,
    Title VARCHAR(100),
    Channel_Id VARCHAR(100),
    Channel_Name VARCHAR(100),
    PublishedAt TIMESTAMP,
    Video_Count INT
);

-- Create table for videos
CREATE TABLE IF NOT EXISTS VIDEOS (
    Channel_Name VARCHAR(100),
    Channel_Id VARCHAR(100),
    Video_Id VARCHAR(30) PRIMARY KEY,
    Title VARCHAR(150),
    Tags TEXT,
    Thumbnail VARCHAR(200),
    Description TEXT,
    Published_Date TIMESTAMP,
    Duration INTERVAL,
    Views BIGINT,
    Likes BIGINT,
    Comments INT,
    Favorite_Count INT,
    Definition VARCHAR(10),
    Caption_Status VARCHAR(50)
);

-- Create table for comments
CREATE TABLE IF NOT EXISTS COMMENT (
    Comment_Id VARCHAR(100) PRIMARY KEY,
    Video_Id VARCHAR(50),
    Comment_Text TEXT,
    Comment_Author VARCHAR(150),
    Comment_Published TIMESTAMP
);
