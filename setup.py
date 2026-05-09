from setuptools import setup, Extension
import pybind11

ext_ik = Extension(
    "ik_fast",
    sources=["ik_fast.cpp"],
    include_dirs=[pybind11.get_include()],
    language="c++",
    extra_compile_args=["-O3", "-march=native", "-ffast-math"],
)

ext_dyn = Extension(
    "robot_dyn_fast",
    sources=["robot_dyn_fast.cpp"],
    include_dirs=[pybind11.get_include()],
    language="c++",
    extra_compile_args=["-O3", "-march=native", "-ffast-math"],
)

setup(
    name="robot-ik",
    version="0.2.0",
    ext_modules=[ext_ik, ext_dyn],
)
