from unittest import TextTestRunner, TextTestResult
import sys

from django.test.runner import DiscoverRunner


def _iter_tests(suite):
    for test in suite:
        if hasattr(test, "__iter__") and not hasattr(test, "_testMethodName"):
            yield from _iter_tests(test)
        else:
            yield test


class LiveProgressTestResult(TextTestResult):
    def __init__(self, stream, descriptions, verbosity, total_tests):
        super().__init__(stream, descriptions, verbosity)
        self.total_tests = total_tests
        self.current_test = 0

    def startTest(self, test):
        self.current_test += 1
        remaining = self.total_tests - self.current_test
        self.stream.write(
            "\n" + "=" * 72 + "\n"
            f"[TEST {self.current_test}/{self.total_tests}] START\n"
            f"{test.id()}\n"
            f"Remaining after this: {remaining}\n"
            + "=" * 72 + "\n"
        )
        self.stream.flush()
        super().startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(
            f"[TEST {self.current_test}/{self.total_tests}] PASS\n"
        )
        self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(
            f"[TEST {self.current_test}/{self.total_tests}] ERROR\n"
        )
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(
            f"[TEST {self.current_test}/{self.total_tests}] FAIL\n"
        )
        self.stream.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.write(
            f"[TEST {self.current_test}/{self.total_tests}] SKIP: {reason}\n"
        )
        self.stream.flush()


class LiveProgressTestRunner(TextTestRunner):
    resultclass = LiveProgressTestResult

    def __init__(self, *args, total_tests=0, **kwargs):
        self.total_tests = total_tests
        super().__init__(*args, **kwargs)

    def _makeResult(self):
        return self.resultclass(
            self.stream,
            self.descriptions,
            self.verbosity,
            self.total_tests,
        )


class DiscoverRunnerWithLiveProgress(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        total_tests = sum(1 for _ in _iter_tests(suite))
        runner = LiveProgressTestRunner(
            verbosity=self.verbosity,
            failfast=self.failfast,
            resultclass=LiveProgressTestResult,
            stream=getattr(self, "stream", sys.stderr),
            descriptions=True,
            total_tests=total_tests,
        )
        return runner.run(suite)
