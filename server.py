#!/usr/bin/env python3.7
import os
import io
import gzip
import collections
import flup.server.fcgi
import common
import configuration
import page

from editor import handler as editor_handler
from gallery import handler as gallery_handler
from download import handler as download_handler
from thumbnail import handler as thumbnail_handler

status_map = {
	200 : 'OK',
	303 : 'See Other',
	400 : 'Bad Request',
	404 : 'Not Found',
	410 : 'Gone',
	500 : 'Internal Server Error'
}

def gzip_wrapper(environ, writer, parameter, handler):
	with gzip.GzipFile(fileobj=writer, mode='wb') as gzwriter:
		result = handler(environ, gzwriter, parameter)
	result[1].append(('Content-Encoding', 'gzip'))
	return result

def default_handler(environ, writer, parameter):
	return page.render_error_page(environ, writer, 404, 'No such module.')

Module = collections.namedtuple('Module', ['prefix', 'handler', 'gzip'])

module_map = {
	'editor': Module(configuration.editor_prefix, editor_handler, False),
	'gallery': Module(configuration.browse_prefix, gallery_handler, True),
	'download': Module(configuration.download_prefix, download_handler, False),
	'thumbnail': Module(configuration.thumbnail_prefix, thumbnail_handler, False)
}

default_module = Module('', default_handler, False)

def dispatcher(environ, start_response):
	with io.BytesIO() as writer:
		module = module_map.get(environ.get('archive.module'), default_module)

		parameter = environ['DOCUMENT_URI'];
		if parameter.startswith(module.prefix):
			parameter = parameter[len(module.prefix):]

		if module.gzip:
			result = gzip_wrapper(environ, writer, parameter, module.handler)
		else:
			result = module.handler(environ, writer, parameter)

		start_response('{0} {1}'.format(result[0], status_map[result[0]]), result[1]);
		return [writer.getvalue()]

if __name__ == '__main__':
	os.umask(0o002)
	flup.server.fcgi.WSGIServer(dispatcher, bindAddress=common.socket_path, umask=0, debug=configuration.debug).run()
