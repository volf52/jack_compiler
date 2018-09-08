

class SymbolTable(dict):
    """A hashtable to perform variable lookup.
    Subclass of dict with a few special methods.
    """

    def __init__(self, *args):
        """Creates a new SymbolTable.
        """

        dict.__init__(self, *args)
        self._index = [0, 0]
        
    def define(self, name, _type, kind):
        """Add a new element.
        
        Args:
            name (str): The name of the variable
            _type (str): The type of the variable
            kind (str): STATIC, ARG, FIELD or VAR
        
        Raises:
            TypeError: The kind of given variable is invalid
        """

        if kind in ('STATIC', 'ARG'):
            i = 0
        elif kind in ('FIELD', 'LOCAL'):
            i = 1
        else:
            raise TypeError('{} is not a supported kind.'.format(kind))
        
        self[name] = (_type, kind, self._index[i])
        self._index[i] += 1
        return self._index[i] - 1

    def reset(self):
        """Clears the table.
        """

        self.clear()
        self._index = [0, 0]


if __name__ == '__main__':
    d = SymbolTable()
    d.define('this', 'Point', 'ARG')
    print(d['this'])
    d.reset()
    print(d)
