# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                '..', '..')))

# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'openstackdocstheme',
    'sphinxcontrib.apidoc',
]

# sphinxcontrib.apidoc options
apidoc_module_dir = '../../glanceclient'
apidoc_output_dir = 'reference/api'
apidoc_excluded_paths = [
    'tests/*',
    'tests']
apidoc_separate_modules = True

# openstackdocstheme options
openstackdocs_repo_name = 'openstack/python-glanceclient'
openstackdocs_bug_project = 'python-glanceclient'
openstackdocs_bug_tag = ''

# autodoc generation is a bit aggressive and a nuisance when doing heavy
# text edit cycles.
# execute "export SPHINX_DEBUG=1" in your terminal to disable

# TODO: remove this once no dependency uses six anymore
autodoc_mock_imports = ['six']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'python-glanceclient'
copyright = 'OpenStack Foundation'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'native'

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
#html_theme = 'nature'
html_theme = 'openstackdocs'

# Output file base name for HTML help builder.
htmlhelp_basename = '%sdoc' % project


# -- Options for man page output ----------------------------------------------

# Grouping the document tree for man pages.
# List of tuples 'sourcefile', 'target', 'title', 'Authors name', 'manual'
man_pages = [
    ('cli/glance', 'glance', 'Client for OpenStack Images API',
     ['OpenStack Foundation'], 1),
]
