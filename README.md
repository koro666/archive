ReadMe
======

What is it?
-----------

`archive` is a web application that allows browsing files on a web server. It's basically auto-indexing on steroids.

It originally started as a loose collection of Bash CGI scripts meant to slightly improve on auto-indexing. The (very unoriginal) name comes from the fact that it allowed browsing an "archive" of files. It grew over time and got converted a Python 2.7 FastCGI server. This latest iteration is a total, much cleaner rewrite targeting Python 3.7.

Features
--------

It is meant to be used as a password-protected browser to directories on the server.

For every file it lists, it generates an automatically expiring short download link that can be used without authentication, ideal for sending out links to files without needing to give out a password. These links support HTTP byte ranges and can be streamed directly using a media player.

It is specifically targeted towards file collections containing lots of pictures and videos, and thus has specific features:

- Automatically generates and shows thumbnails for pictures and videos;
- Video thumbnails are animated (shown on hover);
- Pictures are previewable in-place using a JavaScript viewer;
- One-click `.m3u` playlist generation for a directory.

It also contains an interface to inspect and extend the lifetime of the generated download links.

Requirements
------------

- POSIX operating system (tested on Linux and FreeBSD)
- Python 3.7
- Python's `sqlite` module
- Nginx
- FFmpeg

FreeBSD packages: `python37 py37-sqlite3 nginx ffmpeg`.

How to install
--------------

- `git clone` the repository;
- Edit `configuration.py` to your liking (see [documentation](documentation/configuration.md));
- Add and commit your changes so you can just `git pull --rebase` later;
- Run `nginx.py` to generate an example Nginx configuration
- Set up `server.py` to be run as a daemon: [Linux](https://www.freedesktop.org/software/systemd/man/systemd.service.html), [FreeBSD](https://www.freebsd.org/doc/en/books/porters-handbook/rc-scripts.html) [(advanced)](https://www.freebsd.org/doc/en_US.ISO8859-1/articles/rc-scripting/);
- Either directly use the generated `nginx.conf`, or use it as an inspiration. **Make sure to change the default passwords in the generated `.htpasswd` files if you use them as-is**;
- Add `cron.py hourly` in the server user's `crontab` as an hourly job;
- Add `cron.py daily` in the server user's `crontab` as a daily job;
- Start the server and (re-)start Nginx.

How to use
----------

Simply visit your server's browse URL which will look like `http://example.com/browse/` (assuming the default browse prefix was not changed), and browse away.

The view can be toggled between thumbnail mode and list mode using buttons in the navigation bar. If the directory contains playable files, a "Play" button will appear that will generate an `.m3u` playlist.

In order to get a short link to a file, use your browser's "Copy Link Location" functionality. Each reload of the directory will generate a new batch of short links. To generate an easy to copy-and-paste list of short links to all files in a directory, append `?txt` to the directory URL.

Those short links can be edited to extend their lifetime past the preconfigured expiry. If logged in as an editor user, the "Edit" menu in the navigation bar will appear. Clicking it will show checkboxes to select files. Select which files whose links need to be edited, then pick one of the options from the menu.

The link editor can also be directly accessed from the server's editor URL which will look like `http://example.com/editor/`. In this case, a textbox will appear, allowing you to paste IDs or links to inspect or edit.
