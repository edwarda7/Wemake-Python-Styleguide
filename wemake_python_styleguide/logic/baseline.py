import datetime as dt
import json
import os
from collections import defaultdict
from typing import NamedTuple
from typing import DefaultDict, Dict, Iterable, List, Mapping, Optional, Tuple

import attr
from typing_extensions import Final, TypedDict, final

#: That's a constant filename where we store our baselines.
BASELINE_FILE: Final = '.flake8-baseline.json'

#: We version baseline files independenly. Because we can break things.
BASELINE_FILE_VERSION: Final = '1'

#: Content is: `error_code, line_number, column, text, physical_line`.
CheckReport = Tuple[str, int, int, str, str]

#: This is how we identify the violation.
ViolationKey = Tuple[str, str]

#: Mapping of filename and the report result.
SavedReports = Dict[str, List[CheckReport]]

_BaselineMetadata = NamedTuple('_BaselineMetadata', [
    ('created_at', str),
    ('updated_at', str),
    ('baseline_file_version', str),
])

_BaselineEntry = NamedTuple('_BaselineEntry', [
    ('error_code', str),
    ('line', int),
    ('column', int),
    ('message', str),
    ('physical_line', str),
])


@final
@attr.dataclass(slots=True, frozen=True)
class _BaselineFile(object):
    """
    Baseline file representation.

    How paths are stored?
    We use ``path`` -> ``violations`` mapping.
    """

    metadata: _BaselineMetadata
    paths: Mapping[str, List[_BaselineEntry]]
    _db: Mapping[str, Mapping[ViolationKey, List[_BaselineEntry]]] = attr.ib(
        init=False,
        hash=False,
        eq=False,
        repr=False,
    )

    def __attrs_post_init__(self) -> None:
        """Builds a mutable database of known violations."""
        object.__setattr__(self, '_db', {})
        for filename, violations in self.paths.items():
            groupped: DefaultDict[
                ViolationKey, _BaselineEntry,
            ] = defaultdict(list)
            for one in violations:
                groupped[(one[0], one[3])].append(one)
            self._db.update({filename: groupped})

    def filter_group(
        self,
        filename: str,
        violation_key: ViolationKey,
        violations: List[CheckReport],
    ) -> List[CheckReport]:
        """
        Tells whether or not this violation is saved in the baseline.

        It uses several attempts to guess which violation is which. Why?
        Because one can move the violation upwards or downwards
        in the source code, but it will stay exactly the same.
        Or one can slightly modify the source code of the line,
        but leave it in the same place.

        We do realize that there would be some rear cases
        that old violations will be reported instead of new ones sometimes.
        But that's fine. Probably there's no determenistic algorithm for it.
        """
        candidates = self._db.get(filename, {}).get(violation_key, None)
        if not candidates:  # when we don't have any stored violations
            return violations  # we just return all reported violations

        print('violations', violations)
        print('candidates', candidates)

        # algorithm:
        # 1. find exact matches, remove them from being reported
        # 2. delete exact matches from the db
        # 3. start fuzzy match by `physical_line` and `line`
        # 4. delete fuzzy matches from the db
        # 5. start fuzzy match by `column` and `line`
        # 6. delete fuzzy matches from the db
        # 7. start fuzzy matches by `physical_line`
        # 8. delete fuzzy matches from the db

        matchers = [
            [1, 2, 4],
            [1, 4],
            [1, 2],
            [4],
        ]

        def x(args):
            def factory(c, v):
                print('==', args, c, v, all(c[a] == v[a] for a in args))
                return all(c[a] == v[a] for a in args)
            return factory

        for matcher in matchers:
            ignored_violations = []
            for violation in violations:
                b = self._try_match(candidates, violation, x(matcher))
                print('-----------------------------')
                print('try', violation, b, matcher)
                if b:
                    ignored_violations.append(violation)
            for ignored_violation in ignored_violations:
                violations.remove(ignored_violation)
                print('ignored', ignored_violation, matcher)
                print('left', candidates)
                print()
            # if ignored_violations:
            #     break
        return violations

    def _try_match(self, candidates, violation, matcher) -> bool:
        used_candidate = None
        for candidate in candidates:
            if matcher(candidate, violation):
                used_candidate = candidate
                break

        if used_candidate is not None:
            candidates.remove(used_candidate)
            return True
        return False

    def error_count(self) -> int:
        """Return the error count that is stored in the baseline."""
        return sum(len(per_file) for per_file in self.paths.values())

    @classmethod
    def from_report(
        cls,
        saved_reports: SavedReports,
    ) -> '_BaselineFile':
        """Factory method to construct baselines from ``flake8`` reports."""
        paths: DefaultDict[str, List[_BaselineEntry]] = defaultdict(list)
        for filename, reports in saved_reports.items():
            for report in reports:
                paths[filename].append(report)

        now = dt.datetime.now().isoformat()
        return cls(
            _BaselineMetadata(now, now, BASELINE_FILE_VERSION),
            paths,
        )


def filter_out_saved_in_baseline(
    baseline: Optional[_BaselineFile],
    reported: Iterable[CheckReport],
    filename: str,
) -> Iterable[CheckReport]:
    """We don't need to report violations saved in the baseline."""
    if baseline is None:
        return reported  # baseline does not exist yet, return everything

    new_results = []  # TODO list comp

    groupped = defaultdict(list)
    for check_report in reported:
        groupped[(check_report[0], check_report[3])].append(check_report)

    for violation_key, violations in groupped.items():
        new_results.extend(baseline.filter_group(
            filename, violation_key, violations,
        ))
    return new_results


def baseline_fullpath() -> str:
    """We only store baselines in the current (main) directory."""
    return os.path.join(os.curdir, BASELINE_FILE)


def load_from_file() -> Optional[_BaselineFile]:
    """
    Loads baseline ``json`` files from current workdir.

    It might return ``None`` when file does not exist.
    It means, that we run ``--baseline`` for the very first time.
    """
    try:
        with open(baseline_fullpath()) as baseline_file:
            return _BaselineFile(**json.load(baseline_file))
    except IOError:  # There was probably no baseline file, that's ok.
        return None  # We will create a new one later.


def write_new_file(
    saved_reports: SavedReports,
) -> _BaselineFile:
    """Creates and writes new baseline ``json`` file in current workdir."""
    baseline = _BaselineFile.from_report(saved_reports)
    baseline_data = attr.asdict(
        baseline,
        # We don't need to dump private and protected attributes.
        filter=lambda attrib, _: not attrib.name.startswith('_'),
    )
    with open(baseline_fullpath(), 'w') as baseline_file:
        json.dump(
            baseline_data,
            baseline_file,
            sort_keys=True,
            indent=2,
        )
    return baseline
