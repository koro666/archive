#!/usr/bin/env python3.8
import os
import sys
import time
import contextlib
import fcntl
import json
import base64
import hashlib
import threading
import shutil
import tempfile
import subprocess
import traceback
import common
import configuration
import database
import randomid
import page

nice_binary = '/usr/bin/nice'

if sys.platform.startswith('freebsd') or sys.platform.startswith('openbsd'):
	ffprobe_binary = '/usr/local/bin/ffprobe'
	ffmpeg_binary = '/usr/local/bin/ffmpeg'
else:
	ffprobe_binary = '/usr/bin/ffprobe'
	ffmpeg_binary = '/usr/bin/ffmpeg'

assert(isinstance(configuration.thumbnail_nice, int))
assert(isinstance(configuration.thumbnail_concurrent, int))
assert(isinstance(configuration.thumbnail_filename_salt, bytes))
assert(isinstance(configuration.thumbnail_animated_framecount, int))
assert(isinstance(configuration.thumbnail_animated_framerate, int) or isinstance(configuration.thumbnail_animated_framerate, float))

# If this is changed, hardcoded sizes in static/gallery.css and static/*.svg must also be updated
thumbnail_size = 128

thumbnail_filter = 'format=rgb24,scale=iw*min({0}/iw\,{0}/ih):ih*min({0}/iw\,{0}/ih)'
thumbnail_semaphore = threading.Semaphore(configuration.thumbnail_concurrent)

null_fd = os.open(os.devnull, os.O_RDWR)

def id_scale_from_parameter_unvalidated(parameter):
	split = parameter.split('@', 1)
	if len(split) == 1:
		return (split[0], None)
	else:
		return tuple(split)

def make_thumbnail_error(scale, reason):
	headers = [('Location', '{0}icons/error{1}.png'.format(configuration.static_prefix, '' if scale == 1 else '@{0}x'.format(scale)))]
	if configuration.debug and reason:
		headers.append(('X-Thumbnail-Error', reason))
	return (303, headers)

def make_thumbnail_filename(fs_path, scale, animated):
	md5 = hashlib.md5()

	md5.update(configuration.thumbnail_filename_salt)
	md5.update(b'\0')
	md5.update('@{0}x'.format(scale).encode('utf-8'))
	md5.update(b'\0')
	md5.update(b'animated' if animated else b'static')
	md5.update(b'\0')
	md5.update(fs_path.encode('utf-8', errors='surrogateescape'))

	hash = md5.digest()
	b64hash = base64.urlsafe_b64encode(hash).rstrip(b'=').decode('utf-8')
	return '{0}.{1}'.format(b64hash, 'gif' if animated else 'jpg')

def make_nice_argv():
	return [nice_binary, '-n', str(configuration.thumbnail_nice)] if configuration.thumbnail_nice else []

def probe_duration(path):
	argv = make_nice_argv()
	argv.extend([ffprobe_binary, '-v', 'quiet', '-print_format', 'json', '-show_format', '-i', path])

	with tempfile.TemporaryFile(suffix='.json') as fp:
		subprocess.check_call(argv, stdin=null_fd, stdout=fp, stderr=null_fd)

		fp.seek(0)
		json_data = json.load(fp)

	return float(json_data['format']['duration'])

def convert_media_to_static(in_path, out_path, scale, duration):
	argv = make_nice_argv()
	argv.append(ffmpeg_binary)
	if duration:
		argv.extend(['-ss', str(duration / 3.0)])
	argv.extend(['-i', in_path, '-y', '-vf', thumbnail_filter.format(thumbnail_size * scale),  '-vframes', '1', '-vcodec', 'mjpeg', '-an', out_path])

	subprocess.check_call(argv, stdin=null_fd, stdout=null_fd, stderr=null_fd)

