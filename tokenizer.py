import re


class Tokenizer:
    """A tokenizer to tokenize a Jack source file.
    """

    def __init__(self, raw_code):
        """Turns input raw code to a list of tokens
        
        Args:
            raw_code (list): Input from file.
        """

        self.current_token_index = 0
        self.tokens = []
        clean_code = Tokenizer.clean_code(raw_code)
        for line in clean_code:
            self.tokens.extend(Tokenizer.handle_line(line))
        
        self.total_tokens = len(self.tokens)
    
    def advance(self):
        """Advance the token pointer by one. Throws error if no more tokens."""

        if self.has_more_tokens():
            self.current_token_index += 1
        else:
            raise IndexError('No more tokens.')
    
    def has_more_tokens(self):
        """Check if there are more tokens available."""
        return self.current_token_index < (self.total_tokens - 1)
    
    def token_type(self):
        """Returns the token type. 
        
        Returns:
            str: KEYWORD, SYMBOL, IDENTIFIER, INT_CONST, STRING_CONST
        """

        symbol_type = None
        token = self.current_token
        if token in ('class', 'constructor', 'function', 'method', 
                     'field', 'static', 'var', 'int', 'char', 'if',
                     'boolean', 'void', 'true', 'false', 'null',
                     'this', 'let', 'do', 'return', 'else', 'while'):
            symbol_type = 'KEYWORD'
        elif token in '{}()[].,;+-*/&|<>=':
            symbol_type = 'SYMBOL'
        elif token.isdigit():
            symbol_type = 'INT_CONST'
        elif token.isidentifier():
            symbol_type = 'IDENTIFIER'
        elif token.startswith('"'):
            symbol_type = 'STRING_CONST'
        else:
            raise SyntaxError('Invalid token : {}'.format(token))
        return symbol_type      

    @staticmethod
    def handle_line(line):
        """Converts a line of clean code to a list of tokens.
        Required so that I can tokenize string constants without 
        using re.Scanner. 
        May need to later add token type here instead of parser.         
        
        Args:
            line (string): Line of clean Jack code. 
        
        Returns:
            list: a list of valid Jack tokens. 
        """

        line = line.strip()
        ret = []
        if '"' in line:
            match = re.search(r"(\".*?\")", line)
            ret.extend(Tokenizer.handle_line(match.string[:match.start()]))
            ret.append(match.string[match.start():match.end() - 1])
            ret.extend(Tokenizer.handle_line(match.string[match.end():]))
        else:
            for candidate in line.split():
                ret.extend(Tokenizer.handle_token_candidate(candidate))
        return ret

    @staticmethod
    def handle_token_candidate(candidate):
        """Cleans and handles a possible token
        
        Args:
            candidate (string): A candidate for token (which 
            can consist of multiple tokens)
        
        Returns:
            list: a list of tokens
        """  

        if not candidate:
            return []
        candidate = candidate.split('.')
        if len(candidate) == 1:
            candidate = candidate[0]
            if candidate.endswith(','):
                return [candidate[:-1], ',']
            elif candidate.endswith(';'):
                return Tokenizer.handle_token_candidate(candidate[:-1]) + [';']
            elif candidate.endswith(')'):
                if candidate.startswith('('):
                    return ['(', candidate[1:-1], ')']
                else:
                    return [candidate[:-2], '(', ')']
            elif candidate.startswith('('):
                return ['(', candidate[1:]]
            elif candidate.endswith(']'):
                candidate = candidate.strip().split('[')
                return [candidate[0], '[', candidate[1][:-1], ']']
            return [candidate]
        else:
            ret = [candidate[0], '.']
            ret.extend(Tokenizer.handle_token_candidate(candidate[1]))
            return ret

    @staticmethod
    def clean_code(raw_code):
        """ Removes comments and newlines from the input raw code.
        
        Args:
            raw_code (list): A list (str) of unclean code from the file.
        
        Returns:
            list: A list (str) of clean code.
        """

        lines = [line.strip() for line in raw_code]
        lines = [line.split('//')[0].strip() for line in lines 
                 if Tokenizer.is_valid(line)]
        return lines
    
    @staticmethod
    def is_valid(line):
        """Is it a valid Jack line?
        
        Args:
            line (str): A line from Jack file. 
        
        Returns:
            bool: Is it a valid Jack line?
        """

        return line and (not line.startswith('//')) and (
            not line.startswith('/*'))

    @property
    def current_token(self):
        """Return the current token. 
        
        Returns:
            str: Current token
        """

        return self.tokens[self.current_token_index]


if __name__ == "__main__":
    with open('10/Square/Main.jack', 'r') as f:
        TEST_LINES = f.readlines()
    TOKENIZER = Tokenizer(TEST_LINES)
    print(TOKENIZER.tokens)
    