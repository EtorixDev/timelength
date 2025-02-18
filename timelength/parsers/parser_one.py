from __future__ import annotations

from copy import copy
from datetime import timedelta
from typing import cast

from timelength.dataclasses import Buffer, Numeral, ParsedTimeLength, Scale
from timelength.enums import CharacterType, FailureFlags, NumeralType, ValueType
from timelength.locales import Locale
from timelength.parsers.common import character_type, is_int, remove_diacritics, value_type


# Private methods could be moved to common.py if they become used in multiple parsers.
def _detect_number_segment(content: str, locale: Locale) -> str:
    """Detect a number segment in the content based on the locale settings."""
    # content = content[index:]
    segment_index: int = 0
    segment_str: str = ""
    hhmmss_fraction_delimiters = locale.hhmmss_delimiters + locale.fraction_delimiters
    min_thousand_digits: int = 3 if not locale.settings.allow_thousands_lacking_digits else 1
    encountered_hhmmss_or_fraction: bool = False
    trailing_connectors: int = 0

    # Lookahead for all characters in the number segment.
    while segment_index < len(content) and (
        character_type(current_char := content[segment_index]) is CharacterType.NUMBER
        or current_char in locale.connectors + locale.delimiters
    ):
        prev_char = content[segment_index - 1] if segment_index > 0 else None
        previous_char_type = character_type(prev_char) if prev_char else None
        next_char = content[segment_index + 1] if (segment_index + 1) < len(content) else None
        next_char_type = character_type(next_char) if next_char else None
        encountered_hhmmss_or_fraction = encountered_hhmmss_or_fraction or current_char in hhmmss_fraction_delimiters
        if current_char in locale.connectors:
            trailing_connectors += 1
        else:
            trailing_connectors = 0
        # Check if the number segment needs to be broken due to:
        # - A segmentor (which is also a delimiter) which is not part of a valid format.
        # - A connector surrounded by a non-connector non-delimiter character which is not part of a valid format.
        if (
            current_char in locale.connectors
            and (
                prev_char not in locale.connectors + locale.delimiters
                or next_char not in locale.connectors + locale.delimiters
            )
        ) or (current_char in locale.segmentors):
            if (
                current_char in locale.decimal_delimiters
                and next_char
                and character_type(next_char) is not CharacterType.NUMBER
            ):
                next_non_symbol_is_number: bool = False
                temp_index: int = segment_index + 1
                while temp_index < len(content):
                    char_type = character_type(content[temp_index])
                    if char_type is not CharacterType.SYMBOL:
                        next_non_symbol_is_number = char_type is CharacterType.NUMBER
                        break
                    temp_index += 1

                if not next_non_symbol_is_number:
                    segment_str += current_char
                break
            elif (
                current_char in locale.thousand_delimiters
                and prev_char not in hhmmss_fraction_delimiters
                and next_char not in hhmmss_fraction_delimiters
            ):
                previous_char_type = character_type(prev_char) if prev_char else None
                next_char_type = character_type(next_char) if next_char else None
                if (
                    (next_char in locale.connectors and next_char != current_char)
                    or (next_char in locale.thousand_delimiters and next_char not in locale.connectors)
                    or (
                        current_char in locale.connectors
                        and previous_char_type is CharacterType.NUMBER
                        and next_char_type is CharacterType.NUMBER
                        and not all(
                            (segment_index + i) < len(content)
                            and character_type(content[segment_index + i]) is CharacterType.NUMBER
                            for i in range(1, min_thousand_digits + 1)
                        )
                    )
                    or (
                        previous_char_type is CharacterType.NUMBER
                        and next_char_type is not CharacterType.NUMBER
                        and next_char not in locale.connectors + locale.delimiters
                    )
                    or (
                        next_char_type is CharacterType.NUMBER
                        and previous_char_type is not CharacterType.NUMBER
                        and not encountered_hhmmss_or_fraction
                    )
                ):
                    break
            elif (
                current_char in locale.connectors
                and current_char not in hhmmss_fraction_delimiters
                and prev_char not in hhmmss_fraction_delimiters
                and next_char not in hhmmss_fraction_delimiters
                and (next_char_type is CharacterType.NUMBER)
                and not encountered_hhmmss_or_fraction
            ):
                break

        segment_str += current_char
        segment_index += 1

    # Remove trailing connectors so they can be invalidated per CONSECUTIVE_CONNECTOR should that be applicable.
    trailing_connectors = trailing_connectors - 1 if trailing_connectors else 0
    return segment_str[:-trailing_connectors] if trailing_connectors else segment_str


