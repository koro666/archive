#!/usr/bin/env python3.9
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

def null_wrapper(handler, environ, writer, parameter):
	return handler(environ, writer, parameter)

def text_wrapper(handler, environ, writer, parameter):
	wrapper = io.TextIOWrapper(writer, encoding='utf-8', errors='replace', write_through=True)
	try:
		return handler(environ, wrapper, parameter)
	finally:
		wrapper.detach()

def gzip_wrapper(handler, environ, writer, parameter):
	with gzip.GzipFile(fileobj=writer, mode='wb') as gzwriter:
		result = handler(environ, gzwriter, parameter)
	result[1].append(('Content-Encoding', 'gzip'))
	return result

def default_handler(environ, writer, parameter):
	return page.render_error_page(environ, writer, 404, 'No such module.')

Module = collections.namedtuple('Module', ['prefix', 'handler', 'text', 'gzip'])

module_map = {
	'editor': Module(configuration.editor_prefix, editor_handler, True, False),
	'gallery': Module(configuration.browse_prefix, gallery_handler, True, True),
	'download': Module(configuration.download_prefix, download_handler, True, False),
	'thumbnail': Module(configuration.thumbnail_prefix, thumbnail_handler, False, False)
}

default_module = Module('', default_handler, True, False)

def dispatcher(environ, start_response):
	with io.BytesIO() as writer:
		module = module_map.get(environ.get('archive.module'), default_module)

		parameter = environ['DOCUMENT_URI']
		if parameter.startswith(module.prefix):
			parameter = parameter[len(module.prefix):]

		handler = lambda e,w,p: null_wrapper(module.handler, e, w, p)
		if module.text:
			handler = lambda e,w,p,h=handler: text_wrapper(h, e, w, p)
		if module.gzip:
			handler = lambda e,w,p,h=handler: gzip_wrapper(h, e, w, p)

		result = handler(environ, writer, parameter)
		start_response('{0} {1}'.format(result[0], status_map[result[0]]), result[1])
		return [writer.getvalue()]

if __name__ == '__main__':
	os.umask(0o002)
	flup.server.fcgi.WSGIServer(dispatcher, bindAddress=common.socket_path, umask=0, debug=configuration.debug).run()
