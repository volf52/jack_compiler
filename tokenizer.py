import re

class Tokenizer:
    def __init__(self, raw_code):
        """Turns input raw code to a list of tokens
        
        Arguments:
            raw_code {list} -- List of code lines including the comments and everything. 
        """
        self.current_token_index = 0
        self.tokens = []
        
        clean_code = Tokenizer.clean_code(raw_code)
        for line in clean_code:
            self.tokens.extend(Tokenizer.handle_line(line))
    
    def advance(self):
        self.current_token_index += 1

    @staticmethod
    def handle_line(line):
        line = line.strip()
        ret = []
        if '"' in line:
            match = re.search(r"(\".*?\")", line)
            ret.extend(Tokenizer.handle_line(match.string[:match.start()]))
            ret.append(match.string[match.start()+1:match.end()-1])
            ret.extend(Tokenizer.handle_line(match.string[match.end():]))
        else:
            for candidate in line.split():
                ret.extend(Tokenizer.handle_token_candidate(candidate))
        return ret

    @staticmethod
    def handle_token_candidate(candidate):
        """Cleans and handles a possible token
        
        Arguments:
            candidate {string} -- A candidate for token (which can consist of multiple tokens)
        
        Returns:
            list -- a list of tokens
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
        lines = [line.strip() for line in raw_code]
        lines = [line.split('//')[0].strip() for line in lines if Tokenizer.is_valid(line)]
        return lines
    
    @staticmethod
    def is_valid(line):
        return line and (not line.startswith('//')) and (not line.startswith('/*'))

    @property
    def current_token(self):
        return self.tokens[self.current_token_index]

if __name__ == "__main__":
    with open('10/Square/Main.jack', 'r') as f:
        test_lines = f.readlines()
    tokenizer = Tokenizer(test_lines)
    #tokenizer = Tokenizer(["let game = SquareGame.new();"])
    print(tokenizer.tokens)