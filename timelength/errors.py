class LocaleConfigError(Exception):
    """Exception for when Locale configs are malformed."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DisabledScale(Exception):
    """Exception for when a disabled Scale is used."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
