import os
import subprocess

from zkay.config import cfg
from typing import List


def run_command(cmd: List[str], cwd=None, key: str = None):
    if cwd is not None:
        cwd = os.path.abspath(cwd)

    if key in cfg.debug_output_whitelist and not cfg.is_unit_test:
        process = subprocess.Popen(cmd, cwd=cwd)
        output, error = process.communicate() # will be None
    else:
        # run
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)

        # collect output
        output, error = process.communicate()

        # decode output
        output = output.decode('utf-8').rstrip()
        error = error.decode('utf-8').rstrip()

    # check for error
    if process.returncode != 0:
        cmd = get_command(cmd)
        msg = f"Non-zero exit status {process.returncode} for command:\n{cwd}: $ {cmd}\n\n{output}\n{error}"
        raise subprocess.SubprocessError(msg)

    return output, error


def get_command(cmd: List[str]):
    def format_part(p: str):
        if ' ' in p:
            return f'"{p}"'
        else:
            return p

    str_command = " ".join(format_part(p) for p in cmd)
    return str_command
