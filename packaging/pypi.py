#!/usr/bin/env python3

import os
import pathlib
import sys

root_dir = pathlib.Path(__file__).parents[1]
dool_dir = root_dir / 'dool'
dool_dir.rename('__main__.py')
dool_dir.mkdir()
(root_dir / '__main__.py').rename(dool_dir / '__main__.py')
(root_dir / 'plugins').rename(dool_dir / 'plugins')

sys.path.append(root_dir.as_posix())
import dool.__main__

(dool_dir / '__init__.py').write_text(f'"""{dool.__main__.__doc__}"""\n\n__version__ = "{dool.__main__.__version__}"')

os.execlp('python3', 'python3', '-m', 'build')
