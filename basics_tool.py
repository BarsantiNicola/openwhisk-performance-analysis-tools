import math
import statistics
from math import sqrt

from imblearn.under_sampling import RandomUnderSampler
import statsmodels.api as sm
import numpy
from matplotlib import pyplot as plt
from scipy import stats


def autocorr(values: list) -> list:
    return sm.tsa.acf(values)


def list_mean(values: list) -> float:
    v = numpy.array(values)
    return v.mean()


def list_var(values: list) -> float:
    v = numpy.array(values)
    return v.var()


def list_std(values: list) -> float:
    return sqrt(list_var(values))


def list_median(values: list) -> float:
    return statistics.median(values)


def extract(timestamps: list, values: list, min_threshold: int, max_threshold: int) -> (list, list):
    results = [], []
    for index in range(0, len(values)):
        if max_threshold > values[index] >= min_threshold:
            results[0].append(timestamps[index])
            results[1].append(values[index])
    return results


def steady_state(values: list) -> int:
    threshold = list_std(values) * 1.5
    m_average = moving_average(values)
    steady = 0
    counter = 0
    #for index in range(0, len(m_average) - 1):
    #    if m_average[index] - m_average[index + 1] < threshold:
    #        counter += 1
    #        if counter == 50:
    #            steady = index-50
    #            break

    #if steady == 0:
    steady = math.floor(len(values)/5)
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


def check_autocorr(a_corr: list, ci: float) -> bool:
    for corr in a_corr:
        if corr > ci:
            return False
    return True


def ci(values: list, accuracy: float):
    alpha = 1. - accuracy
    sigma = list_std(values)
    z_critical = stats.norm.ppf(q=accuracy + alpha/2)
    standard_error = sigma / math.sqrt(len(values))
    return z_critical * standard_error


def subsample_to_independence(timestamp: list, values: list, accuracy: float) -> (list, list):
    values_l = len(values)
    cycle = 0
    ci = (stats.norm.ppf(accuracy)) / sqrt(len(values))
    while check_autocorr(autocorr(values), ci):
        cycle += 1
        timestamp, values = subsample(timestamp, values)
        ci = (stats.norm.ppf(accuracy)) / sqrt(len(values))

    print("Subsampling terminated(" + str(values_l) + "->" + str(len(values)) + "). Required " + str(
        cycle) + " iteration.")
    return timestamp, values