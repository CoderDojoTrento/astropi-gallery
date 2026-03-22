"""
Mock sense_hat package for Astro Pi Mission Zero animation recording.
Drop-in replacement — scripts using `from sense_hat import SenseHat` work unchanged.
"""

from ._hat import SenseHat

__all__ = ['SenseHat']