def convert_media_to_animated(in_path, out_path, scale, duration):
	if not duration:
		return

	temporary_directory = None
	try:
		temporary_directory = tempfile.mkdtemp()

		frame_processes = []
		for frame in range(configuration.thumbnail_animated_framecount):
			frame_offset = (float(frame) + 0.5) * (duration / float(configuration.thumbnail_animated_framecount))
			frame_path = os.path.join(temporary_directory, 'frame{0}.png'.format(frame))

			argv = make_nice_argv()
			argv.extend([ffmpeg_binary, '-ss', str(frame_offset), '-i', in_path, '-y', '-vf', thumbnail_filter.format(thumbnail_size * scale), '-vframes', '1', '-vcodec', 'png', '-an', frame_path])

			frame_processes.append(subprocess.Popen(argv, stdin=null_fd, stdout=null_fd, stderr=null_fd))

		failed = False
		for frame_process in frame_processes:
			frame_process.wait()
			if frame_process.returncode:
				failed = True

		del frame_processes
		if failed:
			return

		palette_file = os.path.join(temporary_directory, 'palette.png')

		argv_prefix = make_nice_argv()
		argv_prefix.extend([ffmpeg_binary, '-f', 'image2', '-framerate', str(configuration.thumbnail_animated_framerate), '-i', os.path.join(temporary_directory, 'frame%d.png')])

		argv = argv_prefix + ['-y', '-vf', 'palettegen', palette_file]
		subprocess.check_call(argv, stdin=null_fd, stdout=null_fd, stderr=null_fd)

		argv = argv_prefix + ['-i', palette_file, '-y', '-lavfi', 'paletteuse', out_path]
		subprocess.check_call(argv, stdin=null_fd, stdout=null_fd, stderr=null_fd)
	finally:
		if temporary_directory:
			shutil.rmtree(temporary_directory)

def create_thumbnail(in_path, out_path, scale, is_video, animated):
	duration = probe_duration(in_path) if is_video or animated else None
	if animated:
		convert_media_to_animated(in_path, out_path, scale, duration)
	else:
		convert_media_to_static(in_path, out_path, scale, duration)

def get_or_create_thumbnail(fs_path, scale, animated):
	is_video = os.path.splitext(fs_path)[1].lower() in configuration.video_extensions
	filename = make_thumbnail_filename(fs_path, scale, animated)

	if animated and not is_video:
		return

	out_path = os.path.join(configuration.thumbnail_cache_directory, filename)
	existed = os.path.isfile(out_path)

	fd = None
	fd_locked = False
	try:
		fd = os.open(out_path, os.O_RDONLY|os.O_CREAT, 0o0666)
		fcntl.flock(fd, fcntl.LOCK_EX)
		fd_locked = True

		if not existed and not os.path.getsize(out_path):
			thumbnail_semaphore.acquire()
			try:
				create_thumbnail(fs_path, out_path, scale, is_video, animated)
			finally:
				thumbnail_semaphore.release()

		if os.path.getsize(out_path):
			return filename
	finally:
		if fd_locked:
			fcntl.flock(fd, fcntl.LOCK_UN)
		if not fd is None:
			os.close(fd)

def handler(environ, writer, parameter):
	id, scale = id_scale_from_parameter_unvalidated(parameter)

	if not randomid.validate_id(id):
		return make_thumbnail_error(1, 'invalid-id')

	if scale is None:
		scale = 1
	elif scale == '2x':
		scale = 2
	elif scale == '3x':
		scale = 3
	elif scale == '4x':
		scale = 4
	else:
		return make_thumbnail_error(1, 'invalid-scale')

	with contextlib.closing(database.open_database()) as db:
		csr = db.cursor()
		csr.execute('SELECT mount, path FROM ids WHERE id = ? AND expires > ?', (id, int(time.time())))
		result = csr.fetchone()

	if not result:
		return make_thumbnail_error(scale, 'expired-id')

	mount, path = result
	if isinstance(path, bytes):
		path = path.decode('utf-8', errors='surrogateescape')
	del result

	root = configuration.exported_directories.get(mount)
	if not root:
		return make_thumbnail_error(scale, 'invalid-root')

	fs_path = os.path.join(root, path)
	del root, mount, path

	if not os.path.isfile(fs_path):
		return make_thumbnail_error(scale, 'nonexistant-path')

	animated = page.match_in_qs(environ, {'': False, 'animated': True}, False)

	try:
		filename = get_or_create_thumbnail(fs_path, scale, animated)
	except:
		if configuration.debug:
			traceback.print_exc()
		filename = None

	if not filename:
		return make_thumbnail_error(scale, 'thumbnail-creation-failed')

	return (303, [('Location', configuration.thumbnail_cache_prefix + filename)])
