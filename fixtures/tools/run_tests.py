"""Run the redaction projection unit tests.

A Makefile wrapper so `make test-fixtures` works on Windows: `make` runs recipes
through cmd.exe on this machine, and cmd mangles `python -c "..."` (it treats
the leading `.venv` segment as a separate command). Passing a script path -- the
same shape `make check-fixtures` already uses for `redact.py` -- avoids the
quoting problem entirely.

Usage:
    python fixtures/tools/run_tests.py
"""
import sys
import unittest

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(unittest.TestLoader().discover("fixtures/tools", "test_*.py"))
    sys.exit(0 if result.wasSuccessful() else 1)
