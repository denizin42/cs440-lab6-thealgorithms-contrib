"""For more information about the Binomial Distribution:
https://en.wikipedia.org/wiki/Binomial_distribution
"""

from __future__ import annotations

from math import comb, exp, lgamma, log, log1p


def binomial_distribution(successes: int, trials: int, prob: float) -> float:
    """
    Return probability of k successes out of n tries, with p probability for one
    success.

    Uses ``math.comb`` to avoid intermediate factorial float overflow, and falls
    back to log-space (``lgamma`` and ``log``) when large ``trials`` would
    overflow ``float`` or underflow intermediate powers.

    >>> binomial_distribution(3, 5, 0.7)
    0.30870000000000003
    >>> binomial_distribution(2, 4, 0.5)
    0.375
    >>> binomial_distribution(85, 171, 0.5)
    0.060749764626165485
    >>> round(binomial_distribution(1000, 2000, 0.5), 12)
    0.017839011146
    >>> binomial_distribution(6, 5, 0.5)
    Traceback (most recent call last):
        ...
    ValueError: successes must be lower or equal to trials
    >>> binomial_distribution(-1, 5, 0.5)
    Traceback (most recent call last):
        ...
    ValueError: the function is defined for non-negative integers
    >>> binomial_distribution(2, 4, 1.5)
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
    probability = (prob**successes) * ((1 - prob) ** (trials - successes))
    if probability != 0.0:
        try:
            return probability * comb(trials, successes)
        except OverflowError:
            pass
    # Fall back to log-space when intermediate powers underflow or comb overflows float.
    log_coefficient = (
        lgamma(trials + 1) - lgamma(successes + 1) - lgamma(trials - successes + 1)
    )
    log_probability = successes * log(prob) + (trials - successes) * log1p(-prob)
    return exp(log_coefficient + log_probability)


if __name__ == "__main__":
    from doctest import testmod

    testmod()
