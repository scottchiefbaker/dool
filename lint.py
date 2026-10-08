#!/usr/bin/env python3

"""Stdlib-only lint for the dool repo. Run with `make lint`.

Checks, for every source file:
  - it compiles with warnings treated as errors (syntax errors, TabError,
    invalid escape sequences)
  - it has no unused imports

A line that imports a name only to probe for a dependency can be marked with
a trailing `# noqa` comment to skip the unused-import check for that line.

Pass file paths as arguments to check specific files instead of the repo set.
"""

import ast
import glob
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.abspath(__file__))

DEFAULT_FILES = (
    ['dool', 'install.py']
    + sorted(glob.glob(os.path.join(ROOT, 'plugins', '*.py')))
    + sorted(glob.glob(os.path.join(ROOT, 'tests', '*.py')))
    + sorted(glob.glob(os.path.join(ROOT, 'packaging', '*.py')))
)


def display_name(path):
    return os.path.relpath(path, ROOT)


def check_compile(path, source):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            return ast.parse(source, path), []
    except (SyntaxError, SyntaxWarning, DeprecationWarning) as err:
        return None, ['%s:%s: %s: %s' % (display_name(path), err.lineno or 0,
                                         type(err).__name__, err.msg if hasattr(err, 'msg') else err)]


def check_unused_imports(path, tree, lines):
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [(a.asname or a.name).split('.')[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [a.asname or a.name for a in node.names if a.name != '*']
        else:
            continue
        if node.lineno <= len(lines) and '# noqa' in lines[node.lineno - 1]:
            continue
        for name in names:
            imported[name] = node.lineno

    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    problems = []
    for name, lineno in sorted(imported.items(), key=lambda item: item[1]):
        if name not in used:
            problems.append('%s:%d: unused import %s' % (display_name(path), lineno, name))
    return problems


def lint_file(path):
    with open(path, encoding='utf-8') as fh:
        source = fh.read()
    tree, problems = check_compile(path, source)
    if tree is None:
        return problems
    return check_unused_imports(path, tree, source.splitlines())


def main(argv):
    files = argv or DEFAULT_FILES
    problems = []
    for path in files:
        problems.extend(lint_file(path))

    for line in problems:
        print(line)
    if problems:
        print('%d problem(s) in %d file(s) checked' % (len(problems), len(files)))
        return 1
    print('%d files lint clean' % len(files))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
