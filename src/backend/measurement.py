import os


class Preamble:
    def __init__(self, data):
        self.parse(data)

    def parse(self, data):
        _data = data.split(",")
        # _data[1] is format
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
        self.milliseconds = ""
        try:
            self.milliseconds = _data[25]
        except IndexError:
            pass

    def __str__(self):
        if self.type == "1":
            type = "raw"
        elif self.type == "2":
            type = "average"
        else:
            type = "unknown"
        res = f"""Type:\t {type}
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
Min bandwidth:\t {self.min_bandwidth_limit}"""
        if self.milliseconds:
            res += f"\nNumber of milliseconds from first measurement:\t {self.milliseconds}"
        res += "\n"
        return res


class Measurement:
    def __init__(self, preamble, data, channel, reinterpret_trimmed_data):
        self.preamble = Preamble(preamble)
        self.channel = channel
        self.reinterpret_trimmed_data = reinterpret_trimmed_data
        self.clipped_high = 32256
        self.clipped_low = 31744
        self.max_valid = 30720
        self.min_valid = -32736
        self.hole = 31232
        self.hole_corrected = "HOLE"
        self.data = self.correct_data(data)

    def correct_data(self, data):
        _data = []
        for i in data.split():
            word_value = int(i)
            if self.reinterpret_trimmed_data:
                if word_value == self.clipped_high:
                    word_value = self.max_valid
                elif word_value == self.clipped_low:
                    word_value = self.min_valid
                elif word_value == self.hole:
                    word_value = self.hole_corrected
            if word_value != self.hole_corrected:
                word_value = word_value * float(self.preamble.y_increment) + float(
                    self.preamble.y_origin
                )
            _data.append(word_value)
        return _data

    def __str__(self):
        data = "".join(str(i) + "\n" for i in self.data)
        return f"{self.preamble.__str__()}\n{data}"

    def append_ms_to_preamble(self, ms):
        self.preamble.milliseconds = ms


class Measurements:
    measurements = None

    class FileName:
        def __init__(self, measurement):
            self.date = measurement.preamble.date[1:-1]
            self.time = measurement.preamble.time[1:-1]
            self.channel = measurement.channel
            self.n = 0
            self.extension = ".txt"

        def increase_n(self):
            self.n += 1

        def __str__(self):
            n = "" if self.n == 0 else f"({self.n})"
            return f"{self.date}_{self.time}_ch{self.channel}{n}{self.extension}".replace(":", "-")

    def save_to_disk(self, path):
        try:
            os.makedirs(path)
        except FileExistsError:
            pass

        for i in self.measurements:
            file = self.FileName(i)
            while os.path.isfile(os.path.join(path, str(file))):
                file.increase_n()
            with open(os.path.join(path, str(file)), "w") as f:
                f.writelines(str(i))

    def get_ms_and_data(self, line):
        first_space = line.index(" ")
        return (line[:first_space], line[first_space + 1 :])


class SingleMeasurements(Measurements):
    def __init__(self, measurements):
        self.measurements = measurements


class MultipleMeasurementsNoPreambles(Measurements):
    def __init__(self, file_path, preamble, channels, reinterpret_trimmed_data):
        """
        channels should be string, e.g. "23"
        """
        self.file_path = file_path
        self.preamble = preamble
        self.channels = channels
        self.reinterpret_trimmed_data = reinterpret_trimmed_data
        self.measurements = self.parse_file()

    def parse_file(self):
        measurements = []

        with open(self.file_path, "r") as f:
            for i, line in enumerate(f):
                ms, data = self.get_ms_and_data(line)
                measurement = Measurement(
                    self.preamble,
                    data,
                    self.channels[i % len(self.channels)],
                    self.reinterpret_trimmed_data,
                )
                measurement.append_ms_to_preamble(ms)
                measurements.append(measurement)

        return measurements


class MultipleMeasurementsWithPreambles(Measurements):
    def __init__(self, file_path, channels, reinterpret_trimmed_data):
        """
        channels should be string, e.g. "23"
        """
        self.file_path = file_path
        self.channels = channels
        self.reinterpret_trimmed_data = reinterpret_trimmed_data
        self.measurements = self.parse_file()

    def parse_file(self):
        measurements = []

        with open(self.file_path, "r") as f:
            preamble = None
            channel_index = 0
            for i, line in enumerate(f):
                if i % 2 == 0:
                    preamble = line.strip()
                else:
                    ms, data = self.get_ms_and_data(line)
                    measurement = Measurement(
                        preamble, data, self.channels[channel_index], self.reinterpret_trimmed_data
                    )
                    measurement.append_ms_to_preamble(ms)
                    measurements.append(measurement)
                    if channel_index > len(self.channels) - 2:
                        channel_index = 0
                    else:
                        channel_index += 1

        return measurements
