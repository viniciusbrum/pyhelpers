# sublime_text.py - helpers for sublime text stuffs

import os
import sys


def clear_default_settings(path_settings: str) -> str:
    """
    Print Sublime's default settings ignoring comments lines.

    :return: path to settings after cleaning.
    """
    path_output = os.path.join(os.path.dirname(path_settings),
                               'sublime-settings.txt')
    with open(path_settings) as in_f:
        with open(path_output, 'w') as out_f:
            for line in in_f:
                line_strip = line.strip()
                if not line_strip or line_strip.startswith('//'):
                    continue
                out_f.write(line)
    return path_output


if __name__ == '__main__':
    import sys
    print('path:', clear_default_settings(sys.argv[1]))
