from distutils.core import setup, Extension

setup(name='chimera',
	version='1.2.00',
    scripts = ['chimera.py'],
	ext_modules=[Extension('_chimera', ['chimera_wrap.c'],
        include_dirs = ['../include'],
        extra_objects = ['../src/libchimera.a'],
        libraries = ['pthread', 'crypto']
    )]
)
