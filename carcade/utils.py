import subprocess


def sh(shell_command):
    subprocess.call(shell_command, shell=True)
