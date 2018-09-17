Configuration
=============

This document describes the different configuration options from `configuration.py`.

Global
------

Global settings that control the general behavior.

`name`: Name of the site. Displayed in the navigation bar and other places.

`debug`: Set to `True` to enable debugging. When enabled, exceptions will be shown using `cgitb`, and some URIs will spew additional debug information. Do not leave enabled uselessly.

`theme`: The Bootstrap theme to use. Possible values are `cerulean`, `cosmo`, `cyborg`, `darkly`, `flatly`, `journal`, `lumen`, `paper`, `readable`, `sandstone`, `simplex`, `slate`, `spacelab`, `superhero`, `united`, `yeti`. See [Bootswatch](https://bootswatch.com/3/) for previews of the themes.

`theme_inverse_navbar`: Set to `True` to use the inverse navigation bar colors for the theme.

`browse_users`: List of users who are allowed to use the browse endpoint.

`editor_users`: List of users who are allowed to use the editor endpoint as well. Should not overlap with `browse_users`.

`download_delay`: Amount of time, in seconds, for which generated download short links are valid.

`time_format`: Default format to use to show times. See [documentation](https://docs.python.org/3/library/time.html#time.strftime) for syntax.

Webserver
---------

URI prefixes for different parts of the application. **All prefixes must start and end with a forward slash (`/`).**

`static_prefix`: Prefix for the static assets (stylesheets, images, etc).

`editor_prefix`: Prefix for the link editor.

`browse_prefix`: Prefix for the directory browser.

`download_prefix`: Prefix for the generated download links.

`download_internal_prefix`: Prefix used internally with Nginx for actual file download.

`thumbnail_prefix`: Prefix for the thumbnails.

`thumbnail_cache_prefix`: Prefix for the actual thumbnail files.

Directories
-----------

These controls the different directories used by the application. Relative paths are relative to the current directory at the moment of startup. **All paths must _not_ end with a forward slash.**

`static_directory`: Directory containing the static assets.

`database_directory`: Directory that will contain the database. Must be writable.

`socket_directory`: Directory that will contain the FastCGI socket. Must be writable.

`thumbnail_cache_directory`: Directory that will hold cached thumbnail files. Must be writable.

Assuming the web server and the application don't run under the same user, it's important that the web server user has the same amount of access to the different directories, or weird stuff could happen.

`exported_directories`: Directories that are browsable by the application. Should be a dictionary mapping a "short name" to a directory path.

`hidden_directory_names`: List of directory names that should be hidden from regular (non-editor) users.

`hidden_file_names`: List of file names that should be hidden from regular users.

Random IDs
----------

Controls the look of the random IDs used in the short link generation code.

`rid_seed`: Value used to seed the random generator used to generate the random configuration of links. **This value should be changed from the default, and kept secret.** See [documentation](https://docs.python.org/3/library/random.html#random.seed) for acceptable inputs.

`rid_python2_random`: Set to `True` to generate the exact same random configuration given a certain seed as it would have been in Python 2.x.

`rid_symbols`: String containing every possible character that is allowed in a random ID.

`rid_bits_state` and `rid_bits_noise`: Controls the size, and look, of a generated random ID.

The sum of the amount of state and noise bits control the length of a generated random ID. The amount of state bits controls how many IDs can be generated before "running out", wheres the amount of noise bits control how "random" two sequentially-generated IDs will look. See the [description](randomid.md) of the generation algorithm.

Browsing
--------

`thumbnail_nice`: What `nice` level to use when running sub-processes to generate thumbnails.

`thumbnail_concurrent`: How many concurrent thumbnail generations can be in progress. Additional generations will be blocked.

`thumbnail_filename_salt`: Salt affecting the names of the thumbnail files in the case. **This value should be changed from the default, and kept secret.**

`thumbnail_animated_framecount`: How many frames off the source video to pick for an animated thumbnail. Higher values will slow down thumbnail generation, as well as make for bigger files.

`thumbnail_animated_framerate`: Number of frames per second to show in an animated thumbnail.

`thumbnail_expire_days`: How much time, in days, after which a cached thumbnail file gets deleted.
