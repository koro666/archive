#!/usr/bin/env python3.7
import page

def handler(environ, writer, parameter):
	# TODO:
	return page.render_error_page(environ, writer, 404, 'Unimplemented module: thumbnail\nParameter: {0}'.format(parameter))