def _parse_number(content: str, locale: Locale) -> float | tuple[str, FailureFlags]:
    """Parse a number segment in the content based on the locale settings."""
    content = content.strip()
    num: str = ""
    decimal_locked: bool = False
    min_thousand_digits: int = 3 if not locale.settings.allow_thousands_lacking_digits else 1

    for con in locale.connectors:
        content = content.strip(con)

    for index, char in enumerate(content):
        if character_type(char) is CharacterType.NUMBER:
            num += char
        elif char in locale.decimal_delimiters:
            # Prevent double decimals and decimals with no following number.
            if (
                decimal_locked
                or (
                    (more_characters := (index + 1) < len(content))
                    and character_type(content[index + 1]) is not CharacterType.NUMBER
                )
                or (not more_characters and not locale.settings.allow_decimals_lacking_digits)
            ):
                return (content, FailureFlags.MALFORMED_DECIMAL)

            num += "."
            decimal_locked = True
        elif not decimal_locked and char in locale.thousand_delimiters:
            # Prevent thousands with less than min_thou_digits following
            # digits and thousands with more than 3 digits.
            if not (
                index
                and character_type(content[index - 1]) is CharacterType.NUMBER
                and (index + min_thousand_digits) < len(content)
                and all(
                    character_type(content[index + i]) is CharacterType.NUMBER
                    for i in range(1, (min_thousand_digits + 1))
                )
            ) or (
                not locale.settings.allow_thousands_extra_digits
                and (index + 4) < len(content)
                and character_type(content[index + 4]) is CharacterType.NUMBER
            ):
                return (content, FailureFlags.MALFORMED_THOUSAND)

    return float(num)


def _parse_fraction(content: str, locale: Locale) -> float | list[tuple[str, FailureFlags]]:
    """Parse a fraction segment in the content based on the locale settings."""

    fraction_segments: list[str] = content.split(locale.fraction_delimiters[0])

    if len(fraction_segments) > 2 or any(not segment for segment in fraction_segments):
        return [(content, FailureFlags.MALFORMED_FRACTION)]

    # Only allow one connector between the numerator or denominator and the fraction delimiter.
    num_connectors: int = 0
    for char in reversed(fraction_segments[0]):
        if char in locale.connectors:
            num_connectors += 1
        else:
            break

    if num_connectors > 1:
        return [(content, FailureFlags.MALFORMED_FRACTION)]

    num_connectors = 0
    for char in fraction_segments[1]:
        if char in locale.connectors:
            num_connectors += 1
        else:
            break

    if num_connectors > 1:
        return [(content, FailureFlags.MALFORMED_FRACTION)]

    numerator = _parse_number(fraction_segments[0], locale)
    denominator = _parse_number(fraction_segments[1], locale)

    # Falsy check for denominator to prevent division by zero.
    failures: list[tuple[str, FailureFlags]] = []
    if isinstance(numerator, tuple):
        failures.append(numerator)
    if isinstance(denominator, tuple):
        failures.append(denominator)
    if not denominator:
        failures.append((content, FailureFlags.MALFORMED_FRACTION))

    if failures:
        failure_flag = FailureFlags.NONE
        for _, flag in failures:
            failure_flag |= flag
        return [(content, failure_flag | FailureFlags.MALFORMED_FRACTION)]

    return cast(float, numerator) / cast(float, denominator)


def _parse_hhmmss(content: str, locale: Locale) -> list[float] | list[tuple[str, FailureFlags]]:
    """Parse an HHMMSS segment in the content based on the locale settings."""

    hhmmss_possible: list[str] = content.split(locale.hhmmss_delimiters[0])
    hhmmss_segments: list[float] = []
    failures: list[tuple[str, FailureFlags]] = []

    if any(not segment for segment in hhmmss_possible):
        return [(content, FailureFlags.MALFORMED_HHMMSS)]

    for hhmmss_segment in hhmmss_possible:
        # Allow up to 2 locale.connectors at the start of an hhmmss segment.
        # Do not allow any locale.connectors at the end of an hhmmss segment.
        num_connectors: int = 0
        for char in hhmmss_segment:
            if char in locale.connectors:
                num_connectors += 1
            else:
                break

        if num_connectors > 2:
            return [(content, FailureFlags.MALFORMED_HHMMSS)]

        for char in reversed(hhmmss_segment):
            if char in locale.connectors:
                return [(content, FailureFlags.MALFORMED_HHMMSS)]
            else:
                break

        if any(item in hhmmss_segment for item in locale.fraction_delimiters):
            value = _parse_fraction(hhmmss_segment, locale)
            if isinstance(value, list):
                for val, flag in value:
                    failures.append((val, flag))
        else:
            value = _parse_number(hhmmss_segment, locale)
            if isinstance(value, tuple):
                failures.append(value)

        if not isinstance(value, float):
            failures.append((hhmmss_segment, FailureFlags.MALFORMED_HHMMSS))
            continue

        hhmmss_segments.append(value)

    if failures:
        failure_flag = FailureFlags.NONE
        for _, flag in failures:
            failure_flag |= flag
        return [(content, failure_flag | FailureFlags.MALFORMED_HHMMSS)]

    return hhmmss_segments


