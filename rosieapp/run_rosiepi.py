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
import jinja2
import json
import pathlib

#import rosiepi as rosiepi_version
from rosiepi.rosie import find_circuitpython, test_controller

cli_parser = argparse.ArgumentParser(description="RosieApp")
cli_parser.add_argument(
    "commit",
    help="Commit of circuitpython firmware to build"
)


ROSIE_BOARDS = ["metro_m4_express", "feather_nrf52850"]
GIT_URL_COMMIT = "https://github.com/adafruit/circuitpython/commit/"

def process_rosie_log(log):
    rosie_log = []
    subsection = []
    for line in log.split("\n"):
        if line.count("=") < 25:
            if line.count("-") < 60:
                subsection.append(line)
            else:
                continue
        else:
            rosie_log.append(subsection)
            subsection = []

    return rosie_log


def run_rosie(commit):
    """ Runs rosiepi for each board in `ROSIE_BOARDS`.
        Returns results as a JSON for sending to GitHub.

        :param: commit: The commit of circuitpython to pass to rosiepi.
    """

    template_dir = pathlib.Path() / 'rosieapp/templates'
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir.resolve()))
    )

    app_conclusion = ""
    app_completed_at = None

    summary_template = jinja_env.get_template('completed_check_summary.html')
    summary_params = {
        "commit_title": commit[:5],
        "commit_url": "".join([GIT_URL_COMMIT, commit]),
        "rosie_version": "0.1", #rosiepi_version,
    }
    app_output_summary = summary_template.render(summary_params)
    app_output = {
        "title": "RosiePi",
        "summary": app_output_summary,
        "text": "",
    }

    board_output_text = []
    for board in ROSIE_BOARDS:
        board_results = {
            "board_name": board,
            "outcome": None,
            "rosie_log": [],
        }
        rosie_test = test_controller.TestController(board, commit)
        # check if connection to board was successful
        if rosie_test.state != "error":
            rosie_test.start_test()
        else:
            board_results["outcome"] = "Error"
            print(rosie_test.log.getvalue())
            board_results["rosie_log"] = process_rosie_log(rosie_test.log.getvalue())
            board_output_text.append(board_results)
            app_conclusion = "failure"
            continue

        # now check the result of each board test
        if rosie_test.result: # everything passed!
            board_results["outcome"] = "Passed"
            if app_conclusion != "failure":
                app_conclusion = "success"
        else:
            if rosie_test.state != "error":
                board_results["outcome"] = "Failed"
            else:
                board_results["outcome"] = "Error"
            app_conclusion = "failure"

        board_results["rosie_log"] = process_rosie_log(rosie_test.log.getvalue())
        board_output_text.append(board_results)

    completed_template = jinja_env.get_template('completed_check_run.html')
    html_output = ""
    for test in board_output_text:
        html_output += completed_template.render(test) + "\n"
    #print(html_output)
    app_output["text"] = html_output

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
