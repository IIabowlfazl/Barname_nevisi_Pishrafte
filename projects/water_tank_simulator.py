
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

CAPACITY = 100.0      # tank max (units)
SETPOINT = 60.0       # target water level we want to hold
DT = 0.1              # time step
STEPS = 600           # how many steps we simulate
OUTFLOW = 2.0         # constant drain rate (units per step)


class Tank:
    # the water tank, holds the current level
    def __init__(self, capacity=CAPACITY):
        self.capacity = capacity
        self.level = 0.0

    def update(self, inflow, dt=DT):
        # water in minus water out, clamped to [0, capacity]
        self.level += (inflow - OUTFLOW) * dt
        if self.level < 0:
            self.level = 0.0
        if self.level > self.capacity:
            self.level = self.capacity

    def reset(self):
        self.level = 0.0


class Pump:
    # turns a control signal (0..1) into an inflow rate
    def __init__(self, max_rate=20.0):
        self.max_rate = max_rate

    def inflow(self, signal):
        # signal 0..1 -> 0..max_rate
        s = max(0.0, min(1.0, signal))
        return s * self.max_rate


class Sensor:
    # reads the tank level, with a little noise like a real sensor
    def __init__(self, noise=0.5):
        self.noise = noise

    def read(self, level):
        if self.noise <= 0:
            return level
        return level + np.random.normal(0, self.noise)


class Controller:
    # base controller, has OnOff and PID subclasses
    def control(self, error):
        raise NotImplementedError


class OnOffController(Controller):
    # simple bang-bang: full on if below setpoint, full off above
    def __init__(self, setpoint=SETPOINT, hysteresis=2.0):
        self.setpoint = setpoint
        self.hysteresis = hysteresis

    def control(self, error):
        # error = setpoint - level. if level low -> on, if high -> off
        if error > self.hysteresis:
            return 1.0
        if error < -self.hysteresis:
            return 0.0
        return 1.0  # keep last-ish: default on near setpoint


class PIDController(Controller):
    # proportional-integral-derivative controller
    def __init__(self, setpoint=SETPOINT, kp=0.8, ki=0.2, kd=0.05):
        self.setpoint = setpoint
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0.0
        self.prev_error = 0.0

    def control(self, error):
        deriv = (error - self.prev_error) / DT
        # tentative output with current integral
        out_unsat = self.kp * error + self.ki * self.integral + self.kd * deriv
        if 0.0 <= out_unsat <= 1.0:
            # only integrate when not saturated (anti-windup)
            self.integral += error * DT
        self.prev_error = error
        return max(0.0, min(1.0, out_unsat))


class Simulation:
    # runs one controller and records the level over time
    def __init__(self, controller, tank=None, sensor=None, pump=None,
                 steps=STEPS):
        self.controller = controller
        self.tank = tank if tank else Tank()
        self.sensor = sensor if sensor else Sensor()
        self.pump = pump if pump else Pump()
        self.steps = steps
        self.time = []
        self.level = []
        self.setpoint_line = controller.setpoint

    def run(self):
        self.tank.reset()
        # reset pid memory
        if isinstance(self.controller, PIDController):
            self.controller.integral = 0.0
            self.controller.prev_error = 0.0
        t = 0.0
        for _ in range(self.steps):
            measured = self.sensor.read(self.tank.level)
            error = self.controller.setpoint - measured
            signal = self.controller.control(error)
            inflow = self.pump.inflow(signal)
            self.tank.update(inflow, DT)
            self.time.append(t)
            self.level.append(self.tank.level)
            t += DT
        return self.time, self.level


class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Water Tank Level Control")
        self.root.configure(bg="#0b1021")

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        panel = tk.Frame(self.root, bg="#11182f")
        panel.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(panel, text="Run & Plot", command=self._run).pack(
            side=tk.LEFT, padx=6, pady=6)
        ttk.Button(panel, text="Quit", command=self.root.destroy).pack(
            side=tk.LEFT, padx=6, pady=6)

        lbl = tk.Label(panel,
                       text="Tank=100u  setpoint=60u  PID(kp=0.8,ki=0.2,kd=0.05) "
                            "vs On-Off",
                       fg="#cdd9ef", bg="#11182f")
        lbl.pack(side=tk.LEFT, padx=6)

        self.ax.set_title("Water Level: PID vs On-Off")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Level (units)")
        self.canvas.draw()

    def start(self):
        self.root.mainloop()

    def _run(self):
        sim_pid = Simulation(PIDController())
        sim_oo = Simulation(OnOffController())
        t1, l1 = sim_pid.run()
        t2, l2 = sim_oo.run()

        self.ax.clear()
        self.ax.plot(t1, l1, label="PID", color="#39d98a")
        self.ax.plot(t2, l2, label="On-Off", color="#ff8f6b")
        self.ax.axhline(SETPOINT, color="#7fd1ff", linestyle="--",
                        label=f"Setpoint {SETPOINT}")
        self.ax.set_title("Water Level: PID vs On-Off")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Level (units)")
        self.ax.legend()
        self.canvas.draw()


def main():
    g = GUI()
    g.start()


if __name__ == "__main__":
    main()
