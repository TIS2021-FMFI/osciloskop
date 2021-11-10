import frontend.gui as fr
import backend.adapter as ada

if __name__ == "__main__":
    a = ada.Adapter(True)

    a.start_hpctrl()
    a.connect(7)
    a.enter_cmd_mode()
    a.send("q aaaaa")
    a.exit_cmd_mode()
    a.disconnect()

    # fr.run()
