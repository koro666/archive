#!/usr/bin/env python3.7
import os
import io
import gzip
import collections
import flup.server.fcgi
import common
import configuration
import page

status_map = {
	200 : 'OK',
	303 : 'See Other',
	400 : 'Bad Request',
	404 : 'Not Found',
	410 : 'Gone',
	500 : 'Internal Server Error'
}

def gzip_wrapper(environ, writer, handler):
	with gzip.GzipFile(fileobj=writer, mode='wb') as gzwriter:
		result = handler(environ, gzwriter)
	result[1].append(('Content-Encoding', 'gzip'))
	return result

def default_handler(environ, writer, parameter):
	return page.render_error_page(environ, writer, 404, 'No such module.')

Module = collections.namedtuple('Module', ['prefix', 'handler', 'gzip'])

module_map = {
	# TODO:
}

default_module = Module('', default_handler, False)

socket_path = os.path.join(configuration.socket_directory, 'archive2.socket')

def dispatcher(environ, start_response):
	with io.BytesIO() as writer:
		module = module_map.get(environ.get('archive.module'), default_module)
		parameter = '';
		if module.gzip:
			result = gzip_wrapper(environ, writer, parameter, module.handler)
		else:
			result = module.handler(environ, writer, parameter)

		start_response('{0} {1}'.format(result[0], status_map[result[0]]), result[1]);
		return [writer.getvalue()]

if __name__ == '__main__':
	os.umask(0o002)
	flup.server.fcgi.WSGIServer(dispatcher, bindAddress=socket_path, umask=0, debug=configuration.debug).run()
