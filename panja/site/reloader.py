import os


class Reloader(object):
    """
    Watches ``site.searchpath`` for changes and re-renders any changed
    Templates.

    :param site:
        A :class:`Site <Site>` object.

    """
    def __init__(self, site):
        self.site = site

    @property
    def searchpaths(self):
        return self.site.searchpaths

    def should_handle(self, event_type, filename):
        """Check if an event should be handled.

        An event should be handled if a file in the searchpath was modified.

        :param event_type: a string, representing the type of event

        :param filename: the path to the file that triggered the event.
        """
        return (event_type in ("modified", "created") and
                os.path.isfile(filename))

    def event_handler(self, event_type, src_path):
        """Re-render templates if they are modified.

        :param event_type: a string, representing the type of event

        :param src_path: the path to the file that triggered the event.

        """
        spath = None
        for searchpath in self.searchpaths:
            if src_path.startswith(searchpath):
                spath = searchpath
                break

        if spath is None:
            raise Exception('Couldn\'t find overlapping search path \
                            for file with path {}'.format(src_path))

        filename = os.path.relpath(src_path, spath)
        if self.should_handle(event_type, src_path):
            print("%s %s" % (event_type, filename))
            if self.site.is_static(filename):
                files = self.site.get_dependencies(filename)
                self.site.copy_static(files)
            else:
                templates = self.site.get_dependencies(filename)
                self.site.render_templates(templates)

    def watch(self):
        """Watch and reload modified templates."""
        #import easywatch
        #for searchpath in self.searchpaths:
            #easywatch.watch(searchpath, self.event_handler)
        #easywatch.watch(self.searchpaths[0], self.event_handler)
        owatch(self.searchpaths, self.event_handler)

def owatch(paths, handler):
    import functools
    import time

    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    # let the user just deal with events
    @functools.wraps(handler)
    def wrapper(self, event):
        if not event.is_directory:
            return handler(event.event_type, event.src_path)
    attrs = {'on_any_event': wrapper}
    EventHandler = type("EventHandler", (FileSystemEventHandler,), attrs)
    observer = Observer()
    for path in paths:
        observer.schedule(EventHandler(), path=path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
