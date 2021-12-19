import time
import subprocess
import threading
import queue
import platform
import os


class AdapterError(Exception):
    pass

class Adapter:
    address: int
    out_queue: queue.Queue = None
    connected: bool = False
    in_cmd_mode: bool = False
    process: subprocess.Popen = None
    out_thread: threading.Thread = None
    out_thread_killed: bool = False
    testing: bool = False
    hpctrl_executable: str = "tools/hpctrl/hpctrl"
    cmd_leave_cmd: str = "."
    cmd_enter_cmd: str = "cmd"
    cmd_disconnect: str = "DISCONNECT"
    cmd_logon: str = "LOGON"
    cmd_osci: str = "OSCI"
    cmd_connect: str = "CONNECT"
    cmd_exit: str = "exit"
    cmd_idn: str = "q *IDN?"
    cmd_idn_response: str = "HEWLETT-PACKARD,83480A,US35240110,07.12"

    def __init__(self, testing):
        self.testing = testing
        if platform.system() == "Windows":
            self.hpctrl_executable += ".exe"

        if self.testing:
            self.hpctrl_executable = self.hpctrl_executable.replace("hpctrl", "fake_hpctrl", 1)

        if not os.path.isfile(self.hpctrl_executable):
            raise AdapterError("hpctrl executable not found")

    def enqueue_output(self):
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

    def get_output(self, timeout):
        """
        returns output from hpctrl as str. Timeout arg is in seconds.
        It also calls self.clear_input_queue() before it finishes
        """
        out_str = ""
        get_started = time.time()

        while not self.out_queue.empty():
            if time.time() > get_started + timeout:
                raise AdapterError(f"timeout error: the operation took longer than {timeout} seconds")
            out_str += self.out_queue.get_nowait()

        self.clear_input_queue()
        
        res = out_str.strip()
        if not res:
            raise AdapterError("got empty string as response from hpctrl")
        return res

    def clear_input_queue(self):
        """
        clears self.out_queue
        """
        while not self.out_queue.empty():
            self.out_queue.get_nowait()

    def start_hpctrl(self):
        """
        starts hpctrl with the -i flag
        """
        if self.is_hpctrl_running():
            return

        self.process = subprocess.Popen(
            [self.hpctrl_executable, "-i"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        self.out_queue = queue.Queue()

        self.out_thread = threading.Thread(target=self.enqueue_output)
        self.out_thread.daemon = True
        self.out_thread.start()
        self.out_thread_killed = False

    def kill_hpctrl(self):
        """
        sends exit command to hpctrl or kills it if it's frozen
        """
        if self.process is not None:
            self.send([self.cmd_exit])
            # maybe we'll have to sleep here for a few ms
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
        """
        calls self.kill_hpctrl() and then self.start_hpctrl()
        """
        self.kill_hpctrl()
        self.start_hpctrl()

    def is_hpctrl_running(self):
        """returns True if hpctrl is running"""
        return all([self.process, self.out_thread, self.out_queue])

    def is_osci_responsive(self):
        """
        returns True if oscilloscope responds "HEWLETT-PACKARD,83480A,US35240110,07.12" to "q *IDN?" command
        """
        return self.send_and_get_output([self.cmd_idn], 0.2) == self.cmd_idn_response

    def send(self, messages, clean_output_after=True):
        """
        prints messages into self.process.stdin
        """
        if not self.is_hpctrl_running():
            raise AdapterError("hpctrl is not running")
        if isinstance(messages, list):  
            messages = "\n".join(messages)
        try:
            print(messages, file=self.process.stdin)
            self.process.stdin.flush()
            # TODO toto bolo pri hpctrl zmenene tak otestovat ci funguje bez sleep
            time.sleep(0.1)  # aby HPCTRL stihol spracovat prikaz, inak vypisuje !not ready, try again later (ping)
        except OSError:
            if messages != self.cmd_exit:
                raise AdapterError("could not send the command")
        
        if clean_output_after:
            self.clear_input_queue()

    def send_and_get_output(self, messages, timeout):
        """
        calls self.send(messages) and then self.get_output(timeout, lines)
        """
        self.send(messages, False)
        return self.get_output(timeout)

    def connect(self, address):
        """
        connets with LOGON, OSCI, CONNECT {address} commands
        """
        self.send([self.cmd_logon, self.cmd_osci, f"{self.cmd_connect} {address}"])
        self.address = address
        self.connected = True

    def disconnect(self):
        """
        disconnets with DISCONNECT command if possible
        """
        if not self.connected:
            return
        self.send([self.cmd_disconnect])
        self.address = None
        self.connected = False

    def enter_cmd_mode(self):
        """
        enters cmd mode with CMD command if possible
        """
        if not self.connected or self.in_cmd_mode:
            return
        self.send([self.cmd_enter_cmd])
        self.in_cmd_mode = True

    def exit_cmd_mode(self):
        """
        exits cmd mode with . command if possible
        """
        if not self.connected or not self.in_cmd_mode:
            return
        self.send([self.cmd_leave_cmd])
        self.in_cmd_mode = False
