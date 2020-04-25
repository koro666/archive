#!/usr/bin/env python3.8
import sys
import os
import crypt
import string
import secrets
import common
import configuration
import indent

nginx_conf = 'nginx.conf'
archive_htpasswd = 'archive.htpasswd'
archive_editor_htpasswd = 'archive_editor.htpasswd'

def generate_configuration(root, stream):
	i = indent.Indenter(stream)

	i.line('worker_processes 1;')
	i.line()

	i.begin('events {{')
	i.line('worker_connections 1024;')
	i.end('}}')
	i.line()

	i.begin('http {{')
	i.line('include mime.types;')
	i.line('default_type application/octet-stream;')
	i.line()
	i.line('sendfile on;')
	i.line('#tcp_nopush on;')
	i.line('keepalive_timeout 60;')
	i.line('#gzip on;')
	i.line()

	i.begin('server {{')
	i.line('listen 80;')
	i.line('server_name localhost;')
	i.line()

	i.begin('location {0} {{', configuration.static_prefix)
	i.line('alias {0}/;', configuration.static_directory)
	i.end('}}')
	i.line()

	i.begin('location {0} {{', configuration.editor_prefix)
	i.line('auth_basic "{0} Editor";', configuration.name)
	i.line('auth_basic_user_file {0};', os.path.join(root, archive_editor_htpasswd))
	i.line()
	i.line('fastcgi_pass unix:{0};', common.socket_path)
	i.line('include fastcgi_params;')
	i.line('fastcgi_param REMOTE_USER $remote_user;')
	i.line('fastcgi_param archive.module editor;')
	i.end('}}')
	i.line()

	i.begin('location {0} {{', configuration.browse_prefix)
	i.line('auth_basic "{0}";', configuration.name)
	i.line('auth_basic_user_file {0};', os.path.join(root, archive_htpasswd))
	i.line()
	i.line('fastcgi_pass unix:{0};', common.socket_path)
	i.line('include fastcgi_params;')
	i.line('fastcgi_param REMOTE_USER $remote_user;')
	i.line('fastcgi_param archive.module gallery;')
	i.end('}}')
	i.line()

	i.begin('location {0} {{', configuration.download_prefix)
	i.line('fastcgi_pass unix:{0};', common.socket_path)
	i.line('include fastcgi_params;')
	i.line('fastcgi_param archive.module download;')
	i.end('}}')
	i.line()

	i.begin('location {0} {{', configuration.download_internal_prefix)
	for kvp in configuration.exported_directories.items():
		i.begin('location {0}{1}/ {{', configuration.download_internal_prefix, kvp[0])
		i.line('alias {0}/;', kvp[1])
		i.end('}}')
		i.line()
	i.line('internal;')
	i.end('}}')
	i.line()

	i.begin('location {0} {{', configuration.thumbnail_prefix)
	i.line('fastcgi_pass unix:{0};', common.socket_path)
	i.line('include fastcgi_params;')
	i.line('fastcgi_param archive.module thumbnail;')
	i.end('}}')
	i.line()

	i.begin('location {0} {{', configuration.thumbnail_cache_prefix)
	i.line('alias {0}/;', configuration.thumbnail_cache_directory)
	i.end('}}')

	i.end('}}')
	i.end('}}')

def generate_passwords(root, stream, browse_password, editor_password):
	userlist = []
	if browse_password is not None:
		userlist.extend((user, browse_password) for user in configuration.browse_users)
	if editor_password is not None:
		userlist.extend((user, editor_password) for user in configuration.editor_users)
	userlist.sort()
	for user, password in userlist:
		stream.write('{0}:{1}\n'.format(user, crypt.crypt(password, crypt.mksalt())))

def make_password(length):
	alphabet = string.ascii_letters + string.digits
	return ''.join(secrets.choice(alphabet) for i in range(length))

if __name__ == '__main__':
	if len(sys.argv) > 1:
		root = os.path.normpath(os.path.abspath(sys.argv[1]))
	else:
		root = os.getcwd()

	with open(os.path.join(root, nginx_conf), 'w') as fp:
		generate_configuration(root, fp)

	browse_password = make_password(8)
	editor_password = make_password(12)

	with open(os.path.join(root, archive_htpasswd), 'w') as fp:
		generate_passwords(root, fp, browse_password, editor_password)

	with open(os.path.join(root, archive_editor_htpasswd), 'w') as fp:
		generate_passwords(root, fp, None, editor_password)

	print('Generated passwords:')
	print(' browse: {0}'.format(browse_password))
	print(' editor: {0}'.format(editor_password))