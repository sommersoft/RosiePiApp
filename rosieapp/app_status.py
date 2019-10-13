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

import json
import re
import subprocess
import sh


def get_server_status():
    status = {}

    up_sh = sh.uptime().strip()

    systime_re = re.search(r"^(.+)up", up_sh)
    if systime_re:
        status["system_time"] = systime_re.group(1).strip()
    else:
        status["system_time"] = "Unknown"

    uptime_re = re.search(r"up\s(.+(\:\d\d|min))\,", up_sh)
    if uptime_re:
        status["uptime"] = uptime_re.group(1).strip()
    else:
        status["uptime"] = "Unknown"

    return status

if __name__ == "__main__":

    app_status = {
        "server": get_server_status(),
    }

    print(json.dumps(app_status))
