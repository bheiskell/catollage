"""Setup script for cat-monotage."""
from setuptools import setup

# http://stackoverflow.com/questions/9352656/python-assertionerror-when-running-nose-tests-with-coverage
from multiprocessing import util #pylint: disable=W0611

setup(
    name = "Catollage",
    version = "1.0.0",
    author = "Ben Heiskell",
    author_email = "ben.heiskell@xdxa.org",
    description = "Create a collage of an image using a set of images.",
    keywords = "collage",
    license='MIT',
    long_description=open('README.rst').read(),
    packages=['catollage'],
    url = "http://github.com/bheiskell/catollage",
    include_package_data = True,
    entry_points = {
        'console_scripts': [
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        'Flask==0.9',
        'Pillow==2.0.0',
        'numpy==1.7.0',
        'scipy==0.11.0',
    ],
    test_suite='nose.collector',
    tests_require=['nose', 'mock==1.0.1'],
)
