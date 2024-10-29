"""Define the modules for the :class:`.Envelope1D` beam calculator.

It is a 1d envelope calculator, with two implementations. The first one is in
pure Python. The second one, :class:`.CyEnvelope1D`, is in Cython. It is
faster, but require a compilation. Check out :file:`setup.py`.

"""
