#!/usr/bin/env python3.7
import html
import common
import configuration
import indent

def HtmlIndenter(stream):
	return indent.Indenter(stream, html.escape)

def render_page(environ, writer, headers=[], title=configuration.name, referrer=True, link_cb=None, navbar_cb=None, content_cb=None, script_cb=None):
	# TODO:
	pass

def render_error_page(environ, writer, code, message):
	# TODO: Better error page
	writer.write(message.encode('utf-8', errors='replace'))
	return (code, [("Content-Type", "text/plain")])
