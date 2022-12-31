class Millisecond(object):
    def __init__(self, 
    scale: float = 0.001, 
    singular: str = "millisecond", 
    plural: str = "milliseconds",
    terms: list = ["ms", "millisecond", "Millisecond", "MILLISECOND", "milliseconds", "Milliseconds", "MILLISECONDS", "mil", "Mil", "MIL", "mils", "Mils", "MILS", "milsec", "Milsec", "MILSEC", "milsecs", "Milsecs", "MILSECS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Millisecond {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Second(object):
    def __init__(self,
    scale: float = 1,
    singular: str = "second",
    plural: str = "seconds",
    terms: list = ["s", "second", "Second", "SECOND", "seconds", "Seconds", "SECONDS", "sc", "Sc", "SC", "scs", "Scs", "SCS", "sec", "Sec", "SEC", "secs", "Secs", "SECS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Second {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Minute(object):
    def __init__(self,
    scale: float = 60,
    singular: str = "minute",
    plural: str = "minutes",
    terms: list = ["m", "minute", "Minute", "MINUTE", "minutes", "Minutes", "MINUTES", "mn", "Mn", "MN", "mns", "Mns", "MNS", "min", "Min", "MIN", "mins", "Mins", "MINS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Minute {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Hour(object):
    def __init__(self,
    scale: float = 3600,
    singular: str = "hour",
    plural: str = "hours",
    terms: list = ["h", "hour", "Hour", "HOUR", "hours", "Hours", "HOURS", "hr", "Hr", "HR", "hrs", "Hrs", "HRS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Hour {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Day(object):
    def __init__(self,
    scale: float = 86400,
    singular: str = "day",
    plural: str = "days",
    terms: list = ["d", "day", "Day", "DAY", "days", "Days", "DAYS", "dy", "Dy", "DY", "dys", "Dys", "DYS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Day {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Week(object):
    def __init__(self,
    scale: float = 604800,
    singular: str = "week",
    plural: str = "weeks",
    terms: list = ["w", "week", "Week", "WEEK", "weeks", "Weeks", "WEEKS", "wk", "Wk", "WK", "wks", "Wks", "WKS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Week {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Month(object):
    def __init__(self,
    scale: float = 2635200,
    singular: str = "month",
    plural: str = "months",
    terms: list = ["M", "month", "Month", "MONTH", "months", "Months", "MONTHS", "mth", "Mth", "MTH", "mths", "Mths", "MTHS", "mnth", "Mnth", "MNTH", "mnths", "Mnths", "MNTHS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Month {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Year(object):
    def __init__(self,
    scale: float = 31536000,
    singular: str = "year",
    plural: str = "years",
    terms: list = ["y", "year", "Year", "YEAR", "years", "Years", "YEARS", "yr", "Yr", "YR", "yrs", "Yrs", "YRS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Year {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Decade(object):
    def __init__(self,
    scale: float = 315360000,
    singular: str = "decade",
    plural: str = "decades",
    terms: list = ["D", "decade", "Decade", "DECADE", "decades", "Decades", "DECADES", "dc", "Dc", "DC", "dcs", "Decs", "DECS", "dec", "Dec", "DEC", "decs", "Decs", "DECS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Decade {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class Century(object):
    def __init__(self,
    scale: float = 3153600000,
    singular: str = "century",
    plural: str = "centuries",
    terms: list = ["c", "century", "Century", "CENTURY", "centuries", "Centuries", "CENTURIES", "cn", "Cn", "CN", "cns", "Cns", "CNS", "ct", "Ct", "CT", "cts", "Cts", "CTS", "cnt", "Cnt", "CNT", "cnts", "Cnts", "CNTS", "cent", "Cent", "CENT", "cents", "Cents", "CENTS"]):
        self.scale = scale
        self.singular = singular
        self.plural = plural
        self.terms = terms

    def __str__(self):
        return f"<Century {self.__dict__}>"

    def __repr__(self):
        return self.__str__()