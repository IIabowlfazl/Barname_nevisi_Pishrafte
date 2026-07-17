# Plot a three-phase AC voltage waveform (220 V phase, 50 Hz).

import numpy as np
import matplotlib.pyplot as plt

FREQUENCY = 50
RMS_PHASE = 220
PEAK_VOLTAGE = RMS_PHASE * np.sqrt(2)
ANGULAR_FREQ = 2 * np.pi * FREQUENCY


def main():
    time = np.linspace(0, 0.04, 1000)
    phase_r = PEAK_VOLTAGE * np.sin(ANGULAR_FREQ * time)
    phase_s = PEAK_VOLTAGE * np.sin(ANGULAR_FREQ * time - (2 * np.pi / 3))
    phase_t = PEAK_VOLTAGE * np.sin(ANGULAR_FREQ * time + (2 * np.pi / 3))

    plt.figure(figsize=(10, 5))
    plt.plot(time, phase_r, color="red", label="Phase R (L1)")
    plt.plot(time, phase_s, color="green", label="Phase S (L2)")
    plt.plot(time, phase_t, color="blue", label="Phase T (L3)")
    plt.title("Three Phase AC Voltage (380V Line-to-Line / 50Hz)")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.axhline(0, color="black", linewidth=1)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
