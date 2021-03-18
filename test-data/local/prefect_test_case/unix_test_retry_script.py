#!/usr/bin/env python
import os


def write_file(text, file):
    with open(file, "w") as f:
        f.write(text)


def read_file(file):
    with open(file, "r") as f:
        return f.read()


if __name__ == "__main__":
    file_name = "run.no"
    max_failure_no = 2
    if os.path.exists(file_name):
        run_no = int(read_file(file_name))
        run_no += 1
        write_file(str(run_no), file_name)
    else:
        run_no = 1
        write_file("1", file_name)

    if run_no <= max_failure_no:
        raise Exception(f"Fail run {run_no} out of max failures {max_failure_no}")
