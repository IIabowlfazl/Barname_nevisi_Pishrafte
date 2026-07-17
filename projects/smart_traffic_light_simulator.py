
import argparse
import random
import sys
import time


DIRS = ["N", "S", "E", "W"]

GROUP = {"N": "NS", "S": "NS", "E": "EW", "W": "EW"}

# timing settings (in ticks)
MIN_GREEN = 4          # shortest green we allow
MAX_GREEN = 20         # longest green we allow
ALPHA = 1.0            # green ticks added per waiting car (then capped)
YELLOW_TIME = 2        # yellow clearance between phases
PASS_PER_TICK = 2      # cars that cross per lane per tick on green
DEFAULT_SPAWN = 0.30   # chance per tick a car shows up (if auto on)


class Car:
    # a vehicle waiting at an approach, wanting to leave via another direction
    _next = 1

    def __init__(self, origin, dest, arrival):
        self.cid = Car._next
        Car._next += 1
        self.origin = origin
        self.dest = dest
        self.arrival = arrival
        self.served = None     # tick it crossed
        self.wait = 0.0        # served - arrival


class TrafficLight:
    # one signal for one approach
    def __init__(self, direction):
        self.direction = direction
        self.state = "RED"     # RED / GREEN / YELLOW

    def set(self, s):
        self.state = s


class Lane:
    # the queue of cars waiting on one approach
    def __init__(self, direction):
        self.direction = direction
        self.queue = []

    def add(self, car):
        self.queue.append(car)

    def count(self):
        return len(self.queue)

    def clear(self):
        self.queue.clear()


class Stats:
    def __init__(self):
        self.total_requests = 0
        self.served = 0
        self.total_wait = 0.0

    def record_request(self):
        self.total_requests += 1

    def record_served(self, car):
        self.served += 1
        self.total_wait += car.wait

    @property
    def avg_wait(self):
        return self.total_wait / self.served if self.served else 0.0


class Controller:
    # decides phasing. green/yellow times are set by the user (manual control)
    def __init__(self, inter, green_time=10, yellow_time=YELLOW_TIME):
        self.it = inter
        self.green_time = green_time      # set by user
        self.yellow_time = yellow_time     # set by user
        self.adaptive = False              # bonus mode, off unless ticked
        self.phase = "NS"      # which group is green: NS or EW
        self.sub = "GREEN"     # GREEN or YELLOW
        self.timer = 0
        self.set_phase("NS")

    def demand(self, phase):
        if phase == "NS":
            return self.it.lanes["N"].count() + self.it.lanes["S"].count()
        return self.it.lanes["E"].count() + self.it.lanes["W"].count()

    def set_timings(self, green_time, yellow_time):
        # called from the GUI when the user changes the sliders
        self.green_time = max(1, int(green_time))
        self.yellow_time = max(1, int(yellow_time))
        if self.sub == "GREEN":
            self.timer = self.green_time

    def set_phase(self, phase):
        self.phase = phase
        self.sub = "GREEN"
        if self.adaptive:
            green = int(min(MAX_GREEN, MIN_GREEN + ALPHA * self.demand(phase)))
        else:
            green = self.green_time
        self.timer = green
        for d in DIRS:
            grp = GROUP[d]
            self.it.lights[d].set("GREEN" if grp == phase else "RED")
        self.it.log(f"phase {phase} GREEN for {green} (adaptive={self.adaptive})")

    def update(self):
        self.timer -= 1
        if self.sub == "GREEN":
            self._serve(self.phase)
            if self.timer <= 0:
                # switch to yellow clearance
                self.sub = "YELLOW"
                self.timer = self.yellow_time
                for d in DIRS:
                    self.it.lights[d].set("YELLOW")
                self.it.log("all yellow")
        elif self.sub == "YELLOW":
            if self.timer <= 0:
                nxt = "EW" if self.phase == "NS" else "NS"
                self.set_phase(nxt)

    def _serve(self, phase):
        # let queued cars cross from the green group's approaches
        grp = ("N", "S") if phase == "NS" else ("E", "W")
        for d in grp:
            lane = self.it.lanes[d]
            moved = 0
            while lane.queue and moved < PASS_PER_TICK:
                c = lane.queue.pop(0)
                c.served = self.it.clock
                c.wait = c.served - c.arrival
                self.it.stats.record_served(c)
                moved += 1


