
class VMWriter:
    """Generates the VM code.
    """

    def __init__(self, _stream):
        """Initialize a new VMWriter object.

        Args:
            _stream (list): The output stream to which to write.  
        """

        self._segment_mapping = {key: key.lower() for key in ['POINTER', 
                                 'LOCAL', 'STATIC', 'THIS', 'THAT', 'TEMP']}
        self._segment_mapping.update({
            'ARG': 'argument', 'CONST': 'constant', 'FIELD': 'this'
        })
        self.stream = _stream
    
    def write_push_pop(self, command, segment, index):
        """Writes a push VM command.
        
        Args:
            command (str): 'push' or 'pop'
            segment (str): One of the virtual memory segments on Hack computer
            index (int): The index on the virtual segment to push from/pop to
        """

        seg = self._segment_mapping.get(segment)
        if seg is None:
            raise TypeError("{} segment is not available.".format(segment))
        
        self.stream.append("{} {} {}".format(command, seg, index))
    
    def write_arithmetic(self, command):
        """Writes a VM supported arithmetic command.
        
        Args:
            command (str): One of the supported VM arithmetic commands.
        """
        
        if command not in ('ADD', 'SUB', 'NEG', 'EQ', 'GT', 
                           'LT', 'AND', 'OR', 'NOT'):
            raise TypeError('{} not supported.'.format(command))
        
        self.stream.append(command.lower())
    
    def write_label(self, label):
        self.stream.append('label {}'.format(label))
    
    def write_goto(self, label):
        self.stream.append('goto {}'.format(label))
    
    def write_ifgoto(self, label):
        self.stream.append('if-goto {}'.format(label))
    
    def write_call(self, name, n_args):
        self.stream.append('call {} {}'.format(name, n_args))
    
    def write_function(self, name, n_local):
        self.stream.append('function {} {}'.format(name, n_local))
    
    def write_return(self):
        self.stream.append('return')


if __name__ == '__main__':
    from engine import CompilationEngine
    from tokenizer import Tokenizer
    engine = CompilationEngine(Tokenizer([]), 'Main', 'out.xml', [])
    writer = VMWriter(engine.out_stream)
    writer.write_arithmetic('ADD')
    writer.write_call('abc', 3)
    writer.write_function('abc', 2)
    writer.write_goto('gotolabel')
    writer.write_ifgoto('ifgotolabel')
    writer.write_label('LABEL')
    writer.write_push_pop('push', 'ARG', 2)
    writer.write_push_pop('pop', 'LOCAL', 1)
    writer.write_return()
    print(engine.out_stream)
