#!/usr/bin/env python3.8
import time
import html
import collections
import urllib.parse
import wsgiref.handlers
import common
import configuration
import indent

Theme = collections.namedtuple('Theme', ['url', 'sri', 'navbar', 'navbar2', 'dark'])

# https://bootswatch.com/3/
themes = {
	'cerulean': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/cerulean/bootstrap.min.css', 'sha384-zF4BRsG/fLiTGfR9QL82DrilZxrwgY/+du4p/c7J72zZj+FLYq4zY00RylP9ZjiT', '#54b4eb', '#04519b', False),
	'cosmo': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/cosmo/bootstrap.min.css', 'sha384-h21C2fcDk/eFsW9sC9h0dhokq5pDinLNklTKoxIZRUn3+hvmgQSffLLQ4G4l2eEr', '#222222', '#2780e3', False),
	'cyborg': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/cyborg/bootstrap.min.css', 'sha384-D9XILkoivXN+bcvB2kSOowkIvIcBbNdoDQvfBNsxYAIieZbx8/SI4NeUvrRGCpDi', '#060606', '#282828', True),
	'darkly': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/darkly/bootstrap.min.css', 'sha384-S7YMK1xjUjSpEnF4P8hPUcgjXYLZKK3fQW1j5ObLSl787II9p8RO9XUGehRmKsxd', '#375a7f', '#00bc8c', True),
	'flatly': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/flatly/bootstrap.min.css', 'sha384-+ENW/yibaokMnme+vBLnHMphUYxHs34h9lpdbSLuAwGkOKFRl4C34WkjazBtb7eT', '#2c3e50', '#18bc9c', False),
	'journal': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/journal/bootstrap.min.css', 'sha384-1L94saFXWAvEw88RkpRz8r28eQMvt7kG9ux3DdCqya/P3CfLNtgqzMnyaUa49Pl2', '#ffffff', '#eb6864', False),
	'lumen': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/lumen/bootstrap.min.css', 'sha384-gv0oNvwnqzF6ULI9TVsSmnULNb3zasNysvWwfT/s4l8k5I+g6oFz9dye0wg3rQ2Q', '#f8f8f8', '#ffffff', False),
	'paper': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/paper/bootstrap.min.css', 'sha384-awusxf8AUojygHf2+joICySzB780jVvQaVCAt1clU3QsyAitLGul28Qxb2r1e5g+', '#ffffff', '#2196f3', False),
	'readable': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/readable/bootstrap.min.css', 'sha384-Li5uVfY2bSkD3WQyiHX8tJd0aMF91rMrQP5aAewFkHkVSTT2TmD2PehZeMmm7aiL', '#ffffff', '#ffffff', False),
	'sandstone': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/sandstone/bootstrap.min.css', 'sha384-G3G7OsJCbOk1USkOY4RfeX1z27YaWrZ1YuaQ5tbuawed9IoreRDpWpTkZLXQfPm3', '#3e3f3a', '#93c54b', False),
	'simplex': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/simplex/bootstrap.min.css', 'sha384-C0X5qw1DlkeV0RDunhmi4cUBUkPDTvUqzElcNWm1NI2T4k8tKMZ+wRPQOhZfSJ9N', '#ffffff', '#d9230f', False),
	'slate': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/slate/bootstrap.min.css', 'sha384-RpX8okQqCyUNG7PlOYNybyJXYTtGQH+7rIKiVvg1DLg6jahLEk47VvpUyS+E2/uJ', '#484e55', '#8a9196', True),
	'spacelab': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/spacelab/bootstrap.min.css', 'sha384-L/tgI3wSsbb3f/nW9V6Yqlaw3Gj7mpE56LWrhew/c8MIhAYWZ/FNirA64AVkB5pI', '#ffffff', '#6d94bf', False),
	'superhero': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/superhero/bootstrap.min.css', 'sha384-Xqcy5ttufkC3rBa8EdiAyA1VgOGrmel2Y+wxm4K3kI3fcjTWlDWrlnxyD6hOi3PF', '#4e5d6c', '#df691a', True),
	'united': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/united/bootstrap.min.css', 'sha384-pVJelSCJ58Og1XDc2E95RVYHZDPb9AVyXsI8NoVpB2xmtxoZKJePbMfE4mlXw7BJ', '#e95420', '#772953', False),
	'yeti': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/yeti/bootstrap.min.css', 'sha384-HzUaiJdCTIY/RL2vDPRGdEQHHahjzwoJJzGUkYjHVzTwXFQ2QN/nVgX7tzoMW3Ov', '#333333', '#008cba', False)
}

def HtmlIndenter(stream):
	return indent.Indenter(stream, html.escape)

