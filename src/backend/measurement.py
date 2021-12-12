import os

class Preamble:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.parse()

    def parse(self):
        _data = self.raw_data.split(",")
        # format
        self.type = _data[1]
        self.points = _data[2]
        self.count = _data[3]
        self.x_increment = _data[4]
        self.x_origin = _data[5]
        self.x_reference = _data[6]
        self.y_increment = _data[7]
        self.y_origin = _data[8]
        self.y_reference = _data[9]
        self.coupling = _data[10]
        self.x_display_range = _data[11]
        self.x_display_origin = _data[12]
        self.y_display_range = _data[13]
        self.y_display_origin = _data[14]
        self.date = _data[15]
        self.time = _data[16]
        self.frame_model = _data[17]
        self.plug_in_model = _data[18]
        self.acquisition_mode = _data[19]
        self.completion = _data[20]
        self.x_units = _data[21]
        self.y_units = _data[22]
        self.max_bandwidth_limit = _data[23]
        self.min_bandwidth_limit = _data[24]
    
    def __str__(self):
        type = ""
        if self.type == 1:
            type = "raw"
        elif self.type == 2:
            type = "average"
        else:
            type = "unknown"
        return f"""Type:\t {type}\n
        Points:\t {self.points}\n
        Count:\t {self.count}\n
        X increment:\t {self.x_increment}\n
        X origin:\t {self.x_origin}\n
        X reference:\t {self.x_reference}\n
        Y increment:\t {self.y_increment}\n
        Y origin:\t {self.y_origin}\n
        Y reference:\t {self.y_reference}\n
        Coupling:\t {self.coupling}\n
        X display range:\t {self.x_display_range}\n
        X display origin:\t {self.x_display_origin}\n
        Y display range:\t {self.x_display_range}\n
        Y display origin:\t {self.y_display_origin}\n
        Date:\t {self.date}\n
        Time:\t {self.time}\n
        Frame:\t {self.frame_model}\n
        Module:\t {self.plug_in_model}\n
        Acq mode:\t {self.acquisition_mode}\n
        Completion:\t {self.completion}\n
        X units:\t {self.x_units}\n
        Y units:\t {self.y_units}\n
        Max bandwidth:\t {self.max_bandwidth_limit}\n
        Min bandwidth:\t {self.min_bandwidth_limit}\n
        """

class Measurement:
    def __init__(self, preamble, data, channel):
        self.preamble = preamble
        self.channel = channel
        self.data = data.split()
        self.correct_data()

    def correct_data(self):
        _data = []
        for i in self.data:
            _data.append(i * self.preamble.y_increment * self.preamble.y_origin)
        self.data = _data

class SingleMeasurement:
    def __init__(self, measurements):
        self.measurements = measurements
 
    def save_to_disc(self, path, dir_name):
        _path = os.path.join(path, dir_name)
        os.makedirs(_path)

        for i in self.measurements:
            with open(os.path.join(_path, f"{i.preamble.date}_{i.preamble.time}_{i.channel}"), "w") as f:
                f.writelines(i.preamble + i.data)

class MultipleMeasurementsNoPreambles:
    def __init__(self):
        ...

    def save_to_disc(self, path, dir_name):
        ...

class MultipleMeasurementsWithPreambles:
    def __init__(self):
        ...

    def save_to_disc(self, path, dir_name):
        ...