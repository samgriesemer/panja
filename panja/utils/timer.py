from datetime import datetime

class Timer:
    def __init__(self):
        self.start_time = None
        self.wait       = None

    def start(self, wait):
        if self.is_done() == False: return None
        self.wait = wait
        self.start_time = datetime.now().timestamp()

    def is_done(self):
        time_left = self.time_left()
        if time_left is not None:
            return time_left <= 0
        return True

    def time_left(self):
        if self.start_time is None or self.wait is None:
            return None
        return self.wait-(datetime.now().timestamp()-self.start_time)

def debounce_func(func, delay):
    timer = Timer()
    def temp(*args):
        if not timer.is_done(): return
        func(*args)
        timer.start(delay)
    temp.__name__ = func.__name__
    return temp
