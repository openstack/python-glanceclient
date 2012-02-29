import os
import sys
from setuptools import setup, find_packages

from glanceclient.openstack.common.setup import parse_requirements
from glanceclient.openstack.common.setup import parse_dependency_links
from glanceclient.openstack.common.setup import write_requirements
from glanceclient.openstack.common.setup import write_git_changelog

requires = parse_requirements()
depend_links = parse_dependency_links()
write_requirements()
write_git_changelog()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

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
    install_requires=requires,
    dependency_links=depend_links,

    test_suite = "nose.collector",

    entry_points = {
        'console_scripts': ['glance = glanceclient.shell:main']
    }
)
