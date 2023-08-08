# -*- coding: utf-8 -*-
#
# kmdo documentation build configuration file
#
import os
import sys

on_rtd = os.environ.get("READTHEDOCS", None) == "True"

extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.imgmath",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

project = "kmdo"
copyright = "2023, SAFL"

version = "1.0.5"
release = "1.0.5"

exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

if not on_rtd:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ["_static"]
htmlhelp_basename = "kmdodoc"
