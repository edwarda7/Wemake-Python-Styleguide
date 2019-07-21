# -*- coding: utf-8 -*-

import pytest

from wemake_python_styleguide.violations.consistency import (
    BadNumberSuffixViolation,
)
from wemake_python_styleguide.visitors.tokenize.primitives import (
    WrongNumberTokenVisitor,
)


@pytest.mark.parametrize('number', [
    '0X1',
    '0X1A',
    '0XFF',
    '0XE',
    '1.5E10',
    '0O11',
    '0B1001',
])
def test_bad_number_suffixes(
    parse_tokens,
    assert_errors,
    assert_error_text,
    default_options,
    primitives_usages,
    number,
    number_sign,
    mode,
):
    """Ensures that numbers with suffix not in lowercase raise a warning."""
    file_tokens = parse_tokens(
        mode(primitives_usages.format(number_sign(number))),
    )

    visitor = WrongNumberTokenVisitor(default_options, file_tokens=file_tokens)
    visitor.run()

    assert_errors(visitor, [BadNumberSuffixViolation])
    assert_error_text(visitor, number.lstrip('-').lstrip('+'))


@pytest.mark.parametrize('number', [
    '1',
    '29',

    '0xFF',
    '1.5e10',
    '0o11',
    '0b1001',

    # Regression for 557:
    # https://github.com/wemake-services/wemake-python-styleguide/issues/557
    '0xE',
    '0xB',
    '0xEE',
    '0xEEE',
    '0x1E',
    '0xE1',
])
def test_correct_number_suffixes(
    parse_tokens,
    assert_errors,
    default_options,
    primitives_usages,
    number,
    number_sign,
    mode,
):
    """Ensures that correct numbers are fine."""
    file_tokens = parse_tokens(
        mode(primitives_usages.format(number_sign(number))),
    )

    visitor = WrongNumberTokenVisitor(default_options, file_tokens=file_tokens)
    visitor.run()

    assert_errors(visitor, [])


@pytest.mark.parametrize('code', [
    'print({0})',
    'regular = {0}',
    'as_string = "{0}"',
])
@pytest.mark.parametrize('number', [
    '1',
    '1234567890',

    '0xFF',
    '1.5e10',
    '0o11',
    '0b1001',
])
def test_similar_strings(
    parse_tokens,
    assert_errors,
    default_options,
    code,
    number,
    number_sign,
    mode,
):
    """Ensures that strings are fine."""
    file_tokens = parse_tokens(mode(code.format(number_sign(number))))

    visitor = WrongNumberTokenVisitor(default_options, file_tokens=file_tokens)
    visitor.run()

    assert_errors(visitor, [])
