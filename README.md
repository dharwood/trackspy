Trackspy
========

Trackspy is a script to visit a provided list of websites and collect information on various trackers they use.

Requirements
------------

* Python 2.7+ OR Python 3+ (http://python.org)
* The Selenium libraries for Python (http://seleniumhq.org)
* Firefox (http://getfirefox.com)

Usage
-----

To run this script, the invocation is

     python trackspy.py <file with list of URLs>

After running through all of the provided URLs, Trackspy will output the results to stdout, and in a sqlite3 database that contains a table for each type of web tracker being watched.

Notes
-----

In order to get accurate readings on when LSOs are accessed, the partition holding the directories .macromedia and/or .gnash (typically the home dir of the user running script) needs to be mounted with strictatime. Otherwise, atime will not update at every access of the LSO. This requires that the user have root access on the machine. For the moment, the use of Linux-isms limits Trackspy to use on Linux.

Features, bugs, etc
-------------------

At the moment, there's a bunch of work to be done, from supporting other browsers to tracking more trackers. Take a look at https://dharwood.github.com/trackspy/issues for a rundown.

Author
------

Trackspy is copyright (c) 2013 David Harwood

Trackspy is free software, licensed under the terms of the MIT license. A copy of the license can be found in the file named LICENSE or at http://opensource.org/licenses/MIT
