#! /usr/bin/env python3

from sys import exit
from sys import argv
import os
import re


class JackTokenizer:
    def __init__(self, filename):
        """ Opens the .jack file and initializes it to read from"""
        self.filename = filename
        self.tokens = [token for token in self.process()]
        pass

    def process(self):
        keywords = {'class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean',
                    'void',
                    'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return'}
        tokens_patterns = [
            ("stringConstant", r'"([^"]|.)*"'),
            ("identifier", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
            ("integerConstant", r"\b\d+\b"),
            ("symbol", r"[][(){}.,;+*/&,<>=~|-]"),
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in tokens_patterns)

        with open(self.filename) as inFileHandle:
            isComment = False
            for line in inFileHandle:
                line = line.strip()
                # Handling comments
                if isComment and "*/" in line:
                    line = line[line.find("*/")+2:]
                    isComment = False
                if "//" in line:
                    line = line[:line.find("//")]
                if "/*" in line and "*/" in line:
                    line = line[:line.find("/*")] + line[line.find("*/")+2:]
                if "/*" in line and "*/" not in line:
                    isComment = True
                if isComment:
                    continue
                if line == '':
                    continue
                # End of handling comments
                for mo in re.finditer(tok_regex, line):
                    kind = mo.lastgroup
                    value = mo.group()
                    if kind == "identifier" and value in keywords:
                        yield "keyword", value
                    elif kind == "stringConstant":
                        value = value[1:-1]
                        yield kind, value
                    else:
                        yield kind, value

    def advance(self):
        assert self.hasMoreTokens()
        self.tokens.pop(0)

    def nextToken(self):
        assert len(self.tokens) >= 2
        return self.tokens[1][1]

    def nextTokenType(self):
        assert len(self.tokens) >= 2
        return self.tokens[1][0]

    def currentToken(self):
        assert len(self.tokens) >= 1
        return self.tokens[0][1]

    def tokenType(self):
        assert len(self.tokens) >= 1
        return self.tokens[0][0]

    def hasMoreTokens(self):
        return len(self.tokens) > 0


def main():
    if len(argv) != 2:
        print("Usage: ./JackTokenizer.py [.jack file]")
        return 1
    if not os.path.isfile(argv[1]) and not argv[1].endswith(".jack"):
        print(f"{argv[1]} is not a valid file")

    with open(argv[1].replace(".jack", ".token"), 'w') as outFileHandle:
        outFileHandle.write("<tokens>\n")
        for kind, value in JackTokenizer(argv[1]).tokens:
            outFileHandle.write(f"<{kind}> {value} </{kind}>\n")
        outFileHandle.write("</tokens>\n")
    return 0


if __name__ == "__main__":
    exit(main())
