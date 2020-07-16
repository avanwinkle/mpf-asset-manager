"""MPF Asset Manager (mpfam) setup.py"""
from setuptools import setup

setup(
  name="mpfam",
  version="0.0.1",
  description="MPF Asset Manager",
  long_description="""
    The MPF Asset Manager is a tool for importing, exporting, and
    organizing the audio and video assets of a Mission Pinball project.
  """,
  url="https://github.com/avanwinkle/mpf-asset-manager",
  author="Anthony van Winkle",
  author_email="mpf@anthonyvanwinkle.com",
  license="MIT",
  packages=['mpfam'],
  install_requires=['mpf','pysoundfile','numpy'],
  entry_points={
    'console_scripts': [
      'mpfam = mpfam.mpfam:launch'
    ]
  }
)
