#  Terms Definitions
#  A "Batch Differentiator" is a property that all batches will have, and batches will be organised into time-ordered streams based on this differentiator...
#  e.g. A Batch Differentiator of UserID, batches will be organised into parallel streams with every user having a different stream.
#  ----
from . import queue, datetimeProvider
import threading
from uuid import uuid4
from time import sleep


def default_batch_differentiator_getter(batch):
    print("No batch_differentiator_getter has been set!")
    exit()
    return str()


def default_time_getter(batch):
    print("No time_getter has been set!")
    exit()
    return datetimeProvider.get_current_time()


def default_batch_processor(batch):
    print("No batch_processor has been set!")
    exit()


def testBatchGenerator(batchQuantity):
    identifier = str(uuid4())
    batchBatch = list()
    for x in range(0, batchQuantity):
        batchBatch.append({
            "diff": identifier,
            "time": datetimeProvider.get_current_time()
        })

    return batchBatch


class BatchManager:
    def __init__(self):
        self.batch_differentiator_getter = default_batch_differentiator_getter
        self.time_getter = default_time_getter
        self.batch_processor = None

        self.batchQueue = queue.Queue()

        self.streamLookup = dict()
        self._spawnStreams = False
        self._stream_spawner_thread = None

    def set_batch_differentiator_getter(self, func):
        self.batch_differentiator_getter = func
        return func

    def set_time_getter(self, func):
        self.time_getter = func
        return func

    def set_batch_processor(self, func):
        self.batch_processor = func
        return func

    def receive_batch(self, batch):
        self.batchQueue.insert(batch)

    def start(self):
        self._spawnStreams = True
        self._stream_spawner_thread = threading.Thread(target=self.stream_spawner_thread)
        self._stream_spawner_thread.start()
        print("BatchMan Started!")

    def finishAllBlocking(self):
        stream: BatchStream
        for stream in self.streamLookup.items():
            stream.finish()

        _finished = False
        while not _finished:
            _finished = True
            for stream in self.streamLookup.items():
                if not stream.finished:
                    _finished = False
                else:
                    pass

    def finishAll(self):
        stream: BatchStream
        for stream in self.streamLookup.items():
            stream.finish()

    @property
    def finished(self):
        finished = True
        stream: BatchStream
        for stream in self.streamLookup.items():
            if not stream.finished:
                finished = False
            else:
                pass
        return finished

    def stream_spawner_thread(self):
        for batch in self.batchQueue.iter_gen():
            if self._spawnStreams:
                try:
                    self.streamLookup[self.batch_differentiator_getter(batch)].queueNewBatch(batch)
                except KeyError:
                    self.streamLookup[self.batch_differentiator_getter(batch)] = BatchStream(self.batch_differentiator_getter(batch), self.time_getter, self.batch_processor)
            else:
                break


class BatchStream:
    def __init__(self, differentiator, time_getter, processor_func):
        self.batchQueue = queue.Queue()
        self.batch_processor_func = processor_func
        self.differentiator = differentiator
        self.time_getter = time_getter
        self.last_processed_batch = datetimeProvider.get_current_time()
        print("Stream Spawned!!!", f"Differentiator: {differentiator}")

        self._batch_processing_thread_instance = threading.Thread(target=self._batch_processing_thread, daemon=True)
        self._processing = True
        self.finished = False
        self._batch_processing_thread_instance.start()

    def finish(self):
        self._processing = False

    def restart(self):
        self._processing = True
        self._batch_processing_thread_instance = threading.Thread(target=self._batch_processing_thread, daemon=True)
        self._batch_processing_thread_instance.start()

    def getNextBatch(self):
        self.sortBatchesByTime()
        try:
            return self.batchQueue.next()
        except IndexError:
            return None

    def queueNewBatch(self, batch):
        self.batchQueue.insert(batch)
        self.sortBatchesByTime()
        print("New batch queued!")

    def sortBatchesByTime(self):
        self.batchQueue.queue.sort(key=self.time_getter)

    def _batch_processing_thread(self):
        self.finished = False
        while self._processing:
            nextBatch = self.getNextBatch()
            if nextBatch is None:
                sleep(0.01)
            else:
                self.batch_processor_func(nextBatch)
        self.finished = True
