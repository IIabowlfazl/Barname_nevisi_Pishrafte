
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import signal
import tkinter as tk
from tkinter import ttk


class TransferFunction:
    # builds a standard 2nd order tf:  K*w^2 / (s^2 + 2*z*w*s + w^2)
    # when zeta=1 it is still the same form (critically damped)
    def __init__(self, k=1.0, zeta=0.5, wn=1.0):
        self.k = k
        self.zeta = zeta
        self.wn = wn

    def num_den(self):
        # numerator K*wn^2, denominator [1, 2*zeta*wn, wn^2]
        num = [self.k * self.wn ** 2]
        den = [1.0, 2.0 * self.zeta * self.wn, self.wn ** 2]
        return num, den

    def is_second_order(self):
        return True


class StepResponse:
    # runs the step simulation and keeps time + output arrays
    def __init__(self, tf, t_end=20.0, dt=0.01):
        self.tf = tf
        self.t_end = t_end
        self.dt = dt
        self.t = None
        self.y = None
        self.run()

    def run(self):
        num, den = self.tf.num_den()
        # pick a time vector long enough to settle
        t = np.arange(0, self.t_end, self.dt)
        # scipy returns (T, yout) for step; we use lsim on a step input
        u = np.ones_like(t)
        _, y, _ = signal.lsim((num, den), U=u, T=t)
        self.t = t
        self.y = y
        return self.t, self.y


class Analyzer:
    # computes the metrics from a step response
    def __init__(self, resp, final_value=None):
        self.resp = resp
        self.t = resp.t
        self.y = resp.y
        self.final_value = final_value if final_value else self.y[-1]

    def overshoot(self):
        # only meaningful if it rises above final value
        peak = np.max(self.y)
        if self.final_value > 0 and peak > self.final_value:
            return (peak - self.final_value) / self.final_value * 100.0
        return 0.0

    def settling_time(self, tol=2.0):
        # time to stay within tol% of final value
        band = tol / 100.0 * self.final_value
        lo, hi = self.final_value - band, self.final_value + band
        for i, v in enumerate(self.y):
            if lo <= v <= hi:
                # check it stays in band to the end
                if np.all((self.y[i:] >= lo) & (self.y[i:] <= hi)):
                    return self.t[i]
        return self.t[-1]

    def rise_time(self):
        # 10% to 90% of final value
        fv = self.final_value
        i10 = np.where(self.y >= 0.1 * fv)[0]
        i90 = np.where(self.y >= 0.9 * fv)[0]
        if len(i10) == 0 or len(i90) == 0:
            return 0.0
        return self.t[i90[0]] - self.t[i10[0]]

    def peak(self):
        return float(np.max(self.y))

    def steady(self):
        return float(self.y[-1])


class Plotter:
    # draws the response on a matplotlib axis
    def __init__(self, ax):
        self.ax = ax

    def plot(self, resp, metrics):
        self.ax.clear()
        self.ax.plot(resp.t, resp.y, color="#39d98a", label="Step Response")
        self.ax.axhline(metrics.final_value, color="#7fd1ff", linestyle="--",
                        label=f"Final {metrics.final_value:.2f}")
        self.ax.set_title("Step Response (2nd Order)")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Output")
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Step Response Analyzer")
        self.root.configure(bg="#0b1021")

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self._controls()
        self.ax.set_title("Step Response (2nd Order)")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Output")
        self.canvas.draw()

    def start(self):
        self.root.mainloop()

    def _controls(self):
        f = tk.Frame(self.root, bg="#11182f")
        f.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=6)

        tk.Label(f, text="K", fg="#cdd9ef", bg="#11182f").grid(row=0, column=0)
        tk.Label(f, text="zeta", fg="#cdd9ef", bg="#11182f").grid(row=0, column=2)
        tk.Label(f, text="wn", fg="#cdd9ef", bg="#11182f").grid(row=0, column=4)

        self.k_var = tk.DoubleVar(value=1.0)
        self.z_var = tk.DoubleVar(value=0.5)
        self.w_var = tk.DoubleVar(value=1.0)

        ttk.Entry(f, textvariable=self.k_var, width=6).grid(row=0, column=1)
        ttk.Entry(f, textvariable=self.z_var, width=6).grid(row=0, column=3)
        ttk.Entry(f, textvariable=self.w_var, width=6).grid(row=0, column=5)

        ttk.Button(f, text="Analyze", command=self._analyze).grid(
            row=0, column=6, padx=6)
        ttk.Button(f, text="Quit", command=self.root.destroy).grid(
            row=0, column=7, padx=6)

        self.out = tk.Label(f, text="enter K, zeta, wn and press Analyze",
                            fg="#bfe9c8", bg="#11182f", font=("Consolas", 9))
        self.out.grid(row=1, column=0, columnspan=8, sticky="w", pady=4)

    def _analyze(self):
        try:
            k = float(self.k_var.get())
            z = float(self.z_var.get())
            w = float(self.w_var.get())
        except ValueError:
            self.out.configure(text="bad number")
            return
        if w <= 0:
            self.out.configure(text="wn must be > 0")
            return

        tf = TransferFunction(k, z, w)
        resp = StepResponse(tf, t_end=max(20.0, 15.0 / w))
        an = Analyzer(resp)
        plotter = Plotter(self.ax)
        plotter.plot(resp, an)

        txt = (f"K={k} zeta={z} wn={w} | peak={an.peak():.3f} "
               f"steady={an.steady():.3f} | overshoot={an.overshoot():.2f}% "
               f"rise={an.rise_time():.3f}s settle(2%)={an.settling_time():.3f}s")
        self.out.configure(text=txt)
        self.canvas.draw()


def main():
    g = GUI()
    g.start()


if __name__ == "__main__":
    main()
