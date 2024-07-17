from timelength.dataclasses import Buffer, Numeral, ParsedTimeLength, ParserSettings, Scale
from timelength.enums import CharacterType, FailureFlags, NumeralType, StringType
from timelength.locales import Locale
from timelength.utils import character_type, is_int, remove_diacritics, string_type

# Declare here and update in parser_one() to prevent calling properties
# and list comprehensions many times per parse.
locale_scales: list[Scale] = None
locale_scale_terms: list[str] = None
locale_numerals: list[Numeral] = None
locale_numeral_terms: list[str] = None
locale_specials: list[str] = None


def save_buffer(
    buffer: Buffer, potential_values: list[tuple], locale: Locale
) -> tuple[str, list[tuple[str | float, StringType, NumeralType | None]]]:
    """Update the parsed buffer values list and clear the buffer."""

    if not buffer.value:
        return

    buffer_value_type: StringType = string_type(
        buffer.value,
        locale_scale_terms,
        locale_numeral_terms,
        locale_specials,
    )

    numeral: Numeral = locale.get_numeral(buffer.value) if buffer_value_type is StringType.NUMERAL else None

    potential_values.append(
        (
            float(buffer.value) if buffer_value_type is StringType.NUMBER else buffer.value,
            buffer_value_type,
            numeral,
        )
    )
    buffer.value = ""


