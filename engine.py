import xml.dom.minidom as xml_minidom
from xml.etree import ElementTree as ET
from generator import VMWriter
from symbolTable import SymbolTable


class CompilationEngine:
    """Creates an AST of the input file. 
    """
    
    def __init__(self, input_stream, name, output_file, classes_in_dir):
        self.tokenizer = input_stream
        self.outfile = output_file
        self.class_name = name
        self.out_stream = []
        self.generator = VMWriter(self.out_stream)
        self.class_table = SymbolTable()
        self.subroutine_table = SymbolTable()
        self.classes_in_dir = classes_in_dir + [
            'Array', 'String', 'Screen', 'Math', 'Keyboard', 
            'Memory', 'Screen', 'Sys'
        ]

    def compile_class(self):
        """Compiles a Jack class to XML doc.
        
        Raises:
            SyntaxError: If the current token is not expected, a SyntaxError \
             is raised.
        Returns:
            str: An XML document
        """
        
        tk = self.tokenizer
        current_node = ET.Element('class')
        ET.SubElement(current_node, 'keyword').text = 'class'
        tk.advance()
        
        if tk.current_token != self.class_name:
            raise SyntaxError('Class name expected. {} is not \
                same as file name.'.format(tk.current_token))
        ET.SubElement(current_node, 'identifier', 
                      cat='class').text = tk.current_token
        tk.advance()

        if tk.current_token != '{':
            raise SyntaxError('{ expected after class name.')
        ET.SubElement(current_node, 'symbol').text = '{'
        tk.advance()

        while tk.current_token in ('static', 'field'):
            self.compile_class_var_dec(current_node)
        while tk.current_token in ('constructor', 'function', 'method'):
            self.compile_subroutine_dec(current_node)

        if tk.current_token != '}':
            raise SyntaxError('} expected at end.')
        ET.SubElement(current_node, 'symbol').text = '}'
        
        code = xml_minidom.parseString(ET.tostring(current_node))\
            .documentElement.toprettyxml()
        
        with open(self.outfile, 'w') as f:
                f.write(code)

    def compile_class_var_dec(self, parent_node):
        """Compiles the Jack class variable declaration(s).
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: When the programmer is idiot.
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'classVarDec')

        if tk.current_token not in ('static', 'field'):
            raise SyntaxError("Class variable must be static/field.")
        ET.SubElement(current_node, 'keyword').text = tk.current_token
        cat = tk.current_token.upper()
        tk.advance()

        # Check variable type
        if tk.current_token not in (
                'int', 'boolean', 'char', *self.classes_in_dir
        ):
            raise SyntaxError('{} is not a valid variable type.'
                              .format(tk.current_token))
        _type = tk.current_token
        ET.SubElement(current_node, tk.token_type().lower()).text \
            = tk.current_token
        tk.advance()

        # Check if variable name is a valid identifier
        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a valid Jack identifier'
                              .format(tk.current_token))
        i = self.class_table.define(tk.current_token, _type, cat)
        ET.SubElement(current_node, 'identifier', 
                      cat=cat, type=_type, i=str(i)).text = tk.current_token
        tk.advance()

        while tk.current_token != ';':
            if tk.current_token != ',':
                raise SyntaxError('Variable names must be separated by comma.')
            ET.SubElement(current_node, 'symbol').text = tk.current_token
            tk.advance()

            if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.current_token))        
            i = self.class_table.define(tk.current_token, _type, cat)
            ET.SubElement(current_node, 'identifier',
                          cat=cat, type=_type, i=str(i)
                          ).text = tk.current_token
            tk.advance()
        
        ET.SubElement(current_node, 'symbol').text = ';'
        tk.advance()

    def compile_subroutine_dec(self, parent_node):
        """Compiles a Jack subroutine declaration.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: When unexpected input is given.
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'subroutineDec')

        if tk.current_token not in ('constructor', 'function', 'method'):
            raise SyntaxError('Subroutine dec not valid.')
        ET.SubElement(current_node, 'keyword').text = tk.current_token
        if tk.current_token == 'method':
            self.subroutine_table.define('this', self.class_name, 'ARG')
        tk.advance()

        if tk.current_token not in (
            'int', 'char', 'boolean', 'void', *self.classes_in_dir
        ):
            raise SyntaxError('{} is not a valid variable type.'
                              .format(tk.current_token))
        ET.SubElement(current_node, tk.token_type().lower()).text \
            = tk.current_token
        tk.advance()

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError("Subroutine name ({}) not a valid identifier"
                              .format(tk.current_token))
        ET.SubElement(current_node, 'identifier').text = tk.current_token
        tk.advance()

        if tk.current_token != '(':
            raise SyntaxError('"(" expected after subroutine name.')
        ET.SubElement(current_node, 'symbol').text = '('
        tk.advance()

        self.compile_parameter_list(current_node)

        if tk.current_token != ')':
            raise SyntaxError('")" expected after parameter list.')
        ET.SubElement(current_node, 'symbol').text = ')'
        tk.advance()

        self.compile_subroutine_body(current_node)

    def compile_parameter_list(self, parent_node):
        """Compiles parameter list for a Jack subroutine.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: When unexpected input is given.
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'parameterList')
        cat = 'ARG'

        if tk.current_token == ')':
            current_node.text = '\n'
            return
        
        if tk.current_token not in (
                'int', 'boolean', 'char', *self.classes_in_dir
        ):
            raise SyntaxError('{} is not a valid variable type.'
                              .format(tk.current_token))
        _type = tk.current_token
        ET.SubElement(current_node, tk.token_type().lower()).text \
            = tk.current_token
        tk.advance()

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a valid Jack identifier'
                              .format(tk.current_token))
        i = self.subroutine_table.define(tk.current_token, _type, cat)     
        ET.SubElement(current_node, 'identifier',
                      cat=cat, type=_type, i=str(i)).text = tk.current_token
        tk.advance()

        while tk.current_token != ')':
            if tk.current_token != ',':
                raise SyntaxError('Variable names must be separated by comma.')
            ET.SubElement(current_node, 'symbol').text = tk.current_token
            tk.advance()

            if tk.current_token not in (
                    'int', 'boolean', 'char', *self.classes_in_dir
            ):
                raise SyntaxError('{} is not a valid variable type.'
                                  .format(tk.current_token))
            ET.SubElement(current_node, tk.token_type().lower()).text \
                = tk.current_token
            _type = tk.current_token
            tk.advance()

            if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.current_token))
            i = self.subroutine_table.define(tk.current_token, _type, cat)
            ET.SubElement(current_node, 'identifier',
                          cat=cat, type=_type, i=str(i)
                          ).text = tk.current_token
            tk.advance()

    def compile_subroutine_body(self, parent_node):
        """Compiles a Jack subroutine's body.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: When unexpected input is given.
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'subroutineBody')

        if tk.current_token != '{':
            raise SyntaxError('{ expected.')
        ET.SubElement(current_node, 'symbol').text = '{'
        tk.advance()

        while tk.current_token == 'var':
            self.compile_var_dec(current_node)
        
        self.compile_statements(current_node)

        if tk.current_token != '}':
            raise SyntaxError('{} expected.'.format('}'))
        ET.SubElement(current_node, 'symbol').text = '}'
        tk.advance()
        self.subroutine_table.reset()
    
    def compile_var_dec(self, parent_node):
        """Compiles Jack variable declaration(s).
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: When unexpected input is provided.
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'varDec')

        ET.SubElement(current_node, 'keyword').text = 'var'
        tk.advance()
        cat = 'LOCAL'

        if tk.current_token not in (
                'int', 'boolean', 'char', *self.classes_in_dir
        ):
            raise SyntaxError('{} is not a valid variable type.'
                              .format(tk.current_token))
        ET.SubElement(current_node, tk.token_type().lower()).text \
            = tk.current_token
        _type = tk.current_token
        tk.advance()

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a valid Jack identifer.'
                              .format(tk.current_token))
        i = self.subroutine_table.define(tk.current_token, _type, cat)
        ET.SubElement(current_node, 'identifier',
                      cat=cat, type=_type, i=str(i)).text = tk.current_token
        tk.advance()

        while tk.current_token != ';':
            if tk.current_token != ',':
                raise SyntaxError('Variable names must be separated by comma.')
            ET.SubElement(current_node, 'symbol').text = tk.current_token
            tk.advance()

            if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.current_token))
            i = self.subroutine_table.define(tk.current_token, _type, cat)
            ET.SubElement(current_node, 'identifier',
                          cat=cat, type=_type, i=str(i)
                          ).text = tk.current_token
            tk.advance()
        
        ET.SubElement(current_node, 'symbol').text = ';'
        tk.advance()      
    
    def compile_statements(self, parent_node):
        """Compiles a Jack if/while/do/let/return statement.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'statements')
        func_to_call = {
            'if': self.compile_if_statement,
            'let': self.compile_let_statement,
            'do': self.compile_do_statement,
            'while': self.compile_while_statement,
            'return': self.compile_return_statement
        }

        while tk.current_token in ('if', 'while', 'let', 'do', 'return'):
            f = func_to_call.get(tk.current_token)
            f(current_node)
    
    def compile_let_statement(self, parent_node):
        """Compiles a Jack "let" statement.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'letStatement')

        ET.SubElement(current_node, 'keyword').text = 'let'
        tk.advance()

        if tk.token_type() != 'IDENTIFIER':
                raise SyntaxError('{} is not a valid Jack identifer.'
                                  .format(tk.current_token))
        if tk.current_token in self.subroutine_table:
            _type, cat, i = self.subroutine_table.get(tk.current_token)
        elif tk.current_token in self.class_table:
            _type, cat, i = self.class_table.get(tk.current_token)
        else:
            raise ValueError("{} not declared yet.".format(tk.current_token))
        ET.SubElement(current_node, 'identifier',
                      cat=cat, type=_type, i=str(i)).text = tk.current_token
        tk.advance()

        if tk.current_token == '[':
            ET.SubElement(current_node, 'symbol').text = '['
            tk.advance()

            self.compile_expression(current_node)

            ET.SubElement(current_node, 'symbol').text = ']'
            tk.advance()
        
        ET.SubElement(current_node, 'symbol').text = '='
        tk.advance()

        self.compile_expression(current_node)

        ET.SubElement(current_node, 'symbol').text = ';'
        tk.advance()

    def compile_if_statement(self, parent_node):
        """Compiles a Jack "if" statement.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'ifStatement')

        ET.SubElement(current_node, 'keyword').text = 'if'
        tk.advance()

        ET.SubElement(current_node, 'symbol').text = '('
        tk.advance()

        self.compile_expression(current_node)

        ET.SubElement(current_node, 'symbol').text = ')'
        tk.advance()
        ET.SubElement(current_node, 'symbol').text = '{'
        tk.advance()

        self.compile_statements(current_node)

        ET.SubElement(current_node, 'symbol').text = '}'
        tk.advance()

        if tk.current_token == 'else':
            ET.SubElement(current_node, 'keyword').text = 'else'
            tk.advance()
            ET.SubElement(current_node, 'symbol').text = '{'
            tk.advance()

            self.compile_statements(current_node)

            ET.SubElement(current_node, 'symbol').text = '}'
            tk.advance()
    
    def compile_while_statement(self, parent_node):
        """Compiles a Jack "while" statement.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'whileStatement')

        ET.SubElement(current_node, 'keyword').text = 'while'
        tk.advance()

        if tk.current_token != '(':
            raise SyntaxError('"(" exprected after while.')
        ET.SubElement(current_node, 'symbol').text = '('
        tk.advance()

        self.compile_expression(current_node)

        if tk.current_token != ')':
            raise SyntaxError('")" exprected after while.')
        ET.SubElement(current_node, 'symbol').text = ')'
        tk.advance()

        if tk.current_token != '{':
            raise SyntaxError('"{" exprected after while.')
        ET.SubElement(current_node, 'symbol').text = '{'
        tk.advance()

        self.compile_statements(current_node)

        if tk.current_token != '}':
            raise SyntaxError('"}" exprected after while.')
        ET.SubElement(current_node, 'symbol').text = '}'
        tk.advance()
    
    def compile_do_statement(self, parent_node):
        """Compiles a Jack "do" statement. 
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'doStatement')

        ET.SubElement(current_node, 'keyword').text = 'do'
        tk.advance()

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a proper identifier.'
                              .format(tk.current_token))
        if tk.next_token == '.':
            if tk.current_token in self.classes_in_dir:
                _type, cat, i = tk.current_token, 'CLASS', '-1'
            elif tk.current_token in self.subroutine_table:
                _type, cat, i = self.subroutine_table.get(tk.current_token)
            elif tk.current_token in self.class_table:
                _type, cat, i = self.class_table.get(tk.current_token)
            else:
                raise ValueError('{} not declared.'.format(tk.current_token))
            ET.SubElement(current_node, 'identifier',
                          cat=cat, type=_type, i=str(i)
                          ).text = tk.current_token
            tk.advance()
            ET.SubElement(current_node, 'symbol').text = '.'
            tk.advance()

        if tk.token_type() != 'IDENTIFIER':
            raise SyntaxError('{} is not a proper identifier.'
                              .format(tk.current_token))
        ET.SubElement(current_node, 'identifier').text = tk.current_token
        tk.advance()

        if tk.current_token != '(':
            raise SyntaxError('"(" expected.')
        ET.SubElement(current_node, 'symbol').text = '('
        tk.advance()

        self.compile_expression_list(current_node)

        if tk.current_token != ')':
            raise SyntaxError('")" expected after subroutine name')
        ET.SubElement(current_node, 'symbol').text = ')'
        tk.advance()

        ET.SubElement(current_node, 'symbol').text = ';'
        tk.advance()
    
    def compile_return_statement(self, parent_node):
        """Compiles a Jack "return" statement.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'returnStatement')

        ET.SubElement(current_node, 'keyword').text = 'return'
        tk.advance()

        if tk.current_token != ';':
            self.compile_expression(current_node)
        
        ET.SubElement(current_node, 'symbol').text = ';'
        tk.advance()
    
    def compile_expression_list(self, parent_node):
        """Compiles a Jack expression list.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer

        if tk.current_token == ')':
            ET.SubElement(parent_node, 'expressionList').text = '\n'
            return
        
        current_node = ET.SubElement(parent_node, 'expressionList')
        self.compile_expression(current_node)

        while tk.current_token != ')':
            if tk.current_token != ',':
                raise SyntaxError('Expressions must be separated by comma.')
            ET.SubElement(current_node, 'symbol').text = ','
            tk.advance()

            self.compile_expression(current_node)
 
    def compile_expression(self, parent_node):
        """Compiles a Jack expression.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'expression')

        self.compile_term(current_node)

        while tk.current_token in (
            '+', '-', '*', '/', '&', '|', '<', '>', '='
        ):
            ET.SubElement(current_node, 'symbol').text = tk.current_token
            tk.advance()

            self.compile_term(current_node)

    def compile_term(self, parent_node):
        """Compiles a Jack term.
        
        Args:
            parent_node (xml.etree.ElementTree.Element): parent node in tree
        
        Raises:
            SyntaxError: Unexpected input
        """

        tk = self.tokenizer
        current_node = ET.SubElement(parent_node, 'term')

        if tk.token_type() == 'STRING_CONST':
            ET.SubElement(current_node, 'stringConstant').text \
                = tk.current_token[1:]
            tk.advance()
        elif tk.token_type() == 'INT_CONST':
            ET.SubElement(current_node, 'integerConstant').text \
                = tk.current_token
            tk.advance()
        elif tk.current_token in ('true', 'false', 'null', 'this'):
            ET.SubElement(current_node, 'keyword').text = tk.current_token
            tk.advance()
        elif tk.current_token in ('-', '~'):
            ET.SubElement(current_node, 'symbol').text = tk.current_token
            tk.advance()
            self.compile_term(current_node)
        elif tk.current_token == '(':
            ET.SubElement(current_node, 'symbol').text = '('
            tk.advance()
            self.compile_expression(current_node)
            ET.SubElement(current_node, 'symbol').text = ')'
            tk.advance()
        else:
            if tk.token_type() != 'IDENTIFIER':
                    raise SyntaxError('{} is not a valid identifier.'
                                      .format(tk.current_token))
            
            if tk.next_token == '(':    
                ET.SubElement(current_node, 'identifier').text \
                    = tk.current_token
                tk.advance()
                ET.SubElement(current_node, 'symbol').text = '('
                tk.advance()
                self.compile_expression_list(current_node)
                ET.SubElement(current_node, 'symbol').text = ')'
                tk.advance()
            
            else:   
                if tk.current_token in self.classes_in_dir:
                    _type, cat, i = tk.current_token, 'CLASS', '-1'
                elif tk.current_token in self.subroutine_table:
                    _type, cat, i = self.subroutine_table.get(tk.current_token)
                elif tk.current_token in self.class_table:
                    _type, cat, i = self.class_table.get(tk.current_token)
                else:
                    raise ValueError('{} not defined'.format(tk.current_token))
                ET.SubElement(current_node, 'identifier',
                              cat=cat, type=_type, i=str(i)
                              ).text = tk.current_token
                tk.advance()

                if tk.current_token == '[':
                    ET.SubElement(current_node, 'symbol').text = '['
                    tk.advance()
                    self.compile_expression(current_node)
                    ET.SubElement(current_node, 'symbol').text = ']'
                    tk.advance()
                elif tk.current_token == '.':
                    ET.SubElement(current_node, 'symbol').text = '.'
                    tk.advance()
                    if tk.token_type() != 'IDENTIFIER':
                        raise SyntaxError('{} is not a valid identifier.'
                                          .format(tk.current_token))
                    ET.SubElement(current_node, 'identifier').text \
                        = tk.current_token
                    tk.advance()
                    ET.SubElement(current_node, 'symbol').text = '('
                    tk.advance()
                    self.compile_expression_list(current_node)
                    ET.SubElement(current_node, 'symbol').text = ')'
                    tk.advance()


if __name__ == '__main__':
    engine = CompilationEngine('10/Square/SquareGame.jack', 
                               '10/Square/SquareGame_local.xml', 
                               ['Main', 'Square', 'SquareGame'])
    if engine.tokenizer.current_token == 'class':
        xml_output = engine.compile_class()
        with open(engine.outfile, 'w') as f:
            f.write(xml_output)
    else:
        raise SyntaxError('The {} file should begin with class declaration.'
                          .format(engine.tokenizer.current_token))