class Intersection:
    # the whole junction: 4 lanes, 4 lights, the controller
    def __init__(self, spawn_rate=0.0):
        self.lanes = {d: Lane(d) for d in DIRS}
        self.lights = {d: TrafficLight(d) for d in DIRS}
        self.clock = 0
        self.spawn_rate = spawn_rate
        self.stats = Stats()
        self.on_log = None
        self._log = []
        self.controller = Controller(self)
        self.log("intersection ready")

    def log(self, msg):
        line = f"[t={self.clock:04d}] {msg}"
        self._log.append(line)
        if len(self._log) > 500:
            self._log = self._log[-500:]
        if self.on_log:
            self.on_log(line)

    def total_waiting(self):
        return sum(self.lanes[d].count() for d in DIRS)

    def add_car(self, origin, dest):
        if origin == dest:
            return None
        if origin not in DIRS or dest not in DIRS:
            return None
        c = Car(origin, dest, self.clock)
        self.lanes[origin].add(c)
        self.stats.record_request()
        self.log(f"car {c.cid} {origin}->{dest}")
        return c

    def spawn_random(self):
        o = random.choice(DIRS)
        d = random.choice([x for x in DIRS if x != o])
        self.add_car(o, d)

    def step(self):
        self.clock += 1
        if self.spawn_rate > 0 and random.random() < self.spawn_rate:
            self.spawn_random()
        self.controller.update()

    def reset(self):
        self.clock = 0
        for d in DIRS:
            self.lanes[d].clear()
        self.controller = Controller(self)
        self.stats = Stats()
        self.log("reset")



