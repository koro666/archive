#!/usr/bin/env python3.9
import os
import sqlite3
import common
import configuration

database_path = os.path.join(configuration.database_directory, 'archive.sqlite')

def open_database():
	db = sqlite3.connect(database_path)

	db.execute("PRAGMA journal_mode = WAL")
	with db:
		db.execute("CREATE TABLE IF NOT EXISTS ids (id TEXT NOT NULL, expires INTEGER NOT NULL, user TEXT NULL, download INTEGER NOT NULL, hits INTEGER NOT NULL, mount TEXT NOT NULL, path TEXT NOT NULL)")
		db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ids_id_index ON ids (id ASC)")
		db.execute("CREATE TABLE IF NOT EXISTS state (key TEXT NOT NULL, value)")
		db.execute("CREATE UNIQUE INDEX IF NOT EXISTS state_key_index ON state (key ASC)")

	return db

if __name__ == '__main__':
	with open_database() as db:
		pass
