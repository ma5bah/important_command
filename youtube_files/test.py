#!/bin/bash


import os
import sys


def main():
    list_of_files = os.listdir()
    for file in list_of_files:
        if os.path.isfile(file):
            name_of_file = file
            if name_of_file == "test.py":
                continue
            print(name_of_file)
            print(name_of_file[3:])
            # os.rename(name_of_file, name_of_file[3:])

if __name__ == "__main__":
    main()