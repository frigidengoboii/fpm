'''
    Default argument wrapper for instance methods.
    Loads keyword arguments from instance (self) if available and not specified
    by method call.
'''
def default_args(*defargs):
    def func_wrapper(func):
        def wrap_defaults(self, *args, **kwargs):
            for arg in defargs:
                if getattr(self, arg, None) is not None:
                    kwargs[arg] = getattr(self, arg)
            return func(self, *args, **kwargs)
        return wrap_defaults
    return func_wrapper
