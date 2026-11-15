"""For more information about the Binomial Distribution:
https://en.wikipedia.org/wiki/Binomial_distribution
"""

from __future__ import annotations

from math import comb, exp, lgamma, log


def binomial_distribution(successes: int, trials: int, prob: float) -> float:
    """
    Return probability of k successes out of n tries, with p probability for one
    success

    The function uses `math.comb` and falls back to log-space computation
    (`math.lgamma`) for very large `trials` to avoid float overflow.

    >>> binomial_distribution(3, 5, 0.7)
    0.30870000000000003
    >>> binomial_distribution(2, 4, 0.5)
    0.375
    >>> binomial_distribution(85, 171, 0.5)
    0.060749764626165485
    >>> round(binomial_distribution(1000, 2000, 0.5), 6)
    0.017839
    """
    if successes > trials:
        raise ValueError("successes must be lower or equal to trials")
    if trials < 0 or successes < 0:
        raise ValueError("the function is defined for non-negative integers")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("the function is defined for non-negative integers")
    if not 0 < prob < 1:
        raise ValueError("prob has to be in range of 1 - 0")
    probability = (prob**successes) * ((1 - prob) ** (trials - successes))
    try:
        return probability * comb(trials, successes)
    except OverflowError:
        log_coeff = (
            lgamma(trials + 1) - lgamma(successes + 1) - lgamma(trials - successes + 1)
        )
        log_prob = successes * log(prob) + (trials - successes) * log(1 - prob)
        return exp(log_coeff + log_prob)


if __name__ == "__main__":
    from doctest import testmod

    testmod()
