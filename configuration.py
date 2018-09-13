#!/usr/bin/env python3.7

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

# Random IDs
rid_seed = 12345

rid_symbols = []
rid_symbols.extend(range(0x30, 0x3A))
rid_symbols.extend(range(0x41, 0x5B))
rid_symbols.extend(range(0x61, 0x7B))

rid_bits_state = 32
rid_bits_noise = 31

# Other
browse_users = ['guest']
editor_users = ['editor']

theme = 'united'
theme_alt_navbar = False

download_delay = 3600

image_extensions = [".bmp", ".gif", ".jpe", ".jpg", ".jpeg", ".png"]
audio_extensions = [".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".wma"]
video_extensions = [".3gp", ".asf", ".avi", ".f4v", ".flv", ".m4v", ".mkv", ".mov", ".mpg", ".mpeg", ".mp4", ".mts", ".ts", ".webm", ".wmv"]

thumbnail_size = 128
thumbnail_framecount = 5
