from distutils.core import setup, Extension

setup(name='dstack',
	version='0.0.01',
    scripts = ['dstack.py'],
	ext_modules=[Extension('_dstack', ['dstack.c'],
        include_dirs = [
            '../chimera/include'],
        extra_objects = ['../chimera/src/libchimera.a'],
        libraries = ['pthread', 'crypto']
    )]
)
