class InvalidValue(Exception):
    '''Exception for when a value is not parseable.'''
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class InvalidOrder(Exception):
    '''Exception for when Values and Scales are listed in an incorrect order.'''
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)