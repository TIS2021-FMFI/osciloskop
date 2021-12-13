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
        if self.type == "1":
            type = "raw"
        elif self.type == "2":
            type = "average"
        else:
            type = "unknown"
        return f"""Type:\t {type}
Points:\t {self.points}
Count:\t {self.count}
X increment:\t {self.x_increment}
X origin:\t {self.x_origin}
X reference:\t {self.x_reference}
Y increment:\t {self.y_increment}
Y origin:\t {self.y_origin}
Y reference:\t {self.y_reference}
Coupling:\t {self.coupling}
X display range:\t {self.x_display_range}
X display origin:\t {self.x_display_origin}
Y display range:\t {self.x_display_range}
Y display origin:\t {self.y_display_origin}
Date:\t {self.date}
Time:\t {self.time}
Frame:\t {self.frame_model}
Module:\t {self.plug_in_model}
Acq mode:\t {self.acquisition_mode}
Completion:\t {self.completion}
X units:\t {self.x_units}
Y units:\t {self.y_units}
Max bandwidth:\t {self.max_bandwidth_limit}
Min bandwidth:\t {self.min_bandwidth_limit}
"""

class Measurement:
    def __init__(self, preamble, data, channel, reinterpret_trimmed_data=False):
        self.preamble = Preamble(preamble)
        self.channel = channel
        self.data = data.split()
        self.correct_data()

    def correct_data(self):
        _data = []
        for i in self.data:
            _data.append(int(i) * float(self.preamble.y_increment) * float(self.preamble.y_origin))
        self.data = _data

    def __str__(self):
        data = ""
        for i in self.data:
            data += str(i) + "\n"
        return f"{self.preamble.__str__()}\n{data}"

class SingleMeasurement:
    def __init__(self, measurements):
        self.measurements = measurements
 
    def save_to_disc(self, path):
        try:
            os.makedirs(path)
        except FileExistsError:
            pass

        for i in self.measurements:
            with open(os.path.join(path, f"{i.preamble.date[1:-1]}_{i.preamble.time[1:-1]}_{i.channel}"), "w") as f:
                f.writelines(i.__str__())

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