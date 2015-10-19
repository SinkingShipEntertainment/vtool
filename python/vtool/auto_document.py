import ast

import util_file

class CreateHtml(object):
    
    def __init__(self, name, filepath):
        
        self.name = name
        self.filepath = filepath
    
        self.header_title_string = ''
        self.css_link = ''
        
        self.blocks = []
        
    
    def _create_lines(self):
        lines = []
        
        lines.append('<!DOCTYPE html>')
        lines.append('<html>')
        lines.append('    <head>')
        if self.header_title_string:
            lines.append('        <title> %s </title>' % self.header_title_string )
        if self.css_link:
            lines.append('        <link rel = "stylesheet" type = "text/css" href = "%s">' % self.css_link )
        lines.append('    </head>')
        lines.append('    <body>')
        
        for block in self.blocks:
            lines.append(block)
        
        lines.append('    </body>')
        lines.append('</html>')
        
        return lines
        
    def _create_file(self, lines):
        
        new_filepath = util_file.create_file(self.name, self.filepath)
        util_file.write_lines(new_filepath, lines)
        
    def _create_block(self, indent, prefix, text):
        indent_str = 8 * ' '
        block = '%s<%s> %s </%s>' % (indent_str, prefix, text, prefix)
        return block
        
    def set_header_title(self, string):
        self.header_title_string = string
    
    def set_css_link(self, css_link_string):
        self.css_link = css_link_string
    
    def add_header(self, text, header_number = 1):
        text = self._create_block(8, 'h%s' % header_number, text)
        self.blocks.append(text)
    
    def add_paragraph(self, text):
        text = self._create_block(8, 'p', text)
        self.blocks.append(text)
    
    def create(self):
        
        lines = self._create_lines()
        self._create_file(lines)
        

class CreatePythonModuleHtml(CreateHtml):
    
    def __init__(self, name, filepath):
        super(CreatePythonModuleHtml, self).__init__(name, filepath)
        
        self.python_filepath = ''
    
    def _get_arg_string(self, args):

        arg_strings = '( '
        
        if args:
            
            inc = 0
            
            for arg in args:
                
                if arg == 'self':
                    inc+=1
                    continue
                
                if type(arg) == tuple:
                    arg_value = ' %s = %s' % (arg[0], arg[1])
                if type(arg) != tuple:
                    arg_value = ' %s' % arg 
                 
                if inc < (len(args)-1):
                    arg_value = arg_value + ','
                
                arg_strings = arg_strings + arg_value
                
                inc+=1
            
        arg_strings = arg_strings + ' )'
        
        return arg_strings
    
    def _get_header(self, header_object):
        
        name = header_object.get_name()
        args = header_object.get_args()
        
        arg_string = self._get_arg_string(args)

        header = '%s %s' % (name, arg_string)
                
        return header
    
    def set_python_module(self, filepath):
        self.python_filepath = filepath
        
    def create(self):
        
        if util_file.is_file(self.python_filepath):
            parse = ParsePython(self.python_filepath)
            
            self.add_header('Classes', '1')
            
            for class_object in parse.get_classes():
                
                header = self._get_header(class_object)
                self.add_header(header, '2')
                self.add_paragraph(class_object.get_doc_string())
                
                for sub_class_object in class_object.get_functions():
                    header = self._get_header(sub_class_object)
                    self.add_header(header, '4')
                    self.add_paragraph(sub_class_object.get_doc_string())
                
            self.add_header('Functions', 1)
                
            for class_object in parse.get_functions():
                
                header = self._get_header(class_object)
                self.add_header(header, '4')
                self.add_paragraph(class_object.get_doc_string())
                
        super(CreatePythonModuleHtml, self).create()

class ParsePython(object):
    
    def __init__(self, python_file_name):
        
        self.filename = python_file_name
        
        self.classes = []
        self.functions = []
        
        self._parse()
        
    def _parse(self):
        
        self.functions = []
        self.classes = []
                
        open_file = open(self.filename, 'r')    
        lines = open_file.read()
        open_file.close()
        
        ast_tree = ast.parse(lines)
        
        for node in ast_tree.body:
            
            if isinstance(node, ast.FunctionDef):
                inst = ObjectFunctionData(node)
                self.functions.append(inst)
                
                
            if isinstance(node, ast.ClassDef):
                inst = ObjectClassData(node)
                self.classes.append(inst)
                        
    def get_classes(self):
        return self.classes
    
    def get_functions(self):
        return self.functions

class ObjectData(object):
    
    def __init__(self, object_inst):
        self.object_inst = object_inst
        self.functions = []
    
    def get_name(self):
        
        name = self.object_inst.name
        
        return name
    
    def get_doc_string(self):
        
        doc = ast.get_docstring(self.object_inst)
        return doc
    
    def get_functions(self):
        
        
        for node in self.object_inst.body:
            
            if isinstance(node, ast.FunctionDef):
                inst = ObjectFunctionData(node)
                name = inst.get_name()
                
                if name.startswith('_') and not name.startswith('__'):
                    continue
                
                self.functions.append(inst)
                
        return self.functions
    
class ObjectFunctionData(ObjectData):
    
    def get_args(self):
        
        args = get_sorted_args(self.object_inst)
        
        return args
    
class ObjectClassData(ObjectData):
    
    def get_args(self):
        
        bases = self.object_inst.bases
        
        found_bases = []
        
        for base in bases:
            if isinstance(base, ast.Name):
                found_bases.append( base.id )
        
        return found_bases
    
def get_args(object_inst):
    args = object_inst.args.args
    
    if not args:
        return
    
    found_args = []
    
    for arg in args:
        found_args.append(arg.id)

    return found_args

def get_arg_defaults(object_inst):
    
    args = object_inst.args.args
    
    if not args:
        return
    
    defaults = object_inst.args.defaults
    
    if not defaults:
        return
    
    found_defaults = []
    
    for default in defaults:
        
        print default        
        
        if isinstance(default, ast.Str):
            found_defaults.append("'%s'" % default.s)
        if isinstance(default, ast.Name):
            found_defaults.append(default.id)
        if isinstance(default, ast.Num):
            found_defaults.append(default.n)
        
            
    print 'default end'
        #found_defaults.append(default.id)
        
    return found_defaults
        
def get_sorted_args(object_inst):
    
    args = get_args(object_inst)
    
    if not args:
        return
    
    defaults = get_arg_defaults(object_inst)
    
    defaults_dict = {}
    
    if defaults:
        defaults_dict = dict( zip(reversed(args), reversed(defaults)) )
    
    ordered_args = []
    
    for arg in args:
        
        arg_value = arg
        
        if defaults_dict:    
            if defaults_dict.has_key(arg):
                arg_value = (arg, defaults_dict[arg])
            
        ordered_args.append(arg_value)
        
    return ordered_args
    
        