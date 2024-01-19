class LocaleConfigError(Exception):
    def __init__(self, message):
        """Exception for when Locale configs are malformed."""
        self.message = message
        super().__init__(self.message)


class DisabledScale(Exception):
    def __init__(self, message):
        """Exception for when a disabled Scale is used."""
        self.message = message
        super().__init__(self.message)


class InvalidValue(Exception):
    def __init__(self, message):
        """Exception for when values are not parseable."""
        self.message = message
        super().__init__(self.message)


class NoValidValue(Exception):
    def __init__(self, message):
        """Exception for when no valid values are found."""
        self.message = message
        super().__init__(self.message)


class MultipleConsecutiveScales(Exception):
    def __init__(self, message):
        """Exception for when subsequent Scales are listed."""
        self.message = message
        super().__init__(self.message)

class MultipleConsecutiveSpecials(Exception):
    def __init__(self, message):
        """Exception for when subsequent specials are listed."""
        self.message = message
        super().__init__(self.message)


class MultipleConsecutiveValues(Exception):
    def __init__(self, message):
        """Exception for when subsequent Values are listed."""
        self.message = message
        super().__init__(self.message)


class LeadingScale(Exception):
    def __init__(self, message):
        """Exception for when the passed string starts with a Scale rather than a Value."""
        self.message = message
        super().__init__(self.message)


class LeadingValue(Exception):
    def __init__(self, message):
        """Exception for when the passed string starts with a Value rather than a Scale."""
        self.message = message
        super().__init__(self.message)
