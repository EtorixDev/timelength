from timelength.exceptions import *
from timelength.constants import *
from timelength.helper import *
from timelength.scales import *

class ParsedValues(object):
    def __init__(self, valid_values: list):
        self.valid = valid_values
        self.milliseconds = None
        self.seconds = None
        self.minutes = None
        self.hours = None
        self.days = None
        self.weeks = None
        self.months = None
        self.years = None
        self.decades = None
        self.centuries = None
        for length in valid_values:
            if length[1] in Millisecond().terms: 
                self.milliseconds = length[0]
            if length[1] in Second().terms: 
                self.seconds = length[0]
            if length[1] in Minute().terms: 
                self.minutes = length[0]
            if length[1] in Hour().terms: 
                self.hours = length[0]
            if length[1] in Day().terms: 
                self.days = length[0]
            if length[1] in Week().terms: 
                self.weeks = length[0]
            if length[1] in Month().terms: 
                self.months = length[0]
            if length[1] in Year().terms: 
                self.years = length[0]
            if length[1] in Decade().terms: 
                self.decades = length[0]
            if length[1] in Century().terms: 
                self.centuries = length[0]

    def __str__(self):
        return f"<ParsedValues {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class ParsedTimeLength(object):
    def __init__(self, total_seconds, valid_values):
        self.total_seconds = total_seconds
        self.valid_values = valid_values

class TimeLength(object):
    def __init__(self, passed_value, strict = False):
        self.passed_value = passed_value
        self.strict = strict
        self.__parsed_time_length = self.__parse(self.passed_value, self.strict)
        self.__valid_values = self.__parsed_time_length.valid_values
        self.total_seconds = self.__parsed_time_length.total_seconds
        self.parsed_value = ParsedValues(self.__valid_values)

    def __str__(self):
        return f"<TimeLength \"{self.passed_value}\">"

    def __repr__(self):
        return self.__str__()

    def __parse(self, passed_value, strict):
        buffer = ""
        potential_values = []
        valid_values = []
        skip_iteration = 0
        total_seconds = 0
        last_alphanum = None

        for index, char in enumerate(passed_value):
            # Skip iterations due to decimal encounter
            if skip_iteration > 0:
                skip_iteration -= 1
                continue

            # Check if decimal number is encountered
            if (index + 2) < len(passed_value) and passed_value[index + 1] == "." and passed_value[index + 2].isdigit():
                if isfloat(char):
                    char += "."
                else:
                    char = "0."
                future_index = index + 2
                skip_iteration = 1
                while future_index < len(passed_value) and passed_value[future_index].isdigit():
                    char += passed_value[future_index]
                    future_index += 1
                    skip_iteration += 1
            
            # Catch special characters such as !#$+
            alphanum = check_alphanumeric(char)
            if char in SEPERATORS:
                if buffer and not buffer.strip() in CONNECTORS:
                    potential_values.append(buffer)
                buffer = ""
                last_alphanum = None
            elif not alphanum and (index + 1) < len(passed_value):
                if buffer:
                    potential_values.append(buffer)
                buffer = ""
                index += 1
                skip_iteration = 0
                to_check = passed_value[index]
                # Check if subsequent characters are also non-alphanumeric
                while index < len(passed_value) and to_check is not None and to_check not in SEPERATORS and not isfloat(to_check) and not check_alphanumeric(to_check):
                    char += passed_value[index]
                    skip_iteration += 1
                    index += 1
                    if index < len(passed_value):
                        to_check = passed_value[index]
                potential_values.append(char)
            # Only happens if the passed value ends in a single non-alphanumeric value
            elif not alphanum:
                if buffer:
                    potential_values.append(buffer)
                buffer = char
            else:
                if (alphanum and last_alphanum and alphanum != last_alphanum):
                    potential_values.append(buffer)
                    buffer = char
                else:
                    buffer += char
                last_alphanum = alphanum
        potential_values.append(buffer)

        index = 0
        input_length = None
        input_scale = None
        preceeding_num = False
        preceeding_alpha = True
        invalid_values = [item for item in potential_values if item and not isfloat(item) and item not in ABBREVIATIONS]
        potential_values = [item for item in potential_values if item and item not in invalid_values]
        # If invalid and strict, error
        # If not strict, ignore invalid and proceed
        if invalid_values and self.strict:
            raise InvalidValue(f"Input TimeLength \"{passed_value}\" contains {'invalid values' if len(invalid_values) > 1 else 'an invalid value'}: {invalid_values}")
        for item in potential_values:
            if isfloat(item):
                if preceeding_num is True and strict is True:
                    raise InvalidOrder(f"Input TimeLength \"{passed_value}\" contains multiple subsequent Values with no paired Scales: {potential_values}")
                input_length = float(item)
                preceeding_alpha = False
                preceeding_num = True
            else:
                if index == 0 and preceeding_alpha and strict is True:
                    raise InvalidOrder(f"Input TimeLength \"{passed_value}\" starts with a Scale rather than a Value: {potential_values}")
                elif preceeding_alpha is True and strict is True:
                    raise InvalidOrder(f"Input TimeLength \"{passed_value}\" contains multiple subsequent Scales with no paired Values: {potential_values}")
                if preceeding_num and item in ABBREVIATIONS:
                    # Calculate proper Value THEN Scale pairs
                    input_scale = item
                    for scale in SCALES:
                        if input_scale in scale.terms:
                            total_seconds += input_length * scale.scale
                            if input_length == 1:
                                input_scale = scale.singular
                            else:
                                input_scale = scale.plural
                            break
                    preceeding_num = False
                    preceeding_alpha = True
            index += 1
            # Append pairs to valid_values to be returned
            if input_length and input_scale:
                valid_values.append((input_length, input_scale))
                input_length = None
                input_scale = None
        
        if not valid_values:
            raise InvalidValue(f"Input TimeLength \"{passed_value}\" contains no valid Value and Scale pairs.")

        return ParsedTimeLength(total_seconds, valid_values)

    def to_milliseconds(self, max_precision = 2):
        return round(self.total_seconds / float(Millisecond().scale), max_precision)

    def to_seconds(self, max_precision = 2):
        return round(self.total_seconds, max_precision)

    def to_minutes(self, max_precision = 2):
        return round(self.total_seconds / float(Minute().scale), max_precision)

    def to_hours(self, max_precision = 2):
        return round(self.total_seconds / float(Hour().scale), max_precision)

    def to_days(self, max_precision = 2):
        return round(self.total_seconds / float(Day().scale), max_precision)

    def to_weeks(self, max_precision = 2):
        return round(self.total_seconds / float(Week().scale), max_precision)

    def to_months(self, max_precision = 2):
        return round(self.total_seconds / float(Month().scale), max_precision)

    def to_years(self, max_precision = 2):
        return round(self.total_seconds / float(Year().scale), max_precision)

    def to_decades(self, max_precision = 2):
        return round(self.total_seconds / float(Decade().scale), max_precision)

    def to_centuries(self, max_precision = 2):
        return round(self.total_seconds / float(Century().scale), max_precision)