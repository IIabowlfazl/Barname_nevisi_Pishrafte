
import argparse
import os
import random
import sys
import time
from enum import Enum
from typing import Dict, List, Optional


# settings
DEFAULT_FLOORS = 20
DEFAULT_CAPACITY = 8
DEFAULT_SPEED = 1.0          # floors per tick
DOOR_DWELL = 2               # how long doors stay open
DEFAULT_SPAWN_RATE = 0.10    # chance per tick a new person shows up
MAX_WAITING = 40             # max people waiting at once


class Direction(Enum):
    # which way the elevator is going
    UP = 1
    DOWN = -1
    IDLE = 0


def dir_str(d: Direction) -> str:
    # just for showing direction in text
    if d == Direction.UP:
        return "UP  ^"
    if d == Direction.DOWN:
        return "DOWN v"
    return "IDLE -"


# Person  (a passenger who wants to go from one floor to another)
class Person:
    _next_id = 1

    def __init__(self, origin: int, dest: int, weight: Optional[float] = None,
                 request_time: int = 0):
        if origin == dest:
            raise ValueError("Origin and destination must differ.")
        self.pid = Person._next_id
        Person._next_id += 1

        self.origin_floor = origin
        self.dest_floor = dest
        self.direction = Direction.UP if dest > origin else Direction.DOWN
        self.weight = weight if weight is not None else round(random.uniform(50.0, 100.0), 1)

        # timing (measured in ticks)
        self.request_time = request_time   # when the request was made
        self.board_time = None   # when the person got in the elevator
        self.exit_time = None    # when the person got out
        self.wait_time = 0.0             # board - request
        self.travel_time = 0.0           # exit - board

    def __repr__(self) -> str:
        return (f"Person#{self.pid}(F{self.origin_floor}->F{self.dest_floor},"
                f"w={self.weight})")


# Floor
class Floor:
    # one floor of the building, keeps people waiting split by direction
    def __init__(self, number: int):
        self.number = number
        self.waiting_up = []
        self.waiting_down = []

    def add_person(self, person: Person) -> None:
        if person.direction == Direction.UP:
            self.waiting_up.append(person)
        else:
            self.waiting_down.append(person)

    def waiting_count(self) -> int:
        return len(self.waiting_up) + len(self.waiting_down)

    def clear(self) -> None:
        self.waiting_up.clear()
        self.waiting_down.clear()


# Elevator
class Elevator:
    def __init__(self, capacity: int = DEFAULT_CAPACITY, start_floor: int = 1,
                 speed: float = DEFAULT_SPEED):
        self.capacity = capacity
        self.current_floor = float(start_floor)
        self.speed = speed
        self.direction = Direction.IDLE

        self.passengers = []
        self.target_floor = None

        # states: IDLE, MOVING, DOORS
        self.state = "IDLE"
        self.dwell = 0

    def current_floor_int(self) -> int:
        return int(round(self.current_floor))

    def is_at_floor(self) -> bool:
        return abs(self.current_floor - round(self.current_floor)) < 1e-6

    def load(self) -> int:
        return len(self.passengers)

    def free_space(self) -> int:
        return self.capacity - len(self.passengers)

    def has_space(self) -> bool:
        return len(self.passengers) < self.capacity

    # move the car toward a target floor by one step (speed)
    def move_toward(self, target: int) -> None:
        if abs(target - self.current_floor) <= self.speed:
            self.current_floor = float(target)
        else:
            self.current_floor += self.speed if target > self.current_floor else -self.speed

    def reset(self, start_floor: int = 1) -> None:
        self.current_floor = float(start_floor)
        self.direction = Direction.IDLE
        self.passengers.clear()
        self.target_floor = None
        self.state = "IDLE"
        self.dwell = 0


