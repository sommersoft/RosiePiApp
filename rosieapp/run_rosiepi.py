 # The MIT License (MIT)
 #
 # Copyright (c) 2019 Michael Schroeder
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documentation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to whom the Software is
 # furnished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 #

import argparse
import datetime
import json
from rosiepi.rosie import find_circuitpython, test_controller

cli_parser = argparse.ArgumentParser(description="RosieApp")
cli_parser.add_argument(
    "commit",
    help="Commit of circuitpython firmware to build"
)


ROSIE_BOARDS = ["metro_m4_express"]
GIT_URL_COMMIT = "https://github.com/adafruit/circuitpython/commit/"

markdown_templates = {
    "table_separator": "|",
    "table_header_centered": ":---:",
    "table_header_left": ":---",
    "table_header_right": "---:",
}


def parse_log_for_test(log, test_filename):
    """ Parse the log, extract the `test_filename` section, and return it
        as a string.

        :param: list log: The log as a list. (`split("\n")` is advised.)
        :param: str test_filename: The filename of the test to search for.
    """
    found_start = False
    found_end = False
    for idx, line in enumerate(log):
        if (line.startswith("Starting test:") and test_filename in line):
            found_start = idx
        if (found_start != False and line == "-"*60):
            found_end = idx - 1
        if False not in [found_start, found_start]:
            break

    extract = []
    for line in log[found_start:found_end]:
        if (line.count("=") < 25) and (line.count("-") < 60):
            extract.append(line + "<br>")

    return "\n".join(extract)


def run_rosie(commit):
    """ Runs rosiepi for each board in `ROSIE_BOARDS`.
        Returns results as a JSON for sending to GitHub.

        :param: commit: The commit of circuitpython to pass to rosiepi.
    """
    app_conclusion = ""
    app_completed_at = None
    app_output_summary = [
        "RosiePi",
        "=======",
        "Commit: [{short}]({git_url}{full})".format(short=commit[:5],
                                                    git_url=GIT_URL_COMMIT,
                                                    full=commit)
    ]
    app_output = {"title": "RosiePi", "summary": "\n".join(app_output_summary),
                  "text": ""}

    board_output_text = [
        ["Board", "Result", "Summary"],
        [
            markdown_templates["table_header_left"],
            markdown_templates["table_header_centered"],
            markdown_templates["table_header_left"]
        ],
    ]
    for board in ROSIE_BOARDS:
        rosie_test = test_controller.TestController(board, commit)
        # check if connection to board was successful
        if rosie_test.state != "error":
            rosie_test.start_test()
        else:
            clean_log = []
            for line in rosie_test.log.getvalue().split("\n"):
                if (line.count("=") < 25) and (line.count("-") < 60):
                    clean_log.append(line + "<br>")

            board_output_text.append([board, "failed", "".join(clean_log)])
            app_conclusion = "failure"
            continue

        # now check the result of each board test
        log_extract = rosie_test.log.getvalue().split("\n")
        if rosie_test.result: # everything passed!
            test_output = [
                board,
                "passed",
                ", ".join(log_extract[-5:-2])
            ]
            board_output_text.append(test_output)
            app_conclusion = "success"
        else:
            if rosie_test.state != "error":
                for test in rosie_test.tests:
                    if test.test_result == False:
                        test_output = [
                            board,
                            "failed",
                            parse_log_for_test(log_extract, test.test_file)
                        ]
                        board_output_text.append(test_output)
            else:
                clean_log = []
                for line in rosie_test.log.getvalue().split("\n"):
                    if (line.count("=") < 25) and (line.count("-") < 60):
                        clean_log.append(line + "<br>")

                board_output_text.append([board, "failed", "".join(clean_log)])

            app_conclusion = "failure"

    app_output["text"] = (
        "|\n".join(["|" + "|".join(line) for line in board_output_text]) + "|"
    )
    app_completed_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "conclusion": app_conclusion,
        "completed_at": app_completed_at,
        "output": app_output,
    }
    #print("payload:", payload)
    json_payload = json.dumps(payload)
    print(json_payload)

if __name__ == "__main__":
    cli_arg = cli_parser.parse_args()
    run_rosie(cli_arg.commit)
