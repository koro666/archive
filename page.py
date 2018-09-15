#!/usr/bin/env python3.7
import io
import html
import collections
import urllib.parse
import wsgiref
import common
import configuration
import indent

Theme = collections.namedtuple('Theme', ['url', 'sri', 'dark'])

# https://bootswatch.com/3/
themes = {
	'cerulean': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/cerulean/bootstrap.min.css', 'sha384-zF4BRsG/fLiTGfR9QL82DrilZxrwgY/+du4p/c7J72zZj+FLYq4zY00RylP9ZjiT', False),
	'cosmo': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/cosmo/bootstrap.min.css', 'sha384-h21C2fcDk/eFsW9sC9h0dhokq5pDinLNklTKoxIZRUn3+hvmgQSffLLQ4G4l2eEr', False),
	'cyborg': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/cyborg/bootstrap.min.css', 'sha384-D9XILkoivXN+bcvB2kSOowkIvIcBbNdoDQvfBNsxYAIieZbx8/SI4NeUvrRGCpDi', True),
	'darkly': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/darkly/bootstrap.min.css', 'sha384-S7YMK1xjUjSpEnF4P8hPUcgjXYLZKK3fQW1j5ObLSl787II9p8RO9XUGehRmKsxd', True),
	'flatly': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/flatly/bootstrap.min.css', 'sha384-+ENW/yibaokMnme+vBLnHMphUYxHs34h9lpdbSLuAwGkOKFRl4C34WkjazBtb7eT', False),
	'journal': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/journal/bootstrap.min.css', 'sha384-1L94saFXWAvEw88RkpRz8r28eQMvt7kG9ux3DdCqya/P3CfLNtgqzMnyaUa49Pl2', False),
	'lumen': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/lumen/bootstrap.min.css', 'sha384-gv0oNvwnqzF6ULI9TVsSmnULNb3zasNysvWwfT/s4l8k5I+g6oFz9dye0wg3rQ2Q', False),
	'paper': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/paper/bootstrap.min.css', 'sha384-awusxf8AUojygHf2+joICySzB780jVvQaVCAt1clU3QsyAitLGul28Qxb2r1e5g+', False),
	'readable': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/readable/bootstrap.min.css', 'sha384-Li5uVfY2bSkD3WQyiHX8tJd0aMF91rMrQP5aAewFkHkVSTT2TmD2PehZeMmm7aiL', False),
	'sandstone': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/sandstone/bootstrap.min.css', 'sha384-G3G7OsJCbOk1USkOY4RfeX1z27YaWrZ1YuaQ5tbuawed9IoreRDpWpTkZLXQfPm3', False),
	'simplex': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/simplex/bootstrap.min.css', 'sha384-C0X5qw1DlkeV0RDunhmi4cUBUkPDTvUqzElcNWm1NI2T4k8tKMZ+wRPQOhZfSJ9N', False),
	'slate': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/slate/bootstrap.min.css', 'sha384-RpX8okQqCyUNG7PlOYNybyJXYTtGQH+7rIKiVvg1DLg6jahLEk47VvpUyS+E2/uJ', True),
	'spacelab': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/spacelab/bootstrap.min.css', 'sha384-L/tgI3wSsbb3f/nW9V6Yqlaw3Gj7mpE56LWrhew/c8MIhAYWZ/FNirA64AVkB5pI', False),
	'superhero': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/superhero/bootstrap.min.css', 'sha384-Xqcy5ttufkC3rBa8EdiAyA1VgOGrmel2Y+wxm4K3kI3fcjTWlDWrlnxyD6hOi3PF', True),
	'united': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/united/bootstrap.min.css', 'sha384-pVJelSCJ58Og1XDc2E95RVYHZDPb9AVyXsI8NoVpB2xmtxoZKJePbMfE4mlXw7BJ', False),
	'yeti': Theme('https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/yeti/bootstrap.min.css', 'sha384-HzUaiJdCTIY/RL2vDPRGdEQHHahjzwoJJzGUkYjHVzTwXFQ2QN/nVgX7tzoMW3Ov', False)
}

def HtmlIndenter(stream):
	return indent.Indenter(stream, html.escape)

def uri_to_url(environ, uri):
	assert(uri[0] == '/')

	scheme = environ['wsgi.url_scheme']
	host = environ['HTTP_HOST']
	port = environ['SERVER_PORT']

	port_visible = (scheme == 'http' and port != '80') or (scheme == 'https' and port != '443')
	format = '{0}://{1}:{2}{3}' if port_visible else '{0}://{1}{3}'

	return format.format(scheme, host, port, uri)

def make_content_disposition_header(filename, extension='', inline=True):
	return ('Content-Disposition', '{0}; filename*=UTF-8\'\'{1}'.format('inline' if inline else 'attachment', urllib.parse.quote(filename, encoding='utf-8', errors='ignore')) + extension)

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

def render_page(environ, writer, code=200, headers=[], title=configuration.name, link_cb=None, navbar_cb=None, content_cb=None, script_cb=None):
	theme = themes[configuration.theme]
	wrapper = io.TextIOWrapper(writer, encoding='utf-8', errors='replace')
	h = HtmlIndenter(wrapper)
	h.line('<!doctype html>')
	h.begin('<html lang="en">')
	h.begin('<head>')
	h.line('<meta charset="utf-8">')
	h.line('<meta http-equiv="X-UA-Compatible" content="IE=edge">')
	h.line('<meta name="referrer" content="no-referrer">')
	h.line('<meta name="viewport" content="width=device-width, initial-scale=1">')
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
	wrapper.detach()

	return (code, [("Content-Type", "text/html")] + headers)

def render_error_page(environ, writer, code, message):
	# TODO: Better error page
	writer.write(message.encode('utf-8', errors='replace'))
	return (code, [("Content-Type", "text/plain")])
