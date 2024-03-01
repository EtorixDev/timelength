from fractions import Fraction

from timelength.dataclasses import ParsedTimeLength, Scale
from timelength.enums import BufferType, CharacterType
from timelength.errors import (
    InvalidValue,
    LeadingScale,
    MultipleConsecutiveScales,
    MultipleConsecutiveSpecials,
    MultipleConsecutiveValues,
    NoValidValue,
)
from timelength.locales import Locale
from timelength.utils import buffer_type, character_type, remove_diacritics


def parser_one(
    content: str,
    strict: bool,
    locale: Locale,
    result: ParsedTimeLength,
):
    content = remove_diacritics(content)
    buffer = ""
    buffer_values = []
    valid_values = []
    skip_iteration = 0
    result.seconds = 0
    last_alphanum = None
    current_alphanum = None

    def save_buffer():
        nonlocal buffer
        if buffer:
            numerals = locale._numerals
            scales = locale._scales
            buffer_alphanum = buffer_type(
                buffer,
                [term for scale in scales for term in scale.terms],
                [
                    term
                    for numeral in numerals
                    if "terms" in numerals[numeral]
                    for term in numerals[numeral]["terms"]
                ],
                locale._connectors + locale._segmentors + locale._allowed_symbols,
            )
            buffer_values.append(
                (
                    float(buffer) if buffer_alphanum == BufferType.FLOAT else buffer,
                    buffer_alphanum,
                )
            )
            buffer = ""

    def check_next(
        next_index: int,
        target_chartype: CharacterType,
        decimal_only: bool = False,
    ):
        nonlocal content, buffer, skip_iteration
        skip_thousand = 0
        already_used_decimal = False

        if target_chartype == CharacterType.FLOAT:
            while next_index < len(content) and (
                character_type(content[next_index]) == target_chartype
                or content[next_index]
                in locale._decimal_separators + locale._thousand_separators
            ):
                if skip_thousand:
                    skip_thousand -= 1
                    continue

                if character_type(content[next_index]) == CharacterType.FLOAT:
                    buffer += content[next_index]
                elif content[next_index] in locale._decimal_separators:
                    if already_used_decimal:
                        if strict:
                            result.invalid.append(
                                (
                                    f"{content[next_index - 3]}{content[next_index - 2]}{content[next_index - 1]}{content[next_index]}",
                                    "MALFORMED_DECIMAL",
                                )
                            )
                            raise InvalidValue(
                                "Input TimeLength contains a malformed decimal representation."
                            )
                        else:
                            next_index += 1
                            skip_iteration += 1
                            buffer = ""
                            break
                    buffer += "."
                    decimal_only = True
                    already_used_decimal = True
                elif (
                    not decimal_only
                    and content[next_index] in locale._thousand_separators
                ):
                    if not (
                        next_index + 3 < len(content)
                        and all(
                            character_type(content[next_index + i])
                            == CharacterType.FLOAT
                            for i in range(1, 4)
                        )
                    ):
                        if (
                            next_index + 2 < len(content)
                            and character_type(content[next_index + 1])
                            == CharacterType.FLOAT
                            and content[next_index + 2] in locale._connectors
                        ):
                            pass
                        elif (
                            next_index + 3 < len(content)
                            and character_type(content[next_index + 1])
                            == CharacterType.FLOAT
                            and character_type(content[next_index + 2])
                            == CharacterType.FLOAT
                            and content[next_index + 3] in locale._connectors
                        ):
                            pass
                        elif (
                            next_index + 1 < len(content)
                            and character_type(content[next_index + 1])
                            == CharacterType.FLOAT
                        ):
                            if strict:
                                result.invalid.append(
                                    (
                                        f"{content[next_index - 1]}{content[next_index]}{content[next_index + 1]}",
                                        "MALFORMED_THOUSANDS",
                                    )
                                )
                                raise InvalidValue(
                                    "Input TimeLength contains a malformed thousands representation."
                                )
                            else:
                                next_index += 1
                                skip_iteration += 1
                                buffer = ""
                        break
                    else:
                        for num in range(1, 4):
                            buffer += content[next_index + num]

                        next_index += 4
                        skip_iteration += 4
                        skip_thousand = 4
                        continue
                next_index += 1
                skip_iteration += 1
        else:
            while next_index < len(content) and (
                character_type(content[next_index]) == target_chartype
            ):
                buffer += content[next_index]
                next_index += 1
                skip_iteration += 1

    for index, char in enumerate(content):
        if skip_iteration > 0:
            skip_iteration -= 1
            continue

        current_alphanum = character_type(char)
        if buffer and index and last_alphanum != current_alphanum:
            save_buffer()

        if current_alphanum == CharacterType.FLOAT:
            if (index + 2) < len(content) and (
                character_type(content[index + 2]) == CharacterType.FLOAT
            ):
                if content[index + 1] in locale._decimal_separators:
                    buffer += char
                    check_next(index + 1, CharacterType.FLOAT, True)
                elif content[index + 1] in locale._thousand_separators:
                    buffer += char
                    check_next(index + 1, CharacterType.FLOAT)
                else:
                    buffer += char
            else:
                buffer += char
        elif (
            not buffer
            and (index + 1) < len(content)
            and char in locale._decimal_separators
            and (character_type(content[index + 1]) == CharacterType.FLOAT)
        ):
            buffer += "0."
            check_next(index + 1, CharacterType.FLOAT, True)
        elif current_alphanum == CharacterType.ALPHABET:
            buffer += char
            check_next(index + 1, CharacterType.ALPHABET)
        elif (
            current_alphanum == CharacterType.SPECIAL
            and char
            not in locale._connectors
            + locale._segmentors
            + locale._allowed_symbols
            + locale._decimal_separators
            + locale._thousand_separators
        ):
            buffer += char
            check_next(index + 1, CharacterType.SPECIAL)
        else:
            buffer += char
            save_buffer()

        last_alphanum = current_alphanum

    if buffer:
        save_buffer()

    invalid_values = [
        (item[0], "UNKNOWN_TERM")
        for item in buffer_values
        if item and item[1] == BufferType.UNKNOWN
    ]
    result.invalid = invalid_values
    result.valid = valid_values
    potential_values = [
        item
        for item in buffer_values
        if (item[0], "UNKNOWN_TERM") not in invalid_values
    ]
    if invalid_values and strict:
        raise InvalidValue(
            f"Input TimeLength contains {'invalid values' if len(invalid_values) > 1 else 'an invalid value'}."
        )
    parsed_value = None
    segment_value = None
    parsed_scale = None
    previous_specials = []
    previous_segmentors = []
    current_value_type = None
    current_value_type_converted = None
    previous_value_type = None
    previous_value_type_converted = None
    current_numeral_type = None
    previous_numeral_type = None
    starts_with_modifier = False

    def handle_multiplier(text: str, index: int):
        nonlocal parsed_value, segment_value
        previous_modifier = False
        next_modifier = False
        if (index - 2) >= 0 and (index - 2) < len(potential_values):
            previous_modifier = locale._get_numeral(potential_values[index - 2][0])
            previous_modifier = (
                True if previous_modifier["type"] == "modifiers" else False
            )
        if (
            not previous_modifier
            and (index - 2) >= 0
            and (index - 2) < len(potential_values)
        ):
            next_modifier = locale._get_numeral(potential_values[index + 2][0])
            next_modifier = True if next_modifier["type"] == "modifiers" else False
        if (
            previous_modifier
            and index + 2 < len(potential_values)
            and potential_values[index + 2][1] in [BufferType.FLOAT, BufferType.NUMERAL]
        ):
            if potential_values[index + 2][1] == BufferType.NUMERAL:
                numeral = locale._get_numeral(potential_values[index + 2][0])
                potential_values[index + 2] = (
                    numeral["value"] * parsed_value,
                    BufferType.FLOAT,
                )
            else:
                potential_values[index + 2] = (
                    potential_values[index + 2][0] * parsed_value,
                    BufferType.FLOAT,
                )
        if (
            next_modifier
            and index - 2 >= 0
            and potential_values[index - 2][1] in [BufferType.FLOAT, BufferType.NUMERAL]
        ):
            if potential_values[index - 2][1] == BufferType.NUMERAL:
                numeral = locale._get_numeral(potential_values[index + 2][0])
                potential_values[index - 2] = (
                    numeral["value"] * parsed_value,
                    BufferType.FLOAT,
                )
            else:
                potential_values[index - 2] = (
                    potential_values[index - 2][0] * parsed_value,
                    BufferType.FLOAT,
                )
        elif not previous_modifier and not next_modifier and strict:
            result.invalid.append((text, "MISPLACED_MODIFIER_MULTIPLIER"))
            raise InvalidValue("Input TimeLength contains a misplaced multiplier.")
        else:
            segment_value = None
            parsed_value = None

    def handle_special(symbol: str):
        if symbol in previous_specials and strict:
            result.invalid.append((symbol, "CONSECUTIVE_SPECIALS"))
            raise MultipleConsecutiveSpecials(
                "Input TimeLength contains consecutive identical special items."
            )
        previous_specials.append(symbol)

    def handle_float(number: float):
        nonlocal parsed_value, current_numeral_type, current_value_type_converted
        current_numeral_type = None

        if (
            strict
            and previous_value_type_converted == BufferType.FLOAT
            and not starts_with_modifier
        ):
            result.invalid.append((number, "CONSECUTIVE_VALUES"))
            raise MultipleConsecutiveValues(
                "Input TimeLength contains consecutive Values with no paired Scales."
            )
        parsed_value = number

    def handle_numeral(text: str, index: int):
        nonlocal \
            parsed_value, \
            current_numeral_type, \
            current_value_type_converted, \
            starts_with_modifier

        numeral = locale._get_numeral(text)
        numeral_value = (
            float(Fraction(numeral["value"]))
            if isinstance(numeral["value"], str)
            else float(numeral["value"])
        )
        current_numeral_type = numeral["type"]
        current_value_type_converted = BufferType.FLOAT

        if parsed_value is None:
            parsed_value = 0
            if (
                current_numeral_type == "modifiers"
                and index + 2 < len(potential_values)
                and potential_values[index + 2][1]
                in [BufferType.FLOAT, BufferType.NUMERAL]
            ):
                if potential_values[index + 2][1] == BufferType.NUMERAL:
                    numeral = locale._get_numeral(potential_values[index + 2][0])
                    if numeral["type"] == "modifier_multiplier":
                        parsed_value = numeral_value
                    else:
                        potential_values[index + 2] = (
                            numeral["value"] * numeral_value,
                            BufferType.FLOAT,
                        )
                else:
                    potential_values[index + 2] = (
                        potential_values[index + 2][0] * numeral_value,
                        BufferType.FLOAT,
                    )
                starts_with_modifier = True
            else:
                parsed_value = numeral_value
        elif current_numeral_type in ["modifiers", "thousands"]:
            parsed_value *= numeral_value
        elif current_numeral_type == "digits" and previous_numeral_type == "tens":
            parsed_value = parsed_value + numeral_value
            current_numeral_type = None
        elif current_numeral_type == "digits" and previous_numeral_type == "digits":
            parsed_value = float(f"{int(parsed_value)}{int(numeral_value)}")
            current_numeral_type = None
        elif current_numeral_type in ["teens", "tens"] and previous_numeral_type in [
            "digits",
            "teens",
            "tens",
        ]:
            parsed_value = float(f"{int(parsed_value)}{int(numeral_value)}")
            current_numeral_type = None
        elif (
            previous_value_type_converted == BufferType.FLOAT
            or previous_numeral_type == "modifiers"
        ) and current_numeral_type not in ["thousands", "modifiers"]:
            if strict:
                result.invalid.append((text, "CONSECUTIVE_VALUES"))
                raise MultipleConsecutiveValues(
                    "Input TimeLength contains consecutive Values with no paired Scales."
                )
            else:
                parsed_value = numeral_value
        else:
            parsed_value = numeral_value

    def handle_scale(text: str):
        nonlocal parsed_value, segment_value, result, parsed_scale, current_numeral_type
        current_numeral_type = None

        if index == 0:
            result.invalid.append((text, "LEADING_SCALE"))
            if strict:
                raise LeadingScale(
                    "Input TimeLength starts with a Scale rather than a Value."
                )
        elif previous_value_type == BufferType.SCALE:
            result.invalid.append((text, "CONSECUTIVE_SCALES"))
            if strict:
                raise MultipleConsecutiveScales(
                    "Input TimeLength contains consecutive Scales with no paired Values."
                )
        elif parsed_value is None and segment_value is None:
            result.invalid.append((text, "LONELY_SCALE"))
            if strict:
                raise InvalidValue(
                    "Input TimeLength contains a Scale with no paired Value."
                )

        if parsed_value is not None or segment_value is not None:
            scale: Scale
            scale = locale._get_scale(text)
            if scale:
                if not parsed_value:
                    parsed_value = 0
                if not segment_value:
                    segment_value = 0
                result.seconds += (parsed_value + segment_value) * scale.scale
                parsed_scale = scale

    for index, element in enumerate(potential_values):
        current_value = element[0]
        current_value_type = element[1]
        current_value_type_converted = current_value_type

        modifier_multiplier = False
        if current_value_type == BufferType.NUMERAL:
            modifier_multiplier = locale._get_numeral(current_value)
            modifier_multiplier = (
                True if modifier_multiplier["type"] == "modifier_multiplier" else False
            )
        if modifier_multiplier:
            if parsed_value is None and strict:
                result.invalid.append((current_value, "MISPLACED_MODIFIER_MULTIPLIER"))
                raise InvalidValue(
                    "Input TimeLength contains a misplaced modifier-multiplier."
                )
            elif parsed_value is not None:
                handle_multiplier(current_value, index)
            else:
                segment_value = None
                parsed_value = None
                handle_special(current_value)
        elif current_value_type == BufferType.SPECIAL:
            handle_special(current_value)
        elif current_value_type == BufferType.FLOAT:
            handle_float(current_value)
        elif current_value_type == BufferType.NUMERAL:
            handle_numeral(current_value, index)
        elif current_value_type == BufferType.SCALE:
            handle_scale(current_value)

        if (
            current_value_type != BufferType.SPECIAL
            or current_value in locale._segmentors
        ):
            previous_value_type = current_value_type
            previous_numeral_type = current_numeral_type
            previous_value_type_converted = current_value_type_converted
            current_value_type_converted = None
            current_numeral_type = None
            current_value_type = None
            previous_specials = []

        if (parsed_value is not None or segment_value is not None) and parsed_scale:
            if not parsed_value:
                parsed_value = 0
            if not segment_value:
                segment_value = 0
            result.valid.append((parsed_value + segment_value, parsed_scale))
            parsed_value = None
            segment_value = None
            parsed_scale = None
            starts_with_modifier = False

        if current_value in locale._segmentors:
            if strict and current_value in previous_segmentors:
                result.invalid.append((current_value, "CONSECUTIVE_SPECIALS"))
                raise MultipleConsecutiveSpecials(
                    "Input TimeLength contains consecutive identical special items."
                )
            else:
                if parsed_value is not None:
                    if not segment_value:
                        segment_value = 0
                    segment_value += parsed_value
                parsed_value = None
                starts_with_modifier = False
                previous_segmentors.append(current_value)
        else:
            previous_segmentors = []

    if (parsed_value is not None or segment_value is not None) and not parsed_scale:
        if not parsed_value:
            parsed_value = 0
        if not segment_value:
            segment_value = 0
        if not strict:
            result.valid.append((parsed_value + segment_value, locale._second))
            result.seconds += parsed_value + segment_value
        else:
            result.invalid.append(
                (
                    parsed_value
                    if parsed_value is not None
                    else segment_value
                    if segment_value is not None
                    else "",
                    "LONELY_VALUE",
                )
            )
            raise InvalidValue(
                "Input TimeLength contains a Value with no paired Scale."
            )

    if not valid_values and strict:
        raise NoValidValue("Input TimeLength contains no valid Value and Scale pairs.")

    result.success = True if valid_values else False