# Controller  (decides what the elevator does each step, SCAN method)
class Controller:
    def __init__(self, building: "Building"):
        self.building = building

    def update(self) -> None:
        el = self.building.elevator

        # if doors are open, wait then close
        if el.state == "DOORS":
            el.dwell -= 1
            if el.dwell <= 0:
                el.state = "IDLE"
            return

        cur = el.current_floor_int()

        # if we are on a floor that needs a stop, service it
        if el.is_at_floor() and self._should_stop(cur, el.direction):
            self._service_floor(cur)
            el.state = "DOORS"
            el.dwell = DOOR_DWELL
            return

        # else figure out next target
        target = self._choose_next_target()
        if target is None:
            el.direction = Direction.IDLE
            el.state = "IDLE"
            el.target_floor = None
            return

        if target == cur:
            # already here, open doors and board
            if el.direction == Direction.IDLE:
                fl = self.building.floors[cur]
                if fl.waiting_up:
                    el.direction = Direction.UP
                elif fl.waiting_down:
                    el.direction = Direction.DOWN
            self._service_floor(cur)
            el.state = "DOORS"
            el.dwell = DOOR_DWELL
            return

        el.direction = Direction.UP if target > cur else Direction.DOWN
        el.target_floor = target
        el.state = "MOVING"
        el.move_toward(target)

    # SCAN helpers
    def _car_calls(self) -> set:
        return {p.dest_floor for p in self.building.elevator.passengers}

    def _up_hall(self) -> set:
        return {f for f in range(1, self.building.num_floors + 1)
                if self.building.floors[f].waiting_up}

    def _down_hall(self) -> set:
        return {f for f in range(1, self.building.num_floors + 1)
                if self.building.floors[f].waiting_down}

    def _should_stop(self, cur: int, direction: Direction) -> bool:
        el = self.building.elevator
        fl = self.building.floors[cur]
        # Always stop to let passengers out when their destination is reached.
        if any(p.dest_floor == cur for p in el.passengers):
            return True
        if direction == Direction.UP and fl.waiting_up:
            return True
        if direction == Direction.DOWN and fl.waiting_down:
            return True
        if direction == Direction.IDLE and (fl.waiting_up or fl.waiting_down):
            return True
        return False

    def _choose_next_target(self) -> Optional[int]:
        el = self.building.elevator
        bf = self.building
        cur = el.current_floor_int()

        car = self._car_calls()
        up = self._up_hall()
        down = self._down_hall()
        all_calls = car | up | down

        if not all_calls:
            return None

        
        if el.direction == Direction.IDLE:
            nearest = min(all_calls, key=lambda f: (abs(f - cur), f))
            if nearest > cur:
                el.direction = Direction.UP
            elif nearest < cur:
                el.direction = Direction.DOWN
            else:
                
                if bf.floors[cur].waiting_up:
                    el.direction = Direction.UP
                elif bf.floors[cur].waiting_down:
                    el.direction = Direction.DOWN
                else:
                    el.direction = Direction.UP
            return nearest

       
        if el.direction == Direction.UP:
            stops = [f for f in (car | up) if f > cur]
            if stops:
                return min(stops)
            above = [f for f in all_calls if f > cur]
            if above:
                # continue upward to the highest request, then reverse
                return min(above)
            el.direction = Direction.DOWN
            below = [f for f in (car | down) if f < cur]
            return max(below) if below else None

       
        if el.direction == Direction.DOWN:
            stops = [f for f in (car | down) if f < cur]
            if stops:
                return max(stops)
            below = [f for f in all_calls if f < cur]
            if below:
                return max(below)
            el.direction = Direction.UP
            above = [f for f in (car | up) if f > cur]
            return min(above) if above else None

        return None

    # -- boarding / alighting ---------------------------------------------
    def _service_floor(self, cur: int) -> None:
        el = self.building.elevator
        bf = self.building
        fl = bf.floors[cur]
        clock = bf.clock

        # Alight passengers whose destination is this floor.
        alighted = [p for p in el.passengers if p.dest_floor == cur]
        for p in alighted:
            p.exit_time = clock
            p.travel_time = p.exit_time - p.board_time
            bf.stats.record_exit(p)
        el.passengers = [p for p in el.passengers if p.dest_floor != cur]

        # Decide which queue to board from.
        if el.direction == Direction.UP:
            queue = fl.waiting_up
        elif el.direction == Direction.DOWN:
            queue = fl.waiting_down
        else:
            if fl.waiting_up:
                el.direction = Direction.UP
                queue = fl.waiting_up
            elif fl.waiting_down:
                el.direction = Direction.DOWN
                queue = fl.waiting_down
            else:
                queue = []

        boarded = 0
        while queue and el.has_space():
            p = queue.pop(0)
            p.board_time = clock
            p.wait_time = p.board_time - p.request_time
            el.passengers.append(p)
            bf.stats.record_board()
            boarded += 1

        if alighted or boarded:
            bf.log(f"F{cur:02d}: alighted {len(alighted)}, boarded {boarded} "
                   f"-> load {el.load()}/{el.capacity}")
        if queue:
            bf.log(f"F{cur:02d}: {len(queue)} passenger(s) left waiting "
                   f"(car full)")


