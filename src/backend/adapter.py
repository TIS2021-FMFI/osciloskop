import time
import subprocess
import threading
import queue
import platform
from typing import Sequence


class Adapter:
    address: int
    out_queue: queue.Queue
    connected: bool = False
    in_cmd_mode: bool = False
    process: subprocess.Popen
    out_thread: threading.Thread
    out_thread_killed: bool = False
    testing: bool = False
    hpctrl_executable: str = "tools/hpctrl/hpctrl.exe"

    def __init__(self, testing: bool):
        self.testing = testing

        if self.testing:
            if platform.system() != "Windows":
                self.hpctrl_executable = "tools/fake_hpctrl/hpctrl"
            else:
                self.hpctrl_executable = "tools/fake_hpctrl/hpctrl.exe"

    def enqueue_output(self):
        out = self.process.stdout
        for line in iter(out.readline, b""):
            if self.out_thread_killed:
                out.close()
                return
            if line:
                self.out_queue.put(line)
            else:
                time.sleep(0.001)
            # nekonecny cyklus, thread vzdy cita z pipe a hadze do out_queue po riadkoch

    def get_output(self, timeout, lines=None):
        out_str = ""
        get_started = time.time()
        line_counter = 0
        while time.time() < get_started + timeout:
            if lines is not None and line_counter >= lines:
                return out_str.strip()
            if self.out_queue.empty():
                time.sleep(0.001)
            else:
                out_str += self.out_queue.get_nowait()
                line_counter += 1

        out_str = out_str.strip()
        if out_str:
            return out_str
        return None

    def clear_input_queue(self):
        while not self.out_queue.empty():
            self.out_queue.get_nowait()

    def start_hpctrl(self):
        try:
            self.process = subprocess.Popen(
                [self.hpctrl_executable, "-i"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except FileNotFoundError:
            # TODO: vypis chybovu hlasu v gui, ze nenaslo hpctrl
            quit()

        self.out_queue = queue.Queue()

        self.out_thread = threading.Thread(target=self.enqueue_output)
        self.out_thread.daemon = True
        self.out_thread.start()
        self.out_thread_killed = False

    def kill_hpctrl(self):
        if self.process is not None:
            self.send("exit")
        if self.out_thread is not None:
            self.out_thread_killed = True
            self.out_thread.join()
            self.out_thread = None
        if self.process is not None:
            self.process.terminate()
            self.process.kill()
            self.process = None
        self.out_queue = None

    def restart_hpctrl(self):
        self.kill_hpctrl()  # moze zase zavolat restart
        self.start_hpctrl()

    # TODO: toto bude zrejme inak
    def hpctrl_is_responsive(self):
        return True
        # self.clear_input_queue()
        # if not self.send("ping"):
        #     return False
        # out = self.get_output(4, 1)
        # if out is None:
        #     self.restart_hpctrl()  # restartujem ho, lebo nereaguje
        #     return False
        # if out.strip() == "!unknown command ping":
        #     return True
        # self.restart_hpctrl()
        # return False

    def send(self, messages):
        _messages = list(map(lambda x: x.strip().lower() + "\n", list(filter(lambda x: len(x) > 0, messages.split("\n")))))
        for message in _messages:
            try:
                print(message, file=self.process.stdin)
                self.process.stdin.flush()
                # TODO toto bolo pri hpctrl zmenene tak otestovat ci funguje bez sleep
                time.sleep(0.1)  # aby HPCTRL stihol spracovat prikaz, inak vypisuje !not ready, try again later (ping)
            except OSError:
                if message != "exit":
                    self.restart_hpctrl()
                return False
        return True

    # TODO: toto bude mozno inak (treba tu cmd mode?)
    def connect(self, address):
        if self.send("LOGON\nOSCI\n" + f"CONNECT {address}"):
            if self.hpctrl_is_responsive():
                # if self.send("CMD"):
                self.address = address
                self.connected = True
                return True
        return False

    def disconnect(self):
        self.send("DISCONNECT")
        self.address = None
        self.connected = False

    def enter_cmd_mode(self):
        if self.connected:
            if not self.in_cmd_mode:
                if self.send("CMD"):
                    self.in_cmd_mode = True
                    return True
                return None
            return True
        return False

    def exit_cmd_mode(self):
        if self.connected:
            if self.in_cmd_mode:
                if self.send("."):
                    self.in_cmd_mode = False
                    return True
                return None
            return True
        return False

    # def cmd_send(self, message):
    #     if self.connected:
    #         if self.in_cmd_mode:
    #             message = message.strip()
    #             message = message.lower()
    #             if message in (".", "cmd", "exit"):
    #                 return True
    #             index = message.find(" ")
    #             if index > 0:
    #                 prve_slovo = message[:message.find(" ")]
    #             else:
    #                 prve_slovo = message
    #             if self.send(f"{message}\n"):
    #                 self.in_cmd_mode = True
    #                 prve_slovo = prve_slovo.strip()
    #                 if prve_slovo in ("q", "a", "c", "d", "b", "?", "help"):
    #                     output = self.get_output(10, 1)
    #                     if output is None:
    #                         return None
    #                     while not self.out_queue.empty():
    #                         riadky = self.get_output(0.2)
    #                         if riadky is not None:
    #                             output += "\n" + riadky
    #                     return output
    #                 return True
    #             else:
    #                 return None
    #         return False
    #     return False
