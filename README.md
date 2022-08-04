# rattatouille
Random collection of use(ful|less) scripts

## scripts

* ``grim-reaper``: looks for large files you have never accessed 

## bashrc functions

There are a few useful bash functions under ``/etc``. You can ensure they're
invoked from your ``.bashrc`` by making this symlink:
 
```
cd ~
ln -s ~/rattatouille/etc/.bash_aliases
```

If your rattatouille is checked out somewhere other than ``~``, you'll need
to copy the aliases script and adjust paths instead.

Some useful functions defined by this are:

* ``venv`` to manage virtual environments. ``venv -p3.8 test`` will create a virtual environment under ``~/.venv/test``. ``venv`` with no arguments lists all virtual environments under ``~/.venv``. ``venv test`` activates a virtual environment.

* ``phgrep`` and ``gphgrep`` searches your persistent command history. The former works on a per-directory basis, the latter globally.
