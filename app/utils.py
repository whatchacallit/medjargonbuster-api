from functools import partial, wraps
import logging
from timeit import default_timer as timer


log = logging.getLogger(__name__)


def find_first(d, aliases, default="<unknown>"):
    """
    Returns the value of the first key found in "aliases"
    """
    for a in aliases:
        if a in list(d.keys()):
            return d[a]

    return default


def timed(save_to: str = None, force=False):
    def _timed(func):
        """
        Function Decorator, measures execution time in ms of the wrapped function.
        "save_to" specifies an attribute name on the return value where this decorator will store the result.
        The save_to attribute must exist on the return value, unless you set force=True.
        In which case we try to create the dict-attribute on the fly to store the result.

        TODO: usually does not work as expected for async functions, so be aware
        """

        @wraps(func)
        def wrapper_timed(*f_args, **f_kwargs):
            # 1. Do something before
            log.info(f">>> Starting @timed() function {func.__qualname__!r} ")
            start_timing = timer()
            # 2. call wrapped function
            return_value = func(*f_args, **f_kwargs)
            # 3. Do something after
            runtime_ms = round((timer() - start_timing) * 1000)
            log.info(f"<<< Finished {func.__qualname__!r} in {runtime_ms}ms")

            # We can inidcate a field on the return value to record the timing to.
            # Has to be a dict and specified at the decorator
            # e.g. "@timed (save_to='meta'))" will try to use a dict field called "meta" on the function return value.
            # The dict entry will then be like: assert meta['<function qualifiedname>:timed_ms'] == runtime_ms...
            if save_to:
                try:
                    target = getattr(return_value, save_to, None)
                    if (not target) and force:
                        target = setattr(return_value, save_to, {})
                        target = getattr(return_value, save_to, None)
                    key = f"{func.__qualname__}"
                    if not target.get("timed"):
                        target["timed"] = {}
                    target["timed"][key] = runtime_ms
                except Exception as e:
                    log.error(
                        f"Error saving timing information on {func.__qualname__!r} into '{save_to}': {str(e)}"
                    )

            return return_value

        return wrapper_timed

    return _timed
