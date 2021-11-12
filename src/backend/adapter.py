import time
import subprocess
import threading
import queue
import platform


class Adapter:
    address: int
    out_queue: queue.Queue
    connected: bool = False
    in_cmd_mode: bool = False
    process: subprocess.Popen
    out_thread: threading.Thread
    out_thread_killed: bool = False
    testing: bool = False
    hpctrl_executable: str = "tools/hpctrl/hpctrl"

    def __init__(self, testing: bool) -> None:
        self.testing = testing
        if platform.system() == "Windows":
            self.hpctrl_executable += ".exe"

        if self.testing:
            self.hpctrl_executable = self.hpctrl_executable.replace("hpctrl", "fake_hpctrl", 1)

    def enqueue_output(self) -> None:
        """
        reads what hpctrl is saying on stdout into self.out_queue line by line
        """
        out = self.process.stdout
        for line in iter(out.readline, b""):
            if self.out_thread_killed:
                out.close()
                return
            if line:
                self.out_queue.put(line)
            else:
                time.sleep(0.001)

    def get_output(self, timeout: float, lines: int) -> str:
        """
        returns output from hpctrl as str. Returns empty string if there was no output.
        Timeout arg is in seconds and lines arg is number of lines to be returned
        """
        out_str = ""
        get_started = time.time()
        line_counter = 0

        while (time.time() < get_started + timeout) and line_counter < lines:
            if self.out_queue.empty():
                time.sleep(0.001)
            else:
                out_str += self.out_queue.get_nowait()
                line_counter += 1

        self.clear_input_queue()

        out_str = out_str.strip()
        return out_str

    def clear_input_queue(self) -> None:
        """
        clears self.out_queue
        """
        while not self.out_queue.empty():
            self.out_queue.get_nowait()

    def start_hpctrl(self) -> bool:
        """
        starts hpctrl and returns true if it was successful
        """
        try:
            self.process = subprocess.Popen(
                [self.hpctrl_executable, "-i"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except FileNotFoundError:
            return False
            # maybe we'll have to quit() here

        self.out_queue = queue.Queue()

        self.out_thread = threading.Thread(target=self.enqueue_output)
        self.out_thread.daemon = True
        self.out_thread.start()
        self.out_thread_killed = False

        return True

    def kill_hpctrl(self) -> None:
        """
        kills running hpctrl
        """
        if self.process is not None:
            self.send(["exit"])
        if self.out_thread is not None:
            self.out_thread_killed = True
            self.out_thread.join()
            self.out_thread = None
        # TODO: ma zmysel ze horna a dolna podmienka je rovnaka?
        if self.process is not None:
            self.process.terminate()
            self.process.kill()
            self.process = None
        self.out_queue = None

    def restart_hpctrl(self) -> None:
        """
        calls self.kill_hpctrl() and then self.start_hpctrl()
        """
        self.kill_hpctrl()
        self.start_hpctrl()

    # TODO: toto bude zrejme inak
    def hpctrl_is_responsive(self):
        return True
        # self.clear_input_queue()
        # if not self.send(["ping"]):
        #     return False
        # out = self.get_output(4, 1)
        # if out is None:
        #     self.restart_hpctrl()  # restartujem ho, lebo nereaguje
        #     return False
        # if out.strip() == "!unknown command ping":
        #     return True
        # self.restart_hpctrl()
        # return False

    def send(self, messages: list[str]) -> bool:
        """
        prints messages into self.process.stdin. Returns True if it was successful.
        If it fails it also restarts hpctrl
        """
        message_string = "\n".join(messages)
        try:
            print(message_string, file=self.process.stdin)
            self.process.stdin.flush()
            # TODO toto bolo pri hpctrl zmenene tak otestovat ci funguje bez sleep
            time.sleep(0.1)  # aby HPCTRL stihol spracovat prikaz, inak vypisuje !not ready, try again later (ping)
        except OSError:
            if message_string != "exit":
                self.restart_hpctrl()
                return False
        return True

    def send_and_get_output(self, messages: list[str], timeout: float, lines: int) -> str:
        """
        calls self.send(messages) and then self.get_output(timeout, lines).
        Returns empty string if there was no output.
        """
        if not self.send(messages):
            return ""
        return self.get_output(timeout, lines)

    def connect(self, address: int) -> bool:
        """
        connets with LOGON, OSCI, CONNECT {address} commands. Returns True if successful
        """
        if not self.hpctrl_is_responsive or not self.send(["LOGON", "OSCI", f"CONNECT {address}"]):
            return False
        self.address = address
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """
        disconnets with DISCONNECT command if possible. Returns True if successful
        """
        if not self.connect:
            return True
        if self.send(["DISCONNECT"]):
            self.address = None
            self.connected = False
            return True
        return False

    def enter_cmd_mode(self) -> bool:
        """
        enters cmd mode with CMD command if possible. Returns True if successful
        """
        if not self.connected:
            return False
        if self.in_cmd_mode:
            return True
        if self.send(["CMD"]):
            self.in_cmd_mode = True
            return True
        return False

    def exit_cmd_mode(self) -> bool:
        """
        exits cmd mode with . command if possible. Returns True if successful
        """
        if not self.connected:
            return False
        if not self.in_cmd_mode:
            return True
        if self.send(["."]):
            self.in_cmd_mode = False
            return True
        return False

    # def cmd_send(self, message: str):
    #     if not self.connected or not self.in_cmd_mode:
    #         return False
    #     message = message.strip().lower()
    #     if message in (".", "cmd", "exit"):
    #         return True
    #     index = message.find(" ")
    #     prve_slovo = message[:index] if index > 0 else message
    #     if not self.send([f"{message}"]):
    #         return None

    #     self.in_cmd_mode = True
    #     if prve_slovo in ("q", "a", "c", "d", "b", "?", "help"):
    #         output = self.get_output(10, 1)
    #         if output is None:
    #             return None
    #         while not self.out_queue.empty():
    #             riadky = self.get_output(0.2)
    #             if riadky is not None:
    #                 output += "\n" + riadky
    #         return output
    #     return True
