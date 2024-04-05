from fractions import Fraction

from timelength.dataclasses import ParsedTimeLength, Scale
from timelength.enums import BufferType, CharacterType
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
    result.valid = []
    skip_iteration = 0
    result.seconds = 0.0
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
                locale._connectors + locale._segmentors + locale._allowed_terms,
            )
            buffer_values.append(
                (
                    float(buffer) if buffer_alphanum == BufferType.NUMBER else buffer,
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

        if target_chartype == CharacterType.NUMBER:
            while next_index < len(content) and (
                character_type(content[next_index]) == target_chartype
                or content[next_index]
                in locale._decimal_separators + locale._thousand_separators
            ):
                if skip_thousand:
                    skip_thousand -= 1
                    continue

                if character_type(content[next_index]) == CharacterType.NUMBER:
                    buffer += content[next_index]
                elif content[next_index] in locale._decimal_separators:
                    if already_used_decimal:
                        result.invalid.append(
                            (
                                f"{content[next_index - 3]}{content[next_index - 2]}{content[next_index - 1]}{content[next_index]}",
                                "MALFORMED_DECIMAL",
                            )
                        )
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
                        (next_index + 3) < len(content)
                        and all(
                            character_type(content[next_index + i])
                            == CharacterType.NUMBER
                            for i in range(1, 4)
                        )
                    ):
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

        if current_alphanum == CharacterType.NUMBER:
            if (index + 2) < len(content) and (
                character_type(content[index + 2]) == CharacterType.NUMBER
            ):
                if content[index + 1] in locale._decimal_separators:
                    buffer += char
                    check_next(index + 1, CharacterType.NUMBER, True)
                elif content[index + 1] in locale._thousand_separators:
                    buffer += char
                    check_next(index + 1, CharacterType.NUMBER)
                else:
                    buffer += char
            else:
                buffer += char
        elif (
            not buffer
            and (index + 1) < len(content)
            and char in locale._decimal_separators
            and (character_type(content[index + 1]) == CharacterType.NUMBER)
        ):
            buffer += "0."
            check_next(index + 1, CharacterType.NUMBER, True)
        elif current_alphanum == CharacterType.ALPHABET:
            buffer += char
            check_next(index + 1, CharacterType.ALPHABET)
        elif (
            current_alphanum == CharacterType.SPECIAL
            and char
            not in locale._connectors
            + locale._segmentors
            + locale._allowed_terms
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

    potential_values = []
    skip_buffer = 0
    for index, item in enumerate(buffer_values):
        if skip_buffer:
            skip_buffer -= 1
            continue
        if not item:
            continue
        if item[1] == BufferType.UNKNOWN:
            result.invalid.append((item[0], "UNKNOWN_TERM"))
            if (
                index + 1 < len(buffer_values)
                and buffer_values[index + 1][0] in locale._connectors
            ):
                skip_buffer += 1
        else:
            potential_values.append(item)

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
    larger_numeral = False
    starts_with_modifier = False

    def handle_multiplier(text: str, index: int):
        nonlocal parsed_value, segment_value
        previous_numeric = False
        next_numeric = False
        next_term = False
        previous_value = 0.0
        next_value = 0.0
        if (index - 2) >= 0:
            previous_type = potential_values[index - 2][1]
            if previous_type == BufferType.NUMERAL:
                previous_numeric = True
                previous_value = locale._get_numeral(potential_values[index - 2][0])[
                    "value"
                ]
                if isinstance(previous_value, str):
                    previous_value = float(Fraction(previous_value))
            elif previous_type == BufferType.NUMBER:
                previous_numeric = True
                previous_value = potential_values[index - 2][0]
        if (index + 2) < len(potential_values):
            next_type = potential_values[index + 2][1]
            if next_type == BufferType.NUMERAL:
                next_numeric = True
                next_value = locale._get_numeral(potential_values[index + 2][0])[
                    "value"
                ]
                if isinstance(next_value, str):
                    next_value = float(Fraction(next_value))
            elif next_type == BufferType.NUMBER:
                next_numeric = True
                next_value = potential_values[index + 2][0]
            elif next_type == BufferType.SCALE:
                next_term = True
        if previous_numeric and next_numeric:
            potential_values[index + 2] = (
                previous_value * next_value,
                BufferType.NUMBER,
            )
        else:
            if (not previous_numeric and not next_numeric) or not next_term:
                result.invalid.append((text, "UNUSED_MULTIPLIER"))

    def handle_special(symbol: str):
        if symbol in previous_specials:
            result.invalid.append((symbol, "CONSECUTIVE_SPECIALS"))
        previous_specials.append(symbol)

    def handle_float(number: float):
        nonlocal parsed_value, segment_value

        if (
            previous_value_type_converted == BufferType.NUMBER
            and not starts_with_modifier
        ):
            if segment_value:
                result.invalid.append((segment_value, "LONELY_VALUE"))
                segment_value = None
            result.invalid.append((parsed_value, "CONSECUTIVE_VALUES"))
        parsed_value = number

    def handle_numeral(text: str, index: int):
        nonlocal \
            parsed_value, \
            current_numeral_type, \
            current_value_type_converted, \
            starts_with_modifier, \
            segment_value, \
            larger_numeral

        numeral = locale._get_numeral(text)
        numeral_value = (
            float(Fraction(numeral["value"]))
            if isinstance(numeral["value"], str)
            else float(numeral["value"])
        )
        current_numeral_type = numeral["type"]
        current_value_type_converted = BufferType.NUMBER

        if parsed_value is None:
            parsed_value = 0.0
            if (
                current_numeral_type == "modifiers"
                and index + 2 < len(potential_values)
                and potential_values[index + 2][1]
                in [BufferType.NUMBER, BufferType.NUMERAL]
            ):
                if potential_values[index + 2][1] == BufferType.NUMERAL:
                    numeral = locale._get_numeral(potential_values[index + 2][0])
                    if numeral["type"] == "multiplier":
                        parsed_value = numeral_value
                    else:
                        potential_values[index + 2] = (
                            numeral["value"] * numeral_value,
                            BufferType.NUMBER,
                        )
                else:
                    potential_values[index + 2] = (
                        potential_values[index + 2][0] * numeral_value,
                        BufferType.NUMBER,
                    )
                starts_with_modifier = True
            else:
                parsed_value = numeral_value
        elif current_numeral_type in ["modifiers", "thousands"]:
            parsed_value *= numeral_value
        elif current_numeral_type == "digits" and previous_numeral_type == "tens":
            larger_numeral = True
            parsed_value = parsed_value + numeral_value
        elif (
            current_numeral_type == "digits"
            and previous_numeral_type == "digits"
            and not larger_numeral
        ):
            parsed_value = float(f"{int(parsed_value)}{int(numeral_value)}")
        elif current_numeral_type in ["teens", "tens"] and previous_numeral_type in [
            "digits",
            "teens",
            "tens",
        ]:
            parsed_value = float(f"{int(parsed_value)}{int(numeral_value)}")
        elif (
            current_numeral_type in ["tens", "teens", "digits"]
            and previous_numeral_type == "thousands"
        ):
            parsed_value = parsed_value + numeral_value
            larger_numeral = True
        elif (
            previous_value_type_converted == BufferType.NUMBER
            or previous_numeral_type == "modifiers"
        ) and current_numeral_type not in ["thousands", "modifiers"]:
            if segment_value:
                result.invalid.append((segment_value, "LONELY_VALUE"))
                segment_value = None
            result.invalid.append((parsed_value, "CONSECUTIVE_VALUES"))
            larger_numeral = False
            parsed_value = numeral_value
        else:
            larger_numeral = False
            parsed_value = numeral_value

    def handle_scale(text: str):
        nonlocal parsed_value, segment_value, result, parsed_scale, current_numeral_type

        if index == 0:
            result.invalid.append((text, "LEADING_SCALE"))
        elif previous_value_type == BufferType.SCALE:
            result.invalid.append((text, "CONSECUTIVE_SCALES"))
        elif parsed_value is None and segment_value is None:
            result.invalid.append((text, "LONELY_SCALE"))

        if parsed_value is not None or segment_value is not None:
            scale: Scale
            scale = locale._get_scale(text)
            if scale:
                if not parsed_value:
                    parsed_value = 0.0
                if not segment_value:
                    segment_value = 0.0
                result.seconds += (parsed_value + segment_value) * scale.scale
                parsed_scale = scale

    for index, element in enumerate(potential_values):
        current_value = element[0]
        current_value_type = element[1]
        current_value_type_converted = current_value_type

        multiplier = False
        if current_value_type == BufferType.NUMERAL:
            multiplier = locale._get_numeral(current_value)
            multiplier = True if multiplier["type"] == "multiplier" else False
        if multiplier:
            if parsed_value is not None:
                handle_multiplier(current_value, index)
            else:
                result.invalid.append((current_value, "UNUSED_MULTIPLIER"))
                segment_value = None
                parsed_value = None
                handle_special(current_value)
        elif current_value_type == BufferType.SPECIAL:
            handle_special(current_value)
        elif current_value_type == BufferType.NUMBER:
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
                parsed_value = 0.0
            if not segment_value:
                segment_value = 0.0
            result.valid.append((parsed_value + segment_value, parsed_scale))
            parsed_value = None
            segment_value = None
            parsed_scale = None
            starts_with_modifier = False

        if current_value in locale._segmentors:
            if current_value in previous_segmentors:
                result.invalid.append((current_value, "CONSECUTIVE_SPECIALS"))
            if parsed_value is not None:
                if not segment_value:
                    segment_value = 0.0
                segment_value += parsed_value
            parsed_value = None
            starts_with_modifier = False
            previous_segmentors.append(current_value)
        else:
            previous_segmentors = []

    if (parsed_value is not None or segment_value is not None) and not parsed_scale:
        if not parsed_value:
            parsed_value = 0.0
        if not segment_value:
            segment_value = 0.0
        selected_value = parsed_value + segment_value
        if not strict and len(potential_values) == 1:
            result.valid.append((parsed_value + segment_value, locale._second))
            result.seconds += parsed_value + segment_value
        else:
            result.invalid.append(
                (
                    selected_value,
                    "LONELY_VALUE",
                )
            )

    if result.valid:
        if strict and not result.invalid:
            result.success = True
        elif not strict:
            result.success = True
