#!/usr/bin/env python3.7
import common
import configuration
import page

def handler(environ, writer, parameter):
	# TODO:
	return (303, [('Location', configuration.static_prefix + 'icons/error.png')])
