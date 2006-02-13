#!/usr/bin/env python

# Make 'cwd'/src in the PYTHONPATH
import sys, os, os.path
PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
os.chdir(PATH)
PATH = os.path.join(PATH, "src")
sys.path[0] = PATH

# Start the service
import main
main.main()
