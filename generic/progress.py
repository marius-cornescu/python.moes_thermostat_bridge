#!/usr/bin/env python
import logging
import unittest
import traceback

from multiprocessing import Lock

##########################################################################################################


##########################################################################################################


class Progress(object):

    def __init__(self, total: int = 0):
        self.current = 0
        self.total = total
        self._lock = Lock()

    def __getstate__(self):
        """Return state values to be pickled."""
        return self.current, self.total

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.current, self.total = state
        self._lock = Lock()

    def set_total(self, total: int):
        with self._lock:
            self.total = total

    def set_current(self, current: int):
        with self._lock:
            self.current = current

    def increment(self):
        with self._lock:
            self.current = self.current + 1
            logging.info(f'{self.current}/{self.total} | ')

#
##########################################################################################################


##########################################################################################################

# ***************************************************************************************
class Test(unittest.TestCase):

    def test_generic(self):
        # given
        #under_test =

        # when
        #under_test. call method

        # then

        self.assertTrue(True)


# ***************************************************************************************


if __name__ == '__main__':
    unittest.main()