class GUI:
    def __init__(self, inter, speed_ms=400):
        import tkinter as tk
        from tkinter import ttk, scrolledtext

        self.tk = tk
        self.ttk = ttk
        self.scrolledtext = scrolledtext
        self.it = inter
        inter.on_log = self._append_log

        self.speed_ms = speed_ms
        self.running = True
        self.auto_spawn = False

        self.root = tk.Tk()
        self.root.title("Smart Traffic Light Simulator - 4 Way")
        self.root.configure(bg="#0b1021")

        self._build()
        inter.log("auto spawn OFF. add cars manually or tick Auto Spawn.")
        self._loop()

    def start(self):
        self.root.mainloop()

    def _build(self):
        tk = self.tk
        ttk = self.ttk
        main = tk.Frame(self.root, bg="#0b1021")
        main.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main, width=460, height=460,
                                bg="#0b1021", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=6, pady=6)

        panel = tk.Frame(main, bg="#11182f", width=300)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        panel.pack_propagate(False)

        tk.Label(panel, text="TRAFFIC CONTROL", fg="#7fd1ff", bg="#11182f",
                 font=("Consolas", 13, "bold")).pack(pady=(6, 10))

        # add car
        req = tk.LabelFrame(panel, text="Add Car", fg="#9fb3d1",
                            bg="#11182f", font=("Consolas", 10))
        req.pack(fill=tk.X, padx=6, pady=4)
        row = tk.Frame(req, bg="#11182f")
        row.pack(pady=4)
        tk.Label(row, text="From", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.o_var = tk.StringVar(value="N")
        ttk.Combobox(row, textvariable=self.o_var, values=DIRS, width=4,
                     state="readonly").pack(side=tk.LEFT, padx=4)
        tk.Label(row, text="To", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.d_var = tk.StringVar(value="S")
        ttk.Combobox(row, textvariable=self.d_var, values=DIRS, width=4,
                     state="readonly").pack(side=tk.LEFT, padx=4)
        ttk.Button(req, text="Add Car", command=self._add).pack(
            fill=tk.X, padx=4, pady=2)
        ttk.Button(req, text="Add Random Car", command=self._add_rand).pack(
            fill=tk.X, padx=4, pady=2)

        # sim controls
        sim = tk.LabelFrame(panel, text="Simulation", fg="#9fb3d1",
                            bg="#11182f", font=("Consolas", 10))
        sim.pack(fill=tk.X, padx=6, pady=4)
        self.btn_pause = ttk.Button(sim, text="Pause", command=self._toggle)
        self.btn_pause.pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(sim, text="Step Once", command=self._step).pack(
            fill=tk.X, padx=4, pady=2)
        ttk.Button(sim, text="Reset", command=self._reset).pack(
            fill=tk.X, padx=4, pady=2)
        spd = tk.Frame(sim, bg="#11182f")
        spd.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(spd, text="Speed(ms)", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.spd_var = tk.IntVar(value=self.speed_ms)
        ttk.Scale(spd, from_=100, to=1000, orient=tk.HORIZONTAL,
                  variable=self.spd_var, command=self._spd).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        auto = tk.Frame(sim, bg="#11182f")
        auto.pack(fill=tk.X, padx=4, pady=2)
        self.a_var = tk.BooleanVar(value=False)
        tk.Checkbutton(auto, text="Auto Spawn Cars", fg="#cdd9ef", bg="#11182f",
                        selectcolor="#11182f", variable=self.a_var,
                        command=self._auto).pack(side=tk.LEFT)

        # light timing control (the core requirement)
        tm = tk.LabelFrame(panel, text="Light Timing", fg="#9fb3d1",
                           bg="#11182f", font=("Consolas", 10))
        tm.pack(fill=tk.X, padx=6, pady=4)
        gf = tk.Frame(tm, bg="#11182f")
        gf.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(gf, text="Green", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.green_var = tk.IntVar(value=self.it.controller.green_time)
        ttk.Scale(gf, from_=1, to=30, orient=tk.HORIZONTAL,
                  variable=self.green_var, command=self._green).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.green_lbl = tk.Label(gf, text=str(self.it.controller.green_time),
                                  fg="#e8f0ff", bg="#11182f", width=3)
        self.green_lbl.pack(side=tk.LEFT)
        yf = tk.Frame(tm, bg="#11182f")
        yf.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(yf, text="Yellow", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.yellow_var = tk.IntVar(value=self.it.controller.yellow_time)
        ttk.Scale(yf, from_=1, to=10, orient=tk.HORIZONTAL,
                  variable=self.yellow_var, command=self._yellow).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.yellow_lbl = tk.Label(yf, text=str(self.it.controller.yellow_time),
                                   fg="#e8f0ff", bg="#11182f", width=3)
        self.yellow_lbl.pack(side=tk.LEFT)
        adp = tk.Frame(tm, bg="#11182f")
        adp.pack(fill=tk.X, padx=4, pady=2)
        self.adp_var = tk.BooleanVar(value=False)
        tk.Checkbutton(adp, text="Adaptive (bonus)", fg="#cdd9ef", bg="#11182f",
                       selectcolor="#11182f", variable=self.adp_var,
                       command=self._adp).pack(side=tk.LEFT)
        st = tk.LabelFrame(panel, text="Statistics", fg="#9fb3d1",
                           bg="#11182f", font=("Consolas", 10))
        st.pack(fill=tk.X, padx=6, pady=4)
        self.lbl = {}
        for k in ("Clock", "Served", "Waiting", "Avg Wait", "Phase"):
            f = tk.Frame(st, bg="#11182f")
            f.pack(fill=tk.X, padx=4, pady=1)
            tk.Label(f, text=f"{k}:", fg="#8aa0c6", bg="#11182f", width=12,
                     anchor=tk.W).pack(side=tk.LEFT)
            v = tk.Label(f, text="-", fg="#e8f0ff", bg="#11182f", anchor=tk.W,
                         font=("Consolas", 9))
            v.pack(side=tk.LEFT)
            self.lbl[k] = v

        logf = tk.LabelFrame(panel, text="Event Log", fg="#9fb3d1",
                             bg="#11182f", font=("Consolas", 10))
        logf.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.log_box = self.scrolledtext.ScrolledText(
            logf, bg="#06101f", fg="#bfe9c8", font=("Consolas", 8),
            state=tk.DISABLED, height=10)
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    # callbacks
    def _add(self):
        self.it.add_car(self.o_var.get(), self.d_var.get())
        self.render()

    def _add_rand(self):
        o = random.choice(DIRS)
        d = random.choice([x for x in DIRS if x != o])
        self.it.add_car(o, d)
        self.render()

    def _toggle(self):
        self.running = not self.running
        self.btn_pause.configure(text="Resume" if not self.running else "Pause")

    def _step(self):
        self.it.step()
        self.render()

    def _reset(self):
        self.it.reset()
        self.render()

    def _spd(self, *_):
        self.speed_ms = self.spd_var.get()

    def _green(self, *_):
        v = int(self.green_var.get())
        self.green_lbl.configure(text=str(v))
        self.it.controller.set_timings(v, self.yellow_var.get())

    def _yellow(self, *_):
        v = int(self.yellow_var.get())
        self.yellow_lbl.configure(text=str(v))
        self.it.controller.set_timings(self.green_var.get(), v)

    def _adp(self):
        self.it.controller.adaptive = self.adp_var.get()
        self.it.log("adaptive mode " + ("ON" if self.it.controller.adaptive else "OFF"))

    def _auto(self):
        self.auto_spawn = self.a_var.get()
        self.it.spawn_rate = DEFAULT_SPAWN if self.auto_spawn else 0.0
        self.it.log("auto spawn " + ("ON" if self.auto_spawn else "OFF"))

    def _append_log(self, line):
        try:
            self.log_box.configure(state=self.tk.NORMAL)
            self.log_box.insert(self.tk.END, line + "\n")
            self.log_box.see(self.tk.END)
            self.log_box.configure(state=self.tk.DISABLED)
        except Exception:
            pass

    def _loop(self):
        if self.running:
            self.it.step()
        self.render()
        self.root.after(self.speed_ms, self._loop)

    # drawing
    def render(self):
        try:
            self._draw()
            self.lbl["Clock"].configure(text=str(self.it.clock))
            self.lbl["Served"].configure(text=str(self.it.stats.served))
            self.lbl["Waiting"].configure(text=str(self.it.total_waiting()))
            self.lbl["Avg Wait"].configure(text=f"{self.it.stats.avg_wait:.2f}")
            ph = self.it.controller.phase + " " + self.it.controller.sub
            self.lbl["Phase"].configure(text=ph)
        except Exception:
            pass

    def _draw(self):
        tk = self.tk
        c = self.canvas
        c.delete("all")
        W = 460
        cx = cy = W // 2
        road = 90           # road width
        half = road // 2

        # roads
        c.create_rectangle(0, cy - half, W, cy + half, fill="#1a1f2b")
        c.create_rectangle(cx - half, 0, cx + half, W, fill="#1a1f2b")
        # center box
        c.create_rectangle(cx - half, cy - half, cx + half, cy + half, fill="#232b3d")

        colors = {"RED": "#ff5b5b", "GREEN": "#39d98a", "YELLOW": "#ffd23f"}
        R = 7   # light radius

        # draw each approach: queue + light
        for d in DIRS:
            lane = self.it.lanes[d]
            light = self.it.lights[d]
            q = lane.queue
            col = colors[light.state]
            # light centered on the approach side, just outside the box
            if d == "N":
                lx, ly = cx - R, cy - half - 2*R
            elif d == "S":
                lx, ly = cx - R, cy + half + R
            elif d == "E":
                lx, ly = cx + half + R, cy - R
            else:
                lx, ly = cx - half - 2*R, cy - R
            c.create_oval(lx, ly, lx + 2*R, ly + 2*R, fill=col, outline="#fff")

            # queue of small car squares leading away from the box
            for i, car in enumerate(q[:12]):
                off = 18 + i * 14
                if d == "N":
                    x0, y0 = cx - half + 20, cy - half - off
                    c.create_rectangle(x0, y0, x0 + 26, y0 + 10, fill="#5aa9ff",
                                       outline="#0b1021")
                elif d == "S":
                    x0, y0 = cx + half - 46, cy + half + off
                    c.create_rectangle(x0, y0, x0 + 26, y0 + 10, fill="#5aa9ff",
                                       outline="#0b1021")
                elif d == "E":
                    x0, y0 = cx + half + off, cy - half + 20
                    c.create_rectangle(x0, y0, x0 + 10, y0 + 26, fill="#5aa9ff",
                                       outline="#0b1021")
                else:
                    x0, y0 = cx - half - off, cy + half - 46
                    c.create_rectangle(x0, y0, x0 + 10, y0 + 26, fill="#5aa9ff",
                                       outline="#0b1021")

            # label with count
            label = f"{d}: {lane.count()}"
            if d == "N":
                c.create_text(cx - half + 32, cy - half - 4, text=label,
                              fill="#cfe0ff", font=("Consolas", 9), anchor=tk.W)
            elif d == "S":
                c.create_text(cx + half - 60, cy + half + 8, text=label,
                              fill="#cfe0ff", font=("Consolas", 9), anchor=tk.W)
            elif d == "E":
                c.create_text(cx + half + 6, cy - half + 32, text=label,
                              fill="#cfe0ff", font=("Consolas", 9), anchor=tk.W)
            else:
                c.create_text(cx - half - 70, cy + half - 24, text=label,
                              fill="#cfe0ff", font=("Consolas", 9), anchor=tk.W)



def ascii_frame(it):
    lines = []
    lines.append("=" * 48)
    lines.append(f" TRAFFIC SIM  clock={it.clock:04d}  "
                 f"phase={it.controller.phase} {it.controller.sub}")
    lines.append("=" * 48)
    sym = {"RED": "R", "GREEN": "G", "YELLOW": "Y"}
    for d in DIRS:
        lane = it.lanes[d]
        light = sym[it.lights[d].state]
        cars = "".join("#" for _ in lane.queue[:20])
        lines.append(f"  {d} light={light}  queue={lane.count():3d} {cars}")
    lines.append("-" * 48)
    lines.append(f" served={it.stats.served} waiting={it.total_waiting()} "
                 f"avgWait={it.stats.avg_wait:.2f}")
    return "\n".join(lines)


def run_terminal(it, ticks=400, delay=0.3):
    print("terminal mode: Ctrl+C to stop\n")
    try:
        for _ in range(ticks):
            it.step()
            os_clear()
            print(ascii_frame(it))
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nstopped")


def os_clear():
    if sys.stdout.isatty():
        os_system = "cls" if sys.platform.startswith("win") else "clear"
        import os
        os.system(os_system)
    else:
        print("\n" * 30)



def main(argv=None):
    ap = argparse.ArgumentParser(description="Smart Traffic Light Simulator")
    ap.add_argument("--terminal", action="store_true")
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--spawn-rate", type=float, default=DEFAULT_SPAWN)
    ap.add_argument("--no-spawn", action="store_true")
    a = ap.parse_args(argv)

    if a.terminal:
        rate = 0.0 if a.no_spawn else a.spawn_rate
        it = Intersection(spawn_rate=rate)
        if rate == 0:
            for _ in range(6):
                o = random.choice(DIRS)
                d = random.choice([x for x in DIRS if x != o])
                it.add_car(o, d)
        run_terminal(it, ticks=a.ticks, delay=a.delay)
        return

    it = Intersection(spawn_rate=0.0)
    try:
        g = GUI(it, speed_ms=400)
        if a.no_spawn:
            g.auto_spawn = False
            g.a_var.set(False)
        elif a.spawn_rate > 0:
            g.auto_spawn = True
            g.a_var.set(True)
            it.spawn_rate = a.spawn_rate
        g.start()
    except Exception as e:
        print(f"[warn] gui failed ({e}), terminal fallback")
        run_terminal(it, ticks=a.ticks, delay=a.delay)


if __name__ == "__main__":
    main()
