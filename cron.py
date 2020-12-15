#!/usr/bin/env python3.9
import sys
import time
import contextlib
import subprocess
import common
import configuration
import database

find_binary = '/usr/bin/find'
rm_binary = '/bin/rm'

assert(isinstance(configuration.thumbnail_expire_days, int))

def clean_expired_ids():
	with contextlib.closing(database.open_database()) as db:
		with db:
			db.execute("DELETE FROM ids WHERE expires <= ?", (int(time.time()),))

def clean_old_thumbnails():
	argv = [find_binary, configuration.thumbnail_cache_directory, '-type', 'f', '-mtime', '+{0}'.format(configuration.thumbnail_expire_days), '-exec', rm_binary, '--', '{}', '+']
	subprocess.check_call(argv)

if __name__ == '__main__':
	argv = sys.argv[1:]
	if 'hourly' in argv:
		clean_expired_ids()
	if 'daily' in argv:
		clean_old_thumbnails()
