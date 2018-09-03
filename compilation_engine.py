from tokenizer import Tokenizer
from xml.etree import ElementTree as ET
import xml.dom.minidom as xml_minidom


class CompilationEngine:
    """Creates an AST of the input file. 
    """
    
    def __init__(self, input_file, output_file):
        with open(input_file, 'r') as f:
            self.tokenizer = Tokenizer(f.readlines())
        self.output_stream = None
        self.outfile = output_file

    def compile_class(self):
        main_class_node = ET.Element('class')
        ET.SubElement(main_class_node, 'keyword').text = 'class'
        self.tokenizer.advance()
        
        if self.tokenizer.token_type() == 'IDENTIFIER':
            ET.SubElement(main_class_node, 'identifier').text = \
                self.tokenizer.current_token
        else:
            raise SyntaxError('Class name expected. {} is not a \
                valid identifier.'.format(self.tokenizer.current_token))
        self.tokenizer.advance()

        if self.tokenizer.current_token is not '{':
            raise SyntaxError('{ expected after class name.')
        ET.SubElement(main_class_node, 'symbol').text = '{'
        self.tokenizer.advance()

        self.compile_class_var_dec(main_class_node)
        self.compile_subroutine_dec(main_class_node)

        if self.tokenizer.current_token is not '}':
            raise SyntaxError('} expected at end.')
        ET.SubElement(main_class_node, 'symbol').text = '}'
        
        return xml_minidom.parseString(ET.tostring(main_class_node))\
            .toprettyxml()

    def compile_class_var_dec(self, parent_node):
        pass
    
    def compile_subroutine_dec(self, parent_node):
        pass


if __name__ == '__main__':
    engine = CompilationEngine('test_class.jack', 'outfile.xml')
    print(engine.compile_class())
