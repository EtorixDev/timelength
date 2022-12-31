class Millisecond(object):
    def __init__(self):
        self.scale = 0.001
        self.terms = ["ms", "millisecond", "Millisecond", "MILLISECOND", "milliseconds", "Milliseconds", "MILLISECONDS", "mil", "Mil", "MIL", "mils", "Mils", "MILS", "milsec", "Milsec", "MILSEC", "milsecs", "Milsecs", "MILSECS"]
        self.singular = "millisecond"
        self.plural = "milliseconds"

class Second(object):
    def __init__(self):
        self.scale = 1
        self.terms = ["s", "second", "Second", "SECOND", "seconds", "Seconds", "SECONDS", "sc", "Sc", "SC", "scs", "Scs", "SCS", "sec", "Sec", "SEC", "secs", "Secs", "SECS"]
        self.singular = "second"
        self.plural = "seconds"

class Minute(object):
    def __init__(self):
        self.scale = 60
        self.terms = ["m", "minute", "Minute", "MINUTE", "minutes", "Minutes", "MINUTES", "mn", "Mn", "MN", "mns", "Mns", "MNS", "min", "Min", "MIN", "mins", "Mins", "MINS"]
        self.singular = "minute"
        self.plural = "minutes"

class Hour(object):
    def __init__(self):
        self.scale = 3600
        self.terms = ["h", "hour", "Hour", "HOUR", "hours", "Hours", "HOURS", "hr", "Hr", "HR", "hrs", "Hrs", "HRS"]
        self.singular = "hour"
        self.plural = "hours"

class Day(object):
    def __init__(self):
        self.scale = 86400
        self.terms = ["d", "day", "Day", "DAY", "days", "Days", "DAYS", "dy", "Dy", "DY", "dys", "Dys", "DYS"]
        self.singular = "day"
        self.plural = "days"

class Week(object):
    def __init__(self):
        self.scale = 604800
        self.terms = ["w", "week", "Week", "WEEK", "weeks", "Weeks", "WEEKS", "wk", "Wk", "WK", "wks", "Wks", "WKS"]
        self.singular = "week"
        self.plural = "weeks"

class Month(object):
    def __init__(self):
        self.scale = 2635200
        self.terms = ["M", "month", "Month", "MONTH", "months", "Months", "MONTHS", "mth", "Mth", "MTH", "mths", "Mths", "MTHS", "mnth", "Mnth", "MNTH", "mnths", "Mnths", "MNTHS"]
        self.singular = "month"
        self.plural = "months"

class Year(object):
    def __init__(self):
        self.scale = 31536000
        self.terms = ["y", "year", "Year", "YEAR", "years", "Years", "YEARS", "yr", "Yr", "YR", "yrs", "Yrs", "YRS"]
        self.singular = "year"
        self.plural = "years"

class Decade(object):
    def __init__(self):
        self.scale = 315360000
        self.terms = ["D", "decade", "Decade", "DECADE", "decades", "Decades", "DECADES", "dc", "Dc", "DC", "dcs", "Decs", "DECS", "dec", "Dec", "DEC", "decs", "Decs", "DECS"]
        self.singular = "decade"
        self.plural = "decades"

class Century(object):
    def __init__(self):
        self.scale = 3153600000
        self.terms = ["c", "century", "Century", "CENTURY", "centuries", "Centuries", "CENTURIES", "cn", "Cn", "CN", "cns", "Cns", "CNS", "ct", "Ct", "CT", "cts", "Cts", "CTS", "cnt", "Cnt", "CNT", "cnts", "Cnts", "CNTS", "cent", "Cent", "CENT", "cents", "Cents", "CENTS"]
        self.singular = "century"
        self.plural = "centuries"