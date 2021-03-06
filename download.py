#!/usr/bin/env python3.9
import time
import contextlib
import urllib.parse
import common
import configuration
import database
import randomid
import page

def handler(environ, writer, parameter):
	if not randomid.validate_id(parameter):
		return page.render_error_page(environ, writer, 400, 'Bad link.')

	with contextlib.closing(database.open_database()) as db:
		with db:
			values = (parameter, int(time.time()))

			csr = db.execute('UPDATE ids SET hits = hits + 1 WHERE id = ? AND expires > ?', values)
			if csr.rowcount:
				csr = db.execute('SELECT expires, download, mount, path FROM ids WHERE id = ? AND expires > ?', values)
				result = csr.fetchone()
			else:
				result = None

	if not result:
		return page.render_error_page(environ, writer, 404, 'Bad or expired link.')

	expires, download, mount, path = result
	download = bool(download)
	if isinstance(path, bytes):
		path = path.decode('utf-8', errors='surrogateescape')
	del result

	name = path.split('/')[-1]
	redirect_uri = '{0}{1}/{2}'.format(configuration.download_internal_prefix, mount, urllib.parse.quote(path, encoding='utf-8', errors='surrogateescape'))

	return (200, [page.make_expires_header(expires), page.make_content_disposition_header(name, inline=not download), ('X-Accel-Redirect', redirect_uri)])
