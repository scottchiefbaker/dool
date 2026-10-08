"""Run the unit tests with green/red status output when writing to a terminal.

Colors are disabled when stdout is not a TTY or when NO_COLOR is set.
"""
import os
import sys
import unittest

GREEN = '\033[32m'
RED = '\033[31m'
YELLOW = '\033[33m'
RESET = '\033[0m'


def use_color(stream):
    return hasattr(stream, 'isatty') and stream.isatty() and 'NO_COLOR' not in os.environ


def paint(color_code, text, enabled):
    return color_code + text + RESET if enabled else text


class ColorTextTestResult(unittest.TextTestResult):
    """Prints the status first, e.g. 'ok    test_name ... '.

    Also counts outcomes so main() can print a summary.
    Subtests: a passing subtest is not counted on its own, because its parent
    test is counted once via addSuccess. Each failing subtest counts as failed.
    """
    color = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Not named 'errors'/'failures': TestResult already uses those as lists.
        self.count_passed = 0
        self.count_failed = 0
        self.count_errors = 0
        self.count_skipped = 0

    def startTest(self, test):
        # Skip TextTestResult.startTest, which prints the name before the status.
        unittest.TestResult.startTest(self, test)

    def _write_status(self, test, status):
        if status == 'ok':
            colored = paint(GREEN, status, self.color)
        elif status in ('FAIL', 'ERROR'):
            colored = paint(RED, status, self.color)
        elif status.startswith('skipped'):
            colored = paint(YELLOW, status, self.color)
        else:
            colored = status

        # Pad to a fixed width so the test names line up.
        padding = ' ' * (len('skipped') - len(status)) if status.startswith('skipped') else ' ' * max(0, 7 - len(status))
        indent = '  ' if isinstance(test, unittest.case._SubTest) else ''
        self.stream.write(colored + padding + '  ' + indent + self.getDescription(test))
        self.stream.writeln()
        self.stream.flush()
        self._newline = True

    def addSuccess(self, test):
        super().addSuccess(test)
        self.count_passed += 1

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.count_failed += 1

    def addError(self, test, err):
        super().addError(test, err)
        self.count_errors += 1

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            if issubclass(err[0], subtest.failureException):
                self.count_failed += 1
            else:
                self.count_errors += 1

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.count_skipped += 1


def print_summary(result, stream, enabled):
    rows = [
        ('Passed', result.count_passed, GREEN),
        ('Failed', result.count_failed, RED),
        ('Errors', result.count_errors, RED),
        ('Skipped', result.count_skipped, YELLOW),
    ]
    parts = []
    for label, count, color in rows:
        # Green/red/yellow only when the count is nonzero, so zeros stay plain.
        shown = paint(color, str(count), enabled and count > 0)
        parts.append('%s: %s' % (label, shown))
    stream.writeln()
    stream.writeln('  '.join(parts))


def main():
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.dirname(os.path.abspath(__file__)))

    runner = unittest.TextTestRunner(verbosity=2, resultclass=ColorTextTestResult)
    enabled = use_color(sys.stderr)
    ColorTextTestResult.color = enabled
    result = runner.run(suite)
    print_summary(result, runner.stream, enabled)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
