"""For more information about the Binomial Distribution:
https://en.wikipedia.org/wiki/Binomial_distribution
"""

from __future__ import annotations

from math import comb, exp, lgamma, log


def binomial_distribution(successes: int, trials: int, prob: float) -> float:
    """
    Return probability of k successes out of n tries, with p probability for one
    success

    The function uses the binomial coefficient (falling back to log-space
    gamma functions for very large trial counts) to avoid factorial overflow.

    >>> binomial_distribution(3, 5, 0.7)
    0.30870000000000003
    >>> binomial_distribution(2, 4, 0.5)
    0.375
    >>> round(binomial_distribution(85, 171, 0.5), 10)
    0.0607497646
    >>> round(binomial_distribution(550, 1100, 0.5), 10)
    0.0240516578
    >>> binomial_distribution(6, 5, 0.5)
    Traceback (most recent call last):
        ...
    ValueError: successes must be lower or equal to trials
    >>> binomial_distribution(-1, 5, 0.5)
    Traceback (most recent call last):
        ...
    ValueError: the function is defined for non-negative integers
    >>> binomial_distribution(2, 5, 1.5)
    Traceback (most recent call last):
        ...
    ValueError: prob has to be in range of 1 - 0
    """
    if successes > trials:
        raise ValueError("successes must be lower or equal to trials")
    if trials < 0 or successes < 0:
        raise ValueError("the function is defined for non-negative integers")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("the function is defined for non-negative integers")
    if not 0 < prob < 1:
        raise ValueError("prob has to be in range of 1 - 0")
    try:
        probability = (prob**successes) * ((1 - prob) ** (trials - successes))
        # Calculate the binomial coefficient without factorial(n) float overflow
        return probability * comb(trials, successes)
    except OverflowError:
        log_probability = (
            lgamma(trials + 1)
            - lgamma(successes + 1)
            - lgamma(trials - successes + 1)
            + successes * log(prob)
            + (trials - successes) * log(1 - prob)
        )
        return exp(log_probability)


if __name__ == "__main__":
    from doctest import testmod

    testmod()
