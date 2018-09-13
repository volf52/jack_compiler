from generator import VMWriter
from symbolTable import SymbolTable


class CompilationEngine:
    """Creates an AST of the input file. 
    """
    
    def __init__(self, input_stream, output_file):
        self.tokenizer = input_stream
        self.outfile = output_file
        self.class_name = None
        self.out_stream = []
        self.buffer = []
        self.if_count = 0
        self.while_count = 0
        self.generator = VMWriter(self.out_stream)
        self.symbol_table = SymbolTable()
        self.op_table = {
            '+': 'ADD', '-': 'SUB', '&': 'AND', '|': 'OR', 
            '<': 'LT', '>': 'GT', '=': 'EQ'
        }
        self.convert_kind = {
            'ARG': 'ARG',
            'STATIC': 'STATIC',
            'VAR': 'LOCAL',
            'FIELD': 'THIS'
        }

    def compile_class(self):
        """Compiles a Jack class to VM file.
        
        Raises:
            SyntaxError: If the current token is not expected, a SyntaxError \
             is raised.
        Returns:
            list: Output stream containing the commands 
        """
        
        tk = self.tokenizer
        tk.advance()  # "class"
        self.class_name = tk.curr_token
        tk.advance()
        tk.advance()  # "{"

        while tk.curr_token in ('static', 'field'):
            self.compile_class_var_dec()
        while tk.curr_token in ('constructor', 'function', 'method'):
            self.compile_subroutine()

        if tk.curr_token != '}':
            raise SyntaxError('} expected at end.')
        
        with open(self.outfile, 'w') as f:
                f.write('\n'.join(self.out_stream))
        
    def compile_class_var_dec(self):
        """Compiles the Jack class variable declaration(s).
        
        Raises:
            SyntaxError: When the programmer is idiot.
        """

        tk = self.tokenizer

        cat = tk.curr_token.upper() 
        tk.advance()  # "static" or "field"

        #  variable type
        _type = tk.curr_token
        tk.advance()

        # Check if variable name is a valid identifier
        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a valid Jack identifier'
                              .format(tk.curr_token))
        self.symbol_table.define(tk.curr_token, _type, cat)
        tk.advance()

        while tk.curr_token != ';':
            tk.advance()  # ","

            if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.curr_token))        
            self.symbol_table.define(tk.curr_token, _type, cat)
            tk.advance()
        
        tk.advance()  # ";"

    def compile_subroutine(self):
        """Compiles a Jack subroutine.
        
        Raises:
            SyntaxError: When unexpected input is given.
        """

        tk = self.tokenizer
        self.symbol_table.reset()
        subroutine_type = tk.curr_token
        if subroutine_type == 'method':
            self.symbol_table.define('this', self.class_name, 'ARG')
        tk.advance()
        tk.advance()  # ("void" | type)

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError("Subroutine name ({}) not a valid identifier"
                              .format(tk.curr_token))
        func_name = "{}.{}".format(self.class_name, tk.curr_token)
        tk.advance()

        tk.advance()  # "("
        self.compile_parameter_list()
        tk.advance()  # ")"
        tk.advance()  # "{"

        while 'var' == tk.curr_token:
            self.compile_var_dec()
        
        n_args = self.symbol_table.var_count('VAR')
        self.generator.write_function(func_name, n_args)

        if subroutine_type == 'constructor':
            n_fields = self.symbol_table.var_count('FIELD')
            self.generator.write_push_pop('push', 'CONST', n_fields)
            self.generator.write_call('Memory.alloc', 1)
            self.generator.write_push_pop('pop', 'POINTER', 0)
        elif subroutine_type == 'method':
            self.generator.write_push_pop('push', 'ARG', 0)
            self.generator.write_push_pop('pop', 'POINTER', 0)
        
        self.compile_statements()
        tk.advance()  # "}"

    def compile_parameter_list(self):
        """Compiles parameter list for a Jack subroutine.
        
        Raises:
            SyntaxError: When unexpected input is given.
        """

        tk = self.tokenizer
        cat = 'ARG'

        if tk.curr_token == ')':
            return
        
        _type = tk.curr_token
        tk.advance()

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a valid Jack identifier'
                              .format(tk.curr_token))
        self.symbol_table.define(tk.curr_token, _type, cat)     
        tk.advance()

        while tk.curr_token != ')':
            tk.advance()  # ","

            _type = tk.curr_token
            tk.advance()

            if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.curr_token))
            self.symbol_table.define(tk.curr_token, _type, cat)
            tk.advance()
    
    def compile_var_dec(self):
        """Compiles Jack variable declaration(s).

        Raises:
            SyntaxError: When unexpected input is provided.
        """

        tk = self.tokenizer

        tk.advance()
        cat = 'VAR'

        _type = tk.curr_token
        tk.advance()

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a valid Jack identifer.'
                              .format(tk.curr_token))
        self.symbol_table.define(tk.curr_token, _type, cat)
        tk.advance()

        while tk.curr_token != ';':
            tk.advance()  # ","

            if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.curr_token))
            self.symbol_table.define(tk.curr_token, _type, cat)
            tk.advance()
        
        tk.advance()  # ";"
    
    def compile_statements(self):
        """Compiles a Jack if/while/do/let/return statement.
        """

        tk = self.tokenizer
        func_to_call = {
            'if': self.compile_if_statement,
            'let': self.compile_let_statement,
            'do': self.compile_do_statement,
            'while': self.compile_while_statement,
            'return': self.compile_return_statement
        }

        while tk.curr_token in ('if', 'while', 'let', 'do', 'return'):
            f = func_to_call.get(tk.curr_token)
            f()
    
    def compile_let_statement(self):
        """Compiles a Jack "let" statement.
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer

        tk.advance()  # "let" 

        if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.curr_token))
        _type, cat, i = self.symbol_table.get(tk.curr_token)
        cat = self.convert_kind[cat]
        tk.advance()

        if tk.curr_token == '[':  # array assignment
            tk.advance()  # [
            self.compile_expression()
            tk.advance()  # ]

            self.generator.write_push_pop('push', cat, i)
            self.generator.write_arithmetic('ADD')
            self.generator.write_push_pop('pop', 'TEMP', 0)

            tk.advance()  # =
            self.compile_expression()

            self.generator.write_push_pop('push', 'TEMP', 0)
            self.generator.write_push_pop('pop', 'POINTER', 1)
            self.generator.write_push_pop('pop', 'THAT', 0)
        else:
            tk.advance()  # =
            self.compile_expression()
            self.generator.write_push_pop('pop', cat, i)
        
        tk.advance()  # ";"

    def compile_if_statement(self):
        """Compiles a Jack "if" statement.
        """

        tk = self.tokenizer

        tk.advance()  # "if"
        tk.advance()  # "("
        self.compile_expression()
        tk.advance()  # ")"

        l1 = "IF_TRUE{}".format(self.if_count)
        l2 = "IF_FALSE{}".format(self.if_count)
        l3 = "IF_END{}".format(self.if_count)
        self.generator.write_ifgoto(l1)
        self.generator.write_goto(l2)
        self.generator.write_label(l1)
        self.if_count += 1

        tk.advance()  # "{"
        self.compile_statements()
        self.generator.write_goto(l3)
        tk.advance()  # "}"
        self.generator.write_label(l2)

        if tk.curr_token == 'else':
            tk.advance()  # "else"
            tk.advance()  # "{"
            self.compile_statements()
            tk.advance()  # "}"
        
        self.generator.write_label(l3)
    
    def compile_while_statement(self):
        """Compiles a Jack "while" statement.
        """

        tk = self.tokenizer

        tk.advance()  # "while"
        l1 = "WHILE_EXP{}".format(self.while_count)
        l2 = "WHILE_END{}".format(self.while_count)
        self.while_count += 1

        self.generator.write_label(l1)

        tk.advance()  # "("
        self.compile_expression()
        self.generator.write_arithmetic("NOT")
        tk.advance()  # ")"
        tk.advance()  # "{"

        self.generator.write_ifgoto(l2)
        self.compile_statements()
        self.generator.write_goto(l1)
        self.generator.write_label(l2)

        tk.advance()  # "}"
    
    def compile_do_statement(self):
        """Compiles a Jack "do" statement.
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer

        tk.advance()  # "do"

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a proper identifier.'
                              .format(tk.curr_token))
        var_name = tk.curr_token
        tk.advance()
        
        self.compile_subroutine_call(var_name)
        self.generator.write_push_pop('pop', 'TEMP', 0)  # void method
        tk.advance()  # ";"
    
    def compile_return_statement(self):
        """Compiles a Jack "return" statement.
        """

        tk = self.tokenizer

        tk.advance()  # "return"

        if tk.curr_token != ';':
            self.compile_expression()
        else:
            # if no val to return, push 0 to stack
            self.generator.write_push_pop('push', 'CONST', 0) 
        
        self.generator.write_return()
        tk.advance()  # ";"
    
    def compile_expression_list(self):
        """Compiles a Jack expression list.

        Returns:
            n_args (int): Number of arguments for subroutine call
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer
        n_args = 0

        if tk.curr_token == ')':
            return n_args
        
        self.compile_expression()
        n_args += 1

        while tk.curr_token != ')':
            tk.advance()  # ","
            self.compile_expression()
            n_args += 1
        
        return n_args
 
    def compile_expression(self):
        """Compiles a Jack expression.
        """

        tk = self.tokenizer
        self.compile_term()

        while tk.curr_token in (
            '+', '-', '*', '/', '&', '|', '<', '>', '='
        ):
            op = tk.curr_token
            tk.advance()

            self.compile_term()
            if op in self.op_table:
                self.generator.write_arithmetic(self.op_table.get(op))
            elif op == '*':
                self.generator.write_call('Math.multiply', 2)
            elif op == '/':
                self.generator.write_call('Math.divide', 2)
            else:
                raise ValueError("{} not supported op.".format(op))

    def compile_term(self):
        """Compiles a Jack term.
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer

        if tk.token_type() == 'STRING_CONST':
            self.compile_string()
        elif tk.token_type() == 'INT_CONST':
            self.generator.write_push_pop('push', 'CONST', int(tk.curr_token))
            tk.advance()
        elif tk.curr_token in ('true', 'false', 'null'):
            self.generator.write_push_pop('push', 'CONST', 0)
            if tk.curr_token == 'true':
                self.generator.write_arithmetic("NOT")
            tk.advance()
        elif tk.curr_token == 'this':
            # "this" is the 0th argument
            self.generator.write_push_pop('push', 'POINTER', 0)  
            tk.advance()
        elif tk.curr_token in ('-', '~'):
            op = tk.curr_token
            tk.advance()
            self.compile_term()
            if op == '-':
                self.generator.write_arithmetic('NEG')
            else:
                self.generator.write_arithmetic('NOT')
        elif tk.curr_token == '(':
            tk.advance()  # "("
            self.compile_expression()
            tk.advance()  # ")"
        else:
            if tk.token_type() != 'IDENTIFIER':
                    raise SyntaxError('{} is not a valid identifier.'
                                      .format(tk.curr_token))
            var_name = tk.curr_token
            tk.advance()        
            if tk.curr_token == '[':
                tk.advance()  # "["
                self.compile_expression()
                tk.advance()  # "]"

                _type, cat, i = self.symbol_table.get(var_name)
                cat = self.convert_kind[cat]
                self.generator.write_push_pop('push', cat, i)
                self.generator.write_arithmetic('ADD')
                self.generator.write_push_pop('pop', 'POINTER', 1)
                self.generator.write_push_pop('push', 'THAT', 0)
            elif tk.curr_token in ('.', '('):
                self.compile_subroutine_call(var_name)
            else:
                _type, cat, i = self.symbol_table.get(var_name)
                cat = self.convert_kind[cat]
                self.generator.write_push_pop('push', cat, i)
              
    def compile_subroutine_call(self, var_name):
        tk = self.tokenizer
        func_name = var_name
        n_args = 0

        if tk.curr_token == '.':
            tk.advance()  # "."
            sub_name = tk.curr_token  # subroutine name
            tk.advance()

            _type, cat, i = self.symbol_table.get(var_name)
            if _type != None:  # it's an instance
                cat = self.convert_kind[cat]
                self.generator.write_push_pop('push', cat, i)
                func_name = "{}.{}".format(_type, sub_name)
                n_args += 1
            else:  # it's a class
                func_name = "{}.{}".format(var_name, sub_name)
            
        elif tk.curr_token == '(':
            sub_name = var_name
            func_name = "{}.{}".format(self.class_name, sub_name)
            n_args += 1
            self.generator.write_push_pop('push', 'POINTER', 0)
        
        tk.advance()  # "("
        n_args += self.compile_expression_list()
        tk.advance()  # ")"

        self.generator.write_call(func_name, n_args)
    
    def compile_string(self):
        tk = self.tokenizer
        string = tk.curr_token[1:]

        self.generator.write_push_pop('push', 'CONST', len(string))
        self.generator.write_call('String.new', 1)

        for char in string:
            self.generator.write_push_pop('push', 'CONST', ord(char))
            self.generator.write_call('String.appendChar', 2)
        
        tk.advance()
        
        
if __name__ == '__main__':
    engine = CompilationEngine('10/Square/SquareGame.jack', 
                               '10/Square/SquareGame_local.xml', 
                               ['Main', 'Square', 'SquareGame'])
    if engine.tokenizer.curr_token == 'class':
        xml_output = engine.compile_class()
        with open(engine.outfile, 'w') as f:
            f.write(xml_output)
    else:
        raise SyntaxError('The {} file should begin with class declaration.'
                          .format(engine.tokenizer.curr_token))
