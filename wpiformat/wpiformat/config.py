"""Handles wpiformat config files."""

import re
from pathlib import Path
from typing import ClassVar


class Config:
    # Dict from filepath to file contents
    __config_cache: ClassVar[dict[Path, list[str]]] = {}

    def __init__(self, directory: Path, filename: Path):
        """
        Constructor for Config object.

        Args:
            directory: Directory in which to start search for file.
            filename: Filename.
        """
        self.__config_dict = self.__parse_config_file(directory, filename)
        self.__c_header_include_regex = self.regex("cHeaderFileInclude")
        self.__cpp_header_include_regex = self.regex("cppHeaderFileInclude")
        self.__cpp_src_include_regex = self.regex("cppSrcFileInclude")
        self.__generated_exclude_regex = self.regex("generatedFileExclude")
        self.__modifiable_exclude_regex = self.regex("modifiableFileExclude")

    @staticmethod
    def read_file(directory: Path, filename: Path) -> tuple[Path, list[str]]:
        """
        Find file and return contents.

        Checks current directory for file. If one doesn't exist, try all parent
        directories as well.

        Args:
            directory: Current directory from which to start search.
            filename: Filename.

        Raises:
            OSError: If no file was found.

        Returns:
            Tuple of filename and list containing file contents.
        """
        for parent in (directory / filename).parents:
            filepath = parent / filename
            try:
                # If filepath in config cache, return cached version instead
                if config_file := Config.__config_cache.get(filepath):
                    return filepath, config_file

                contents = filepath.read_text().splitlines()
                Config.__config_cache[filepath] = contents

                # TODO: Remove deprecation message
                if filename.name.startswith(".styleguide"):
                    new_name = filename.name.replace("styleguide", "wpiformat")
                    print(
                        f"warning: rename deprecated {filepath} to {filepath.with_name(new_name)}"
                    )

                return filepath, contents
            except OSError:
                # .git files are ignored, which are created within submodules
                if (parent / ".git").is_dir():
                    raise
        raise OSError

    def group(self, group_name: str) -> list[str]:
        """
        Returns value from config dictionary given key string.

        Args:
            group_name: Config group name.
        """
        if not self.__config_dict:
            return []

        try:
            return self.__config_dict[group_name]
        except KeyError:
            return []

    def regex(self, *args) -> re.Pattern:
        """
        Converts contents of group from config file into regex.

        Args:
            *args: Argument list of groups. They are all joined by "|".

        Returns:
            Compiled regex.
        """
        group_contents = []

        for group_name in args:
            group = self.group(group_name)

            # If group exists
            if len(group) > 0:
                group_contents.extend(group)

        if len(group_contents) == 0:
            # If regex string is empty, make regex match nothing
            return re.compile(r"a^")
        else:
            return re.compile(r"|".join(group_contents))

    def is_c_file(self, filename: Path) -> bool:
        """
        Returns True if file is either C header or C source file.

        Args:
            filename: Filename.
        """
        return self.is_c_header_file(filename) or self.is_c_src_file(filename)

    def is_c_header_file(self, filename: Path) -> bool:
        """
        Returns True if file is C header file.

        Args:
            filename: Filename.
        """
        return self.__c_header_include_regex.search(filename.as_posix()) is not None

    @staticmethod
    def is_c_src_file(filename: Path) -> bool:
        """
        Returns True if file is C source file.

        Args:
            filename: Filename.
        """
        return filename.suffix == ".c"

    def is_cpp_file(self, filename: Path) -> bool:
        """
        Returns True if file is either C++ header or C++ source file.

        Args:
            filename: Filename.
        """
        return self.is_cpp_header_file(filename) or self.is_cpp_src_file(filename)

    def is_cpp_header_file(self, filename: Path) -> bool:
        """
        Returns True if file is C++ header file.

        Args:
            filename: Filename.
        """
        return (
            filename.suffix == ".hpp"
            or self.__cpp_header_include_regex.search(filename.as_posix()) is not None
        )

    def is_cpp_src_file(self, filename: Path) -> bool:
        """
        Returns True if file is C++ source file.

        Args:
            filename: Filename.
        """
        return (
            filename.suffix == ".cpp"
            or self.__cpp_src_include_regex.search(filename.as_posix()) is not None
        )

    def is_header_file(self, filename: Path) -> bool:
        """
        Returns True if file is either C or C++ header file.

        Args:
            filename: Filename.
        """
        return self.is_c_header_file(filename) or self.is_cpp_header_file(filename)

    def is_generated_file(self, filename: Path) -> bool:
        """
        Returns True if file is generated (generated files are skipped).

        Args:
            filename: Filename.
        """
        return self.__generated_exclude_regex.search(filename.as_posix()) is not None

    def is_modifiable_file(self, filename: Path) -> bool:
        """
        Returns True if file is modifiable but should be skipped.

        Args:
            filename: Filename.
        """
        return self.__modifiable_exclude_regex.search(filename.as_posix()) is not None

    def __parse_config_file(
        self, directory: Path, filename: Path
    ) -> dict[str, list[str]]:
        """
        Parse values from config file.

        Checks current directory for config file. If one doesn't exist, try all
        parent directories as well.

        Args:
            directory: Current directory from which to start search.
            filename: Config filename.

        Returns:
            Dictionary of groups (group name -> list of values).
        """
        in_group = False
        config_group = {}
        group_name = ""
        group_elements = []

        try:
            self.filename, lines = self.read_file(directory, filename)
        except OSError:
            self.filename = "<none found>"
            return {}
        if not lines:
            return {}

        for line in lines:
            # Skip empty lines
            if line.strip() == "":
                continue

            if "{" in line:
                in_group = True

                # Group name is on same line as "{"
                group_name = line[: line.find("{")].strip()
            elif "}" in line:
                in_group = False

                # After group closes, save element list and clear it
                config_group[group_name] = group_elements
                group_elements = []
            elif in_group:
                group_elements.append(line.strip())
        return config_group
