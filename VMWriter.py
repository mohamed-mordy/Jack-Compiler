#!/usr/bin/env python3

from sys import exit


class VMWriter:
    def __init__(self, output_file):
        self.file_ptr = open(output_file, "w")

    def writePush(self, segment, index):
        """ Writes a VM push command"""
        self.file_ptr.write(f"push {segment} {index}\n")

    def writePop(self, segment, index):
        """ Writes a VM pop command"""
        self.file_ptr.write(f"pop {segment} {index}\n")

    def writeArithmetic(self, command, unary=False):
        """ Writes a VM arithmetic-logic command"""
        if unary:
            operators = {'-': 'neg', '~': 'not'}
            self.file_ptr.write(f'{operators[command]}\n')
        else:
            operators = {'+': 'add', '-': 'sub', '*': 'call Math.multiply 2',
                         '/': 'call Math.divide 2', '&': 'and', '|': 'or',
                         '=': 'eq', '>': 'gt', '<': 'lt'}
            self.file_ptr.write(f"{operators[command]}\n")

    def writeLabel(self, label):
        """ Writes a VM label command"""
        self.file_ptr.write(f"label {label}\n")

    def writeGoto(self, label):
        """ Writes a VM goto command"""
        self.file_ptr.write(f"goto {label}\n")

    def writeIf(self, label):
        """ Writes a VM if-goto command"""
        self.file_ptr.write(f"if-goto {label}\n")

    def writeCall(self, name, n_args):
        """ Writes a VM call command"""
        self.file_ptr.write(f"call {name} {n_args}\n")

    def writeFunction(self, name, n_locals):
        """ Writes a VM function command"""
        self.file_ptr.write(f"function {name} {n_locals}\n")

    def writeReturn(self):
        """ Writes a VM return command"""
        self.file_ptr.write("return\n")

    def writeMessage(self, message):
        """ this method is for debugging purposes"""
        self.file_ptr.write(f'{message}\n')

    def close(self):
        """ Closes the output file"""
        self.file_ptr.close()


def main():
    return 0


if __name__ == "__main__":
    exit(main())
