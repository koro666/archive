#!/usr/bin/env python3.7
import os
import sys
import configuration

assert(configuration.static_prefix[0] == '/' and configuration.static_prefix[-1] == '/')
assert(configuration.editor_prefix[0] == '/' and configuration.editor_prefix[-1] == '/')
assert(configuration.browse_prefix[0] == '/' and configuration.browse_prefix[-1] == '/')
assert(configuration.download_prefix[0] == '/' and configuration.download_prefix[-1] == '/')
assert(configuration.download_internal_prefix[0] == '/' and configuration.download_internal_prefix[-1] == '/')
assert(configuration.thumbnail_prefix[0] == '/' and configuration.thumbnail_prefix[-1] == '/')
assert(configuration.thumbnail_cache_prefix[0] == '/' and configuration.thumbnail_cache_prefix[-1] == '/')

configuration.static_directory = os.path.normpath(os.path.abspath(configuration.static_directory))
configuration.database_directory = os.path.normpath(os.path.abspath(configuration.database_directory))
configuration.socket_directory = os.path.normpath(os.path.abspath(configuration.socket_directory))
configuration.thumbnail_cache_directory = os.path.normpath(os.path.abspath(configuration.thumbnail_cache_directory))

for key, path in configuration.exported_directories.items():
	configuration.exported_directories[key] = os.path.normpath(os.path.abspath(path))

configuration.hidden_directory_names = set(configuration.hidden_directory_names)
configuration.hidden_file_names = set(configuration.hidden_file_names)

configuration.image_extensions = set(configuration.image_extensions)
configuration.audio_extensions = set(configuration.audio_extensions)
configuration.video_extensions = set(configuration.video_extensions)

assert(sys.getfilesystemencoding() == 'utf-8')

socket_path = os.path.join(configuration.socket_directory, 'archive.socket')
