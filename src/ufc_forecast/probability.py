# +200 mean 33%
# -200 mean 67%


def american_probabilities(odds):
    if odds == 0:
        raise ValueError("odds cannot be 0")

    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
