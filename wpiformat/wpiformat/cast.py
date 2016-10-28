"""This task disallows C-style casts."""

import re

from wpiformat.task import Task


class Cast(Task):
    def should_process_file(self, config_file, name):
        return config_file.is_cpp_file(name)

    def run_pipeline(self, config_file, name, lines):
        linesep = Task.get_linesep(lines)
        format_succeeded = True

        # C-style casts are surrdounded by parenthesis, have a space, left
        # parenthesis, or comma before them, and contain a type name optionally
        # followed by pointer asterisks.
        regex_str = "(?<=[^>])\s*\([A-Za-z][A-Za-z0-9]*\s*\**\)\s*"

        for match in re.finditer(regex_str, lines):
            token = match.group(0)

            linenum = lines.count(linesep, 0, match.start()) + 1
            format_succeeded = False

            # Casts aren't followed by ")", ",", or "?"
            if (
                lines[match.end()] == ")"
                or lines[match.end()] == ","
                or lines[match.end()] == "?"
                or (match.start() >= 6 and lines[match.start() - 6 : 6] == "return")
            ):
                print(
                    name
                    + ": "
                    + str(linenum)
                    + ": unnecessary parentheses '"
                    + token.lstrip()
                    + "'"
                )
            elif lines[match.start() - 1] == "(" or lines[match.start() - 1] == ",":
                print(
                    name
                    + ": "
                    + str(linenum)
                    + ": C-style cast '"
                    + token.lstrip()
                    + "'"
                )

        return (lines, False, format_succeeded)
