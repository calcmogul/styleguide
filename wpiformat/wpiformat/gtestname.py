"""This task ensures GoogleTest test names follow the format
"TEST(ThingTest, Thing)".
"""

import regex

from wpiformat.task import PipelineTask


class GTestName(PipelineTask):
    @staticmethod
    def should_process_file(config_file, name):
        return config_file.is_cpp_file(name)

    def run_pipeline(self, config_file, name, lines):
        output = ""
        success = True

        # List of tuples containing old and new test suite name
        test_suite_renames = []

        test_name_rgx = regex.compile(
            r"\b(?P<test_type>TEST(_F|_P)?)\((?P<whitespace>\s*)(?P<test_suite>\w+), (?P<test_case>\w+)\)"
        )
        extract_location = 0
        for match in test_name_rgx.finditer(lines):
            test_type = match.group("test_type")
            test_suite = match.group("test_suite")
            test_case = match.group("test_case")

            # Write lines prior to test
            output += lines[extract_location : match.start()]

            # Write test type
            output += test_type + "("
            if match.group("whitespace"):
                output += match.group("whitespace")

            # Fix test suite name
            old_test_suite = test_suite
            if test_suite.endswith("Tests"):
                test_suite = test_suite[:-1]
            if not test_suite.endswith("Test"):
                test_suite += "Test"
            if old_test_suite != test_suite:
                test_suite_renames.append((old_test_suite, test_suite))

            # Write test suite name
            output += test_suite

            # Fix test case name
            if test_case == "Test" or test_case == "Tests":
                print(
                    f"Error: {name}: undescriptive test case name '{test_case}' in '{test_suite}.{test_case}'"
                )
                success = False
            else:
                if test_case.endswith("Test"):
                    test_case = test_case[:-4]
                if test_case.endswith("Tests"):
                    test_case = test_case[:-5]
            if test_case.startswith("Test") or test_case.startswith("test"):
                test_case = test_case[4:]

            # Write test case name
            output += ", " + test_case + ")"

            extract_location = match.end()

        # If input has unprocessed lines, write them to output
        if extract_location < len(lines):
            output += lines[extract_location:]

        # Reset for next regex iteration
        lines = output
        output = ""

        inst_rgx = regex.compile(
            r"INSTANTIATE_TEST_SUITE_P\((?P<whitespace>\s*)(?P<test_suite>\w+), (?P<test_case>\w+)"
        )
        extract_location = 0
        for match in inst_rgx.finditer(lines):
            test_suite = match.group("test_suite")
            test_case = match.group("test_case")

            # Write lines prior to test
            output += lines[extract_location : match.start()]
            output += "INSTANTIATE_TEST_SUITE_P("
            if match.group("whitespace"):
                output += match.group("whitespace")

            # Fix test suite name
            old_test_suite = test_suite
            if test_suite.endswith("Test"):
                test_suite += "s"
            if not test_suite.endswith("Tests"):
                test_suite += "Tests"
            if old_test_suite != test_suite:
                test_suite_renames.append((old_test_suite, test_suite))

            # Write test suite name
            output += test_suite

            # Fix test case name
            # TODO: Add NOLINT support since TimedRobot has a "TestMode" test
            # case
            # linenum = lines.count(linesep, 0, match.start()) + 1
            # if "NOLINT" not in lines.splitlines()[linenum - 1]:
            #     format_succeeded = False
            #     print(name + ": " + str(linenum) + ": '" + token + \
            #           "' in global namespace")
            if test_case.endswith("Tests"):
                test_case = test_case[:-1]
            if not test_case.endswith("Test"):
                test_case += "Test"
            if test_case.startswith("Test") or test_case.startswith("test"):
                test_case = test_case[4:]

            # Write test case name
            output += ", " + test_case

            extract_location = match.end()

        # If input has unprocessed lines, write them to output
        if extract_location < len(lines):
            output += lines[extract_location:]

        # If test suites for fixtures or parameterized tests were renamed,
        # rename the corresponding classes too
        for rename in test_suite_renames:
            output = regex.sub(f"class {rename[0]}", f"class {rename[1]}", output)

        return output, success