def _get_unique_scale(encountered_scales: dict[Scale, Scale], scale: Scale) -> Scale:
    """Return or create a unique scale and store it in a dictionary for future calls during this parsing call."""

    if scale not in encountered_scales:
        encountered_scales[scale] = copy(scale)

    return encountered_scales[scale]


def _segment_content(
    content: str, locale: Locale, invalid: list[tuple[float | str, FailureFlags]]
) -> list[tuple[str | float | list[tuple[float, Scale, str]], ValueType]]:
    """Segment the content into potential values based on the locale settings."""

    buffer: Buffer = Buffer()
    previous_chartype: CharacterType | None = None
    current_chartype: CharacterType | None = None
    skip_iterations: int = 0
    skip_save: bool = False
    usable_scales: list[Scale] = locale.usable_scales
    usable_numerals: list[Numeral] = locale.usable_numerals
    scale_terms: list[str] = [term for scale in usable_scales for term in scale.terms]
    numeral_terms: list[str] = [term for numeral in usable_numerals for term in numeral.terms]
    potential_values: list[tuple[str | float | list[tuple[float, Scale, str]], ValueType]] = []

    def save_buffer() -> None:
        buffer_value_type: ValueType = value_type(buffer.value, scale_terms, numeral_terms, locale.specials)

        potential_values.append(
            (float(buffer.value) if buffer_value_type is ValueType.NUMBER else buffer.value, buffer_value_type)
        )

        buffer.value = ""

    def handle_number(content: str) -> float | None:
        value = _parse_number(content, locale)
        if isinstance(value, tuple):
            invalid.append((value[0], value[1]))
            value = None
        return value

    def handle_fraction(content: str) -> float | None:
        value = _parse_fraction(content, locale)
        if isinstance(value, list):
            for val, flag in value:
                invalid.append((val, flag))
            return None
        else:
            return value

    def handle_hhmmss(content: str) -> list[float] | None:
        value = _parse_hhmmss(content, locale)
        if isinstance(value[0], float):
            value = cast(list[float], value)
            return value
        else:
            value = cast(list[tuple[str, FailureFlags]], value)
            for val, flag in value:
                invalid.append((val, flag))
            return None

    # Enumerate over each character in the content to group them by CharacterType.
    for index, char in enumerate(content):
        # Skip iterations due to lookahead during number segment parsing.
        if skip_iterations:
            skip_iterations -= 1
            # previous_chartype = None
            continue

        current_chartype = character_type(char)
        if not skip_save and buffer.value and current_chartype != previous_chartype:
            save_buffer()

        skip_save = False

        decimal_delim: bool = char in locale.decimal_delimiters
        previous_special: bool = index == 0 or previous_chartype is CharacterType.SYMBOL
        next_number: bool = (index + 1 < len(content)) and character_type(content[index + 1]) is CharacterType.NUMBER

        if decimal_delim and previous_special and next_number:
            # Required conditions for decimal numbers with no leading zero.
            buffer.value += f"0{char}"
            skip_save = True
            continue

        if current_chartype is CharacterType.NUMBER:
            detected_number_segment: str = _detect_number_segment(content[index:], locale)
            number_segment: str = buffer.value + detected_number_segment
            buffer.value = ""
            skip_iterations = len(detected_number_segment) - 1

            if any(item in number_segment for item in locale.hhmmss_delimiters):
                for delim in locale.hhmmss_delimiters:
                    number_segment = number_segment.replace(delim, locale.hhmmss_delimiters[0])

                vals: list[float] | None = handle_hhmmss(number_segment)

                if vals is None:
                    continue

                # The base scale is assumed as the smallest for hhmmss segments unless as
                # many scales are provided as there are segments, then every scale is used.
                base_index: int = usable_scales.index(locale.base_scale) if len(vals) != len(usable_scales) else 0
                if len(vals) > len(usable_scales) - base_index:
                    invalid.append((number_segment, FailureFlags.MALFORMED_HHMMSS))
                    continue

                hhmmss_buffer_segments: list[tuple[float, Scale, str]] = []
                for index, hhmmss_val in enumerate(reversed(vals)):
                    hhmmss_buffer_segments.append((hhmmss_val, usable_scales[base_index + index], number_segment))

                # Bypass save_buffer() and append straight to potential_values to account for hhmmss_buffer_segments
                # being a list rather than a string. This is done to prevent duplicate scales from being blocked
                # from the center of an hhmmss segment while the rest of the hhmmss segment is valid. If any
                # part of the hhmmss is invalid, the entire segment should be invalid as well.
                potential_values.append((list(reversed(hhmmss_buffer_segments)), ValueType.MIXED))
            elif any(item in number_segment for item in locale.fraction_delimiters):
                for delim in locale.fraction_delimiters:
                    number_segment = number_segment.replace(delim, locale.fraction_delimiters[0])

                val: float | None = handle_fraction(number_segment)
                buffer.value = str(val) if val is not None else ""
            else:
                val: float | None = handle_number(number_segment)
                buffer.value = str(val) if val is not None else ""
        elif current_chartype is CharacterType.ALPHABET or (
            current_chartype is CharacterType.SYMBOL and char not in locale.specials
        ):
            # Allow any alphabet characters or unknown characters not defined in the config to be grouped together.
            buffer.value += char
        else:
            # Do not allow special characters defined in the config to be grouped.
            buffer.value += char
            save_buffer()

        previous_chartype = current_chartype

    if buffer.value:
        save_buffer()

    return potential_values


