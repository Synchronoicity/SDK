class Queue:
    def __init__(self):
        self.queue: list = list()

    def insert(self, item):
        self.queue.append(item)

    def next(self):
        return self.queue.pop(0)

    def join(self, *queues):
        for queue in queues:
            self.queue = self.queue + queue.queue

    def pop(self, index):
        return self.queue.pop(index)

    def iter_gen(self):
        while True:
            try:
                yield self.next()
            except IndexError:
                pass

    def __len__(self):
        return len(self.queue)
