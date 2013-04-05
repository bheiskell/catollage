Catollage
=========

Create a collage of an image using a set of images! For example, make a cat out of other cats!

.. image:: images/example.jpg

Install
-------

For some reason, pysci is complaining about not having numpy. Although numpy in declared earlier in the setup.py, that doesn't seem to resolve the issue. To fix, install numpy explicitly first.

::

  git clone https://github.com/bheiskell/catollage.git
  cd catollage
  virtualenv --no-site-packages venv
  . venv/bin/activate
  pip install numpy .

Packages
~~~~~~~~

You will need to install some packages on the system for PIL image processing and PySci's implementation of K-D trees.
