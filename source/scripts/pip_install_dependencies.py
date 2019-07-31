#!/usr/bin/env python

import os
import subprocess

def install_dependencies(function_path):
    """get dependencies in requirements.txt

    """
    function_path = os.path.normpath(function_path)
    requirements_path = os.path.join(function_path, 'requirements.txt')
    if os.path.isfile(requirements_path):
        try:
            subprocess.call(["pip", "install", "-r", requirements_path, "--upgrade"])
        except Exception as e:
            print("Error: %s" % (e))

if __name__ == "__main__":
    if 'scripts' not in os.getcwd():
        os.chdir('./source/scripts')
    # package files in this directory
    function_path = '../../source'
    install_dependencies(function_path)