def uri_to_url(environ, uri):
	assert(uri[0] == '/')

	scheme = environ['wsgi.url_scheme']
	host = environ['HTTP_HOST']

	return '{0}://{1}{2}'.format(scheme, host, uri)

def match_in_qs(environ, values, fallback):
	result = None

	for key, value in urllib.parse.parse_qsl(environ['QUERY_STRING'], keep_blank_values=True):
		if key == '' or value != '':
			continue
		if not key in values:
			continue

		if result is None:
			result = key
		elif result != key:
			return fallback

	if result is None:
		result = ''

	return values[result]

def make_content_disposition_header(filename, extension='', inline=True):
	filename = filename + extension
	disposition = 'inline' if inline else 'attachment'
	try:
		attachment = 'filename={0}'.format(urllib.parse.quote(filename, encoding='ascii'))
	except UnicodeEncodeError:
		attachment = 'filename*=UTF-8\'\'{0}'.format(urllib.parse.quote(filename, encoding='utf-8', errors='ignore'))
	return ('Content-Disposition', '{0}; {1}'.format(disposition, attachment))

def make_nocache_header():
	return ('Cache-Control', 'no-cache, no-store, must-revalidate')

def make_expires_header(expires):
	return ('Expires', wsgiref.handlers.format_date_time(expires))

def make_tag(tag, attributes):
	format = [tag]
	values = []

	for attribute in attributes:
		if attribute[1] == '':
			continue

		format.append('{0}="{{}}"'.format(attribute[0]))
		values.append(attribute[1])

	format = '<{0}>'.format(' '.join(format))
	return [format] + values

def pretty_time(value):
	return time.strftime(configuration.time_format, time.localtime(value))

def pretty_size(value):
	if value < 1024:
		return '%uB' % value
	elif value < 1048576:
		return '%uK' % (value / 1024)
	elif value < 8589934592:
		return '%.1fM' % (value / 1048576.0)
	elif value < 1099511627776:
		return '%.2fG' % (value / 1073741824.0)
	else:
		return '%.2fT' % (value / 1099511627776.0)

def render_page(environ, writer, code=200, headers=[], title=configuration.name, link_cb=None, navbar_cb=None, content_cb=None, script_cb=None):
	theme = themes[configuration.theme]
	h = HtmlIndenter(writer)
	h.line('<!doctype html>')
	h.begin('<html lang="en">')
	h.begin('<head>')
	h.line('<meta name="viewport" content="width=device-width, initial-scale=1">')
	h.line('<meta name="theme-color" content="{0}">', theme.navbar2 if configuration.theme_inverse_navbar else theme.navbar)
	h.line('<title>{0}</title>', title)
	h.line('<link href="{0}" rel="stylesheet" integrity="{1}" crossorigin="anonymous">', theme.url, theme.sri)
	if link_cb:
		link_cb(h)
	h.end('</head>')
	h.begin('<body>')
	h.begin('<nav class="navbar navbar-{0}">', 'inverse' if configuration.theme_inverse_navbar else 'default')
	h.begin('<div class="container-fluid">')
	h.begin('<div class="navbar-header">')
	if navbar_cb:
		h.begin('<button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navbar">')
		h.line('<span class="icon-bar"></span>')
		h.line('<span class="icon-bar"></span>')
		h.line('<span class="icon-bar"></span>')
		h.end('</button>')
	h.line('<a class="navbar-brand" href="/">{0}</a>', configuration.name)
	h.end('</div>')
	if navbar_cb:
		h.begin('<div class="collapse navbar-collapse" id="navbar">')
		h.begin('<ul class="nav navbar-nav navbar-right">')
		navbar_cb(h)
		h.end('</ul>')
		h.end('</div>')
	h.end('</div>')
	h.end('</nav>')
	h.begin('<div class="container">')
	if content_cb:
		content_cb(h)
	h.end('</div>')
	h.line('<script src="https://code.jquery.com/jquery-2.2.4.min.js" integrity="sha256-BbhdlvQf/xTY9gja0Dq3HiwQF8LaCRTXxZKRutelT44=" crossorigin="anonymous"></script>')
	h.line('<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>')
	if script_cb:
		script_cb(h)
	h.end('</body>')
	h.end('</html>')

	return (code, [('Content-Type', 'text/html; charset=utf-8')] + headers)

def render_error_page(environ, writer, code, message):
	h = HtmlIndenter(writer)
	h.line('<!doctype html>')
	h.begin('<html lang="en">')
	h.begin('<head>')
	h.line('<meta name="viewport" content="width=device-width, initial-scale=1">')
	h.line('<style>@media (max-width: 767px) {{ body {{ text-align: center; }} }} </style>')
	h.end('</head>')
	h.line('<body>{0}</body>', message)
	h.end('</html>')

	return (code, [('Content-Type', 'text/html; charset=utf-8')])