# Building + Stats (Stats keeps the running numbers)
class Stats:
    def __init__(self):
        self.total_requests = 0
        self.boarded = 0
        self.served = 0
        self.total_wait = 0.0
        self.total_travel = 0.0

    def record_request(self):
        self.total_requests += 1

    def record_board(self):
        self.boarded += 1

    def record_exit(self, p: Person):
        self.served += 1
        self.total_wait += p.wait_time
        self.total_travel += p.travel_time

    @property
    def avg_wait(self) -> float:
        return self.total_wait / self.served if self.served else 0.0

    @property
    def avg_travel(self) -> float:
        return self.total_travel / self.served if self.served else 0.0

    def summary(self) -> str:
        return (f"Requests={self.total_requests}  Boarded={self.boarded}  "
                f"Served={self.served}  AvgWait={self.avg_wait:.2f}  "
                f"AvgTravel={self.avg_travel:.2f}")


class Building:
    # the building owns the floors, the elevator and the controller
    def __init__(self, num_floors: int = DEFAULT_FLOORS,
                 capacity: int = DEFAULT_CAPACITY,
                 spawn_rate: float = DEFAULT_SPAWN_RATE,
                 start_floor: int = 1):
        self.num_floors = num_floors
        self.spawn_rate = spawn_rate
        self.clock = 0
        self.floors = {f: Floor(f) for f in range(1, num_floors + 1)}
        self.elevator = Elevator(capacity=capacity, start_floor=start_floor)
        self.controller = Controller(self)
        self.stats = Stats()
        self.on_log = None          # callback(message) set by the UI
        self._log_buffer = []

    def log(self, message: str) -> None:
        line = f"[t={self.clock:04d}] {message}"
        self._log_buffer.append(line)
        if len(self._log_buffer) > 500:
            self._log_buffer = self._log_buffer[-500:]
        if self.on_log is not None:
            self.on_log(line)

    def recent_logs(self, n: int = 200) -> List[str]:
        return self._log_buffer[-n:]

    # -- requests ----------------------------------------------------------
    def total_waiting(self) -> int:
        return sum(f.waiting_count() for f in self.floors.values())

    def add_request(self, origin: int, dest: int,
                    weight: Optional[float] = None) -> Optional[Person]:
        if origin == dest:
            return None
        if not (1 <= origin <= self.num_floors and 1 <= dest <= self.num_floors):
            return None
        p = Person(origin, dest, weight, request_time=self.clock)
        self.floors[origin].add_person(p)
        self.stats.record_request()
        self.log(f"New request: Person#{p.pid} F{origin} -> F{dest}")
        return p

    def _maybe_spawn(self) -> None:
        if self.spawn_rate <= 0:
            return
        if self.total_waiting() >= MAX_WAITING:
            return
        if random.random() < self.spawn_rate:
            origin = random.randint(1, self.num_floors)
            dest = random.randint(1, self.num_floors)
            while dest == origin:
                dest = random.randint(1, self.num_floors)
            self.add_request(origin, dest)

    # -- simulation tick ---------------------------------------------------
    def step(self) -> None:
        self.clock += 1
        self._maybe_spawn()
        self.controller.update()

    def reset(self, start_floor: int = 1) -> None:
        self.clock = 0
        self.floors = {f: Floor(f) for f in range(1, self.num_floors + 1)}
        self.elevator.reset(start_floor)
        self.stats = Stats()
        self.log("System reset.")

    # -- demo seed ---------------------------------------------------------
    def seed_demo(self, n: int = 6) -> None:
        for _ in range(n):
            origin = random.randint(1, self.num_floors)
            dest = random.randint(1, self.num_floors)
            while dest == origin:
                dest = random.randint(1, self.num_floors)
            self.add_request(origin, dest)


