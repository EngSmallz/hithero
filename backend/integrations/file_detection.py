try:
    import puremagic
except ImportError:
    class _PuremagicFallback:
        @staticmethod
        def magic_buffer(_buffer):
            return []

    puremagic = _PuremagicFallback()


def detect_file_type(buffer):
    if hasattr(puremagic, "magic_string"):
        return puremagic.magic_string(buffer)
    return puremagic.magic_buffer(buffer)
