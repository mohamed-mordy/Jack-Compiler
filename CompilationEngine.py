#! /usr/bin/env python3


from sys import exit
from JackTokenizer import JackTokenizer
from VMWriter import VMWriter
from SymbolTable import ST

"""
* Static variables:
    * seen by all the class subroutines; must exist throughout
        the program execution.
    * of a .jack class file are mapped on the virtual memory
        segment static of the compiled .vm class file.
* Local variables:
    * during run-time, each time a subroutine is invoked,
        it must get a fresh set of local variables;
        each time a subroutine returns, its local variables must be recycled.
    * are mapped on the virtual segment 'local'.
* Argument variables:
    * same as local variables.
    * are mapped on the virtual segment 'argument'.
* Field variables:
    * unique to object-oriented languages.
    * of the current object are accessed as follow:
        * 'pointer 0' is set to 'argument 0'.
        * the i-th field of this object is mapped on 'this i'.
"""

op = "+-*/&|=><"
unaryOp = "-~"
keywordConstant = {"true", "false", "null", "this"}


class CompilationEngine:

    def __init__(self, input_filename, output_filename):
        """ Creates a new compilation engine with the given input and output.
            The next routine called must be compileClass. """
        self.className = None
        self.subroutineName = None
        self.subroutineKind = None
        self.classST = None
        self.subroutineST = None

        self.labelCount = 0
        self.tokenizer = JackTokenizer(input_filename)

        self.vmWriter = VMWriter(output_filename)
        self.compileClass()
        self.vmWriter.close()

    def incLabelCount(self):
        self.labelCount = self.labelCount + 1

    def compileClass(self):
        """ Compiles a complete class. """
        self.tokenizer.advance()  # steps over 'class'
        self.className = self.tokenizer.currentToken()  # gets 'className'
        self.tokenizer.advance()  # steps over 'className'
        self.tokenizer.advance()  # steps over '{'

        self.classST = ST()  # builds class-level symbol-table
        while self.tokenizer.currentToken() in ["field", "static"]:
            self.compileClassVarDec()

        #  compiles every subroutine in the class, and writes the appropriate code
        while self.tokenizer.currentToken() in ["constructor", "method", "function"]:
            self.compileSubroutineDec()

        self.tokenizer.advance()  # steps over '}'

    def compileClassVarDec(self):
        """ Compiles a static variable declaration, or a field declaration. """
        kind = self.tokenizer.currentToken()  # whatis kind of class variable
        self.tokenizer.advance()  # steps over 'kind'
        type = self.tokenizer.currentToken()  # whatis type of class variable
        self.tokenizer.advance()  # steps over 'type'

        while True:
            name = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over 'name'
            if kind == 'field':
                self.classST.add(name, type, kind)
            elif kind == 'static':
                self.classST.add(name, type, kind)
            else:
                assert False
            if self.tokenizer.currentToken() == ',':
                self.tokenizer.advance()  # steps over ',', if it exists
            else:
                break
        self.tokenizer.advance()  # steps over ";"

    def compileSubroutineDec(self):
        """ Compiles a complete method, function, or constructor. """
        self.subroutineST = ST()  # get new symbol-table for this subroutine

        if self.tokenizer.currentToken() == "method":
            self.subroutineST.add('this', self.className, 'argument')

        self.subroutineKind = self.tokenizer.currentToken()
        self.tokenizer.advance()  # steps over subroutineKind ('constructor', 'method', 'function')

        return_type = self.tokenizer.currentToken()
        self.tokenizer.advance()  # steps over return-type

        self.subroutineName = self.tokenizer.currentToken()
        self.tokenizer.advance()  # steps over subroutineName

        self.tokenizer.advance()  # steps over '('
        self.compileParameterList()
        self.tokenizer.advance()  # steps over ')'

        self.compileSubroutineBody()  # including '{', '}'

        self.subroutineST = None  # by now we are done with the subroutineST

    def compileParameterList(self):
        """ Compiles a possibly empty parameter list.
            Does not handle the enclosing ().
            Returns the number of parameters."""
        count = 0
        while self.tokenizer.currentToken() != ")":
            type = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over 'type'
            name = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over 'name'
            self.subroutineST.add(name, type, 'argument')
            count = count + 1
            if self.tokenizer.currentToken() == ',':
                self.tokenizer.advance()  # steps over ',', if it exists
        return count

    def compileSubroutineBody(self):
        """ Compiles a subroutine's body.
            Handles the enclosing {}. """
        self.tokenizer.advance()  # steps over '{'

        while self.tokenizer.currentToken() == "var":
            self.compileVarDec()

        self.vmWriter.writeFunction(self.className + '.' + self.subroutineName, self.subroutineST.n_locals())
        if self.subroutineKind == 'constructor':
            self.vmWriter.writePush('constant', self.classST.n_fields())
            self.vmWriter.writeCall('Memory.alloc', 1)
            self.vmWriter.writePop('pointer', 0)
        if self.subroutineKind == 'method':
            self.vmWriter.writePush('argument', 0)
            self.vmWriter.writePop('pointer', 0)

        self.compileStatements()

        self.tokenizer.advance()  # steps over '}'

    def compileVarDec(self):
        """ Compiles a var declaration. """
        self.tokenizer.advance()  # steps over 'var'
        type = self.tokenizer.currentToken()
        self.tokenizer.advance()  # steps over 'type'

        while self.tokenizer.currentToken() != ";":
            name = self.tokenizer.currentToken()
            self.tokenizer.advance()
            self.subroutineST.add(name, type, 'local')
            if self.tokenizer.currentToken() == ',':
                self.tokenizer.advance()  # steps over ',', if it exists

        self.tokenizer.advance()  # steps over ';'

    def compileStatements(self):
        """ Compiles a sequence of statements
            Does not handle the enclosing {}. """
        while True:
            token = self.tokenizer.currentToken()
            if token == "if":
                self.compileIf()
            elif token == "while":
                self.compileWhile()
            elif token == "let":
                self.compileLet()
            elif token == "do":
                self.compileDo()
            elif token == "return":
                self.compileReturn()
            else:
                break

    def compileIf(self):
        """ Compiles an if statement, possibly with a trailing else clause. """
        self.tokenizer.advance()  # steps over "if"
        self.tokenizer.advance()  # steps over "("
        self.compileExpression()
        self.vmWriter.writeArithmetic('~', unary=True)  # not
        l1 = 'ifLbl' + str(self.labelCount)
        self.incLabelCount()
        self.vmWriter.writeIf(l1)
        self.tokenizer.advance()  # steps over ")"

        self.tokenizer.advance()  # steps over "{"
        self.compileStatements()
        self.tokenizer.advance()  # steps over "}"

        if self.tokenizer.currentToken() == "else":  # handling "else" clause, if exists
            l2 = 'ifLbl' + str(self.labelCount)
            self.incLabelCount()
            self.vmWriter.writeGoto(l2)
            self.vmWriter.writeLabel(l1)

            self.tokenizer.advance()  # steps over "else"
            self.tokenizer.advance()  # steps over "{"
            self.compileStatements()
            self.tokenizer.advance()  # steps over "}"

            self.vmWriter.writeLabel(l2)
        else:
            self.vmWriter.writeLabel(l1)

    def compileWhile(self):
        """ Compiles a while statement. """
        l1 = "whileLbl" + str(self.labelCount)
        self.incLabelCount()
        l2 = "whileLbl" + str(self.labelCount)
        self.incLabelCount()

        self.vmWriter.writeLabel(l1)
        self.tokenizer.advance()  # steps over "while"
        self.tokenizer.advance()  # steps over "("
        self.compileExpression()
        self.tokenizer.advance()  # steps over ")"
        self.vmWriter.writeArithmetic('~', unary=True)  # not
        self.vmWriter.writeIf(l2)

        self.tokenizer.advance()  # steps over "{"
        self.compileStatements()
        self.vmWriter.writeGoto(l1)
        self.vmWriter.writeLabel(l2)
        self.tokenizer.advance()  # steps over "}"

    def compileLet(self):
        """ Compiles a let statement. """
        self.tokenizer.advance()  # steps over "let"
        varName = self.tokenizer.currentToken()
        if varName in self.subroutineST:
            name, type, kind, index = self.subroutineST.get(varName)
        elif varName in self.classST:
            name, type, kind, index = self.classST.get(varName)
        else:
            assert False, f'using unknown variable \"{varName}\"'
        self.tokenizer.advance()  # steps over varName

        if self.tokenizer.currentToken() == '[':  # varName[expression] = .....
            self.tokenizer.advance()  # steps over '['
            self.compileExpression()
            self.tokenizer.advance()  # steps over ']'
            self.vmWriter.writePush(kind, index)
            self.vmWriter.writeArithmetic('+')
            assert self.tokenizer.currentToken() == '='  # just a healthy check
            self.tokenizer.advance()  # steps over '='
            self.compileExpression()
            self.vmWriter.writePop('temp', 0)
            self.vmWriter.writePop('pointer', 1)
            self.vmWriter.writePush('temp', 0)
            self.vmWriter.writePop('that', 0)
        elif self.tokenizer.currentToken() == '=':
            self.tokenizer.advance()  # steps over '='

            self.compileExpression()

            self.vmWriter.writePop(kind, index)
        else:
            assert False
        self.tokenizer.advance()  # steps over ';'

    def compileDo(self):
        """ Compiles a do statement. """
        self.tokenizer.advance()  # steps over 'do'
        currentToken = self.tokenizer.currentToken()
        self.tokenizer.advance()  # steps over currentToken

        if self.tokenizer.currentToken() == '.':  # varName.methodName(....) or className.functionName(....)
            self.tokenizer.advance()  # steps over '.'
            subroutineName = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over subroutineName
            self.tokenizer.advance()  # steps over '('
            if currentToken in self.classST or currentToken in self.subroutineST:
                name, type, kind, index = self.subroutineST.get(currentToken) if currentToken in self.subroutineST \
                    else self.classST.get(currentToken)
                self.vmWriter.writePush(kind, index)
                self.vmWriter.writeCall(type+'.'+subroutineName, self.compileExpressionList()+1)
                # +1 for the implicit argument 'this'
            else:
                self.vmWriter.writeCall(currentToken+'.'+subroutineName, self.compileExpressionList())
            self.tokenizer.advance()  # steps over ')'
        elif self.tokenizer.currentToken() == '(':  # method call on the current object
            self.vmWriter.writePush('pointer', 0)
            self.tokenizer.advance()  # steps over '('
            self.vmWriter.writeCall(self.className+'.'+currentToken, self.compileExpressionList()+1)
            # +1 for the implicit argument 'this'
            self.tokenizer.advance()  # steps over ')'
        else:
            assert False
        assert self.tokenizer.currentToken() == ';'  # healthy check
        self.tokenizer.advance()  # steps over ';'
        self.vmWriter.writePop('temp', 0)

    def compileReturn(self):
        """ Compiles a return statement. """
        self.tokenizer.advance()  # steps over 'return'
        if self.tokenizer.currentToken() == ";":  # returns void
            self.tokenizer.advance()  # steps over ';'
            self.vmWriter.writePush('constant', 0)  # void methods returns 0
        else:
            self.compileExpression()
            self.tokenizer.advance()  # steps over ';'
        self.vmWriter.writeReturn()

    def compileExpression(self):
        """ Compiles an expression. """
        self.compileTerm()
        while self.tokenizer.currentToken() in op:
            operator = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over operator
            self.compileTerm()
            self.vmWriter.writeArithmetic(operator)

    def compileTerm(self):
        """ Compiles a term, if the current token is an identifier, the routine must distinguish
            between a variable, an array entry, or a subroutine call.
            A single look-ahead token, which may be one of '(', '[', or '.', suffices to distinguish
            between the possibilities.
            Any other token is not part of this term, and should not be advanced over. """

        if self.tokenizer.tokenType() == 'integerConstant':  # case no 1; integerConstant
            self.vmWriter.writePush('constant', self.tokenizer.currentToken())
            self.tokenizer.advance()  # steps over integerConstant
        elif self.tokenizer.tokenType() == 'stringConstant':  # case no 2; stringConstant
            string = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over stringConstant
            self.vmWriter.writePush('constant', len(string))
            self.vmWriter.writeCall('String.new', 1)
            for s in string:
                self.vmWriter.writePush('constant', ord(s))
                self.vmWriter.writeCall('String.appendChar', 2)
        elif self.tokenizer.currentToken() in keywordConstant:  # case no 3; keywordConstant
            constant = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over constant
            if constant == 'true':
                self.vmWriter.writePush('constant', 0)
                self.vmWriter.writeArithmetic('~', unary=True)  # not
                pass
            elif constant == 'false':
                self.vmWriter.writePush('constant', 0)
                pass
            elif constant == 'null':
                self.vmWriter.writePush('constant', 0)
                pass
            elif constant == 'this':
                self.vmWriter.writePush('pointer', 0)
                pass
            else:
                assert False, 'disaster'
        elif self.tokenizer.tokenType() == "identifier":  # case no 4, 5, 6;
            # varName
            # varName '['expression']'
            # subroutineCall:
            #     subroutineName '('expressionList')'
            #     (className|varName)'.'subroutineName'('expressionList')'
            currentToken = self.tokenizer.currentToken()
            if currentToken in self.subroutineST or currentToken in self.classST:

                name, type, kind, index = self.subroutineST.get(currentToken) \
                    if currentToken in self.subroutineST else self.classST.get(currentToken)

                if self.tokenizer.nextToken() == '[':  # varName'['expression']'
                    self.tokenizer.advance()  # steps over currentToken, which is a variable
                    self.tokenizer.advance()  # steps over '['
                    self.compileExpression()  # compute the offset (i.e. the result of evaluating '['expression']')
                    self.tokenizer.advance()  # steps over ']'
                    self.vmWriter.writePush(kind, index)  # push varName, the base-address
                    self.vmWriter.writeArithmetic('+')  # compute base-address + offset
                    self.vmWriter.writePop('pointer', 1)
                    self.vmWriter.writePush('that', 0)  # the result of varName[expression] in topmost of stack
                    pass

                elif self.tokenizer.nextToken() == '.':  # varName'.'subroutineName'('expressionList')'
                    self.vmWriter.writePush(kind, index)
                    self.tokenizer.advance()  # steps over currentToken
                    self.tokenizer.advance()  # steps over '.'
                    subroutineName = self.tokenizer.currentToken()
                    self.tokenizer.advance()  # steps over subroutineName
                    self.tokenizer.advance()  # steps over '('
                    self.vmWriter.writeCall(type+'.'+subroutineName, self.compileExpressionList() + 1)  # +1 is for
                    # the implicit argument
                    self.tokenizer.advance()  # steps over ')'
                    pass
                else:  # varName
                    self.vmWriter.writePush(kind, index)
                    self.tokenizer.advance()  # steps over varName
                    pass
            else:
                if self.tokenizer.nextToken() == '(':  # subroutineName '(' expressionList')'
                    # the subroutine in this case is a method
                    self.tokenizer.advance()  # steps over currentToken
                    self.tokenizer.advance()  # steps over '('
                    self.vmWriter.writePush('pointer', 0)
                    self.vmWriter.writeCall(self.className + '.' + currentToken, self.compileExpressionList() + 1)
                    # +1 is for the implicit argument
                    self.tokenizer.advance()  # steps over ')'
                elif self.tokenizer.nextToken() == '.':  # className.subroutineName'('expressionList')'
                    # the subroutine in this case is a function
                    self.tokenizer.advance()  # steps over currentToken
                    self.tokenizer.advance()  # steps over '.'
                    subroutineName = self.tokenizer.currentToken()
                    self.tokenizer.advance()  # steps over subroutineName
                    self.tokenizer.advance()  # steps over '('
                    self.vmWriter.writeCall(currentToken+'.'+subroutineName, self.compileExpressionList())
                    self.tokenizer.advance()  # steps over ')'
                else:  # disaster
                    assert False

        elif self.tokenizer.currentToken() == "(":  # case no 7; '('expression')'
            self.tokenizer.advance()  # steps over '('
            self.compileExpression()
            self.tokenizer.advance()  # steps over ')'
        elif self.tokenizer.currentToken() in unaryOp:  # case no 8; unaryOp term
            command = self.tokenizer.currentToken()
            self.tokenizer.advance()  # steps over unaryOp
            self.compileTerm()
            self.vmWriter.writeArithmetic(command, unary=True)
        else:
            #  disaster
            #  none of the above works
            assert False, f'huge disaster, WTF!@%@^!%$!^%$'

    def compileExpressionList(self):
        """ Compiles (a possibly empty) comma-separated list of expressions.
            Returns the number of expressions"""
        count = 0
        while self.tokenizer.currentToken() != ")":
            self.compileExpression()
            count = count + 1
            if self.tokenizer.currentToken() == ",":
                self.tokenizer.advance()  # steps over ',', if exists
        return count


def main():
    return 0


if __name__ == "__main__":
    exit(main())
