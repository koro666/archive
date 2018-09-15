#!/usr/bin/env python3.7
import os
import io
import time
import json
import urllib.parse
import common
import configuration
import database
import randomid
import page

def parameter_to_mount_path(parameter):
	if not parameter:
		return None

	split = parameter.split('/', 1)
	if len(split) == 1:
		return (split[0], '')
	else:
		if len(split[1]) and split[1][-1] == '/':
			split[1] = split[1][:-1]
		return (split[0], split[1])

def mount_path_to_fspath(mount, path):
	root = configuration.exported_directories.get(mount)
	if not root:
		return None

	return os.path.join(root, path)

def is_hidden_name(name, is_editor, name_list):
	return not is_editor and (name[0] == '.' or name in name_list)

def is_hidden_directory_name(name, is_editor):
	return is_hidden_name(name, is_editor, configuration.hidden_directory_names)

def is_hidden_file_name(name, is_editor):
	return is_hidden_name(name, is_editor, configuration.hidden_file_names)

def make_static_icons(name):
	return {
		'1x': '{0}icons/{1}.png'.format(configuration.static_prefix, name),
		'2x': '{0}icons/{1}@2x.png'.format(configuration.static_prefix, name)
	}

def scan_root():
	drive_icons = make_static_icons('drive')

	result = []

	for name, fs_path in configuration.exported_directories.items():
		statbuf = None
		try:
			statbuf = os.statvfs(fs_path)
		except:
			pass

		if statbuf:
			size = (statbuf.f_blocks - statbuf.f_bfree) * statbuf.f_frsize
		else:
			size = None

		result.append({
			'id': None,
			'name': name,
			'fs_path': fs_path,
			'type': 'drive',
			'hidden': False,
			'size': size,
			'uri': '{0}{1}/'.format(configuration.browse_prefix, name),
			'icons': drive_icons,
			'lazy': False,
			'animate': False,
			'preview': False,
			'playable': False,
			'glyphicon': 'hdd'
		})

	return result

def scan_directory(mount_path, fs_path, user, is_editor):
	raw_result_directories = []
	raw_result_files = []
	with os.scandir(fs_path) as entries:
		for entry in entries:
			is_directory = False
			try:
				is_directory = entry.is_dir()
			except:
				pass

			if is_directory:
				if not is_hidden_directory_name(entry.name, is_editor):
					raw_result_directories.append(entry)
			else:
				if not is_hidden_file_name(entry.name, is_editor):
					raw_result_files.append(entry)

	sort_key = lambda x: x.name.lower()
	raw_result_directories.sort(key=sort_key)
	raw_result_files.sort(key=sort_key)

	directory_icons = make_static_icons('folder')
	file_icons = make_static_icons('file')

	result = []
	expires = int(time.time()) + configuration.download_delay

	with database.open_database() as db:
		with db:
			for raw_entry in raw_result_directories:
				result.append({
					'name': raw_entry.name,
					'fs_path': raw_entry.path,
					'type': 'directory',
					'hidden': is_hidden_directory_name(raw_entry.name, is_editor),
					'id': None,
					'size': None,
					'uri': '{0}{1}/{2}/{3}/'.format(
						configuration.browse_prefix,
						urllib.parse.quote(mount_path[0] , encoding='utf-8', errors='replace'),
						urllib.parse.quote(mount_path[1] , encoding='utf-8', errors='replace'),
						urllib.parse.quote(raw_entry.name, encoding='utf-8', errors='replace')),
					'icons': directory_icons,
					'lazy': False,
					'animate': False,
					'preview': False,
					'playable': False,
					'glyphicon': 'folder-open'
				})

			states = randomid.get_state_range_unlocked(db, len(raw_result_files))
			state_fetcher = iter(states)

			for raw_entry in raw_result_files:
				buf = None
				try:
					buf = raw_entry.stat()
				except:
					pass

				state = next(state_fetcher)
				if state >= randomid.invalid:
					raise Exception('Exhausted ID space.')

				unique_id = randomid.make_id(state)
				db.execute('INSERT INTO ids (id, expires, user, download, hits, mount, path) VALUES (?, ?, ?, ?, ?, ?, ?)', (unique_id, expires, user, 0, 0, mount_path[0], '{0}/{1}'.format(mount_path[0], raw_entry.name)))

				extension = os.path.splitext(raw_entry.name)[1].lower()
				is_image = extension in configuration.image_extensions
				is_audio = extension in configuration.audio_extensions
				is_video = extension in configuration.video_extensions
				is_thumbnailable = is_image or is_video

				if is_thumbnailable:
					base_thumbnail = configuration.thumbnail_prefix + unique_id
					icons = {
						'1x': base_thumbnail,
						'2x': '{0}@2x'.format(base_thumbnail),
						'3x': '{0}@3x'.format(base_thumbnail),
						'4x': '{0}@4x'.format(base_thumbnail)
					}
				else:
					icons = file_icons

				result.append({
					'name': raw_entry.name,
					'fs_path': raw_entry.path,
					'type': 'file',
					'hidden': is_hidden_file_name(raw_entry.name, is_editor),
					'id': unique_id,
					'size': buf.st_size if buf else None,
					'uri': configuration.download_prefix + unique_id,
					'icons': icons,
					'lazy': is_thumbnailable,
					'animate': is_video,
					'preview': is_image,
					'playable': is_audio or is_video,
					'glyphicon': 'picture' if is_image else 'music' if is_audio else 'facetime-video' if is_video else 'file'
				})

	return result

