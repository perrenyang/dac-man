from cache import Cache

# StreamSource Implementation
class BasicStreamSrc(object):
    def __init__(self, host, port):
        self.cache = Cache(host, port)
        self.dataset_iterator = None

        self.stats_dir = None

    def set_stats_dir(self, stats_dir):
        self.stats_dir = stats_dir

    def set_dataset_iterator(self, fn):
        self.dataset_iterator = fn

    def data_send(self, datablocks):
        datablock_ids = self.cache.put_multi_datablocks(datablocks)
        cache.create_task(*datablock_ids)

    def stream(self, *stream_args):
        '''
        Main Streaming Engine
        '''
        if not self.dataset_iterator:
            raise ValueError("dataset_iterator must be set")

        stream_gen = dataset_iterator(*stream_args)

        try:
            datablock_1 = next(stream_gen)
            while True:
                datablock_2 = next(stream_gen)
                self.data_send(datablock_1, datablock_2)
                datablock_1 = datablock_2
        except StopIteration:
            break

        if self.stats_dir is not None:
            cache.write_stats(self.stats_dir)


# WindowedStreamSrc Implementation
class WindowedStreamSrc(BasicStreamSrc):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.window_key = None
        self.window_size = 2
        # measurement of interest
        # ex: data_row["CO2"]
        self.measurement = None

    def set_window_key(self, window_key):
        self.window_key = window_key

    def set_window_size(self, window_size):
        self.window_size = window_size

    def set_measurement(self, measurement):
        self.measurement = measurement

    def data_send(self, win_key, datablocks):
        datablock_ids = self.cache.put_multi_datablocks(datablocks)
        self.cache.assign_datablocks_to_window(win_key, datablock_ids)

        n_datablocks = self.cache.get_current_window_size(win_key)
        if n_datablocks == self.window_size:
            datablock_ids = cache.get_windowed_datablock_ids(win_key)
            assert len(datablock_ids) == self.window_size,
                "Actual window size: %d > intended window size: %d" \
                    % (self.cache.get_current_window_size(win_key), self.window_size)
            cache.create_task(*datablock_ids)

    def get_window_key(self, row):
        window_key = row[self.window_key]
        return window_key

    def stream(self, *stream_args):
        '''
        Main Streaming Engine
        '''
        if not self.window_key:
            raise ValueError("window key must be set")

        if not self.measurement:
            raise ValueError("measurement field must be set")

        if not self.dataset_iterator:
            raise ValueError("dataset_iterator must be set")

        stream_gen = dataset_iterator(*stream_args)

        for datablock in stream_gen:
            window_key_val = self.get_window_key(datablock)
            self.data_send(window_key_val, [datablock[measurement]])

        if self.stats_dir is not None:
            cache.write_stats(self.stats_dir)
