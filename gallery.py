#!/usr/bin/env python3.7
import os
import time
import json
import shlex
import contextlib
import urllib.parse
import http.cookies
import traceback
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

def get_sort_info(cookies):
	try:
		sort_key = cookies['sortkey'].value
	except:
		sort_key = None

	if sort_key != 'name' and sort_key != 'mtime' and sort_key != 'used' and sort_key != 'size':
		sort_key = 'name'

	try:
		sort_mode = cookies['sortmode'].value == 'desc'
	except:
		sort_mode = False

	try:
		sort_mixed = bool(int(cookies['mixed'].value))
	except:
		sort_mixed = False

	return (sort_key, sort_mode, sort_mixed)

def get_uri_components_from_mount_path(mount_path):
	components = configuration.browse_prefix[:-1].split('/')

	if mount_path:
		components.append(mount_path[0])
		if mount_path[1]:
			components.extend(mount_path[1].split('/'))

	return components

def make_uri_from_mount_path(mount_path, extra=None, is_directory=False):
	components = get_uri_components_from_mount_path(mount_path)

	if extra:
		components.append(extra)
	if is_directory:
		components.append('')

	return '/'.join(components)

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
			used = (statbuf.f_blocks - statbuf.f_bfree) * statbuf.f_frsize
			size = statbuf.f_blocks * statbuf.f_frsize
		else:
			used = None
			size = None

		result.append({
			'id': None,
			'name': name,
			'fs_path': fs_path,
			'type': 'drive',
			'hidden': False,
			'mtime': None,
			'used': used,
			'size': size,
			'uri': urllib.parse.quote(make_uri_from_mount_path((name, ''), None, True), encoding='utf-8', errors='surrogateescape'),
			'icons': drive_icons,
			'lazy': False,
			'animate': False,
			'preview': False,
			'playable': False,
			'glyphicon': 'hdd'
		})

	return result

