def logging_wrapper(before=None, after=None):
    def log_decorator(func):
        def wrapper_func(*args, **kwargs):
            if before is not None:
                before(*args, **kwargs)

            result = func(*args, **kwargs)

            if after is not None:
                after(result)

            return result

        return wrapper_func

    return log_decorator
