# -*- coding:utf-8 -*-

"""
Simple static page generator.

Uses Jinja2 to compile templates.
"""

import inspect
import logging
import os
import re
import shutil
import warnings

from jinja2 import Environment, FileSystemLoader
from livereload import Server


def _has_argument(func):
    """Test whether a function expects an argument.

    :param func:
        The function to be tested for existence of an argument.
    """
    if hasattr(inspect, 'signature'):
        # New way in python 3.3
        sig = inspect.signature(func)
        return bool(sig.parameters)
    else:
        # Old way
        return bool(inspect.getargspec(func).args)


class Site(object):
    """The Site object.

    :param environment:
        A :class:`jinja2.Environment`.

    :param searchpaths:
        A string representing the name of the directory to search for
        templates.

    :param contexts:
        A list of `regex, context` pairs. Each context is either a dictionary
        or a function that takes either no argument or or the current template
        as its sole argument and returns a dictionary. The regex, if matched
        against a filename, will cause the context to be used.

    :param rules:
        A list of *(regex, function)* pairs. The Site will delegate
        rendering to *function* if *regex* matches the name of a template
        during rendering. *function* must take a :class:`staticjinja.Site`
        object, a :class:`jinja2.Template`, and a context dictionary as
        parameters and render the template. Defaults to ``[]``.

    :param encoding:
        The encoding of templates to use.

    :param logger:
        A logging.Logger object used to log events.

    :param staticpaths:
        List of directory names to get static files from.

    :param mergecontexts:
        A boolean value. If set to ``True``, then all matching regex from the
        contexts list will be merged (in order) to get the final context.
        Otherwise, only the first matching regex is used. Defaults to
        ``False``.
    """

    def __init__(self,
                 environment,
                 searchpaths,
                 outpath,
                 encoding,
                 logger,
                 contexts=None,
                 rules=None,
                 staticpaths=None,
                 basepath=None,
                 mergecontexts=False,
                 ):
        self.env = environment
        self.searchpaths = searchpaths
        self.outpath = outpath
        self.encoding = encoding
        self.logger = logger
        self.contexts = contexts or []
        self.rules = rules or []
        self.staticpaths = staticpaths or []
        self.basepath = basepath
        self.mergecontexts = mergecontexts

    @classmethod
    def make_site(cls,
                  searchpaths=["templates"],
                  outpath=".",
                  contexts=None,
                  rules=None,
                  encoding="utf8",
                  followlinks=True,
                  extensions=None,
                  staticpaths=None,
                  basepath=None,
                  filters={},
                  env_globals={},
                  env_kwargs=None,
                  mergecontexts=False):
        """Create a :class:`Site <Site>` object.

        :param searchpaths:
            A list of absolute paths to directories that the Site should
            search to discover templates. Defaults to ``['templates']``.

            If any of the provided paths are relative, it will be coerced to
            an absolute path by prepending the directory name of the calling
            module. For example, if you invoke staticjinja using ``python
            build.py`` in directory ``/foo``, then *searchpaths* will be
            ``['/foo/templates']``.

        :param outpath:
            A string representing the name of the directory that the Site
            should store rendered files in. Defaults to ``'.'``.

        :param contexts:
            A list of *(regex, context)* pairs. The Site will render templates
            whose name match *regex* using *context*. *context* must be either
            a dictionary-like object or a function that takes either no
            arguments or a single :class:`jinja2.Template` as an argument and
            returns a dictionary representing the context. Defaults to ``[]``.

        :param rules:
            A list of *(regex, function)* pairs. The Site will delegate
            rendering to *function* if *regex* matches the name of a template
            during rendering. *function* must take a :class:`staticjinja.Site`
            object, a :class:`jinja2.Template`, and a context dictionary as
            parameters and render the template. Defaults to ``[]``.

        :param encoding:
            A string representing the encoding that the Site should use when
            rendering templates. Defaults to ``'utf8'``.

        :param followlinks:
            A boolean describing whether symlinks in searchpaths should be
            followed or not. Defaults to ``True``.

        :param extensions:
            A list of :ref:`Jinja extensions <jinja-extensions>` that the
            :class:`jinja2.Environment` should use. Defaults to ``[]``.

        :param staticpaths:
            List of directories to get static files from. Like searchpaths,
            these may be absolute or relative. If relative, the path will be
            coerced to an absolute in the same manner as search paths are.
            Defaults to ``None``.

        :param basepath:
            A string  specifying the absolute or relative path that
            `searchpaths` and `outpath` should be taken relative to, if they
            themselves are relative. 

            An absolute search path or outpath will be unaffected by any
            basepath value. However, if any search or output path is relative,
            the basepath will be the path assumed that those paths are
            relative to. If no basepath is supplied, then it is assumed to be
            the current directory from which make_site is called.

        :param filters:
            A dictionary of Jinja2 filters to add to the Environment.  Defaults
            to ``{}``.

        :param env_globals:
            A mapping from variable names that should be available all the time
            to their values. Defaults to ``{}``.

        :param env_kwargs:
            A dictionary that will be passed as keyword arguments to the
            jinja2 Environment. Defaults to ``{}``.

        :param mergecontexts:
            A boolean value. If set to ``True``, then all matching regex from
            the contexts list will be merged (in order) to get the final
            context.  Otherwise, only the first matching regex is used.
            Defaults to ``False``.
        """
        # TODO: Determine if there is a better way to write do this
        calling_module = inspect.getmodule(inspect.stack()[-1][0])
        project_path = os.path.realpath(os.path.dirname(
            calling_module.__file__))

        # update basepath if not supplied or relative
        if basepath is None:
            basepath = project_path
        else:
            if not os.path.isabs(basepath):
                basepath = os.path.join(project_path, basepath)

        # make any relative search paths absolute
        for i, searchpath in enumerate(searchpaths):
            if not os.path.isabs(searchpath):
                searchpaths[i] = os.path.join(basepath, searchpath)

        # update relative outpath
        if not os.path.isabs(outpath):
            outpath = os.path.join(basepath, outpath)

        if env_kwargs is None:
            env_kwargs = {}
        env_kwargs['loader'] = FileSystemLoader(searchpath=searchpaths,
                                                encoding=encoding,
                                                followlinks=followlinks)
        env_kwargs.setdefault('extensions', extensions or [])
        environment = Environment(**env_kwargs)
        environment.filters.update(filters)
        environment.globals.update(env_globals)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler())
        return cls(environment,
                   searchpaths=searchpaths,
                   outpath=outpath,
                   encoding=encoding,
                   logger=logger,
                   rules=rules,
                   contexts=contexts,
                   staticpaths=staticpaths,
                   basepath=basepath,
                   mergecontexts=mergecontexts,
                   )

    @property
    def template_names(self):
        return self.env.list_templates(filter_func=self.is_template)

    @property
    def templates(self):
        """Generator for templates."""
        for template_name in self.template_names:
            yield self.get_template(template_name)

    @property
    def static_names(self):
        return self.env.list_templates(filter_func=self.is_static)

    def get_template(self, template_name):
        """Get a :class:`jinja2.Template` from the environment.

        :param template_name: A string representing the name of the template.
        """
        try:
            return self.env.get_template(template_name)
        except UnicodeDecodeError as e:
            raise UnicodeError('Unable to decode %s: %s' % (template_name, e))

    def get_context(self, template):
        """Get the context for a template.

        If no matching value is found, an empty context is returned.
        Otherwise, this returns either the matching value if the value is
        dictionary-like or the dictionary returned by calling it with
        *template* if the value is a function.

        If several matching values are found, the resulting dictionaries will
        be merged before being returned if mergecontexts is True. Otherwise,
        only the first matching value is returned.

        :param template: the template to get the context for
        """
        context = {}
        for regex, context_generator in self.contexts:
            if re.match(regex, template.name):
                if inspect.isfunction(context_generator):
                    if _has_argument(context_generator):
                        context.update(context_generator(self, template))
                    else:
                        context.update(context_generator())
                else:
                    context.update(context_generator)

                if not self.mergecontexts:
                    break
        return context

    def get_rule(self, template_name):
        """Find a matching compilation rule for a function.

        Raises a :exc:`ValueError` if no matching rule can be found.

        :param template_name: the name of the template
        """
        for regex, render_func in self.rules:
            if re.match(regex, template_name):
                return render_func
        raise ValueError("no matching rule")

    def is_static(self, filename):
        """Check if a file is a static file. Static files are copied, rather
        than compiled using Jinja2.

        A file is considered static if it lives in any of the directories
        specified in ``staticpaths``.

        :param filename: the name of the file to check

        """
        return any(filename.startswith(path) for path in self.staticpaths)

    def is_partial(self, filename):
        """Check if a file is a partial. Partial files are not rendered,
        but they are used in rendering templates.

        A file is considered a partial if it or any of its parent directories
        are prefixed with an ``'_'``.

        :param filename: the name of the file to check
        """
        return any((x.startswith("_") for x in filename.split(os.path.sep)))

    def is_ignored(self, filename):
        """Check if a file is an ignored file. Ignored files are neither
        rendered nor used in rendering templates.

        A file is considered ignored if it or any of its parent directories
        are prefixed with an ``'.'``.

        :param filename: the name of the file to check
        """
        return any((x.startswith(".") for x in filename.split(os.path.sep)))

    def is_template(self, filename):
        """Check if a file is a template.

        A file is a considered a template if it is not partial, ignored, or
        static.

        :param filename: the name of the file to check
        """
        if self.is_partial(filename):
            return False
        if self.is_ignored(filename):
            return False
        if self.is_static(filename):
            return False
        return True

    def _ensure_dir(self, template_name):
        """Ensure the output directory for a template exists."""
        head = os.path.dirname(template_name)
        if head:
            file_dirpath = os.path.join(self.outpath, head)
            if not os.path.exists(file_dirpath):
                os.makedirs(file_dirpath)

    def render_template(self, template, context=None, filepath=None):
        """Render a single :class:`jinja2.Template` object.

        If a Rule matching the template is found, the rendering task is
        delegated to the rule.

        :param template:
            A :class:`jinja2.Template` to render.

        :param context:
            Optional. A dictionary representing the context to render
            *template* with. If no context is provided, :meth:`get_context` is
            used to provide a context.

        :param filepath:
            Optional. A file or file-like object to dump the complete template
            stream into. Defaults to to ``os.path.join(self.outpath,
            template.name)``.

        """
        self.logger.info("Rendering %s..." % template.name)

        if context is None:
            context = self.get_context(template)

        if not os.path.exists(self.outpath):
            os.makedirs(self.outpath)
        self._ensure_dir(template.name)

        try:
            rule = self.get_rule(template.name)
        except ValueError:
            if filepath is None:
                filepath = os.path.join(self.outpath, template.name)
            template.stream(**context).dump(filepath, self.encoding)
        else:
            rule(self, template, **context)

    def render_templates(self, templates, filepath=None):
        """Render a collection of :class:`jinja2.Template` objects.

        :param templates:
            A collection of Templates to render.

        :param filepath:
            Optional. A file or file-like object to dump the complete template
            stream into. Defaults to to ``os.path.join(self.outpath,
            template.name)``.

        """
        for template in templates:
            self.render_template(template, filepath)

    def copy_static(self, files):
        for f in files:
            input_location = None

            # find associated search path for static file
            for searchpath in self.searchpaths:
                fpath = os.path.join(searchpath, f)
                if os.path.isfile(fpath):
                    input_location = fpath
                    break

            if input_location is None:
                raise Exception("Static file {} has no matching search \
                        path".format(f))

            output_location = os.path.join(self.outpath, f)
            self.logger.info("Copying %s to output." % f)
            self._ensure_dir(f)
            shutil.copy2(input_location, output_location)

    def get_dependencies(self, filename):
        """Get a list of files that depends on the file named *filename*.

        :param filename: the name of the file to find dependencies of
        """
        if self.is_partial(filename):
            return self.templates
        elif self.is_template(filename):
            return [self.get_template(filename)]
        elif self.is_static(filename):
            return [filename]
        else:
            return []

    def render(self, build=True, server=False, reloader=False, liveport=False):
        """Generate the site. A number of options may be specified to control the behavior
        of site's build process and downstream access to output files. 

        :param build:    Build the site, rendering the files from search paths to the
                         output path. Default = True
        :param server:   Serve the files using a simple HTTP request handler. Does nothing
                         more than sit on top of the output path and serve those file.
        :param reloader: Watch and reload files that change in the search paths. These
                         changed files will be reprocessed according the compilation rules
                         of the site object.
        :param liveport: Start a livereload server, which automatically reloads a browser
                         tab (which is current accessing the site files) when a file
                         changes in the output directory. Unless you plan to modify the
                         files that are in the output path directly, this option should
                         almost always be paired with `--reloader` to ensure changes to
                         the unprocessed files get processed, pushed to the output
                         directory, and liveport recognizes the change.

        Note that these options can and should be used together in many cases. Note that
        some combinations are redundant, namely specifying either `reloader` or `liveport`
        AND `server; both of the former options require the later implicitly. However,
        this is not true the other way around, and both `reloader` and `liveport` are
        independent of each other.
        """
        if build:
            self.render_templates(self.templates)
            self.copy_static(self.static_names)
        
        if server or reloader or liveport:
            server = Server()

        if reloader:
            self.logger.info("Watching '%s' for changes..." %
                             self.searchpaths)
            self.logger.info("Press Ctrl+C to stop.")

            # add searchpaths to watch list, need to be globs
            for searchpath in self.searchpaths:
                server.watch(os.path.join(searchpath, '*'), self.watch_handler)

        if server or liveport:
            port = 8000
            liveport = 35729
            if not liveport:
                server.serve(port=port, host='0.0.0.0', root=self.outpath)
            else:
                server.serve(port=port, host='0.0.0.0', root=self.outpath, liveport=liveport)

    def watch_handler(self, files):
        spaths = []
        for f in files:
            spath = None
            for searchpath in self.searchpaths:
                if f.startswith(searchpath):
                    spath = searchpath
                    break
            spaths.append((f, spath))

        for f, spath in spaths:
            if spath is None:
                raise Exception('Couldn\'t find overlapping search path \
                                for file with path {}'.format(f))

        for f, spath in spaths:
            filename = os.path.relpath(f, spath)
            if self.is_static(filename):
                files = self.get_dependencies(filename)
                self.copy_static(files)
            else:
                templates = self.get_dependencies(filename)
                self.render_templates(templates)

    def __repr__(self):
        return "%s('%s', '%s')" % (type(self).__name__,
                                   self.searchpaths, self.outpath)


