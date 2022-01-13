import os
import PySimpleGUI as sg
from datetime import datetime


class Preamble:
    def __init__(self, data):
        self.preamble_dict = self.parse(data)

    def parse(self, data):
        _data = data.split(",")
        type = _data[1]
        if type == "1":
            type = "raw"
        elif type == "2":
            type = "average"
        else:
            type = "unknown"
        preamble_dict = {
            'Type': type,
            'Points': _data[2],
            'Count': _data[3],
            'X increment': _data[4],
            'X origin': _data[5],
            'X reference': _data[6],
            'Y increment': _data[7],
            'Y origin': _data[8],
            'Y reference': _data[9],
            'Coupling': _data[10],
            'X display range': _data[11],
            'X display origin': _data[12],
            'Y display range': _data[13],
            'Y display origin': _data[14],
            'Date': _data[15],
            'Time': _data[16],
            'Frame': _data[17],
            'Module': _data[18],
            'Acq mode': _data[19],
            'Completion': _data[20],
            'X units': _data[21],
            'Y units': _data[22],
            'Max bandwidth': _data[23],
            'Min bandwidth': _data[24],
        }
        if len(_data) == 25+1:
            preamble_dict["Number of microseconds from the first measurement"] = _data[25]
        return preamble_dict

    def __str__(self):
        return "".join(f"{key}:\t {val}\n" for key, val in self.preamble_dict.items())


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
        p_dict = self.preamble.preamble_dict
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
                word_value = word_value * float(p_dict["Y increment"]) + float(
                    p_dict["Y origin"]
                )
            _data.append(word_value)
        return _data

    def __str__(self):
        data = "".join(str(i) + "\n" for i in self.data)
        return f"{self.preamble.__str__()}\n{data}"

    def append_us_to_preamble(self, us):
        self.preamble.preamble_dict["Number of microseconds from the first measurement"] = us


class Measurements:
    measurements = None

    def __init__(self, file_path, channels, reinterpret_trimmed_data, saving_gui_text: sg.Text):
        self.file_path = file_path
        self.channels = channels
        self.reinterpret_trimmed_data = reinterpret_trimmed_data
        self.saving_gui_text = saving_gui_text
    
    class FileName:
        def __init__(self, channel):
            self.channel = channel
            self.extension = ".txt"

        def __str__(self):
            now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S-%f")
            return f"{now}_ch{self.channel}{self.extension}"

    def save_to_disk(self, path):
        try:
            os.makedirs(path)
        except FileExistsError:
            pass

        for i, measurement in enumerate(self.measurements):
            file = self.FileName(measurement.channel)
            with open(os.path.join(path, str(file)), "w") as f:
                f.write(str(measurement))
            self.saving_gui_text.update(value=f"Saving {i}/{len(self.measurements)}")

    def get_us_and_data(self, line):
        first_space = line.index(" ")
        return (line[:first_space], line[first_space + 1 :])


class SingleMeasurements(Measurements):
    def __init__(self, measurements, saving_gui_text: sg.Text):
        self.measurements = measurements
        self.saving_gui_text = saving_gui_text



class MultipleMeasurementsNoPreambles(Measurements):

    def __init__(self, file_path, preambles, channels, reinterpret_trimmed_data, saving_gui_text: sg.Text):
        """
        channels should be string, e.g. "23"
        """
        super().__init__(file_path, channels, reinterpret_trimmed_data, saving_gui_text)
        self.preambles = preambles
        self.measurements = self.parse_file()

    def parse_file(self):
        measurements = []

        with open(self.file_path, "r") as f:
            self.saving_gui_text.update(value="Reading temp.txt")
            for i, line in enumerate(f):
                us, data = self.get_us_and_data(line)
                measurement = Measurement(
                    self.preambles[i % len(self.channels)],
                    data,
                    self.channels[i % len(self.channels)],
                    self.reinterpret_trimmed_data,
                )
                measurement.append_us_to_preamble(us)
                measurements.append(measurement)

        return measurements


class MultipleMeasurementsWithPreambles(Measurements):

    def __init__(self, file_path, channels, reinterpret_trimmed_data, saving_gui_text: sg.Text):
        """
        channels should be string, e.g. "23"
        """
        super().__init__(file_path, channels, reinterpret_trimmed_data, saving_gui_text)
        self.measurements = self.parse_file()

    def parse_file(self):
        measurements = []

        with open(self.file_path, "r") as f:
            self.saving_gui_text.update(value="Reading temp.txt")
            preamble = None
            channel_index = 0
            for i, line in enumerate(f):
                if i % 2 == 0:
                    preamble = line.strip()
                    continue
                us, data = self.get_us_and_data(line)
                measurement = Measurement(
                    preamble, data, self.channels[channel_index], self.reinterpret_trimmed_data
                )
                measurement.append_us_to_preamble(us)
                measurements.append(measurement)
                if channel_index > len(self.channels) - 2:
                    channel_index = 0
                else:
                    channel_index += 1

        return measurements