def parser_one(content: str, locale: Locale, result: ParsedTimeLength):
    """Parser for the English and Spanish locales."""
    global locale_scales, locale_scale_terms, locale_numerals, locale_numeral_terms, locale_specials

    locale_scales = locale._scales
    locale_scale_terms = [term for scale in locale_scales for term in scale.terms]
    locale_numerals = locale._numerals
    locale_numeral_terms = [term for numeral in locale_numerals for term in numeral.terms]
    locale_specials = locale._specials
    flags: FailureFlags = locale.flags
    settings: ParserSettings = locale.settings
    content = remove_diacritics(content)
    buffer: Buffer = Buffer()
    potential_values: list[tuple[str | float, StringType, Numeral | None]] = []
    skip_buffer_iterations: int = 0
    previous_chartype: CharacterType = None
    current_chartype: CharacterType = None
    contains_hhmmss: bool = False
    leading_decimal: bool = False
    connectors_non_delimiters: list[str] = [
        con
        for con in locale._connectors
        if con not in locale._decimal_delimiters + locale._thousand_delimiters + locale._hhmmss_delimiters
    ]
    min_digits_after_thousand_delim: int = 3 if not settings.allow_thousands_lacking_digits else 1

    # Enumerate over each character in the content to group them by CharacterTypes.
    for index, char in enumerate(content):
        # Skip iterations due to lookahead during number segment parsing.
        if skip_buffer_iterations:
            skip_buffer_iterations -= 1
            continue

        current_chartype = character_type(char)
        if buffer.value and current_chartype != previous_chartype:
            save_buffer(buffer, potential_values, locale)

        if (
            char in locale._decimal_delimiters
            and (index + 1) < len(content)
            and (index == 0 or previous_chartype is CharacterType.UNKNOWN)
            and character_type(content[index + 1]) is CharacterType.NUMBER
        ):  # Required conditions for decimal numbers with no leading zero.
            buffer.value += "0"
            leading_decimal = True

        if current_chartype is CharacterType.NUMBER or leading_decimal:
            segment_index: int = index
            number_segment: str = buffer.value
            buffer.value = ""
            leading_decimal = False
            encountered_number: bool = False

            # Lookahead for all characters in the number segment while accounting for special characters.
            while segment_index < len(content) and (
                character_type(content[segment_index]) is CharacterType.NUMBER
                or content[segment_index]
                in locale._decimal_delimiters
                + locale._thousand_delimiters
                + locale._hhmmss_delimiters
                + connectors_non_delimiters
            ):
                if content[segment_index] in locale._hhmmss_delimiters:
                    encountered_number = False
                elif character_type(content[segment_index]) is CharacterType.NUMBER:
                    encountered_number = True

                if content[segment_index] in locale._decimal_delimiters + locale._thousand_delimiters and not (
                    (
                        # Check continuation of HH:MM:SS segment, allowing for minor connector usage.
                        content[segment_index] in locale._connectors
                        and (
                            segment_index
                            and content[segment_index - 1] in locale._hhmmss_delimiters
                            or (
                                (segment_index + 1) < len(content)
                                and content[segment_index + 1] in locale._hhmmss_delimiters
                            )
                        )
                    )
                    or (
                        # Check for continuation of thousands segment, taking into consideration the settings
                        # for allowing thousands with less than or more than 3 digits following the delimiter.
                        content[segment_index] in locale._thousand_delimiters
                        and (
                            not encountered_number
                            or (
                                content[segment_index] not in locale._connectors
                                and (segment_index + 1) < len(content)
                                and character_type(content[segment_index + 1]) is CharacterType.NUMBER
                            )
                            or (
                                (segment_index + min_digits_after_thousand_delim) < len(content)
                                and (
                                    segment_index
                                    and character_type(content[segment_index - 1]) is CharacterType.NUMBER
                                    and all(
                                        character_type(content[segment_index + i]) is CharacterType.NUMBER
                                        for i in range(1, (min_digits_after_thousand_delim + 1))
                                    )
                                )
                            )
                        )
                    )
                    or (
                        # Check for continuation of decimal segment taking into consideration the settings for
                        # allowing decimals with no number following the delimiter.
                        (char := content[segment_index]) in locale._decimal_delimiters
                        and (
                            not ((segment_index + 1) < len(content))
                            or (
                                character_type((next_char := content[segment_index + 1])) is CharacterType.NUMBER
                                or (next_char in locale_specials and char not in locale._segmentors)
                            )
                        )
                    )
                ):  # Break if thousands, decimal, or HH:MM:SS segment checks fail.
                    break

                number_segment += content[segment_index]
                segment_index += 1

            skip_buffer_iterations = segment_index - index - 1
            skip_number_segment_iterations: int = 0
            decimal_locked: bool = False
            flag_tripped: str = ""
            hhmmss_segments: list[str] = []
            used_hms_delim: bool = False
            used_connectors: list[str] = []
            encountered_number = False

            # Iterate over each character in the number segment to verify their integrity.
            # If integrity is broken, the loop is broken and the entire segment is marked as invalid.
            number_segment = number_segment.strip()
            for segment_index, segment_char in enumerate(number_segment):
                if skip_number_segment_iterations:
                    skip_number_segment_iterations -= 1
                    continue

                # Allow two unique connectors in a row per segment of the HH:MM:SS format.
                if (
                    segment_char in connectors_non_delimiters
                    and segment_char not in used_connectors
                    and not (
                        (segment_index + 1) < len(number_segment)
                        and number_segment[segment_index + 1] in locale._hhmmss_delimiters
                    )
                ):
                    used_connectors.append(segment_char)
                    continue
                elif len(used_connectors) > 2:
                    flag_tripped = FailureFlags.MALFORMED_HHMMSS
                    break
                elif character_type(segment_char) is CharacterType.NUMBER:
                    buffer.value += segment_char
                    used_hms_delim = False
                    encountered_number = True
                elif segment_char in locale._decimal_delimiters:
                    if segment_char in locale._connectors and (
                        # Commenting this out prevents multiple connectors that are also decimal delimiters
                        # from being allowed in a row at the start.
                        # not encountered_number
                        # or
                        segment_char not in used_connectors
                        # Setting this to "not" in conjunction with the commented out "or" below along with the
                        # section directly above this being commented as well as the "and not" chunk in the first
                        # if in this block being uncommented prevents connectors from trailing an HHMMSS segment.
                        and not (
                            (segment_index + 1) < len(number_segment)
                            and number_segment[segment_index + 1] in locale._hhmmss_delimiters
                        )
                        # or (
                        #     (segment_index - 1) > 0
                        #     and character_type(number_segment[segment_index - 1]) is CharacterType.NUMBER
                        # )
                    ):
                        used_connectors.append(segment_char)
                        continue
                    else:
                        if (
                            decimal_locked
                            or (
                                (more_segments := (segment_index + 1) < len(number_segment))
                                and character_type(number_segment[segment_index + 1]) is not CharacterType.NUMBER
                                and not settings.allow_decimals_lacking_digits
                            )
                            or (not more_segments and not settings.allow_decimals_lacking_digits)
                        ):
                            # Decimal delimiter already found in the segment.
                            flag_tripped = FailureFlags.MALFORMED_DECIMAL
                            break

                        buffer.value += "."
                        decimal_locked = True
                        used_hms_delim = False
                elif not decimal_locked and segment_char in locale._thousand_delimiters:
                    if segment_char in locale._connectors and (
                        # Commenting this out prevents multiple connectors that are also decimal delimiters
                        # from being allowed in a row at the start.
                        # not encountered_number
                        # or
                        segment_char not in used_connectors
                        # Setting this to "not" in conjunction with the commented out "or" below along with the
                        # section directly above this being commented as well as the "and not" chunk in the first
                        # if in this block being uncommented prevents connectors from trailing an HHMMSS segment.
                        and not (
                            (segment_index + 1) < len(number_segment)
                            and number_segment[segment_index + 1] in locale._hhmmss_delimiters
                        )
                        # or (
                        #     (segment_index - 1) > 0
                        #     and character_type(number_segment[segment_index - 1]) is CharacterType.NUMBER
                        # )
                    ):
                        used_connectors.append(segment_char)
                        continue
                    elif not (
                        segment_index
                        and (segment_index + min_digits_after_thousand_delim) < len(number_segment)
                        and character_type(number_segment[segment_index - 1]) is CharacterType.NUMBER
                        and all(
                            character_type(number_segment[segment_index + i]) is CharacterType.NUMBER
                            for i in range(1, (min_digits_after_thousand_delim + 1))
                        )
                        and not (
                            not settings.allow_thousands_lacking_digits
                            and not settings.allow_thousands_extra_digits
                            and (segment_index + 4) < len(number_segment)
                            and character_type(number_segment[segment_index + 4]) is CharacterType.NUMBER
                        )
                    ):  # Thousand either doesn't start with a number or doesn't have 3 numbers following a delimiter.
                        # If allow_thousands_lacking_digits is set True, the thousand will be parsed with at least 1 following digit.
                        # If allow_thousands_extra_digits is set True, the thousand will be parsed with as many following digits as present.
                        flag_tripped = (
                            FailureFlags.MALFORMED_HHMMSS if hhmmss_segments else FailureFlags.MALFORMED_THOUSAND
                        )
                        break
                    else:
                        for num in range(1, (min_digits_after_thousand_delim + 1)):
                            buffer.value += number_segment[segment_index + num]
                        skip_number_segment_iterations = min_digits_after_thousand_delim
                        used_hms_delim = False
                        continue
                elif segment_char in locale._hhmmss_delimiters:
                    if (
                        (segment_index + 1) < len(number_segment)
                        and (
                            character_type(number_segment[segment_index + 1]) is CharacterType.NUMBER
                            or number_segment[segment_index + 1]
                            in locale._decimal_delimiters + locale._thousand_delimiters + connectors_non_delimiters
                        )
                        and not used_hms_delim
                    ):
                        hhmmss_segments.append(buffer.value)
                        buffer.value = ""
                        decimal_locked = False
                        used_hms_delim = True
                        used_connectors = []
                        encountered_number = False
                    else:
                        # HH:MM:SS delimiter found with no number following it, or with no
                        # number between it and then next delimiter.
                        flag_tripped = FailureFlags.MALFORMED_HHMMSS
                        break
                elif segment_char in locale._connectors:
                    flag_tripped = FailureFlags.MALFORMED_HHMMSS
                    break
                else:
                    flag_tripped = FailureFlags.MALFORMED_CONTENT
                    break

            if not flag_tripped:
                if used_hms_delim:
                    flag_tripped = FailureFlags.MALFORMED_HHMMSS
                elif not settings.allow_duplicate_scales and contains_hhmmss and hhmmss_segments:
                    flag_tripped = FailureFlags.DUPLICATE_SCALE

            if flag_tripped:
                result.invalid.append((number_segment.strip(), flag_tripped))
                buffer.value = ""
            elif hhmmss_segments:
                if buffer.value:
                    hhmmss_segments.append(buffer.value)

                # If there as as many HH:MM:SS segments as scales, milliseconds are given their own segment.
                # With any fewer number of segments the milliseconds must be specified as a decimal to the seconds.
                if (num_segments := len(hhmmss_segments)) > (num_scales := len(locale_scales)):
                    result.invalid.append((number_segment, FailureFlags.MALFORMED_HHMMSS))
                    hhmmss_segments = []
                else:
                    # Parse the HH:MM:SS segments in reverse order to ensure the smallest scale is parsed first, allowing
                    # for any number of segments between 2 and the number of scales to be parsed.
                    contains_hhmmss = True
                    skip_ms: bool = False

                    if num_segments != num_scales:
                        skip_ms = True

                    hhmmss_buffer_segments: list[tuple[str, str]] = []
                    for hhmmss_segment, hhmmss_value in enumerate(reversed(hhmmss_segments)):
                        if skip_ms:
                            hhmmss_segment += 1

                        hhmmss_buffer_segments.append((hhmmss_value, locale_scales[hhmmss_segment].plural))

                    for value, term in reversed(hhmmss_buffer_segments):
                        buffer.value = value
                        save_buffer(buffer, potential_values, locale)
                        buffer.value = term
                        save_buffer(buffer, potential_values, locale)
        elif current_chartype is CharacterType.ALPHABET or (
            current_chartype is CharacterType.UNKNOWN and char not in locale_specials
        ):
            # Allow any alphabet characters or unknown characters not defined in the config to be grouped together.
            buffer.value += char
        else:
            # Do not allow special characters defined in the config to be grouped.
            buffer.value += char
            save_buffer(buffer, potential_values, locale)

        previous_chartype = current_chartype

    if buffer.value:
        save_buffer(buffer, potential_values, locale)

    skip_potential_iterations: int = skip_buffer_iterations
    reset_segment_progress: bool = False
    segment_progress: str = ""
    segment_progress_raw: str = ""
    parsed_scales: list[Scale] = []
    parsed_scale: Scale | None = None
    parsed_value: float | None = None
    segment_value: float | None = None
    segment_modifier: float | None = None
    previous_specials: list[str] = []
    previous_connectors: list[str] = []
    previous_segmentors: list[str] = []
    current_value: str | float = ""
    current_numeral_type: NumeralType | None = None
    current_value_type: StringType | None = None
    current_value_type_converted: StringType | None = None
    previous_numeral_type: NumeralType | None = None
    previous_value_type: StringType | None = None
    previous_value_type_converted: StringType | None = None
    starts_with_modifier: bool = False
    encountered_hundred_thousand: bool = False
    highest_numeral_value: float = 0.0
    abandoned_segments: list[str] = []

    # Enumerate over each potential value and parse them into valid or invalid segments.
    for index, value in enumerate(potential_values):
        # Skip iterations due to lookahead during special character parsing.
        if skip_potential_iterations:
            skip_potential_iterations -= 1
            continue

        current_value, current_value_type, current_numeral = value
        current_numeral_type = current_numeral.type if current_numeral else None
        # Numerals become converted to numbers further down. This is to allow for easy usage with actual numbers.
        current_value_type_converted = current_value_type

        if current_value_type is StringType.UNKNOWN:
            if parsed_value:
                result.invalid.append((parsed_value, FailureFlags.LONELY_VALUE))
            elif segment_value:
                result.invalid.append((segment_value, FailureFlags.LONELY_VALUE))

            result.invalid.append((current_value, FailureFlags.UNKNOWN_TERM))
            reset_segment_progress = True
        elif current_value_type is StringType.SCALE:
            if not index:
                result.invalid.append((current_value, FailureFlags.LEADING_SCALE))
                reset_segment_progress = True
            elif previous_value_type is StringType.SCALE:
                result.invalid.append((current_value, FailureFlags.CONSECUTIVE_SCALE))
                reset_segment_progress = True
            elif parsed_value is None and segment_value is None and segment_modifier is None:
                result.invalid.append((current_value, FailureFlags.LONELY_SCALE))
                reset_segment_progress = True

            parsed_scale = locale.get_scale(current_value)
        elif current_value_type is StringType.NUMBER:
            # Account for a weird and uncommon mixing of numerals and numbers.
            if encountered_hundred_thousand and previous_numeral_type:
                parsed_value = float(current_value)

                next_index: int = index + 1
                while next_index < len(potential_values) and potential_values[next_index][1] is StringType.SPECIAL:
                    if potential_values[next_index][0] in locale._segmentors:
                        skip_potential_iterations += 1
                        if potential_values[next_index + 1][0] in locale._connectors:
                            skip_potential_iterations += 1

                    next_index += 1
            else:
                # If the previous value was a modifier it will have been converted to its number
                # equivalent, so this would trigger without checking for starts_with_modifier.
                if previous_value_type_converted is StringType.NUMBER and not starts_with_modifier:
                    if segment_value:
                        result.invalid.append((segment_value, FailureFlags.CONSECUTIVE_VALUE))
                        segment_value = None

                    result.invalid.append((parsed_value, FailureFlags.CONSECUTIVE_VALUE))
                parsed_value = float(current_value)
        elif current_value_type is StringType.SPECIAL:
            if previous_connectors.count(current_value) >= 2:
                # Allow up to 2 consecutive connectors rather than 1 to account for more formats.
                result.invalid.append((current_value, FailureFlags.CONSECUTIVE_CONNECTOR))
                reset_segment_progress = True
            elif current_value in previous_segmentors:
                result.invalid.append((current_value, FailureFlags.CONSECUTIVE_SEGMENTOR))
                reset_segment_progress = True
            elif current_value in previous_specials:
                result.invalid.append((current_value, FailureFlags.CONSECUTIVE_SPECIAL))
                reset_segment_progress = True

            if current_value in locale._connectors:
                previous_connectors.append(current_value)
            elif current_value in locale._segmentors:
                previous_segmentors.append(current_value)
            else:
                # While FailureFlags.MISPLACED_ALLOWED_TERM is set, _allowed_terms may not appear in the middle of a
                # segment/sentence, thus interrupting a value/scale pair. In that case, the current segment becomes abandoned.
                if settings.limit_allowed_terms and current_value in locale._allowed_terms:
                    reset_segment_progress = True
                    if segment_progress.strip():
                        abandoned_segments.append(segment_progress + current_value)
                previous_specials.append(current_value)
        elif current_value_type is StringType.NUMERAL:
            next_index: int = index + 1

            while next_index < len(potential_values) and potential_values[next_index][1] is StringType.SPECIAL:
                if potential_values[next_index][0] in locale._segmentors:
                    skip_potential_iterations += 1
                    if potential_values[next_index + 1][0] in locale._connectors:
                        skip_potential_iterations += 1

                next_index += 1

            if current_numeral_type is NumeralType.MULTIPLIER:
                previous_modifier: bool = False
                previous_numeric: bool = False
                next_modifier: bool = False
                next_numeric: bool = False
                next_scale: bool = False
                previous_value: float = 0.0
                next_value: float = 0.0
                next_exists: bool = False

                if (index - 2) >= 0:
                    if previous_value_type is StringType.NUMERAL:
                        previous_numeric = True
                        previous_value = locale.get_numeral(potential_values[index - 2][0]).value
                    elif previous_value_type is StringType.NUMBER:
                        previous_numeric = True
                        previous_value = potential_values[index - 2][0]

                    if previous_numeral_type is NumeralType.MODIFIER:
                        previous_modifier = True

                if (index + 2) < len(potential_values):
                    next_exists = True
                    next_value_type: StringType = potential_values[index + 2][1]
                    next_numeral: Numeral | None = potential_values[index + 2][2]

                    if next_numeral and next_numeral.type is NumeralType.MODIFIER:
                        next_modifier = True

                    if next_value_type is StringType.NUMERAL:
                        next_numeric = True
                        next_value = locale.get_numeral(potential_values[index + 2][0]).value
                    elif next_value_type is StringType.NUMBER:
                        next_numeric = True
                        next_value = potential_values[index + 2][0]
                    elif next_value_type is StringType.SCALE:
                        next_scale = True

                if previous_numeric and next_numeric and not previous_modifier and not next_modifier:
                    potential_values[index + 2] = (
                        previous_value * next_value,
                        StringType.NUMBER,
                        potential_values[index + 2][2],
                    )
                elif (not previous_modifier and not next_modifier or not next_exists) and (
                    (not previous_numeric and not next_numeric) or not next_scale
                ):
                    # If the previous and next term aren't both numbers, or the next term isn't a scale, the multiplier is unused.
                    # Allowance is made if the previous or next terms are a modifier causing this multiplier to act more as a connector.
                    result.invalid.append((current_value, FailureFlags.UNUSED_MULTIPLIER))
            else:
                numeral = locale.get_numeral(current_value)
                current_value_type_converted = StringType.NUMBER

                if parsed_value is None:
                    encountered_hundred_thousand = False

                    if current_numeral_type is NumeralType.MODIFIER:
                        starts_with_modifier = True
                        if segment_modifier:
                            segment_modifier *= numeral.value
                        else:
                            segment_modifier = numeral.value
                    else:
                        parsed_value = numeral.value
                elif current_numeral_type is NumeralType.THOUSAND:
                    encountered_hundred_thousand = True
                    next_numeral_type: NumeralType | None = None
                    next_string_type: StringType | None = None
                    trimmed_potential_values: list[tuple[str | float, StringType, Numeral | None]] = potential_values[
                        index + 1 :
                    ]

                    for item in trimmed_potential_values:
                        item_string_type = item[1]
                        item_numeral = item[2]

                        if not next_numeral_type and item_string_type is not StringType.SPECIAL:
                            next_numeral_type = item_numeral.type if item_numeral else None
                            next_string_type = item_string_type

                        if next_numeral_type or item_string_type not in [StringType.SPECIAL, StringType.NUMERAL]:
                            break

                    if (
                        next_numeral_type in [NumeralType.DIGIT, NumeralType.TEEN, NumeralType.TEN, NumeralType.HUNDRED]
                        or next_string_type is StringType.NUMBER
                    ):
                        parsed_value *= numeral.value

                        if segment_value:
                            if highest_numeral_value > numeral.value:
                                segment_value += parsed_value
                            else:
                                result.invalid.append((segment_value, FailureFlags.LONELY_VALUE))
                                segment_value = parsed_value
                        else:
                            segment_value = parsed_value

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
                elif current_numeral_type is NumeralType.MODIFIER:
                    if segment_modifier:
                        segment_modifier *= numeral.value
                    else:
                        segment_modifier = numeral.value
                elif (
                    segment_value
                    and (current_numeral_type in [NumeralType.DIGIT, NumeralType.TEEN, NumeralType.TEN])
                    and (
                        previous_numeral_type is NumeralType.DIGIT
                        if current_numeral_type in [NumeralType.DIGIT, NumeralType.TEEN, NumeralType.TEN]
                        else previous_numeral_type in NumeralType.TEEN
                        if current_numeral_type in [NumeralType.TEEN, NumeralType.TEN]
                        else previous_numeral_type is NumeralType.TEN
                        if current_numeral_type is NumeralType.TEN
                        else False
                    )
                ):  # Handle a few edge cases to prevent awkward f-string numeral appending down below.
                    segment_value += parsed_value
                    result.invalid.append((segment_value, FailureFlags.CONSECUTIVE_VALUE))
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
                    previous_value_type_converted is StringType.NUMBER or previous_numeral_type is NumeralType.MODIFIER
                ) and current_numeral_type not in [
                    NumeralType.HUNDRED,
                    NumeralType.THOUSAND,
                    NumeralType.MODIFIER,
                ]:
                    if segment_value:
                        result.invalid.append((segment_value, FailureFlags.LONELY_VALUE))
                        segment_value = None

                    result.invalid.append((parsed_value, FailureFlags.CONSECUTIVE_VALUE))
                    parsed_value = numeral.value
                else:
                    parsed_value = numeral.value

        # Update previous variables and reset current variables for the next loop.
        if current_value_type is not StringType.SPECIAL or current_value in locale._segmentors:
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

        # Segment the parsed value if segmentor encountered or track progress of current segment otherwise.
        progress_char: str = str(int(current_value) if is_int(current_value) else current_value)
        segment_progress_raw += progress_char

        if current_value not in locale._segmentors:
            segment_progress += progress_char
            previous_segmentors = []
        else:
            if parsed_value is not None:
                if not segment_value:
                    segment_value = 0.0
                segment_value += parsed_value
            parsed_value = None
            starts_with_modifier = False

        # If a value and a scale have been parsed, add them to the result and reset the variables.
        if (parsed_value is not None or segment_value is not None or segment_modifier is not None) and parsed_scale:
            if not parsed_value:
                parsed_value = 0.0

            if not segment_value:
                segment_value = 0.0

            if not parsed_value and not segment_value and segment_modifier:
                parsed_value = segment_modifier
                segment_modifier = None

            if not settings.allow_duplicate_scales and parsed_scale in parsed_scales:
                result.invalid.append((segment_progress.strip(), FailureFlags.DUPLICATE_SCALE))
            else:
                segment_total: float = parsed_value + segment_value
                if segment_modifier:
                    segment_total *= segment_modifier
                result.seconds += (segment_total) * parsed_scale.scale
                result.valid.append((segment_total, parsed_scale))

            parsed_scales.append(parsed_scale)
            reset_segment_progress = True

        # Reset just the variables relevant to segmentation. Skip previous_specials
        # to prevent consecutive specials from crossing segments.
        if reset_segment_progress:
            highest_numeral_value = 0.0
            encountered_hundred_thousand = False
            reset_segment_progress = False
            starts_with_modifier = False
            segment_progress = ""
            segment_progress_raw = ""
            segment_value = None
            parsed_scale = None
            parsed_value = None
            segment_modifier = None

    # Account for tailing values with no accompanying scale.
    if parsed_value is not None or segment_value is not None or segment_modifier is not None:
        if not parsed_value:
            parsed_value = 0.0

        if not segment_value:
            segment_value = 0.0

        if not parsed_value and not segment_value and segment_modifier:
            parsed_value = segment_modifier
            segment_modifier = None

        if (settings.assume_seconds == "LAST") or (
            settings.assume_seconds == "SINGLE"
            and (len(potential_values) == 1 or (len(result.valid) == 0 and len(result.invalid) == 0))
        ):
            segment_total: float = parsed_value + segment_value
            if segment_modifier:
                segment_total *= segment_modifier
            result.valid.append((segment_total, locale._second if locale._second.scale else locale_scales[0]))
            result.seconds += (segment_total) * locale._second.scale
        else:
            result.invalid.append((parsed_value + segment_value, FailureFlags.LONELY_VALUE))

    if settings.limit_allowed_terms and abandoned_segments:
        for segment in abandoned_segments:
            result.invalid.append((segment, FailureFlags.MISPLACED_ALLOWED_TERM))

    # If any failure flags were triggered, or no valid results were found, parsing failed.
    # If at least one valid result was found and no failure flags were triggered, parsing succeeded.
    result.success = (
        False
        if not result.valid
        else all((invalid_flag & flags) == FailureFlags.NONE for _, invalid_flag in result.invalid)
    )
