from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy as np

sourcefiles = ["geometry.pyx"]

setup(
    name="geometry",
    cmdclass={"build_ext": build_ext},
    ext_modules=[Extension("geometry", sourcefiles, include_dirs=[np.get_include()])],
)
