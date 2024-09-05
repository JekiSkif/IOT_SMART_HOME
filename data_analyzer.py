# data collection and analyzing module
from manager import *
import time
from scipy.spatial import distance
import statistics
import matplotlib.pyplot as plt
import numpy as np
from data_acquisition import *
from init import *

# Threshold computation based on energy information
def thrh_comp(Y: np.ndarray):
    ''' 
    Used for Dynamic Threshold calculation and carries scattered energy info.
    :param Y: Array of frequency domain data
    :return: Computed threshold value (float)
    '''
    # percen_thr = 0.05  # 5% of max energy holds - defined in init.py
    return np.mean(np.sort(abs(Y))[-int(len(Y) * percen_thr):-1])

# FFT processing block that computes frequency domain data and thresholding
def fft_block(Xdata: np.ndarray, isplot: bool, issave: bool, fname: str = 'data/AxisX_pass.png'):
    '''
    Perform FFT on the provided data and plot/save results if required.
    :param Xdata: Time-domain data array
    :param isplot: Flag to enable/disable plotting of results
    :param issave: Flag to enable/disable saving of the plot
    :param fname: Filename for saving the plot
    :return: Computed threshold value scaled by an empirical factor (float)
    '''
    # Fs = 2048.0  # Sampling rate - defined in init.py
    Ts = 1.0 / Fs  # Sampling interval
    t = np.arange(0, len(Xdata) / Fs, Ts)  # Time vector
    y = Xdata - np.mean(Xdata)  # Detrended data
    n = len(y)  # Length of the signal
    k = np.arange(n)
    T = n / Fs
    frq = k / T  # Two-sided frequency range    
    frq = frq[range(int(n / 2))]  # One-sided frequency range
    Y = np.fft.fft(y) / n  # FFT computation and normalization
    Y = Y[range(int(n / 2))]
    thrh = thrh_comp(Y)  # Compute threshold

    # Plotting and saving if required
    if isplot:
        fig, ax = plt.subplots(2, 1)
        ax[0].plot(t, y)
        ax[0].set_xlabel('Time')
        ax[0].set_ylabel('Amplitude')
        ax[1].plot(frq, abs(Y), 'b', frq, thrh + abs(Y) * 0, 'r')  # Plotting the spectrum
        ax[1].vlines([230, 240], 0, np.max(abs(Y)), colors='g')  # Example frequency bands
        ax[1].vlines([470, 480], 0, np.max(abs(Y)), colors='g')
        ax[1].vlines([710, 720], 0, np.max(abs(Y)), colors='g')
        ax[1].vlines([565, 630], 0, np.max(abs(Y)), colors='g')
        ax[1].set_xlabel('Freq (Hz)')
        ax[1].set_ylabel('|Y(freq)|')
        ax[0].grid(True)
        ax[1].grid(True)
        if issave:
            plt.savefig(fname)
        plt.show()

    return thrh * 10000  # Empirical normalization factor applied

# Main function for FFT processing across multiple axes
def fft_main():
    '''
    Main function to perform FFT analysis on data from multiple axes.
    :return: List of threshold values for each axis (list of floats)
    '''
    data = acq_data()  # Acquire data
    datapool = [data.AxisX.to_numpy(), data.AxisY.to_numpy(), data.AxisZ.to_numpy()]
    Ax_thrh = []
    # Process each axis data
    for cnt, Xdata in enumerate(datapool):
        Ax_thrh.append(fft_block(Xdata, isplot, issave, fname='data/Axis' + str(cnt) + '.png'))
    return Ax_thrh

# Function to display vibration data and check against thresholds
def vib_dsp():
    '''
    Compute and compare FFT data with predefined thresholds, checking for anomalies.
    :return: Boolean indicating if the vibration analysis exceeded thresholds (bool)
    '''
    current = fft_main()  # Get current thresholds
    d = distance.euclidean(current, Axes_Threshold)  # Compute Euclidean distance
    print("Euclidean distance:", d)
    std = statistics.stdev([abs(j - i) for i, j in zip(current, Axes_Threshold)])  # Compute standard deviation
    print("Standard Deviation of sample is % s" % (std))

    # Check against max allowable Euclidean distance or deviation percentage
    if d > max_eucl or std * 100 > deviation_percentage:
        return True
    return False
