# Panja
[![build status](https://circleci.com/gh/samgriesemer/panja.svg?style=shield)](https://circleci.com/gh/samgriesemer/panja)

**Note**: At the moment, this repo and README are mostly for myself. While the main
site-building core is rather general, the surrounding utilities in this repository are
mostly customized for my use case, which is building a static site from Jinja templates
and Markdown files that are wikilinked among themselves. This doesn't mean you can't use
this repo to suit your needs, but for the time being it's less general than I'd like.

# Introduction
Panja is a simple, extendable file conversion pipeline builder written in Python. The name
"panja" comes from the two primary tools used for file conversion and templating: [Pan]doc
and Jin[ja], respectively. At its core, the goal of the library is to make it easy to
piece together custom pipelines for for processing and converting files. One of the
simplest examples of this is a basic static site renderer, taking Jinja template theme
files and rendering a collection of pages (along with other static files).

# Static site builder
The main `Site` object is a custom fork of the `staticjinja` repo. Here we extend the site
builder in a few key ways:

- Enabling multiple search paths (instead of just one), ultimately "gluing" together the
  local structure in each directory to yield the final structure of the output directory.
  This ensures you can link in files across your file system to be a part of the final
  site that would otherwise not be possible under a single directory (even with symlinks).
- Using `livereload` for watching, serving, and autoreloading content. The in-built
  `reloader` object of `staticjinja` has many drawbacks, and is unable to detect
  certain types of changes to files. The `livereload` library provides a much more
  convenient and reliable API for serving and watching content in directories, and has the
  added benefit of being able to live reload the browser window when the underlying
  content changes. This is incredibly convenient for live development or note taking,
  where it's helpful to see the final rendered output immediately without intervention
  (i.e. manually reloading a webpage). This `livereload` library replaces the default
  reloader inside of the `Site` core.

# Note processing utilities
Panja also provides a collection of useful utilities for processing note files. This
begins with the `Article` object, which is responsible for extracting metadata from
Markdown files, applying transformations to the underlying content, and converting to
other files types (e.g. HTML, PDF, etc).

The `Graph` object operates on a collection of notes stored in a directory, and aims to
provide useful global tools for the files and their relations. Right now its primary
purpose is to produce a graph representation of wikilinks networked across files, yielding
a JSON edge list for downstream tasks. It also extracts backlinked content around these
links

# Setup/installation
Panja can be installed by first cloning this repo into the desired working directory.
Then create a Python virtual environment:

```
python3 -m venv panja_env
```

and install the local library with

```
pip install -e panja
```

To set up your build process, create a `build.py` file (or copy/start from one in
`examples/`). This is where you will instantiate a `Site` object, provide your search
paths, and define any custom context generators or compilation rules. You will then render
the site to the output directory, further specifying if you'd like to watch, serve, and/or
autoreload browser pages when files change on disk.
