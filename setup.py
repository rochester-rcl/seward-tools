from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = ['lxml._elementpath'], excludes = [])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('seward_file_checker.py', base=base)
]

setup(name='SewardQC',
      version = '1.0',
      description = '',
      options = dict(build_exe = buildOptions),
      executables = executables)
