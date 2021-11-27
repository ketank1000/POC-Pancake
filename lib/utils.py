import time

class MeasureTime:
    def __init__(self, task):
        self.start = time.time()
        self.task = task
    def kill(self):
        print (f'Time elapsed ({self.task}): ' + time.strftime("%H:%M:%S", time.gmtime(time.time()-self.start)))
        del self