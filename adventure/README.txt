This is a faithful port of the “Adventure” game to Python 3 from the
original 1977 FORTRAN code by Crowther and Woods (it is driven by the
same ``advent.dat`` file!) that lets you explore Colossal Cave, where
others have found fortunes in treasure and gold, though it is rumored
that some who enter are never seen again.  To encourage the use of
Python 3, the game is designed to be played right at the Python prompt.
Single-word commands can be typed by themselves, but two-word commands
should be written as a function call (since a two-word command would not
be valid Python)::

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

You can save your game at any time by calling the ``save()`` command
with a filename, and then can resume it later at any time::

    >>> save('advent.save')
    GAME SAVED

    >>> adventure.resume('advent.save')
    GAME RESTORED
    >>> look
    SORRY, BUT I AM NOT ALLOWED TO GIVE MORE DETAIL.  I WILL REPEAT THE
    LONG DESCRIPTION OF YOUR LOCATION.
    YOU ARE IN A VALLEY IN THE FOREST BESIDE A STREAM TUMBLING ALONG A
    ROCKY BED.

You can find two complete, working walkthroughs of the game in its
``tests`` directory, which you can run using the ``discover`` module that
comes built-in with Python 3.2::

    $ python3.2 -m unittest discover adventure

I wrote most of this package over Christmas vacation 2010, to learn more
about the workings of the game that so enthralled me as a child; the
project also gave me practice writing Python 3.  I still forget the
parentheses when writing ``print()`` if I am not paying attention.

Notes
=====

* Several Adventure commands conflict with standard Python built-in
  functions.  The function “exit” is so important that I refused to
  overwrite it, so you will have to use one of the synonyms “out,”
  “outside,” or “leave” instead.  Similarly, use “unlock” instead of
  “open.”

* I use the Python functions “quit” and “help” less often, so I allow
  the game to replace them with Colossal Cave commands.

* The word “break” is a Python keyword, so there was no possibility of
  using it in the game.  Instead, use one of the two synonyms defined by
  the PDP version of Adventure: “shatter” or “smash.”

Changelog
=========

| 1.0 — 2011 February 15 — 100% test coverage, feature-complete
| 0.3 — 2011 January 31 — first public release
