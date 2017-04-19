========
apemouse
========

``apemouse`` is a virtual mouse device controlled with numpad. It works by
grabbing a keyboard device, creating a new keyboard+mouse device, and emitting
events on the new device.

Dependencies
============

- Python 3
- ``python-numpy``
- ``python-evdev``

Usage
=====

You must specify a keyboard device that controls the mouse. For example:

::

	$ ./main.py /dev/input/event0

Use ``./main.py --help`` for more information about the command line arguments:

::

	usage: main.py [-h] [--speed SPEED] [--speedup SPEEDUP] [--freq FREQ] device

	Create a virtual mouse device controlled with numpad

	positional arguments:
	  device             the controlling keyboard device

	optional arguments:
	  -h, --help         show this help message and exit
	  --speed SPEED      mouse movement speed (default 400)
	  --speedup SPEEDUP  speedup when holding shift (default 3)
	  --freq FREQ        mouse event frequency (default 200)

When ``apemouse`` is running you can control the mouse by holding down the left
super key (or Windows key) and then pressing one of the following keys:

============  ============
Key           Command
============  ============
numpad 5      left click
numpad 0      right click
numpad enter  middle click
numpad 1      down-left
numpad 2      down
numpad 3      down-right
numpad 4      left
numpad 6      right
numpad 7      up-left
numpad 8      up
numpad 9      up-right
left shift    faster speed
============  ============
