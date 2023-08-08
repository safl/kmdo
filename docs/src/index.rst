..
    Parts of the documentation is autogerated using kdmo

======
 kmdo
======

Maintaining documentation can be prone to error and cumbersome. Especially for
demos, tutorials, and usage guides for command-line tools.  To aid that,
``kmdo`` runs through a directory and executes command-files, storing
``stdout`` and ``stderr`` in corresponding output-files.

This documentation is an example of how this can be used in concert with
`Sphinx <http://www.sphinx-doc.org/>`_ and `Read the Docs
<https://readthedocs.org/>`_.

Installation
============

Install ``kmdo`` system-wide via the pip using ``pipx``:

.. code:: bash

  pipx install kmdo

.. note::
   Ensure that command-line tools installed using ``pipx`` are added to
   ``PATH`` by running ``pipx ensurepath``.

Usage
=====

.. literalinclude:: examples/kmdo.out
   :language: bash

Error-handling
~~~~~~~~~~~~~~

``kmdo`` has exit code 0 upon success, that is when all commands succeed,
ignoring command errors from command-files with ``.uone`` in the file name. On
error, ``kmdo`` has a non zero exit code.

Additionally, ``kmdo`` outputs a **YAML** representation of what it has
executed to ``stdout``. For example, when using ``kmdo`` to generate command
output for the documentation you are reading now.

.. literalinclude:: kmdo-examples.cmd
   :language: bash

Outputs the following **YAML**:

.. literalinclude:: kmdo-examples.out
   :language: bash

Empty command-file and update-on-error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the command-file is empty, then the **fname** part of the command-file
file name is treated as the command to execute.

For example, the empty file named ``kmdo.uone.cmd``, will execute the command
``kmdo``, and because of ``.uone`` in the file name then it create the output
file ``kmdo.uone.out``:

.. literalinclude:: examples/kmdo.uone.out
   :language: bash
