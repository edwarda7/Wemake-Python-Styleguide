# -*- coding: utf-8 -*-

from wemake_python_styleguide.options.config import Configuration


def test_all_violations_are_documented(all_module_violations):
    """Ensures that all violations are documented."""
    for module, classes in all_module_violations.items():
        for violation_class in classes:
            # Once per `summary` and once per `autoclass`:
            assert module.__doc__.count(violation_class.__qualname__) == 2


def test_all_violations_have_versionadded(all_violations):
    """Ensures that all violations have `versionadded` tag."""
    for violation in all_violations:
        assert '.. versionadded:: ' in violation.__doc__


def test_violation_name(all_violations):
    """Ensures that all violations have `Violation` suffix."""
    for violation in all_violations:
        class_name = violation.__qualname__
        assert class_name.endswith('Violation'), class_name


def test_configuration(all_violations):
    """Ensures that all configuration options are listed in the docs."""
    option_listed = {
        option.long_option_name: False for option in Configuration.options
    }

    for violation in all_violations:
        for option in option_listed.keys():
            if option in violation.__doc__:
                option_listed[option] = True

                assert 'Configuration:' in violation.__doc__
                assert 'Default:' in violation.__doc__

    for option, is_listed in option_listed.items():
        assert is_listed, option
