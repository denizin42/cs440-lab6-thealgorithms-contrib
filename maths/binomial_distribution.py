"""For more information about the Binomial Distribution:
https://en.wikipedia.org/wiki/Binomial_distribution
"""

from __future__ import annotations

from math import comb, exp, lgamma, log, log1p


def binomial_distribution(successes: int, trials: int, prob: float) -> float:
    """
    Return probability of k successes out of n tries, with p probability for one
    success.

    Uses exact integer combinations for small trial counts and log-gamma
    arithmetic for larger trial counts to avoid float factorial overflow.

    >>> binomial_distribution(3, 5, 0.7)
    0.30870000000000003
    >>> binomial_distribution(2, 4, 0.5)
    0.375
    >>> round(binomial_distribution(85, 171, 0.5), 12)
    0.060749764626
    >>> round(binomial_distribution(1000, 2000, 0.5), 12)
    0.017839011146
    """
    if successes > trials:
        raise ValueError("successes must be lower or equal to trials")
    if trials < 0 or successes < 0:
        raise ValueError("the function is defined for non-negative integers")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("the function is defined for non-negative integers")
    if not 0 < prob < 1:
        raise ValueError("prob has to be in range of 1 - 0")
    if trials < 171:
        probability = (prob**successes) * ((1 - prob) ** (trials - successes))
        return probability * comb(trials, successes)
    log_coeff = (
        lgamma(trials + 1) - lgamma(successes + 1) - lgamma(trials - successes + 1)
    )
    return exp(log_coeff + successes * log(prob) + (trials - successes) * log1p(-prob))


if __name__ == "__main__":
    from doctest import testmod

    testmod()