def subhandler_json(environ, writer, mount_path, fs_path, name, is_editor, directory, message):
	wrapper = io.TextIOWrapper(writer, encoding='utf-8', errors='replace')

	if not is_editor:
		for entry in directory:
			entry.pop('fs_path', None)

	json.dump(directory, wrapper, sort_keys=True)

	wrapper.detach()
	return (200, [('Content-Type', 'application/json'), page.make_nocache_header(), page.make_content_disposition_header(name, '.json')])

def subhandler_playlist(environ, writer, mount_path, fs_path, name, is_editor, directory, message):
	wrapper = io.TextIOWrapper(writer, encoding='utf-8', errors='replace')

	wrapper.write('\ufeff#EXTM3U\n')
	for entry in directory:
		if not entry['playable']:
			continue

		wrapper.write('#EXTINF:0,{0}\n'.format(entry['name']))
		wrapper.write('{0}\n'.format(page.uri_to_url(environ, entry['uri'])))

	wrapper.detach()
	return (200, [('Content-Type', 'application/vnd.apple.mpegurl'), page.make_nocache_header(), page.make_content_disposition_header(name, '.m3u8')])

def subhandler_text(environ, writer, mount_path, fs_path, name, is_editor, directory, message):
	wrapper = io.TextIOWrapper(writer, encoding='utf-8', errors='replace')

	for entry in directory:
		wrapper.write('{0}\n'.format(page.uri_to_url(environ, entry['uri'])))

	wrapper.detach()
	return (200, [('Content-Type', 'text/plain'), page.make_nocache_header(), page.make_content_disposition_header(name, '.txt')])

def subhandler_html(environ, writer, mount_path, fs_path, name, is_editor, directory, message):
	# TODO:
	return page.render_error_page(environ, writer, 200, 'Unimplementer subhandler: html.')

def subhandler_error(environ, writer, mount_path, fs_path, name, is_editor, directory, message):
	return page.render_error_page(environ, writer, 400, 'Bad format.')

subhandlers = {
	'': subhandler_html,
	'json': subhandler_json,
	'm3u': subhandler_playlist,
	'txt': subhandler_text,
	'html': subhandler_html
}

def handler(environ, writer, parameter):
	mount_path = parameter_to_mount_path(parameter)

	if mount_path is None:
		fs_path = None
		name = 'Root'
	else:
		fs_path = mount_path_to_fspath(*mount_path)
		if fs_path is None:
			return page.render_error_page(environ, writer, 404, 'Bad path.')
		if mount_path[1]:
			name = mount_path[1].split('/')[-1]
		else:
			name = mount_path[0]

	is_editor = environ.get('REMOTE_USER') in configuration.editor_users

	message = None
	if fs_path:
		directory = []
		try:
			directory = scan_directory(mount_path, fs_path, environ.get('REMOTE_USER', ''), is_editor)
		except Exception as e:
			try:
				message = '{0}.'.format(e.strerror)
			except AttributeError:
				message = 'An error occured.'
	else:
		directory = scan_root()

	if not message and not directory:
		message = 'There is nothing here.'

	subhandler = subhandlers.get(environ['QUERY_STRING'], subhandler_error)
	return subhandler(environ, writer, mount_path, fs_path, name, is_editor, directory, message)
