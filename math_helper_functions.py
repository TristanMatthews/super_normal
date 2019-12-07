import math
import random


def logistic(x, alpha):
    return math.exp(x * alpha) / (1 + math.exp(x * alpha))

def convert_odds_to_cdf(odds):
    cdf = []
    total = 0
    for value in odds:
        total += value
        cdf.append(total)
    return cdf

def convert_cdf_to_odds(cdf):
    odds = []
    last = 0
    for value in cdf:
        odds.append(value - last)
        last = value
    return odds


def get_index_from_cdf(cdf):
    rand_seed = random.random()
    for index, value in enumerate(cdf):
        if value > rand_seed:
            return index
    return index
