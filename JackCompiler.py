#!/usr/bin/env python3

from sys import exit
from sys import argv
from CompilationEngine import CompilationEngine
import os


def main():
    if len(argv) != 2:
        print("Usage: JackCompiler [.jack file_name] | [directory_name]")
        return 1
    if os.path.isfile(argv[1]) and argv[1].endswith(".jack"):
        CompilationEngine(argv[1], argv[1].replace(".jack", ".vm"))
    elif os.path.isdir(argv[1]):
        files = [file for file in os.listdir(argv[1]) if file.endswith(".jack")]
        os.chdir(argv[1])
        files = map(os.path.abspath, files)
        [CompilationEngine(file, file.replace(".jack", ".vm")) for file in files]
    else:
        print("Provide a valid input..")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())


