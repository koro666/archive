#!/usr/bin/env python3.7
import time
import contextlib
import urllib.parse
import common
import configuration
import database
import randomid
import page

def get_ids_from_raw(environ, raw):
	prefix = page.uri_to_url(environ, configuration.download_prefix)
	result = []
	for line in raw.splitlines():
		line = line.strip()
		if line.startswith(prefix):
			line = line[len(prefix):]
		if not randomid.validate_id(line):
			continue
		result.append(line)

	return result

def get_parameters_from_post(environ):
	if not environ['REQUEST_METHOD'] == 'POST':
		return [], 0, None

	ids = set()
	delay = 0
	download = None
	try:
		length = int(environ['CONTENT_LENGTH'])
		body = environ['wsgi.input'].read(length)
		body = body.decode('utf-8', errors='replace')
		parameters = urllib.parse.parse_qs(body)

		if 'ids' in parameters:
			ids.update(parameters['ids'])
		if 'ids_raw' in parameters:
			ids.update(get_ids_from_raw(environ, parameters['ids_raw'][0]))
		if 'delay' in parameters:
			delay = int(parameters['delay'][0])
		if 'download' in parameters:
			download = int(parameters['download'][0])
	except:
		return

	ids = sorted(ids, key=str.lower)
	return ids, delay, download

def fetch_update_ids(ids, delay=0, download=None):
	if not ids:
		return []

	result = []
	with contextlib.closing(database.open_database()) as db:
		with db:
			for id in ids:
				if not randomid.validate_id(id):
					continue

				csr = db.cursor()
				csr.execute('SELECT expires, download, hits, mount, path FROM ids WHERE id = ?', (id,))
				entry = csr.fetchone()

				if not entry:
					result.append({
						'valid': False,
						'id': id
					})
					continue

				if delay:
					db.execute('UPDATE ids SET expires = MAX(0, expires + ?) WHERE id = ?', (delay, id))
				if download is not None:
					db.execute('UPDATE ids SET download = ? WHERE id = ?', (int(download), id))

				in_expires, in_download, in_hits, in_mount, in_path = entry
				del entry

				in_expires = max(0, in_expires + delay)
				if download is None:
					in_download = bool(in_download)
				else:
					in_download = download
				if isinstance(in_path, bytes):
					in_path = in_path.decode('utf-8', errors='surrogateescape')

				in_mount_path = (in_mount, in_path)
				del in_mount, in_path

				result.append({
						'valid': True,
						'id': id,
						'expires': in_expires,
						'download': in_download,
						'hits': in_hits,
						'mount_path': in_mount_path
					})

	return result

def handler(environ, writer, parameter):
	parameters = get_parameters_from_post(environ)
	if not parameters:
		return page.render_error_page(environ, writer, 400, 'Bad request.')

	ids, delay, download = parameters
	del parameters

	ids = fetch_update_ids(ids, delay, download)

	def contents(h):
		h.line('<h1>Link Editor</h1>')

		if ids and (delay or download):
			h.begin('<div class="alert alert-success alert-dismissable">')
			h.line('<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>')
			if delay and download:
				h.line('The expiration time and disposition for the specified links have been updated.')
			elif delay:
				h.line('The expiration time for the specified links has been updated.')
			elif download:
				h.line('The disposition for the specified links has been updated.')
			h.end('</div>')

		if configuration.debug:
			h.line('<div class="well">{0}</div>', repr(ids))

		h.begin('<form method="post">')

		now = int(time.time())
		if ids:
			h.begin('<table class="table table-striped table-bordered">')
			h.begin('<colgroup>')
			h.line('<col class="col-xs-5 col-sm-2 col-md-2 col-lg-2">')
			h.line('<col class="col-xs-0 col-sm-0 col-md-1 col-lg-1 hidden-xs hidden-sm">')
			h.line('<col class="col-xs-7 col-sm-4 col-md-3 col-lg-2">')
			h.line('<col class="col-xs-0 col-sm-6 col-md-6 col-lg-7 hidden-xs">')
			h.end('</colgroup>')
			h.begin('<thead>')
			h.begin('<tr>')
			h.line('<th>ID</th>')
			h.line('<th class="hidden-xs hidden-sm">Hits</th>')
			h.line('<th>Expires</th>')
			h.line('<th class="hidden-xs">Path</th>')
			h.end('</tr>')
			h.end('</thead>')
			h.begin('<tbody>')

			for id in ids:
				h.begin('<tr>')

				if id['valid']:
					h.begin('<td>')
					h.line('<input type="checkbox" name="ids" value="{0}" checked style="margin: 0px 2px 0px 0px">', id['id'])
					if now < id['expires']:
						h.line('<a href="{0}{1}">{1}</a>', configuration.download_prefix, id['id'])
					else:
						h.line('{0}', id['id'])
					h.end('</td>')
					h.line('<td class="hidden-xs hidden-sm">{0}</td>', str(id['hits']))
					h.line('<td>{0}</td>', time.strftime(configuration.time_format, time.localtime(id['expires'])))
					h.begin('<td class="hidden-xs" style="font-size: 90%">')
					if id['download']:
						h.line('<span class="glyphicon glyphicon-download-alt" style="margin: 0px 2px 0px 0px"></span>')
					h.line('{0}', '{0}/{1}'.format(*id['mount_path']).replace('/', '/\u200b'))
					h.end('</td>')
				else:
					h.line('<td><input type="checkbox" disabled style="margin: 0px 2px 0px 0px"> {0}</td>', id['id'])
					h.line('<td class="hidden-xs hidden-sm">&ndash;</td>')
					h.line('<td>&ndash;</td>')
					h.line('<td class="hidden-xs">&ndash;</td>')

				h.end('</tr>')

			h.end('</tbody>')
			h.end('</table>')
		else:
			h.begin('<div class="form-group">')
			h.line('<label for="ids_raw">Links:</label>')
			h.line('<textarea class="form-control" name="ids_raw" rows="10" placeholder="Paste some IDs or download links here, one per line."></textarea>')
			h.end('</div>')

		h.begin('<div class="form-group">')
		h.line('<label for="delay">Expiration:</label>')
		h.begin('<select class="form-control" name="delay">')
		h.line('<option value="{0}">Expired</option>', str(-(now + configuration.download_delay)))
		h.line('<option value="0" selected>Keep</option>')
		h.line('<option value="3600">+1 hour</option>')
		h.line('<option value="7200">+2 hours</option>')
		h.line('<option value="14400">+4 hours</option>')
		h.line('<option value="28800">+8 hours</option>')
		h.line('<option value="86400">+1 day</option>')
		h.line('<option value="172800">+2 days</option>')
		h.line('<option value="259200">+3 days</option>')
		h.line('<option value="345600">+4 days</option>')
		h.line('<option value="604800">+1 week</option>')
		h.line('<option value="1209600">+2 weeks</option>')
		h.line('<option value="2592000">+1 month</option>')
		h.end('</select>')
		h.end('</div>')

		h.begin('<div class="form-group">')
		h.line('<label for="download">Disposition:</label>')
		h.begin('<select class="form-control" name="download">')
		h.line('<option value="">Keep</option>')
		h.line('<option value="0">View</option>')
		h.line('<option value="1">Download</option>')
		h.end('</select>')
		h.end('</div>')

		h.line('<button type="submit" class="btn btn-default">Update</button>')

		h.end('</form>')

	return page.render_page(
		environ,
		writer,
		headers = [page.make_nocache_header()],
		title = 'Link Editor',
		content_cb = contents)