def parser_one(content: str, locale: Locale) -> ParsedTimeLength:
    """---
    Parser for the English and Spanish locales.

    #### Arguments
    - content: `str` — The length of time to be parsed.
    - locale: `English | Spanish` — The locale content used for parsing the content.

    #### Returns
    - A `ParsedTimeLength` with the outcome of parsing.
    """

    content = remove_diacritics(content)
    invalid: list[tuple[float | str, FailureFlags]] = []
    valid: list[tuple[float, Scale]] = []
    seconds: float = 0.0
    encountered_scales: dict[Scale, Scale] = {}
    skip_iterations: int = 0
    reset_segment_progress: bool = False
    segment_progress: str = ""
    parsed_scales: list[Scale] = []
    parsed_scale: Scale | None = None
    parsed_value: float | None = None
    segment_value: float | None = None
    segment_multiplier: float | None = None
    previous_specials: list[str] = []
    previous_connectors: list[str] = []
    previous_segmentors: list[str] = []
    current_value: str | float | list[tuple[float, Scale, str]] = ""
    current_numeral: Numeral | None = None
    current_numeral_type: NumeralType | None = None
    current_value_type: ValueType | None = None
    current_value_type_converted: ValueType | None = None
    previous_numeral_type: NumeralType | None = None
    previous_value_type: ValueType | None = None
    previous_value_type_converted: ValueType | None = None
    encountered_hundred_thousand: bool = False
    highest_numeral_value: float = 0.0

    potential_values: list[tuple[str | float | list[tuple[float, Scale, str]], ValueType]] = _segment_content(
        content, locale, invalid
    )

    # Enumerate over each potential value and parse them into valid or invalid segments.
    for index, value in enumerate(potential_values):
        # Skip iterations due to lookahead during special character parsing.
        if skip_iterations:
            skip_iterations -= 1
            continue

        current_value, current_value_type = value
        current_numeral = locale.get_numeral(str(current_value)) if current_value_type is ValueType.NUMERAL else None
        current_numeral_type = current_numeral.type if current_numeral else None
        # Numerals become converted to numbers further down. This is to allow for usage with actual numbers.
        current_value_type_converted = current_value_type

        if current_value_type is ValueType.MIXED:
            some_invalid: bool = False
            previous_lonely_value: bool = bool(invalid and invalid[-1][1] & FailureFlags.LONELY_VALUE)

            if segment_value:
                invalid.append(
                    (
                        segment_value,
                        FailureFlags.LONELY_VALUE
                        if not some_invalid and not previous_lonely_value
                        else FailureFlags.LONELY_VALUE,
                    )
                )
                segment_value = None
                some_invalid = True
                previous_lonely_value = True
            if segment_multiplier:
                invalid.append(
                    (
                        segment_multiplier,
                        FailureFlags.LONELY_VALUE
                        if not some_invalid and not previous_lonely_value
                        else FailureFlags.LONELY_VALUE,
                    )
                )
                segment_multiplier = None
                some_invalid = True
                previous_lonely_value = True
            if parsed_value:
                invalid.append(
                    (
                        parsed_value,
                        FailureFlags.LONELY_VALUE
                        if not some_invalid and not previous_lonely_value
                        else FailureFlags.LONELY_VALUE,
                    )
                )
                parsed_value = None
                some_invalid = True
                previous_lonely_value = True

            # Potential to add a ValueType.HHMMSS in the future. ValueType.FRACTION will be
            # included as well if so. Will need to properly handle fractions throughout and
            # consider returning instances of fractions.Fraction in the valid list.
            if isinstance(current_value, list):
                if not locale.settings.allow_duplicate_scales and any(
                    scale in parsed_scales for _, scale, _ in current_value
                ):
                    invalid.append((current_value[0][2], FailureFlags.DUPLICATE_SCALE))
                else:
                    for val, scale, _ in current_value:
                        seconds += val * scale.scale
                        valid.append((val, _get_unique_scale(encountered_scales, scale)))
                        parsed_scales.append(scale)
                continue  # Skip the rest of the loop as the HHMMSS has been fully handled.
            else:
                invalid.append((current_value, FailureFlags.UNKNOWN_TERM))
                reset_segment_progress = True
        elif current_value_type is ValueType.SCALE:
            current_value = cast(str, current_value)

            if previous_value_type is ValueType.SCALE:
                invalid.append((current_value, FailureFlags.LONELY_SCALE))
                reset_segment_progress = True
            elif parsed_value is None and segment_value is None and segment_multiplier is None:
                invalid.append((current_value, FailureFlags.LONELY_SCALE))
                reset_segment_progress = True

            parsed_scale = locale.get_scale(current_value)
        elif current_value_type is ValueType.NUMBER:
            current_value = cast(float, current_value)

            # Account for a weird and uncommon mixing of numerals and numbers.
            if encountered_hundred_thousand and previous_numeral_type:
                parsed_value = current_value

                next_index: int = index + 1
                while next_index < len(potential_values) and potential_values[next_index][1] is ValueType.SYMBOL:
                    if potential_values[next_index][0] in locale.segmentors:
                        skip_iterations += 1
                        has_another_index: bool = next_index + 1 < len(potential_values)
                        if has_another_index and potential_values[next_index + 1][0] in locale.connectors:
                            skip_iterations += 1
                    next_index += 1
            else:
                # If the first value was a multiplier it will have been converted to its number
                # equivalent, but will be stored in segment_multiplier, so it's necessary to check
                # segment_value and parsed_value before declaring them invalid.
                if previous_value_type_converted is ValueType.NUMBER:
                    if segment_value:
                        invalid.append((segment_value, FailureFlags.LONELY_VALUE))
                        segment_value = None

                    if parsed_value:
                        invalid.append((parsed_value, FailureFlags.LONELY_VALUE))
                parsed_value = current_value
        elif current_value_type is ValueType.SYMBOL:
            current_value = cast(str, current_value)
            to_invalidate: list[tuple[str, FailureFlags]] = []

            # Append segmentors only if they are not at the start of the segment progress.
            if segment_progress.strip() and current_value in locale.segmentors:
                segment_progress += current_value

            if previous_connectors.count(current_value) >= 2:
                # Allow up to 2 consecutive locale.connectors rather than 1 to account for more formats.
                to_invalidate.append((current_value, FailureFlags.CONSECUTIVE_CONNECTOR))
                reset_segment_progress = True
            elif current_value in previous_segmentors:
                to_invalidate.append((current_value, FailureFlags.CONSECUTIVE_SEGMENTOR))
                reset_segment_progress = True
            elif current_value in previous_specials:
                to_invalidate.append((current_value, FailureFlags.CONSECUTIVE_SPECIAL))
                reset_segment_progress = True

            if to_invalidate:
                if parsed_value is not None or segment_value is not None:
                    invalid.append(((parsed_value or 0) + (segment_value or 0), FailureFlags.LONELY_VALUE))
                invalid.extend(to_invalidate)

            if current_value in locale.connectors:
                previous_connectors.append(current_value)
            elif current_value in locale.segmentors:
                previous_segmentors.append(current_value)
            else:
                # While ParserSettings.limit_allowed_terms is set, locale.allowed_terms may not appear in the middle of a
                # segment/sentence, thus interrupting a value/scale pair. In that case, the current segment becomes abandoned.
                if locale.settings.limit_allowed_terms and current_value in locale.allowed_terms:
                    reset_segment_progress = True
                    if segment_progress.strip():
                        to_abandon: str = segment_progress + current_value
                        next_index: int = index + 1
                        while (
                            next_index < len(potential_values)
                            and potential_values[next_index][0] in locale.allowed_terms
                        ):
                            to_abandon += cast(str, potential_values[next_index][0])
                            skip_iterations += 1
                            next_index += 1

                        invalid.append((to_abandon, FailureFlags.MISPLACED_ALLOWED_TERM))
                if current_value not in locale.allowed_terms:
                    if segment_value:
                        invalid.append((segment_value, FailureFlags.LONELY_VALUE))
                        segment_value = None

                    if parsed_value:
                        invalid.append((parsed_value, FailureFlags.LONELY_VALUE))

                    invalid.append((current_value, FailureFlags.MISPLACED_SPECIAL))
                    reset_segment_progress = True
                else:
                    previous_specials.append(current_value)
        elif current_value_type is ValueType.NUMERAL:
            current_value = cast(str, current_value)

            numeral = cast(Numeral, locale.get_numeral(current_value))
            current_value_type_converted = (
                ValueType.NUMBER if current_numeral_type is not NumeralType.OPERATOR else current_value_type_converted
            )

            next_index: int = index + 1
            connectors_before_segmentor: int = 0
            if encountered_hundred_thousand:
                while next_index < len(potential_values) and potential_values[next_index][1] is ValueType.SYMBOL:
                    connectors_before_segmentor += 1
                    if connectors_before_segmentor > 2:
                        break
                    if potential_values[next_index][0] in locale.segmentors:
                        skip_iterations += 1 + (connectors_before_segmentor - 2)
                        has_another_index: bool = next_index + 1 < len(potential_values)
                        if has_another_index and potential_values[next_index + 1][0] in locale.connectors:
                            skip_iterations += 1

                    next_index += 1

            if current_numeral_type is NumeralType.OPERATOR:
                previous_multiplier: bool = False
                previous_numeric: bool = False
                next_multiplier: bool = False
                next_numeric: bool = False
                next_scale: bool = False
                previous_value: float = 0.0
                next_value: float = 0.0
                next_exists: bool = False

                if (index - 2) >= 0:
                    if previous_numeral_type is NumeralType.MULTIPLIER:
                        previous_multiplier = True

                    if previous_value_type is ValueType.NUMERAL:
                        previous_numeral = locale.get_numeral(str(potential_values[index - 2][0]))
                        if previous_numeral:
                            previous_numeric = True
                            previous_value = previous_numeral.value
                    elif previous_value_type is ValueType.NUMBER:
                        previous_numeric = True
                        previous_value = cast(float, potential_values[index - 2][0])

                if (index + 2) < len(potential_values):
                    next_exists = True
                    next_value_type = potential_values[index + 2][1]
                    next_numeral: Numeral | None = (
                        locale.get_numeral(str(potential_values[index + 2][0]))
                        if next_value_type is ValueType.NUMERAL
                        else None
                    )

                    if next_numeral and next_numeral.type is NumeralType.MULTIPLIER:
                        next_multiplier = True

                    if next_value_type is ValueType.NUMERAL:
                        next_numeral = locale.get_numeral(str(potential_values[index + 2][0]))
                        if next_numeral:
                            next_numeric = True
                            next_value = next_numeral.value
                    elif next_value_type is ValueType.NUMBER:
                        next_numeric = True
                        next_value = cast(float, potential_values[index + 2][0])
                    elif next_value_type is ValueType.SCALE:
                        next_scale = True

                no_multipliers: bool = not previous_multiplier and not next_multiplier
                previous_is_operator: bool = previous_numeral_type is NumeralType.OPERATOR
                at_end: bool = not next_exists
                no_numerics: bool = not previous_numeric and not next_numeric
                no_next_scale: bool = not next_scale

                if previous_numeric and next_numeric and no_multipliers and not previous_is_operator:
                    potential_values[index + 2] = (previous_value * next_value, ValueType.NUMBER)
                elif (no_multipliers or at_end or previous_is_operator) and (no_numerics or no_next_scale):
                    # If the previous and next term aren't both numbers, or the next term isn't a scale, the operator
                    # is unused. Allowance is made if the previous or next terms are multipliers causing this operator
                    # to act more as a connector.
                    invalid.append((str(current_value), FailureFlags.UNUSED_OPERATOR))
            elif current_numeral_type is NumeralType.MULTIPLIER:
                # Multiple multipliers in a single segment leads to ambiguity on which multipliers apply to how much of the segment.
                # Some are more clear than others, but until a better method of handling all possible scenarios is established, it's
                # best to fail all occurrences of multiple multipliers in a single segment.
                if segment_multiplier:
                    invalid.append((segment_progress + current_value, FailureFlags.AMBIGUOUS_MULTIPLIER))
                    reset_segment_progress = True
                else:
                    if segment_value:
                        invalid.append((segment_value, FailureFlags.LONELY_VALUE))
                        segment_value = None
                    segment_multiplier = numeral.value
            elif parsed_value is None:
                parsed_value = numeral.value
            elif current_numeral_type is NumeralType.THOUSAND:
                encountered_hundred_thousand = True
                next_numeral_type: NumeralType | None = None
                next_value_type: ValueType | None = None
                trimmed_potential_values: list[tuple[str | float | list[tuple[float, Scale, str]], ValueType]] = (
                    potential_values[index + 1 :]
                )

                for item in trimmed_potential_values:
                    item_value_type = item[1]
                    item_numeral: Numeral | None = (
                        locale.get_numeral(str(item[0])) if item_value_type is ValueType.NUMERAL else None
                    )

                    if not next_numeral_type and item_value_type is not ValueType.SYMBOL:
                        next_numeral_type = item_numeral.type if item_numeral else None
                        next_value_type = item_value_type

                    if next_numeral_type or item_value_type not in [ValueType.SYMBOL, ValueType.NUMERAL]:
                        break

                if (
                    next_numeral_type in [NumeralType.DIGIT, NumeralType.TEEN, NumeralType.TEN, NumeralType.HUNDRED]
                    or next_value_type is ValueType.NUMBER
                ):
                    if segment_value and highest_numeral_value <= numeral.value:
                        invalid.append((segment_value, FailureFlags.LONELY_VALUE))

                    parsed_value *= numeral.value
                    segment_value = (
                        segment_value + parsed_value
                        if segment_value and highest_numeral_value > numeral.value
                        else parsed_value
                    )
                    parsed_value = None
                else:
                    if (segment_value and not highest_numeral_value) or (
                        segment_value and highest_numeral_value < numeral.value
                    ):
                        segment_value += parsed_value
                        segment_value *= numeral.value
                        parsed_value = None
                    else:
                        parsed_value *= numeral.value

                highest_numeral_value = numeral.value
            elif current_numeral_type is NumeralType.HUNDRED:
                encountered_hundred_thousand = True
                # Account for the difference between "hundred" as a multiplier and
                # hundred-level standalone numerals such as 200, 300, etc.
                if numeral.value == 100:
                    parsed_value *= numeral.value
                else:
                    parsed_value += numeral.value
            elif (
                segment_value
                and (current_numeral_type in [NumeralType.DIGIT, NumeralType.TEEN, NumeralType.TEN])
                and (
                    previous_numeral_type is NumeralType.DIGIT
                    if current_numeral_type in [NumeralType.DIGIT, NumeralType.TEEN, NumeralType.TEN]
                    else previous_numeral_type is NumeralType.TEEN
                    if current_numeral_type in [NumeralType.TEEN, NumeralType.TEN]
                    else previous_numeral_type is NumeralType.TEN
                    if current_numeral_type is NumeralType.TEN
                    else False
                )
            ):  # Handle a few edge cases to prevent awkward f-string numeral appending down below.
                segment_value += parsed_value
                invalid.append((segment_value, FailureFlags.LONELY_VALUE))
                segment_value = None
                parsed_value = numeral.value
            elif current_numeral_type is NumeralType.DIGIT and previous_numeral_type is NumeralType.TEN:
                parsed_value += numeral.value
            elif (
                current_numeral_type is NumeralType.DIGIT
                and previous_numeral_type is NumeralType.DIGIT
                and not encountered_hundred_thousand
            ):
                parsed_value = float(f"{int(parsed_value)}{int(numeral.value)}")
            elif (
                current_numeral_type in [NumeralType.TEEN, NumeralType.TEN]
                and previous_numeral_type in [NumeralType.DIGIT, NumeralType.TEEN, NumeralType.TEN]
                and not encountered_hundred_thousand
            ):  # The above two if statements are separate to account for the different ways numerals interact
                # together, as well as to specifically exclude the case of a TEEN numeral following a DIGIT
                # numeral. There is no logic applied to this decision other than TEEN-DIGIT not sounding right.
                # Example: Fifteen One
                #
                # encountered_hundred_thousand is used to prevent inappropriate f-string concatenation following
                # a hundred or thousand numeral.
                parsed_value = float(f"{int(parsed_value)}{int(numeral.value)}")
            elif current_numeral_type in [
                NumeralType.DIGIT,
                NumeralType.TEEN,
                NumeralType.TEN,
            ] and previous_numeral_type in [
                NumeralType.HUNDRED,
                NumeralType.THOUSAND,
            ]:
                parsed_value += numeral.value
            elif (
                previous_value_type_converted is ValueType.NUMBER or previous_numeral_type is NumeralType.MULTIPLIER
            ) and current_numeral_type not in [
                NumeralType.HUNDRED,
                NumeralType.THOUSAND,
                NumeralType.MULTIPLIER,
            ]:
                if segment_value:
                    invalid.append((segment_value, FailureFlags.LONELY_VALUE))
                    segment_value = None

                if parsed_value:
                    invalid.append((parsed_value, FailureFlags.LONELY_VALUE))

                parsed_value = numeral.value

        # Update previous variables and reset current variables for the next loop.
        if current_value_type is not ValueType.SYMBOL or current_value in locale.segmentors:
            previous_value_type = current_value_type
            previous_numeral_type = current_numeral_type
            previous_value_type_converted = current_value_type_converted
            current_value_type_converted = None
            current_value_type = None
            current_numeral_type = None
            # Reset the non-segmentor consecutive special character tracking lists as
            # neither have occurred, and therefore are not consecutive.
            previous_connectors = []
            previous_specials = []

        # Segment the parsed value if segmentor encountered. Track progress of current segment otherwise.
        if current_value not in locale.segmentors:
            segment_progress += str(int(current_value) if is_int(current_value) else current_value)
            # Only clear the segmentors list if a valid non-connector is encountered. Check against
            # reset_segment_progress as that is True when an invalid value is encountered.
            if current_value not in locale.connectors and not reset_segment_progress:
                previous_segmentors = []

            if skip_iterations:
                for num in range(skip_iterations):
                    num += 1
                    segment_progress += str(
                        int(potential_values[index + num][0])
                        if is_int(str(potential_values[index + num][0]))
                        else potential_values[index + num][0]
                    )
        else:
            if parsed_value is not None:
                if not segment_value:
                    segment_value = 0.0
                segment_value += parsed_value
            parsed_value = None

        # If a value and a scale have been parsed, add them to the result and reset the variables.
        if (parsed_value is not None or segment_value is not None or segment_multiplier is not None) and parsed_scale:
            if not parsed_value:
                parsed_value = 0.0

            if not segment_value:
                segment_value = 0.0

            if not parsed_value and not segment_value and segment_multiplier:
                parsed_value = segment_multiplier
                segment_multiplier = None

            if not locale.settings.allow_duplicate_scales and parsed_scale in parsed_scales:
                invalid.append((segment_progress.strip(), FailureFlags.DUPLICATE_SCALE))
            else:
                segment_total: float = parsed_value + segment_value
                if segment_multiplier:
                    segment_total *= segment_multiplier
                seconds += (segment_total) * parsed_scale.scale
                valid.append((segment_total, _get_unique_scale(encountered_scales, parsed_scale)))

            parsed_scales.append(parsed_scale)
            reset_segment_progress = True

        # Reset just the variables relevant to segmentation. Skip previous_specials
        # to prevent consecutive specials from crossing segments.
        if reset_segment_progress:
            highest_numeral_value = 0.0
            encountered_hundred_thousand = False
            reset_segment_progress = False
            segment_progress = ""
            segment_value = None
            parsed_scale = None
            parsed_value = None
            segment_multiplier = None

    # Account for tailing values with no accompanying scale.
    if parsed_value is not None or segment_value is not None or segment_multiplier is not None:
        if not parsed_value:
            parsed_value = 0.0

        if not segment_value:
            segment_value = 0.0

        if not parsed_value and not segment_value and segment_multiplier:
            parsed_value = segment_multiplier
            segment_multiplier = None

        base = locale.base_scale

        if (locale.settings.assume_scale == "LAST") or (
            locale.settings.assume_scale == "SINGLE"
            and (len(potential_values) == 1 or (len(valid) == 0 and len(invalid) == 0))
        ):
            segment_total: float = parsed_value + segment_value
            if segment_multiplier:
                segment_total *= segment_multiplier
            valid.append((segment_total, _get_unique_scale(encountered_scales, base)))
            seconds += (segment_total) * base.scale
        else:
            invalid.append((parsed_value + segment_value, FailureFlags.LONELY_VALUE))

    # If any failure flags were triggered, or no valid results were found, parsing failed.
    # If at least one valid result was found and no failure flags were triggered, parsing succeeded.
    success: bool = False if not valid else all(not (invalid_flag & locale.flags) for _, invalid_flag in invalid)

    try:
        delta = timedelta(seconds=seconds)
    except OverflowError:
        delta = None

    return ParsedTimeLength(success, seconds, delta, tuple(invalid), tuple(valid))
