"""Test-only readline stub for Python builds with a broken readline extension.

Pytest imports readline during early capture setup. The local Python 3.13 build
used for this project currently segfaults on that import, so Makefile test
commands put this stub first on PYTHONPATH. This is not used by the app.
"""


def _noop(*args, **kwargs):
    return None


set_completer = _noop
parse_and_bind = _noop
read_init_file = _noop
set_history_length = _noop
clear_history = _noop
add_history = _noop
write_history_file = _noop
read_history_file = _noop
get_current_history_length = lambda: 0
