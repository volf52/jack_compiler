

class SymbolTable(dict):
    """A hashtable to perform variable lookup.
    Subclass of dict with a few special methods.
    """

    def __init__(self, *args):
        """Creates a new SymbolTable.
        """

        dict.__init__(self, *args)
        self._field_scope = {}
        self._static_scope = {}
        self._subroutine_scope = {}
        self._count = {
            'STATIC': 0,
            'ARG': 0,
            'FIELD': 0,
            'VAR': 0
        }
    
    def __getitem__(self, key):
            if key in self._subroutine_scope:
                return self._subroutine_scope[key]
            elif key in self._field_scope:
                return self._field_scope[key]
            elif key in self._static_scope:
                return self._static_scope[key]
            else:
                raise KeyError("{} not in any scope.")
    
    def get(self, key, default=(None, None, -1)):
            try:
                ret = self[key]
            except KeyError:
                ret = default
            finally:
                return ret
        
    def define(self, name, _type, kind):
        """Add a new element.
        
        Args:
            name (str): The name of the variable
            _type (str): The type of the variable
            kind (str): STATIC, ARG, FIELD or VAR
        
        Raises:
            TypeError: The kind of given variable is invalid
        """

        try:
            i = self._count[kind]
        except KeyError:
            raise TypeError('{} is not a supported kind.'.format(kind))
        
        if kind in ('ARG', 'VAR'):
            self._subroutine_scope[name] = (_type, kind, i)
        elif kind == 'STATIC':
            self._static_scope[name] = (_type, kind, i)
        else:  # == 'FIELD
            self._field_scope[name] = (_type, kind, i)
        
        self._count[kind] += 1
        return i

    def reset(self):
        """Clears the _subroutine_scope.
        """

        self._subroutine_scope.clear()
        self._count['ARG'] = 0
        self._count['VAR'] = 0
    
    def var_count(self, kind):
        return self._count[kind]


if __name__ == '__main__':
    d = SymbolTable()
    d.define('this', 'Point', 'ARG')
    print(d['this'])
    d.reset()
    print(d.get('this'))
    print(d)
