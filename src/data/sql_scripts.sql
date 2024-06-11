-- Create channels table
CREATE TABLE IF NOT EXISTS channels (
    channel_name VARCHAR(100),
    channel_id VARCHAR(80) PRIMARY KEY,
    subscribers BIGINT,
    views BIGINT,
    total_videos INT,
    channel_description TEXT,
    playlist_id VARCHAR(80)
);

-- Create playlists table
CREATE TABLE IF NOT EXISTS playlists (
    playlist_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(100),
    channel_id VARCHAR(100),
    channel_name VARCHAR(100),
    published_at TIMESTAMP,
    video_count INT
);

-- Create videos table
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
);

-- Create comments table
CREATE TABLE IF NOT EXISTS comments (
    comment_id VARCHAR(100) PRIMARY KEY,
    video_id VARCHAR(50),
    comment_text TEXT,
    comment_author VARCHAR(150),
    comment_published TIMESTAMP
);

-- Optional: Create an index on video_id in the comments table for faster lookups
CREATE INDEX IF NOT EXISTS idx_video_id ON comments (video_id);

-- Optional: Create an index on channel_id in the videos table for faster lookups
CREATE INDEX IF NOT EXISTS idx_channel_id ON videos (channel_id);

-- Optional: Create an index on channel_name in the channels table for faster lookups
CREATE INDEX IF NOT EXISTS idx_channel_name ON channels (channel_name);
