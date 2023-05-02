import math
import statistics
from math import sqrt

import pandas
import numpy
from matplotlib import pyplot as plt
from numpy import random
from scipy import stats


def autocorr(values: list, max_lag: int = 10) -> list:
    ser = pandas.Series(values)
    result = []
    for i in range(1, max_lag + 1):
        result.append(ser.autocorr(i))
    return result


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
    threshold = list_std(values)*0.1
    m_average = moving_average(values)
    mean = list_mean(values)
    steady = 0
    counter = 0
    for index in range(0, len(values) - 1):
        if abs(mean-values[index]) < threshold:
            counter += 1
            if counter == 50:
                steady = index
                break
        else:
            counter = 0
    if steady == 0:
        steady = math.floor(len(values) / 5)

    plt.plot(range(0, len(m_average)), m_average)
    plt.axvline(x=steady, color='r')
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


def subsample(timestamp: list, values: list, p=.8) -> (list, list):
    ret_times = []
    ret_values = []
    for i in range(0, len(values)):
        if numpy.random.rand() < p:
            ret_times.append(timestamp[i])
            ret_values.append(values[i])
    return ret_times, ret_values


def check_autocorr(a_corr: list, conf_i: float) -> bool:
    for corr in a_corr:
        if corr > conf_i:
            return False
    return True


def ci(values: list, accuracy: float):
    alpha = 1. - accuracy
    sigma = list_std(values)
    z_critical = stats.norm.ppf(q=accuracy + alpha / 2)
    standard_error = sigma / math.sqrt(len(values))
    return z_critical * standard_error


def subsample_to_independence(timestamp: list, values: list, accuracy: float, retrials: int = 10, shuffle: bool = False) -> (list, list):
    values_l = len(values)
    cycle = 0
    sub_sample = values
    sub_sample_times = timestamp
    p = .9
    conf_i = (stats.norm.ppf(accuracy)) / sqrt(len(values))
    if shuffle:
        random.shuffle(values)
    while not check_autocorr(autocorr(sub_sample), conf_i) :
        cycle += 1

        sub_sample_times, sub_sample = subsample(timestamp, values, p)
        if len(sub_sample) == 0:
            sub_sample_times, sub_sample = subsample(timestamp, values, p+0.01)
            break
        if shuffle:
            random.shuffle(values)
        if cycle % retrials == 0:
            p -= .01
        print(str(len(sub_sample)))
        conf_i = (stats.norm.ppf(accuracy)) / sqrt(len(sub_sample))

    print("Subsampling terminated(" + str(values_l) + "->" + str(len(values)) + "). Required " + str(
        cycle) + " iteration.")
    return sub_sample_times, sub_sample
