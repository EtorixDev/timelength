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


class InvalidValue(Exception):
    """Exception for when values are not parseable."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class NoValidValue(Exception):
    """Exception for when no valid values are found."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MultipleConsecutiveScales(Exception):
    """Exception for when subsequent Scales are listed."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class MultipleConsecutiveSpecials(Exception):
    """Exception for when subsequent specials are listed."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MultipleConsecutiveValues(Exception):
    """Exception for when subsequent Values are listed."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class LeadingScale(Exception):
    """Exception for when the passed string starts with a Scale rather than a Value."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class LeadingValue(Exception):
    """Exception for when the passed string starts with a Value rather than a Scale."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
