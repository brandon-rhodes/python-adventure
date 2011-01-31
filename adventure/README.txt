This is a faithful port of the “Adventure” game to Python 3 from the
original 1977 FORTRAN code by Crowther and Woods, driven by the same
``advent.dat`` file, that lets you explore Colossal Cave, where others
have found fortunes in treasure and gold, though it is rumored that some
who enter are never seen again.  To encourage the use of Python 3, the
game is designed to be played right at the Python prompt.  Single-word
commands can be typed by themselves, but two-word commands should be
written as a function call (since a two-word command would not be valid
Python)::

    >>> import adventure
    >>> adventure.play()
    WELCOME TO ADVENTURE!!  WOULD YOU LIKE INSTRUCTIONS?

    >>> no
    YOU ARE STANDING AT THE END OF A ROAD BEFORE A SMALL BRICK BUILDING.
    AROUND YOU IS A FOREST.  A SMALL STREAM FLOWS OUT OF THE BUILDING AND
    DOWN A GULLY.

    >>> east
    YOU ARE INSIDE A BUILDING, A WELL HOUSE FOR A LARGE SPRING.

    THERE ARE SOME KEYS ON THE GROUND HERE.

    THERE IS A SHINY BRASS LAMP NEARBY.

    THERE IS FOOD HERE.

    THERE IS A BOTTLE OF WATER HERE.

    >>> get(lamp)
    OK

    >>> leave
    YOU'RE AT END OF ROAD AGAIN.

    >>> south
    YOU ARE IN A VALLEY IN THE FOREST BESIDE A STREAM TUMBLING ALONG A
    ROCKY BED.

The original Adventure payed attention to only the first five letters of
each command, so a long command like ``inventory`` could simply be typed
as ``inven``.  This package defines a symbol for both versions of every
long word, so you can type the long or short version as you please.

You can find two complete, working walkthroughs of the game in its
``tests`` directory, which you can run using the ``discover`` module that
comes built-in with Python 3.2::

    $ python3.2 -m unittest discover adventure

I wrote most of this package over Christmas vacation 2010, to learn more
about the workings of the game that so entralled me as a child; the
project also gave me practice writing Python 3.  I still forget the
parentheses when writing ``print()`` if I am not paying attention.

Todo
====

* Add commands to save and load the game.
* Improve the test coverage with situation-specific tests.
* Once coverage has reached 100%, start cleaning, refactoring, and
  improving the code — right now it is laid out very much like the
  original FORTRAN, to make it easier to determine whether its logic
  really matches.

Changelog
=========

| 2011 January 31 — 0.3 — first public release
