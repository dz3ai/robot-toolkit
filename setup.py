from setuptools import setup, Extension
import pybind11

ext = Extension(
    "ik_fast",
    sources=["ik_fast.cpp"],
    include_dirs=[pybind11.get_include()],
    language="c++",
    extra_compile_args=["-O3", "-march=native", "-ffast-math"],
)

setup(
    name="ik_fast",
    version="0.1.0",
    ext_modules=[ext],
)