# GUI  (the tkinter window)
class GUI:
    def __init__(self, building: Building, speed_ms: int = 400):
        import tkinter as tk
        from tkinter import ttk, scrolledtext

        self.tk = tk
        self.ttk = ttk
        self.scrolledtext = scrolledtext
        self.building = building
        self.building.on_log = self._append_log

        self.speed_ms = speed_ms
        self.running = True
        self.auto_spawn = False        # auto-generated requests OFF by default

        self.root = tk.Tk()
        self.root.title("Smart Elevator Simulator - 20 Story Building")
        self.root.configure(bg="#0b1021")

        self._build_widgets()
        self.building.log("System initialized: "
                          f"{building.num_floors} floors, 1 elevator, "
                          f"capacity {building.elevator.capacity}.")
        self.building.log("Auto spawn is OFF. Add requests manually "
                          "(Add Specific / Add Random).")
        self._loop()

    def start(self) -> None:
        """Enter the Tkinter event loop (called once after construction)."""
        self.root.mainloop()

    # ---- widget construction --------------------------------------------
    def _build_widgets(self):
        tk = self.tk
        ttk = self.ttk

        main = tk.Frame(self.root, bg="#0b1021")
        main.pack(fill=tk.BOTH, expand=True)

        # Canvas (building shaft visualisation)
        self.canvas = tk.Canvas(main, width=400, height=700,
                                bg="#0b1021", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=6, pady=6)

        # Right-hand control panel
        panel = tk.Frame(main, bg="#11182f", width=320)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        panel.pack_propagate(False)

        title = tk.Label(panel, text="SMART ELEVATOR CONTROL",
                         fg="#7fd1ff", bg="#11182f",
                         font=("Consolas", 13, "bold"))
        title.pack(pady=(6, 10))

        # --- request controls ---
        req = tk.LabelFrame(panel, text="Add Request", fg="#9fb3d1",
                            bg="#11182f", font=("Consolas", 10))
        req.pack(fill=tk.X, padx=6, pady=4)

        row = tk.Frame(req, bg="#11182f")
        row.pack(pady=4)
        tk.Label(row, text="From", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.origin_var = tk.IntVar(value=1)
        self.spin_from = ttk.Spinbox(row, from_=1, to=self.building.num_floors,
                                     width=5, textvariable=self.origin_var)
        self.spin_from.pack(side=tk.LEFT, padx=4)
        tk.Label(row, text="To", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.dest_var = tk.IntVar(value=10)
        self.spin_to = ttk.Spinbox(row, from_=1, to=self.building.num_floors,
                                   width=5, textvariable=self.dest_var)
        self.spin_to.pack(side=tk.LEFT, padx=4)

        ttk.Button(req, text="Add Specific Request",
                   command=self._add_specific).pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(req, text="Add Random Request",
                   command=self._add_random).pack(fill=tk.X, padx=4, pady=2)

        # --- simulation controls ---
        sim = tk.LabelFrame(panel, text="Simulation", fg="#9fb3d1",
                            bg="#11182f", font=("Consolas", 10))
        sim.pack(fill=tk.X, padx=6, pady=4)

        self.btn_pause = ttk.Button(sim, text="Pause", command=self._toggle_pause)
        self.btn_pause.pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(sim, text="Step Once", command=self._step_once).pack(
            fill=tk.X, padx=4, pady=2)
        ttk.Button(sim, text="Reset", command=self._reset).pack(
            fill=tk.X, padx=4, pady=2)

        spd = tk.Frame(sim, bg="#11182f")
        spd.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(spd, text="Speed (ms)", fg="#cdd9ef", bg="#11182f").pack(side=tk.LEFT)
        self.speed_var = tk.IntVar(value=self.speed_ms)
        self.scale = ttk.Scale(spd, from_=100, to=1000, orient=tk.HORIZONTAL,
                               variable=self.speed_var,
                               command=self._change_speed)
        self.scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # auto-spawn toggle (off by default - no surprise self-generated requests)
        auto = tk.Frame(sim, bg="#11182f")
        auto.pack(fill=tk.X, padx=4, pady=2)
        self.auto_var = tk.BooleanVar(value=self.auto_spawn)
        self.chk_auto = tk.Checkbutton(
            auto, text="Auto Spawn Requests", fg="#cdd9ef", bg="#11182f",
            selectcolor="#11182f", variable=self.auto_var,
            command=self._toggle_auto)
        self.chk_auto.pack(side=tk.LEFT)

        # --- stats ---
        stats = tk.LabelFrame(panel, text="Statistics", fg="#9fb3d1",
                              bg="#11182f", font=("Consolas", 10))
        stats.pack(fill=tk.X, padx=6, pady=4)
        self.stat_labels = {}
        for key in ("Clock", "Served", "Waiting", "Avg Wait",
                    "Avg Travel", "Elevator", "Direction", "Load"):
            f = tk.Frame(stats, bg="#11182f")
            f.pack(fill=tk.X, padx=4, pady=1)
            tk.Label(f, text=f"{key}:", fg="#8aa0c6", bg="#11182f",
                     width=12, anchor=tk.W).pack(side=tk.LEFT)
            v = tk.Label(f, text="-", fg="#e8f0ff", bg="#11182f",
                         anchor=tk.W, font=("Consolas", 9))
            v.pack(side=tk.LEFT)
            self.stat_labels[key] = v

        # --- log ---
        logf = tk.LabelFrame(panel, text="Event Log", fg="#9fb3d1",
                             bg="#11182f", font=("Consolas", 10))
        logf.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.log_box = self.scrolledtext.ScrolledText(
            logf, bg="#06101f", fg="#bfe9c8", font=("Consolas", 8),
            state=tk.DISABLED, height=12)
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    # ---- control callbacks ----------------------------------------------
    def _add_specific(self):
        o = self.origin_var.get()
        d = self.dest_var.get()
        if o == d:
            self.building.log("Rejected request: origin equals destination.")
            return
        self.building.add_request(o, d)
        self.render()

    def _add_random(self):
        nf = self.building.num_floors
        o = random.randint(1, nf)
        d = random.randint(1, nf)
        while d == o:
            d = random.randint(1, nf)
        self.building.add_request(o, d)
        self.render()

    def _toggle_pause(self):
        self.running = not self.running
        self.btn_pause.configure(text="Resume" if not self.running else "Pause")

    def _step_once(self):
        self.building.step()
        self.render()

    def _toggle_auto(self):
        self.auto_spawn = self.auto_var.get()
        self.building.spawn_rate = DEFAULT_SPAWN_RATE if self.auto_spawn else 0.0
        self.building.log(f"Auto spawn {'ENABLED' if self.auto_spawn else 'DISABLED'}.")

    def _reset(self):
        self.building.reset(1)
        # do not auto-seed; respect the user's auto-spawn toggle
        self.building.spawn_rate = DEFAULT_SPAWN_RATE if self.auto_spawn else 0.0
        self.render()

    def _change_speed(self, *_):
        self.speed_ms = self.speed_var.get()

    def _append_log(self, line: str):
        try:
            self.log_box.configure(state=self.tk.NORMAL)
            self.log_box.insert(self.tk.END, line + "\n")
            self.log_box.see(self.tk.END)
            self.log_box.configure(state=self.tk.DISABLED)
        except Exception:
            pass

    # ---- main loop -------------------------------------------------------
    def _loop(self):
        if self.running:
            self.building.step()
        self.render()
        self.root.after(self.speed_ms, self._loop)

    # ---- rendering -------------------------------------------------------
    def render(self):
        try:
            self._render_canvas()
            self._render_stats()
        except Exception:
            pass

    def _render_canvas(self):
        tk = self.tk
        c = self.canvas
        c.delete("all")

        W = 400
        H = 700
        nf = self.building.num_floors
        fh = H / nf
        shaft_x0 = 250
        shaft_x1 = 388
        car_w = shaft_x1 - shaft_x0 - 10

        el = self.building.elevator
        car_f = el.current_floor

        # shaft background
        c.create_rectangle(shaft_x0, 0, shaft_x1, H, fill="#05070f",
                           outline="#243b66")

        for f in range(1, nf + 1):
            top = H - f * fh
            bot = H - (f - 1) * fh
            yc = (top + bot) / 2

            # floor band (highlight if elevator is here)
            if abs(car_f - f) < 0.5:
                band_fill = "#1c2b4d"
            else:
                band_fill = "#0e1626"
            c.create_rectangle(6, top + 1, shaft_x0 - 4, bot - 1,
                               fill=band_fill, outline="#1b2740")

            fl = self.building.floors[f]
            up = len(fl.waiting_up)
            dn = len(fl.waiting_down)

            c.create_text(14, yc, text=f"F{f:02d}", fill="#cfe0ff",
                          font=("Consolas", 10, "bold"), anchor=tk.W)
            # hall-call indicators
            up_col = "#39d98a" if up else "#3a4a66"
            dn_col = "#ff8f6b" if dn else "#3a4a66"
            c.create_text(70, yc, text=f"up:{up:2d}", fill=up_col,
                          font=("Consolas", 9), anchor=tk.W)
            c.create_text(130, yc, text=f"dn:{dn:2d}", fill=dn_col,
                          font=("Consolas", 9), anchor=tk.W)

        # elevator car  (centered on the same y as the floor band it sits on)
        car_top = H - (car_f - 0.5) * fh + 3
        car_bot = H - (car_f - 0.5) * fh - 3
        if el.state == "DOORS":
            car_fill = "#2ecc71"
        elif el.state == "MOVING":
            car_fill = "#2f80ed"
        else:
            car_fill = "#6b7a99"

        c.create_rectangle(shaft_x0 + 5, car_top, shaft_x0 + 5 + car_w, car_bot,
                           fill=car_fill, outline="#dff1ff", width=2)
        arrow = "^" if el.direction == Direction.UP else (
            "v" if el.direction == Direction.DOWN else "-")
        c.create_text(shaft_x0 + 5 + car_w / 2, (car_top + car_bot) / 2,
                      text=f"{arrow} {el.load()}/{el.capacity}",
                      fill="#ffffff", font=("Consolas", 11, "bold"))

    def _render_stats(self):
        b = self.building
        el = b.elevator
        self.stat_labels["Clock"].configure(text=str(b.clock))
        self.stat_labels["Served"].configure(text=str(b.stats.served))
        self.stat_labels["Waiting"].configure(text=str(b.total_waiting()))
        self.stat_labels["Avg Wait"].configure(text=f"{b.stats.avg_wait:.2f}")
        self.stat_labels["Avg Travel"].configure(text=f"{b.stats.avg_travel:.2f}")
        self.stat_labels["Elevator"].configure(text=el.state)
        self.stat_labels["Direction"].configure(text=dir_str(el.direction).strip())
        self.stat_labels["Load"].configure(text=f"{el.load()}/{el.capacity}")


# terminal mode (ascii view)
def _clear_screen() -> None:
    if sys.stdout.isatty():
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    else:
        # not a real terminal, just scroll
        print("\n" * 30)


def ascii_frame(building: Building) -> str:
    el = building.elevator
    car_f = el.current_floor
    lines = []
    lines.append("=" * 64)
    lines.append(f" SMART ELEVATOR SIMULATOR   Clock: {building.clock:04d}   "
                 f"State: {el.state:6s}  Dir: {dir_str(el.direction).strip()}")
    lines.append("=" * 64)
    lines.append(f" {'FL':>3} | {'up':>3} {'dn':>3} | {'CAR':^5} |  shaft")
    lines.append("-" * 64)

    for f in range(building.num_floors, 0, -1):
        fl = building.floors[f]
        up = len(fl.waiting_up)
        dn = len(fl.waiting_down)
        near = abs(car_f - f) < 0.5
        if near:
            car = f"E{el.load():02d}"
            shaft = f"[{'#' * el.load()}{'.' * (el.capacity - el.load())}]"
        else:
            car = "  . "
            shaft = "|........|"
        line = f" F{f:02d} | {up:3d} {dn:3d} | {car:^5} |  {shaft}"
        lines.append(line)
    lines.append("-" * 64)
    arrow = "^" if el.direction == Direction.UP else (
        "v" if el.direction == Direction.DOWN else "-")
    lines.append(f" Car position: floor {car_f:.1f}   direction {arrow}   "
                 f"load {el.load()}/{el.capacity}   doors: {el.state}")
    lines.append(building.stats.summary())
    return "\n".join(lines)


def run_terminal(building: Building, ticks: int = 400, delay: float = 0.3):
    print("Terminal mode: press Ctrl+C to stop.\n")
    try:
        for _ in range(ticks):
            building.step()
            _clear_screen()
            print(ascii_frame(building))
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")


# run it
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Smart Elevator Simulator for a 20-story building.")
    parser.add_argument("--terminal", action="store_true",
                        help="Run the ASCII terminal visualisation instead of the GUI.")
    parser.add_argument("--floors", type=int, default=DEFAULT_FLOORS,
                        help="Number of floors (default 20).")
    parser.add_argument("--capacity", type=int, default=DEFAULT_CAPACITY,
                        help="Elevator passenger capacity (default 8).")
    parser.add_argument("--ticks", type=int, default=400,
                        help="Terminal mode: number of simulation ticks.")
    parser.add_argument("--delay", type=float, default=0.3,
                        help="Terminal mode: seconds between ticks.")
    parser.add_argument("--spawn-rate", type=float, default=DEFAULT_SPAWN_RATE,
                        help="Probability per tick of a new random request.")
    parser.add_argument("--no-spawn", action="store_true",
                        help="Disable automatic random request generation.")
    args = parser.parse_args(argv)

    if args.terminal:
        spawn = 0.0 if args.no_spawn else args.spawn_rate
        building = Building(num_floors=args.floors, capacity=args.capacity,
                            spawn_rate=spawn)
        building.seed_demo(6)
        run_terminal(building, ticks=args.ticks, delay=args.delay)
        return

    # GUI mode: requests are user-controlled. Auto-spawn starts OFF so the
    # simulator never self-generates requests unless the user checks the box.
    building = Building(num_floors=args.floors, capacity=args.capacity,
                        spawn_rate=0.0)

    # GUI mode (fall back to terminal if Tk cannot initialise a display).
    try:
        gui = GUI(building, speed_ms=400)
        # honour --spawn-rate / --no-spawn as the initial checkbox state
        if args.no_spawn:
            gui.auto_spawn = False
            gui.auto_var.set(False)
        elif args.spawn_rate > 0:
            gui.auto_spawn = True
            gui.auto_var.set(True)
            building.spawn_rate = args.spawn_rate
            building.log(f"Auto spawn preset to rate {args.spawn_rate}.")
        gui.start()
    except Exception as exc:  # pragma: no cover - environment specific
        print(f"[warn] Could not start Tkinter GUI ({exc}).")
        print("Falling back to terminal visualisation.\n")
        run_terminal(building, ticks=args.ticks, delay=args.delay)


if __name__ == "__main__":
    main()
