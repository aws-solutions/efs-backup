#!/usr/bin/env python

import os
import pip

def install_dependencies(function_path):
    """get dependencies in requirements.txt

    """
    function_path = os.path.normpath(function_path)
    if os.path.isfile(os.path.join(function_path, 'requirements.txt')):
        f = open(os.path.join(function_path, 'requirements.txt'), 'r')
        for package in f.readlines():
            package = package.replace('\n', '')
            print "\n Installing {} \n -------------------------".format(package)
            try:
                pip.main(["install", "--upgrade", package])
                # pip.main(['install', '--upgrade', '--target', function_path, package])
            except Exception as e:
                print "Unable to install %s using pip. Please read the instructions for \
                            manual installation.. Exiting" % package
                print "Error: %s" % (e)
        f.close()


if __name__ == "__main__":
    if 'scripts' not in os.getcwd():
        os.chdir('./source/scripts')
    # package files in this directory
    function_path = '../../source'
    install_dependencies(function_path)
