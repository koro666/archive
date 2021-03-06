#!/usr/bin/env python3.9

# Global
name = 'Archive'
debug = False

theme = 'united'
theme_inverse_navbar = False

browse_users = ['guest']
editor_users = ['editor']

download_delay = 3600
time_format = '%x %X'

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
database_directory = '/var/db/archive'
socket_directory = '/var/run/archive'
thumbnail_cache_directory = '/var/cache/archive/thumbnail'

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
image_extensions = ['.bmp', '.gif', '.jpe', '.jpg', '.jpeg', '.png']
audio_extensions = ['.aiff', '.flac', '.m4a', '.mp3', '.ogg', '.wav', '.wma']
video_extensions = ['.3gp', '.asf', '.avi', '.f4v', '.flv', '.m4v', '.mkv', '.mov', '.mpg', '.mpeg', '.mp4', '.mts', '.ts', '.webm', '.wmv']

thumbnail_nice = 20
thumbnail_concurrent = 4
thumbnail_filename_salt = b'changeme'
thumbnail_animated_framecount = 5
thumbnail_animated_framerate = 1.0
thumbnail_expire_days = 30
