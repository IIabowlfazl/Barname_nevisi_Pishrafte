

import argparse
import random
import sys
import time

OPEN_TICKS = 3        # how long the gate stays open after a tap
MOVE_TICKS = 2        # ticks for the motor to open/close
FARE = 2.0            # cost of one trip


class Card:
    # a subway card with a balance
    _next = 1

    def __init__(self, balance=10.0):
        self.cid = Card._next
        Card._next += 1
        self.balance = balance
        self.valid = True

    def charge(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False


class Passenger:
    # a person wanting to pass the gate, holding a card
    def __init__(self, card=None, name=None):
        self.card = card if card else Card()
        self.name = name
        self.passed = False


class Sensor:
    # a presence sensor at the gate (entry or exit side)
    def __init__(self, side):
        self.side = side          # "entry" or "exit"
        self.detected = False

    def sense(self, someone_there):
        self.detected = someone_there
        return self.detected


class Motor:
    # drives the gate bar between closed and open
    def __init__(self):
        self.state = "CLOSED"     # CLOSED, OPEN, OPENING, CLOSING
        self.timer = 0

    def open(self):
        if self.state in ("CLOSED", "CLOSING"):
            self.state = "OPENING"
            self.timer = MOVE_TICKS

    def close(self):
        if self.state in ("OPEN", "OPENING"):
            self.state = "CLOSING"
            self.timer = MOVE_TICKS

    def step(self):
        if self.state == "OPENING":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "OPEN"
        elif self.state == "CLOSING":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "CLOSED"


class Gate:
    # the turnstile: two sensors + a motor
    def __init__(self):
        self.entry = Sensor("entry")
        self.exit = Sensor("exit")
        self.motor = Motor()
        self.busy = False         # a passenger is currently passing

    def is_open(self):
        return self.motor.state == "OPEN"

    def update(self):
        self.motor.step()


class Controller:
    # decides the gate behaviour each tick
    def __init__(self, gate):
        self.gate = gate
        self.open_timer = 0
        self.log = []

    def msg(self, m):
        line = f"[gate] {m}"
        self.log.append(line)
        if len(self.log) > 300:
            self.log = self.log[-300:]
        if self.on_log:
            self.on_log(line)

    def try_pass(self, passenger):
        # called when a passenger taps at the gate
        g = self.gate
        if g.busy or g.is_open():
            self.msg("gate busy, wait")
            return False
        if not passenger.card.valid:
            self.msg(f"card {passenger.card.cid} invalid")
            return False
        if not passenger.card.charge(FARE):
            self.msg(f"card {passenger.card.cid} no balance")
            return False
        g.motor.open()
        g.busy = True
        self.open_timer = OPEN_TICKS
        self.msg(f"passenger passed, card {passenger.card.cid} "
                 f"balance {passenger.card.balance:.1f}")
        passenger.passed = True
        return True

    def update(self):
        g = self.gate
        g.update()
        if g.busy:
            self.open_timer -= 1
            if self.open_timer <= 0:
                g.motor.close()
                g.busy = False


class Sim:
    # top level: holds gate/controller, queues passengers, steps time
    def __init__(self, spawn_rate=0.0):
        self.gate = Gate()
        self.ctrl = Controller(self.gate)
        self.ctrl.on_log = None
        self.clock = 0
        self.spawn_rate = spawn_rate
        self.queue = []
        self.served = 0
        self.on_log = None
        self.ctrl.on_log = self._fwd

    def _fwd(self, line):
        if self.on_log:
            self.on_log(line)

    def add_passenger(self, card_balance=10.0):
        p = Passenger(Card(card_balance))
        self.queue.append(p)
        if self.on_log:
            self.on_log(f"[sim] passenger arrives (card bal {card_balance:.1f})")
        return p

    def step(self):
        self.clock += 1
        if self.spawn_rate > 0 and random.random() < self.spawn_rate:
            self.add_passenger()
        # if someone is waiting and gate free, let them tap
        if self.queue and not self.gate.busy and not self.gate.is_open():
            p = self.queue.pop(0)
            if self.ctrl.try_pass(p):
                self.served += 1
        self.ctrl.update()


def text_frame(sim):
    g = sim.gate
    bar = {
        "CLOSED": "|",
        "OPEN": " ",
        "OPENING": "/",
        "CLOSING": "\\",
    }[g.motor.state]
    q = len(sim.queue)
    return (f"t={sim.clock:04d} gate[{bar}] state={g.motor.state:7s} "
            f"queue={q} served={sim.served}")


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
class GUI:
    def __init__(self, sim, speed_ms=500):
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        self.tk = tk
        self.ttk = ttk
        self.scrolledtext = scrolledtext
        self.sim = sim
        sim.on_log = self._append
        self.speed_ms = speed_ms
        self.running = True
        self.auto = False

        self.root = tk.Tk()
        self.root.title("Subway Gate Simulator")
        self.root.configure(bg="#0b1021")

        self.canvas = tk.Canvas(self.root, width=420, height=260,
                                bg="#0b1021", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=6, pady=6)

        panel = tk.Frame(self.root, bg="#11182f", width=300)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        panel.pack_propagate(False)

        tk.Label(panel, text="SUBWAY GATE", fg="#7fd1ff", bg="#11182f",
                 font=("Consolas", 13, "bold")).pack(pady=(6, 10))

        req = tk.LabelFrame(panel, text="Actions", fg="#9fb3d1",
                            bg="#11182f", font=("Consolas", 10))
        req.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(req, text="Card balance", fg="#cdd9ef", bg="#11182f").pack(
            side=tk.LEFT)
        self.bal = tk.DoubleVar(value=10.0)
        ttk.Entry(req, textvariable=self.bal, width=6).pack(
            side=tk.LEFT, padx=4)
        ttk.Button(req, text="Send Passenger", command=self._send).pack(
            fill=tk.X, padx=4, pady=2)
        ttk.Button(req, text="Send No-Balance", command=self._send_broke).pack(
            fill=tk.X, padx=4, pady=2)

        simf = tk.LabelFrame(panel, text="Simulation", fg="#9fb3d1",
                             bg="#11182f", font=("Consolas", 10))
        simf.pack(fill=tk.X, padx=6, pady=4)
        self.btn_pause = ttk.Button(simf, text="Pause",
                                    command=self._toggle)
        self.btn_pause.pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(simf, text="Step Once", command=self._step).pack(
            fill=tk.X, padx=4, pady=2)
        ttk.Button(simf, text="Reset", command=self._reset).pack(
            fill=tk.X, padx=4, pady=2)
        au = tk.Frame(simf, bg="#11182f")
        au.pack(fill=tk.X, padx=4, pady=2)
        self.a_var = tk.BooleanVar(value=False)
        tk.Checkbutton(au, text="Auto Arrivals", fg="#cdd9ef", bg="#11182f",
                       selectcolor="#11182f", variable=self.a_var,
                       command=self._auto).pack(side=tk.LEFT)

        st = tk.LabelFrame(panel, text="Stats", fg="#9fb3d1",
                           bg="#11182f", font=("Consolas", 10))
        st.pack(fill=tk.X, padx=6, pady=4)
        self.lbl = {}
        for k in ("Clock", "Served", "Queue", "Gate"):
            f = tk.Frame(st, bg="#11182f")
            f.pack(fill=tk.X, padx=4, pady=1)
            tk.Label(f, text=f"{k}:", fg="#8aa0c6", bg="#11182f", width=10,
                     anchor=tk.W).pack(side=tk.LEFT)
            v = tk.Label(f, text="-", fg="#e8f0ff", bg="#11182f", anchor=tk.W,
                         font=("Consolas", 9))
            v.pack(side=tk.LEFT)
            self.lbl[k] = v

        logf = tk.LabelFrame(panel, text="Log", fg="#9fb3d1",
                             bg="#11182f", font=("Consolas", 10))
        logf.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.log_box = self.scrolledtext.ScrolledText(
            logf, bg="#06101f", fg="#bfe9c8", font=("Consolas", 8),
            state=tk.DISABLED, height=10)
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._loop()

    def start(self):
        self.root.mainloop()

    def _send(self):
        self.sim.add_passenger(self.bal.get())
        self.render()

    def _send_broke(self):
        self.sim.add_passenger(0.0)
        self.render()

    def _toggle(self):
        self.running = not self.running
        self.btn_pause.configure(text="Resume" if not self.running else "Pause")

    def _step(self):
        self.sim.step()
        self.render()

    def _reset(self):
        self.sim.queue.clear()
        self.sim.served = 0
        self.sim.gate = Gate()
        self.sim.ctrl = Controller(self.sim.gate)
        self.sim.ctrl.on_log = self.sim._fwd
        self.sim.clock = 0
        self.render()

    def _auto(self):
        self.auto = self.a_var.get()
        self.sim.spawn_rate = 0.4 if self.auto else 0.0

    def _append(self, line):
        try:
            self.log_box.configure(state=self.tk.NORMAL)
            self.log_box.insert(self.tk.END, line + "\n")
            self.log_box.see(self.tk.END)
            self.log_box.configure(state=self.tk.DISABLED)
        except Exception:
            pass

    def _loop(self):
        if self.running:
            self.sim.step()
        self.render()
        self.root.after(self.speed_ms, self._loop)

    def render(self):
        try:
            self._draw()
            self.lbl["Clock"].configure(text=str(self.sim.clock))
            self.lbl["Served"].configure(text=str(self.sim.served))
            self.lbl["Queue"].configure(text=str(len(self.sim.queue)))
            self.lbl["Gate"].configure(text=self.sim.gate.motor.state)
        except Exception:
            pass

    def _draw(self):
        tk = self.tk
        c = self.canvas
        c.delete("all")
        W = 420
        cx = W // 2
        # gate posts
        c.create_rectangle(cx - 70, 40, cx - 60, 220, fill="#3a4a66")
        c.create_rectangle(cx + 60, 40, cx + 70, 220, fill="#3a4a66")
        # the moving bar
        st = self.sim.gate.motor.state
        if st == "CLOSED":
            c.create_rectangle(cx - 60, 120, cx + 60, 140, fill="#ff5b5b")
        elif st == "OPEN":
            c.create_rectangle(cx - 60, 60, cx + 60, 80, fill="#39d98a")
        elif st == "OPENING":
            c.create_rectangle(cx - 60, 90, cx + 60, 110, fill="#ffd23f")
        else:
            c.create_rectangle(cx - 60, 150, cx + 60, 170, fill="#ffd23f")
        # waiting passengers as dots
        for i in range(min(len(self.sim.queue), 8)):
            c.create_oval(cx - 110 - i * 14, 200, cx - 96 - i * 14, 214,
                         fill="#5aa9ff", outline="#0b1021")
        c.create_text(cx, 30, text=f"Gate: {st}", fill="#cfe0ff",
                      font=("Consolas", 11, "bold"))


def run_terminal(sim, ticks=200, delay=0.25):
    print("terminal mode: Ctrl+C to stop\n")
    try:
        for _ in range(ticks):
            sim.step()
            print(text_frame(sim))
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nstopped")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Subway Gate Simulator")
    ap.add_argument("--terminal", action="store_true")
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--delay", type=float, default=0.25)
    ap.add_argument("--spawn-rate", type=float, default=0.4)
    ap.add_argument("--no-spawn", action="store_true")
    a = ap.parse_args(argv)

    if a.terminal:
        rate = 0.0 if a.no_spawn else a.spawn_rate
        sim = Sim(spawn_rate=rate)
        run_terminal(sim, ticks=a.ticks, delay=a.delay)
        return

    sim = Sim(spawn_rate=0.0)
    try:
        g = GUI(sim, speed_ms=500)
        if a.no_spawn:
            g.auto = False
            g.a_var.set(False)
        elif a.spawn_rate > 0:
            g.auto = True
            g.a_var.set(True)
            sim.spawn_rate = a.spawn_rate
        g.start()
    except Exception as e:
        print(f"[warn] gui failed ({e}), terminal fallback")
        run_terminal(sim, ticks=a.ticks, delay=a.delay)


if __name__ == "__main__":
    main()
