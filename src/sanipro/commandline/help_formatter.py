import argparse


class SaniproHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """A help formatter for this application.
    This features displaying the type name of a metavar, and the default value
    for the positional/optional arguments.

    `argparse.MetavarTypeHelpFormatter` throws a error
    when a user does not define the type of the positional/optional argument,
    which defaults to `None`. Consequently, the original module tries to get
    the attribute of `None`.

    So it seemed we could not directly inhererit the class.

    Instead, we are now implementing the same features by renewing it."""

    def _get_default_metavar_for_optional(self, action):
        metavar = action.dest.upper()
        if action.type is not None:
            return getattr(action.type, "__name__", metavar)
        return metavar

    def _get_default_metavar_for_positional(self, action):
        metavar = action.dest
        if action.type is not None:
            return getattr(action.type, "__name__", metavar)
        return metavar