def scan_directory(mount_path, fs_path, sort_info, user, is_editor):
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

	directory_icons = make_static_icons('folder')
	file_icons = make_static_icons('file')

	result_directories = []
	result_files = []
	expires = int(time.time()) + configuration.download_delay

	with contextlib.closing(database.open_database()) as db:
		with db:
			for raw_entry in raw_result_directories:
				buf = None
				try:
					buf = raw_entry.stat()
				except:
					pass

				result_directories.append({
					'name': raw_entry.name,
					'fs_path': raw_entry.path,
					'type': 'directory',
					'hidden': is_hidden_directory_name(raw_entry.name, False),
					'id': None,
					'mtime': int(buf.st_mtime) if buf else None,
					'used': None,
					'size': None,
					'uri': urllib.parse.quote(make_uri_from_mount_path(mount_path, raw_entry.name, True), encoding='utf-8', errors='surrogateescape'),
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
				path_value = ('{0}/{1}'.format(mount_path[1], raw_entry.name) if mount_path[1] else raw_entry.name)
				try:
					path_value.encode('utf-8')
				except UnicodeEncodeError:
					path_value = path_value.encode('utf-8', errors='surrogateescape')
				db.execute('INSERT INTO ids (id, expires, user, download, hits, mount, path) VALUES (?, ?, ?, ?, ?, ?, ?)', (unique_id, expires, user, 0, 0, mount_path[0], path_value))

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

				result_files.append({
					'name': raw_entry.name,
					'fs_path': raw_entry.path,
					'type': 'file',
					'hidden': is_hidden_file_name(raw_entry.name, False),
					'id': unique_id,
					'mtime': int(buf.st_mtime) if buf else None,
					'used': buf.st_blocks * 512 if buf else None,
					'size': buf.st_size if buf else None,
					'uri': configuration.download_prefix + unique_id,
					'icons': icons,
					'lazy': is_thumbnailable,
					'animate': is_video,
					'preview': is_image,
					'playable': is_audio or is_video,
					'glyphicon': 'picture' if is_image else 'music' if is_audio else 'facetime-video' if is_video else 'file'
				})

	if sort_info[0] == 'name':
		sort_key = lambda x: x['name'].lower()
	elif sort_info[0] == 'mtime' or sort_info[0] == 'used' or sort_info[0] == 'size':
		sort_key = lambda x: (x[sort_info[0]] or 0, x['name'].lower())
	else:
		sort_key = None

	if sort_info[2]:
		result = result_directories + result_files
		result.sort(key=sort_key, reverse=sort_info[1])
	else:
		result_directories.sort(key=sort_key, reverse=sort_info[1])
		result_files.sort(key=sort_key, reverse=sort_info[1])
		result = result_directories + result_files

	return result

def subhandler_json(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	if not is_editor:
		for entry in directory:
			entry.pop('fs_path', None)

	json.dump(directory, writer, sort_keys=True)

	return (200, [('Content-Type', 'application/json'), page.make_nocache_header(), page.make_content_disposition_header(name, '.json')])

def subhandler_playlist(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	writer.write('#EXTM3U\n')
	for entry in directory:
		if not entry['playable']:
			continue

		writer.write('#EXTINF:0,{0}\n'.format(entry['name']))
		writer.write('{0}\n'.format(page.uri_to_url(environ, entry['uri'])))

	return (200, [('Content-Type', 'application/vnd.apple.mpegurl'), page.make_nocache_header(), page.make_content_disposition_header(name, '.m3u8')])

def subhandler_text(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	for entry in directory:
		writer.write('{0}\n'.format(page.uri_to_url(environ, entry['uri'])))

	return (200, [('Content-Type', 'text/plain'), page.make_nocache_header(), page.make_content_disposition_header(name, '.txt')])

def subhandler_wget(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	writer.write('#!/bin/sh\n')
	for entry in directory:
		if entry['type'] != 'file':
			continue

		writer.write('\n')
		writer.write('# {0}\n'.format(entry['name']))
		writer.write('wget -c --content-disposition {0}\n'.format(shlex.quote(page.uri_to_url(environ, entry['uri']))))

	return (200, [('Content-Type', 'application/x-sh'), page.make_nocache_header(), page.make_content_disposition_header(name, '.sh')])

def subhandler_bbcode(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	for entry in directory:
		if entry['type'] != 'file':
			continue

		writer.write('[url={0}]{1}[/url]\n'.format(page.uri_to_url(environ, entry['uri']), entry['name']))

	return (200, [('Content-Type', 'text/plain'), page.make_nocache_header(), page.make_content_disposition_header(name, '.txt')])

def subhandler_bbcode_table(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	writer.write('[table]\n')
	writer.write('[tr][td][b]Name[/b][/td][td][b]Size[/b][/td][td][b]Modified[/b][/td][/tr]\n')

	for entry in directory:
		if entry['type'] != 'file':
			continue

		writer.write('[tr]\n')
		writer.write('[td][url={0}]{1}[/url][/td]\n'.format(page.uri_to_url(environ, entry['uri']), entry['name']))
		writer.write('[td]{0}[/td]\n'.format(page.pretty_size(entry['size'])))
		writer.write('[td]{0}[/td]\n'.format(page.pretty_time(entry['mtime'])))
		writer.write('[/tr]\n')

	writer.write('[/table]\n')

	return (200, [('Content-Type', 'text/plain'), page.make_nocache_header(), page.make_content_disposition_header(name, '.txt')])

def subhandler_html(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	try:
		list_mode = bool(int(cookies['listmode'].value))
	except:
		list_mode = False

	sort_info = get_sort_info(cookies)

	theme_is_dark = page.themes[configuration.theme].dark

	def links(h):
		if not list_mode:
			h.line('<link href="https://cdnjs.cloudflare.com/ajax/libs/jquery.swipebox/1.4.4/css/swipebox.min.css" rel="stylesheet" integrity="sha256-5KRlt3ls3xVyu0Fv7M6hvDH0wCDqHraymjiBtOAhZZU=" crossorigin="anonymous">')
		h.line('<link href="{0}archive.css" rel="stylesheet">', configuration.static_prefix)
		h.begin('<style>')
		if not list_mode:
			if theme_is_dark:
				h.line('div.archive_thumbnail {{ background-image: url("{0}background-dark.svg"); }}', configuration.static_prefix)
				h.line('div.archive_thumbnail:hover {{ filter: brightness(125%); }}')
				h.line('div.archive_name {{ color: white; text-shadow: 0px 0px 4px black; }}')
			else:
				h.line('div.archive_thumbnail {{ background-image: url("{0}background-light.svg"); }}', configuration.static_prefix)
				h.line('div.archive_thumbnail:hover {{ filter: brightness(90%); }}')
				h.line('div.archive_name {{ color: black; text-shadow: 0px 0px 4px white; }}')
		h.end('</style>')

	def navbar(h):
		if any(map(lambda x: x['playable'], directory)):
			h.line('<li><a href="?m3u"><span class="glyphicon glyphicon-play"></span> Play</a></li>')

		if is_editor:
			h.begin('<li class="dropdown">')
			h.begin('<a class="dropdown-toggle" id="show_editor" data-toggle="dropdown" href="#">')
			h.line('<span class="glyphicon glyphicon-pencil"></span>')
			h.line('Edit')
			h.line('<span class="caret"></span>')
			h.end('</a>')
			h.begin('<ul class="dropdown-menu">')
			h.line('<li><a href="#" id="select_all"><span class="glyphicon glyphicon-asterisk"></span> Select All</a></li>')
			h.line('<li><a href="#" id="select_none"><span class="glyphicon glyphicon-remove"></span> Select None</a></li>')
			h.line('<li role="separator" class="divider"></li>')
			h.line('<li><a href="#" id="link_submit_x" data-delay="0"><span class="glyphicon glyphicon-edit"></span> Open Editor</a></li>')
			h.line('<li role="separator" class="divider"></li>')
			h.line('<li><a href="#" id="link_submit_h" data-delay="3600"><span class="glyphicon glyphicon-time"></span> Extend <span class="text-muted">(1 hour)</span></a></li>')
			h.line('<li><a href="#" id="link_submit_d" data-delay="86400"><span class="glyphicon glyphicon-time"></span> Extend <span class="text-muted">(1 day)</span></a></li>')
			h.line('<li><a href="#" id="link_submit_w" data-delay="604800"><span class="glyphicon glyphicon-time"></span> Extend <span class="text-muted">(1 week)</span></a></li>')
			h.end('</ul>')
			h.end('</li>')

		h.begin('<li class="dropdown">')
		h.begin('<a class="dropdown-toggle" data-toggle="dropdown" href="#">')
		h.line('<span class="glyphicon glyphicon-eye-open"></span>')
		h.line('View')
		h.line('<span class="caret"></span>')
		h.end('</a>')
		h.begin('<ul class="dropdown-menu">')
		h.line('<li><a href="#" id="listmode_enable"><span class="glyphicon glyphicon-th-list"></span> List</a></li>')
		h.line('<li><a href="#" id="listmode_disable"><span class="glyphicon glyphicon-th-large"></span> Grid</a></li>')
		h.end('</ul>')
		h.end('</li>')

		if mount_path:
			h.begin('<li class="dropdown">')
			h.begin('<a class="dropdown-toggle" data-toggle="dropdown" href="#">')
			h.line('<span class="glyphicon glyphicon-sort"></span>')
			h.line('Sort')
			h.line('<span class="caret"></span>')
			h.end('</a>')
			h.begin('<ul class="dropdown-menu">')
			h.line('<li><a href="#" id="sortkey_name"><span class="glyphicon glyphicon-sort-by-alphabet"></span> Name</a></li>')
			h.line('<li><a href="#" id="sortkey_size"><span class="glyphicon glyphicon-sort-by-order"></span> Size</a></li>')
			h.line('<li><a href="#" id="sortkey_mtime"><span class="glyphicon glyphicon-time"></span> Modified</a></li>')
			h.line('<li role="separator" class="divider"></li>')
			h.line('<li><a href="#" id="sortmode_asc"><span class="glyphicon glyphicon-sort-by-attributes"></span> Ascending</a></li>')
			h.line('<li><a href="#" id="sortmode_desc"><span class="glyphicon glyphicon-sort-by-attributes-alt"></span> Descending</a></li>')

			h.end('</ul>')
			h.end('</li>')

	def breadcrumb(h):
		h.begin('<ol class="breadcrumb">')

		components = get_uri_components_from_mount_path(mount_path)
		for i in range(1, len(components) - 1):
			h.line('<li><a href="{0}">{1}</a></li>', urllib.parse.quote('/'.join(components[:i + 1] + ['']), encoding='utf-8', errors='replace'), components[i])
		h.line('<li class="active">{0}</li>', components[-1])

		h.end('</ol>')

	def contents_images(h):
		h.begin('<div class="archive_list"><!--')

		for entry in directory:
			h.begin('--><div class="archive_thumbnail">')

			h.begin(*page.make_tag('a', [
				('href', entry['uri']),
				('class', 'archive_swipebox' if entry['preview'] else ''),
				('title', entry['name'])]))

			img_classes = []
			if entry['lazy']:
				img_classes.append('archive_lazy')
			if entry['animate']:
				img_classes.append('archive_video')
			if entry['hidden']:
				img_classes.append('archive_hidden')

			img_attributes = []
			icon_1x = entry['icons']['1x']
			icons_except_1x = sorted(filter(lambda x: x[0] != '1x', entry['icons'].items()))

			if entry['animate']:
				icon_1x_animated = icon_1x + '?animated'
				icons_except_1x_animated = map(lambda x: (x[0], x[1] + '?animated'), icons_except_1x)
			else:
				icon_1x_animated = ''
				icons_except_1x_animated = []

			src = icon_1x
			src_animated = icon_1x_animated
			srcset = ', '.join(map(lambda x: '{0} {1}'.format(x[1], x[0]), icons_except_1x))
			srcset_animated = ', '.join(map(lambda x: '{0} {1}'.format(x[1], x[0]), icons_except_1x_animated))

			if entry['lazy']:
				# Loading comes from: http://jxnblk.com/loading/
				img_attributes.append(('src', configuration.static_prefix + ('loading-white.svg' if theme_is_dark else 'loading-gray.svg')))
			else:
				img_attributes.append(('src', src))
				img_attributes.append(('srcset', srcset))

			if entry['lazy'] or entry['animate']:
				img_attributes.append(('data-src', src))
				img_attributes.append(('data-srcset', srcset))
				img_attributes.append(('data-src-animated', src_animated))
				img_attributes.append(('data-srcset-animated', srcset_animated))

			img_attributes.append(('class', ' '.join(img_classes)))
			img_attributes.append(('alt', entry['name']))

			h.line(*page.make_tag('img', img_attributes))

			h.end('</a>')

			if is_editor and entry['id']:
				h.line('<input type="checkbox" name="ids" value="{0}" style="display: none">', entry['id'])

			h.line('<div class="archive_name">{0}</div>', entry['name'])
			h.end('</div><!--')

		h.end('--></div>')

	def contents_list(h):
		h.begin('<table class="table table-striped table-bordered">')
		h.begin('<colgroup>')
		h.line('<col class="col-xs-12 col-sm-10 col-md-8">')
		h.line('<col class="col-xs-0 col-sm-2 hidden-xs">')
		h.line('<col class="col-xs-0 col-sm-0 col-md-0 col-lg-2 hidden-xs hidden-sm hidden-md">')
		h.end('</colgroup>')
		h.begin('<thead>')
		h.begin('<tr class="hidden-xs">')
		h.line('<th>Name</th>')
		h.line('<th class="hidden-xs">{0}</th>', 'Size' if mount_path else 'Used')
		h.line('<th class="hidden-xs hidden-sm hidden-md">{0}</th>', 'Modified' if mount_path else 'Size')
		h.end('</tr>')
		h.end('</thead>')
		h.begin('<tbody>')

		for entry in directory:
			h.begin('<tr>')
			h.begin('<td>')
			if is_editor:
				if entry['id']:
					h.line('<input type="checkbox" name="ids" value="{0}" style="display: none; margin: 0px">', entry['id'])
				else:
					h.line('<input type="checkbox" name="ids" disabled style="display: none; margin: 0px">')
			h.line('<span class="killme glyphicon{0} glyphicon-{1}"></span>', ' archive_hidden' if entry['hidden'] else '', entry['glyphicon'])
			h.line('&nbsp;')
			h.line('<a href="{0}">{1}</a>', entry['uri'], entry['name'])
			h.end('</td>')

			info0 = None
			info1 = None
			if mount_path:
				if entry['size'] is not None:
					info0 = page.pretty_size(entry['size'])
				if entry['mtime'] is not None:
					info1 = page.pretty_time(entry['mtime'])
			else:
				if entry['used'] is not None:
					info0 = page.pretty_size(entry['used'])
				if entry['size'] is not None:
					info1 = page.pretty_size(entry['size'])

			if info0 is None:
				h.line('<td class="hidden-xs">&ndash;</td>')
			else:
				h.line('<td class="hidden-xs">{0}</td>', info0)

			if info1 is None:
				h.line('<td class="hidden-xs hidden-sm hidden-md">&ndash;</td>')
			else:
				h.line('<td class="hidden-xs hidden-sm hidden-md">{0}</td>', info1)

			h.end('</tr>')

		h.end('</tbody>')
		h.end('</table>')

	def contents_entries(h):
		if is_editor:
			h.begin('<form id="editorform" action="{0}" method="post">', configuration.editor_prefix)
		if list_mode:
			contents_list(h)
		else:
			contents_images(h)
		if is_editor:
			h.line('<input type="hidden" name="delay" value="0">')
			h.end('</form>')

	def contents_editor(h):
		h.begin('<div class="well">')

		with contextlib.closing(database.open_database()) as db:
			next_state = randomid.peek_state(db)

		invalid_state = randomid.invalid

		percent = float(next_state) / float(invalid_state) * 100.0
		if percent > 100.0:
			percent = 100.0
		percent_string = '%.2f' % percent

		if percent > 90.0:
			progress_type = 'danger'
		elif percent > 75.0:
			progress_type = 'warning'
		else:
			progress_type = 'success'

		h.begin('<div class="row">')
		h.line('<div class="col-xs-8 col-sm-8 "><strong>RID State Usage</strong></div>')
		h.line('<div class="col-xs-4 hidden-sm hidden-md hidden-lg text-right">{0} %</div>', percent_string)
		h.line('<div class="hidden-xs col-sm-4 text-right">{0} / {1} <span class="text-muted">({2} %)</span></div>', str(next_state), str(invalid_state), percent_string)
		h.end('</div>')
		h.begin('<div class="progress">')
		h.line('<div class="progress-bar progress-bar-{0}" role="progressbar" aria-valuenow="{1}" aria-valuemin="0" aria-valuemax="100" style="width: {1}%"></div>', progress_type, percent_string)
		h.end('</div>')

		h.end("</div>")

	def contents_message(h):
		h.line('<p class="text-muted text-center">{0}</p>', message)

	def contents_select(h):
		breadcrumb(h)
		if message:
			contents_message(h)
		else:
			contents_entries(h)
		if not mount_path and is_editor:
			contents_editor(h)

	def scripts(h):
		if not list_mode:
			h.line('<script src="https://cdn.jsdelivr.net/npm/lazyload@2.0.0-beta.2/lazyload.min.js" integrity="sha256-ZO+TjdBAooji40k/g0tbo3uIBP0LpMGCnpgWd/2uyU8=" crossorigin="anonymous"></script>')
			h.line('<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.hoverintent/1.9.0/jquery.hoverIntent.min.js" integrity="sha256-IKN/+QULYYgqeTGhzPJWZpa1fYBur4u4BaJbdAyVRu8=" crossorigin="anonymous"></script>')
			h.line('<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.swipebox/1.4.4/js/jquery.swipebox.min.js" integrity="sha256-Yc+GwTnlWzpuQ6grDKOT67UA8d1M4Fx33JkNqX3Ke50=" crossorigin="anonymous"></script>')
		h.begin('<script>')
		h.line('const cookie_path = \'{0}\';', configuration.browse_prefix)
		h.line('const is_editor = {0};', str(is_editor).lower())
		h.line('const list_mode = {0};', str(list_mode).lower())
		h.line('const sort_key = \'{0}\';', sort_info[0]);
		h.line('const sort_mode = \'{0}\';', 'desc' if sort_info[1] else 'asc');
		#h.line('const mixed = {0};', str(sort_info[1]).lower())
		h.end('</script>')
		h.line('<script src="{0}archive.js"></script>', configuration.static_prefix)

	return page.render_page(
		environ,
		writer,
		headers = [page.make_nocache_header(), page.make_content_disposition_header(name, '.html')],
		title = 'Index of {0}'.format(make_uri_from_mount_path(mount_path)),
		link_cb = links,
		navbar_cb = navbar,
		content_cb = contents_select,
		script_cb = scripts)

def subhandler_error(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message):
	return page.render_error_page(environ, writer, 400, 'Bad format.')

subhandlers = {
	'': subhandler_html,
	'json': subhandler_json,
	'm3u': subhandler_playlist,
	'txt': subhandler_text,
	'wget': subhandler_wget,
	'bbcode': subhandler_bbcode,
	'bbtable': subhandler_bbcode_table,
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

	user = environ.get('REMOTE_USER')
	is_editor = user in configuration.editor_users

	try:
		cookies = http.cookies.SimpleCookie(environ['HTTP_COOKIE'])
	except:
		cookies = http.cookies.SimpleCookie()

	message = None
	if fs_path:
		sort_info = get_sort_info(cookies)
		try:
			directory = scan_directory(mount_path, fs_path, sort_info, user, is_editor)
		except OSError as e:
			if configuration.debug:
				traceback.print_exc()
			directory = []
			message = '{0}.'.format(e.strerror)
	else:
		directory = scan_root()

	if not message and not directory:
		message = 'There is nothing here.'

	subhandler = subhandlers.get(environ['QUERY_STRING'], subhandler_error)
	return subhandler(environ, cookies, writer, mount_path, fs_path, name, is_editor, directory, message)
