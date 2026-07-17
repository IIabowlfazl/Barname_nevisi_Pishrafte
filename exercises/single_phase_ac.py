# Plot a single-phase AC voltage waveform (220 V RMS, 50 Hz).

import numpy as np
import matplotlib.pyplot as plt

FREQUENCY = 50
RMS_VOLTAGE = 220
PEAK_VOLTAGE = RMS_VOLTAGE * np.sqrt(2)
ANGULAR_FREQ = 2 * np.pi * FREQUENCY


def main():
    time = np.linspace(0, 0.04, 1000)
    voltage = PEAK_VOLTAGE * np.sin(ANGULAR_FREQ * time)

    plt.figure(figsize=(10, 4))
    plt.plot(time, voltage, color="blue", label="Single Phase 220V (RMS)")
    plt.title("Single Phase AC Voltage (220V RMS / 50Hz)")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.axhline(0, color="black", linewidth=1)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
