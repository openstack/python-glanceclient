import os
import sys
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requirements = ['httplib2', 'prettytable']
if sys.version_info < (2, 6):
    requirements.append('simplejson')
if sys.version_info < (2, 7):
    requirements.append('argparse')

setup(
    name = "python-glanceclient",
    version = "2012.1",
    description = "Client library for OpenStack Glance API",
    long_description = read('README.rst'),
    url = 'https://github.com/openstack/python-glanceclient',
    license = 'Apache',
    author = 'Jay Pipes, based on work by Rackspace and Jacob Kaplan-Moss',
    author_email = 'jay.pipes@gmail.com',
    packages = find_packages(exclude=['tests', 'tests.*']),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires = requirements,

    tests_require = ["nose", "mock", "mox"],
    test_suite = "nose.collector",

    entry_points = {
        'console_scripts': ['glance = glanceclient.shell:main']
    }
)
