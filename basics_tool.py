from math import sqrt

from imblearn.under_sampling import RandomUnderSampler
import statsmodels.api as sm
import numpy
from matplotlib import pyplot as plt
from scipy import stats


def autocorr(values: list) -> float:
    return sm.tsa.acf(values)


def list_mean(values: list) -> float:
    v = numpy.array(values)
    return v.mean()


def list_var(values: list) -> float:
    v = numpy.array(values)
    return v.var()


def list_std(values: list) -> float:
    return sqrt(list_var(values))


def steady_state(values: list) -> int:
    threshold = list_std(values) * 1.5
    m_average = moving_average(values)
    steady = 0
    for index in range(0, len(m_average) - 1):
        if m_average[index] - m_average[index + 1] < threshold:
            steady = index
            break
    plt.plot(range(0, len(m_average)), m_average)
    plt.axvline(x=steady)
    plt.title = "Steady state analysis"
    plt.show()
    plt.clf()
    return steady


def moving_average(values: list) -> list:
    i = 0
    moving_averages = []
    window_size = 5
    while i < len(values) - window_size + 1:
        window = values[i: i + window_size]
        window_average = round(sum(window) / window_size, 2)
        moving_averages.append(window_average)
        i += 1

    return moving_averages


def subsample(timestamp: list, values: list) -> (list, list):
    rus = RandomUnderSampler()
    return rus.fit_sample(timestamp, values)


def subsample_to_independence(timestamp: list, values: list, accuracy: float) -> (list, list):
    ci = (stats.norm.ppf(accuracy)) / sqrt(len(values))
    while autocorr(values) > ci:
        timestamp, values = subsample(timestamp, values)
        ci = (stats.norm.ppf(accuracy)) / sqrt(len(values))
    return timestamp, values
