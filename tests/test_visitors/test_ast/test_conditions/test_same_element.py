# -*- coding: utf-8 -*-

import pytest

from wemake_python_styleguide.violations.best_practices import (
    SameElementsInConditionViolation,
)
from wemake_python_styleguide.violations.consistency import (
    ImplicitTernaryViolation,
)
from wemake_python_styleguide.visitors.ast.conditions import (
    BooleanConditionVisitor,
)


@pytest.mark.parametrize('code', [
    'some or other',
    'other and some',
    'first or second and third',
    '(first or second) and third',
    'first or (second and third)',
    'very and complex and long and condition',
])
def test_regular_conditions(
    assert_errors,
    parse_ast_tree,
    code,
    default_options,
):
    """Testing that correct conditions work."""
    tree = parse_ast_tree(code)

    visitor = BooleanConditionVisitor(default_options, tree=tree)
    visitor.run()

    assert_errors(visitor, [])


@pytest.mark.parametrize('code', [
    'call() or call()',
    'attr.name and attr.name',
    '4 and 4',

    'name or name',
    'name and name',

    'name and proxy or name',
    '(name and proxy) or name',
    'name and (proxy or name)',

    'name and proxy and name',
    '(name and proxy) and name',
    'name and (proxy and name)',

    'name and name and name',
    'name or name or name',
])
def test_duplicate_element(
    assert_errors,
    parse_ast_tree,
    code,
    default_options,
):
    """Testing that duplicates raise a violation."""
    tree = parse_ast_tree(code)

    visitor = BooleanConditionVisitor(default_options, tree=tree)
    visitor.run()

    assert_errors(
        visitor,
        [SameElementsInConditionViolation],
        ImplicitTernaryViolation,
    )
