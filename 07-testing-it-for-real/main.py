"""Module 07: run the whole suite; exit non-zero if anything fails."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tests  # noqa: E402


def main() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), "the tutorial server's test suite failed"
    assert result.testsRun >= 10
    print(f"\nmodule 07 ok ({result.testsRun} tests, {len(result.skipped)} skipped)")


if __name__ == "__main__":
    main()
