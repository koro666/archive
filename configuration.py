#!/usr/bin/env python3.7

# Global
name = 'Archive'
debug = False

theme = 'united'
theme_inverse_navbar = False

browse_users = ['guest']
editor_users = ['editor']

download_delay = 3600

# Webserver
static_prefix = '/static/'
editor_prefix = '/editor/'
browse_prefix = '/browse/'
download_prefix = '/download/'
download_internal_prefix = '/download/internal/'
thumbnail_prefix = '/thumbnail/'
thumbnail_cache_prefix = '/thumbnail/cache/'

# Directories
static_directory = 'static'
database_directory = '/var/db/archive2'
socket_directory = '/var/run/archive2'
thumbnail_cache_directory = '/var/cache/archive2/thumbnail'

exported_directories = {
	'example': '/mnt/other'
}

hidden_directory_names = ['$RECYCLE.BIN']
hidden_file_names = ['desktop.ini', 'Thumbs.db']

# Random IDs
rid_seed = 12345
rid_python2_random = False

rid_symbols = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

rid_bits_state = 32
rid_bits_noise = 31

# Browsing
image_extensions = [".bmp", ".gif", ".jpe", ".jpg", ".jpeg", ".png"]
audio_extensions = [".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".wma"]
video_extensions = [".3gp", ".asf", ".avi", ".f4v", ".flv", ".m4v", ".mkv", ".mov", ".mpg", ".mpeg", ".mp4", ".mts", ".ts", ".webm", ".wmv"]

thumbnail_animated_framecount = 5
