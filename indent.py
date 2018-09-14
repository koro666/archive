#!/usr/bin/env python3.7
class Indenter:
	def __init__(self, stream, transform=None):
		self.stream = stream
		self.transform = transform
		self.indent = 0

	def begin(self, text, *args):
		self.line(text, *args)
		self.indent = self.indent + 1

	def line(self, text='', *args):
		if text:
			self._write_indent()
			if self.transform:
				self.stream.write(text.format(*map(transform, args)))
			else:
				self.stream.write(text.format(*args))
		self._write_nl()

	def end(self, text, *args):
		self.indent = self.indent - 1
		self.line(text, *args)

	def _write_indent(self):
		self.stream.write('\t' * self.indent)

	def _write_nl(self):
		self.stream.write('\n')
