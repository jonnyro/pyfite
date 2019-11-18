"""Utility constants and methods for general use.

Attributes:
    DECIMAL_REGEX (str): A regex that matches decimals.
        These matches may lead with a negative sign, a digit, or a period.
        Scientific notation is supported.
        Ex: 0 1. .2 3.4 5.6e-4
"""
import math
import re
from typing import Tuple

DECIMAL_REGEX = '[+-]?(?:\\.\\d+|\\d+\\.?\\d*)(?:[eE][+-]?\\d+)?'
__EXTENTS_REGEX = re.compile(rf'\(\[({DECIMAL_REGEX}), ?({DECIMAL_REGEX})\], ?\[({DECIMAL_REGEX}), ?({DECIMAL_REGEX})\], ?\[({DECIMAL_REGEX}|nan), ?({DECIMAL_REGEX}|nan)\]\)', re.IGNORECASE)

class ParseError(Exception):
    """Exception for parsing errors.
    """
    def __init__(self, message: str = 'Failed to parse string'):  # pylint: disable=useless-super-delegation
        super().__init__(message)

def static_vars(**kwargs):
    """Decorates a function with static variables

    Taken from https://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
    """
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

def parseExtents(extents: str) -> Tuple[float, float, float, float, float, float]:
    """Parses extents from a string.

    Parsed strings are expected to be in the form (with spaces being optional) ([minX, maxX], [minY, maxY], [minZ, maxZ]).
    Z values are optional and may be "NaN" (case insensitive)

    Args:
        extents (str): The extents string to parse

    Returns:
        Tuple[float x 6]: The parsed min/max for X, Y, and Z

    Raises:
        ParseError: If the string can't be matched or any values aren't interpretable
    """
    match = re.match(__EXTENTS_REGEX, extents)
    if not match:
        raise ParseError('Provided extents did not match expected pattern')

    vals = [0] * 6  # Prepare array
    for i in range(1, 7):  # Expect to access match[1] through match[6]
        vals[i] = float(match[i])

    return tuple(vals)

@static_vars(m1=111132.92, m2=-559.82, m3=1.175, m4=-0.0023, p1=111412.84, p2=-93.5, p3=0.118)
def computeDegreeSize(lat: float) -> Tuple[float, float]:
    """Computes the size (m) of 1 degree of lon/lat at a given ``lat``.

    Obtained from http://www.csgnetwork.com/degreelenllavcalc.html

    Args:
        lat (float): The latitude at which to compute the size of 1 degree

    Returns:
        Tuple[float,float]: The length of 1 degree longitude and latitude at ``lat``
    """
    lat = math.radians(lat)
    latlen = computeDegreeSize.m1 + (computeDegreeSize.m2 * math.cos(2 * lat)) + (computeDegreeSize.m3 * math.cos(4 * lat)) + (computeDegreeSize.m4 * math.cos(6 * lat))
    lonlen = (computeDegreeSize.p1 * math.cos(lat)) + (computeDegreeSize.p2 * math.cos(3 * lat)) + (computeDegreeSize.p3 * math.cos(5 * lat))
    return (lonlen, latlen)
