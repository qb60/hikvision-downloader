#!/usr/bin/python3
import datetime
import os
import re
import sys

OUT_FILE_NAME = 'test/out.py'
MAIN_FILE_NAME = 'test/main.py'
SOURCE_DIR_NAME = 'src'
TOKEN_TO_FIND = 'from ' + SOURCE_DIR_NAME + '.'


def emplace_imports(base_dir, file_name, used_imports):
    print('Process {}'.format(file_name))

    input_file = open(file_name, 'r')
    lines = input_file.readlines()

    new_lines = []
    for line in lines:
        if line[-1] != '\n':
            line += '\n'

        import_found = re.search(TOKEN_TO_FIND + '\w+', line)
        if import_found:
            import_name = import_found.group()[len(TOKEN_TO_FIND):]
            if import_name not in used_imports:
                new_lines.append('# {}'.format(line))
                new_lines.append('# ================= START {} ===================\n'.format(import_name))

                submodule_lines = emplace_imports(base_dir, '{}/{}/{}.py'.format(base_dir, SOURCE_DIR_NAME, import_name), used_imports)

                new_lines += submodule_lines
                new_lines.append('# ================= END {} ===================\n'.format(import_name))

                used_imports.append(import_name)
        else:
            new_lines.append(line)

    return new_lines


def main():
    if len(sys.argv) == 3:
        in_file_name = sys.argv[1]
        out_file_name = sys.argv[2]

        subdir = os.path.dirname(in_file_name)
        new_file = emplace_imports(subdir, in_file_name, [])

        today = datetime.datetime.now().strftime('# %Y-%m-%d\n')
        new_file.insert(1, today)

        output_file = open(out_file_name, 'w')
        output_file.writelines(new_file)
        output_file.close()

    else:
        print('USAGE:')
        print('    {} INPUT_FILE OUTPUT_FILE'.format(sys.argv[0]))

    print('')


if __name__ == '__main__':
    main()