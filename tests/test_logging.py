import unittest

from src.log_wrapper import logging_wrapper


class TestLoggingDecorator(unittest.TestCase):
    def test_log_decorator_with_before_wrapper(self):
        expected_arg1 = 1
        expected_arg2 = 2
        expected_arg3 = 3
        expected_result = 4

        def wrapper_before(arg1, arg2, arg3):
            self.assertEqual(expected_arg1, arg1)
            self.assertEqual(expected_arg2, arg2)
            self.assertEqual(expected_arg3, arg3)

        @logging_wrapper(before=wrapper_before)
        def wrapped_func(arg1, arg2, arg3):
            self.assertEqual(expected_arg1, arg1)
            self.assertEqual(expected_arg2, arg2)
            self.assertEqual(expected_arg3, arg3)

            return expected_result

        actual_result = wrapped_func(expected_arg1, expected_arg2, expected_arg3)

        self.assertEqual(expected_result, actual_result)

    def test_log_decorator_with_after_wrapper(self):
        expected_arg1 = 1
        expected_arg2 = 2
        expected_arg3 = 3
        expected_result = 4

        def wrapper_after(result):
            self.assertEqual(expected_result, result)

        @logging_wrapper(after=wrapper_after)
        def wrapped_func(arg1, arg2, arg3):
            self.assertEqual(expected_arg1, arg1)
            self.assertEqual(expected_arg2, arg2)
            self.assertEqual(expected_arg3, arg3)

            return expected_result

        actual_result = wrapped_func(expected_arg1, expected_arg2, expected_arg3)

        self.assertEqual(expected_result, actual_result)
