import sys
import traceback

from vtool import util
from vtool import util_file
from vtool import data
#from setup import SCRIPTS

if util.is_in_maya():
    import maya.cmds as cmds

def find_processes(directory = None):
    
    if not directory:
        directory = util_file.get_cwd()
    
    files = util_file.get_folders(directory)
    
    found = []
    
    for file_name in files:
        
        full_path = util_file.join_path(directory, file_name)
        
        if not util_file.is_dir(full_path):
            continue
        
        process = Process()
        process.set_directory(full_path)
        
        if process.is_process():
            found.append(file_name)
            
    found.sort()
               
    return found

def get_unused_process_name(directory = None):
    
    if not directory:
        directory = util_file.get_cwd()
    
    processes = find_processes(directory)
    
    
    name = Process.description
    new_name = name
    
    not_name = True
    
    inc = 1
    
    while not_name:
        if new_name in processes:
            new_name = (name + str(inc))
            inc += 1
            not_name = True
        
        if not new_name in processes:
            not_name = False
            
        if inc > 1000:
            break
        
    return new_name
    

class Process(object):
    
    description = 'process'
    data_folder_name = '_data'
    code_folder_name = '_code'
    process_data_filename = 'manifest.data'
    
    def __init__(self, name = None):
        
        self.directory = util_file.get_cwd()
        
        self.process_name = name
        self.parts = []
        self.external_code_path = None
        
    def _set_name(self, new_name):
        
        self.process_name = new_name
            
    def _create_folder(self):
                
        if not util_file.is_dir(self.directory):
            print '%s was not created.' %  self.process_name
            return
        
        path = util_file.create_dir(self.process_name, self.directory)
    
        if path and util_file.is_dir(path):
        
            util_file.create_dir(self.data_folder_name, path)
            util_file.create_dir(self.code_folder_name, path)
            
            code_files = self.get_code_files()
            
            found = False
            
            for code_file in code_files:
                basename = util_file.get_basename(code_file)
                if basename == self.process_data_filename:
                    found = True
                    break
            
            
            if not found:
                print 'creating manifest'
                self.create_code('manifest', 'script.manifest')        
        
        return path
            
    def _get_path(self, name):
        
        directory = util_file.join_path(self.get_path(), name)
                
        return directory
    
    def _center_view(self):
        if util.is_in_maya():
            try:
                cmds.select(cl = True)
                cmds.viewFit(an = True)
            except:
                print 'Could not center view.'
            
    def set_directory(self, directory):
        self.directory = directory
        
    def set_external_code_library(self, directory):
        self.external_code_path = directory
        
    def is_process(self):
        if not util_file.is_dir(self.get_code_path()):
            return False
        
        if not util_file.is_dir(self.get_data_path()):
            return False
        
        return True
        
    def get_path(self):
        
        if self.process_name:
            return util_file.join_path(self.directory, self.process_name)
        
        if not self.process_name:
            return self.directory
    
    def get_name(self):
        return self.process_name
    
    def get_relative_process(self, relative_path):
        
        process = Process(relative_path)
        process.set_directory(self.directory)
        
        return process
    
    def get_sub_processes(self):
        
        process_path = self.get_path()
        
        found = find_processes(process_path)
                                
        return found
    
    def get_sub_process(self, part_name):
        
        part_process = Process(part_name)
        
        part_process.set_directory(self.get_path())  
        
        return part_process    
        
    #--- data
        
    def is_data_folder(self, name):
        
        path = self.get_data_folder(name)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
        
    def get_data_path(self):
        return self._get_path(self.data_folder_name)        
    
    def get_data_folder(self, name):
        folders = self.get_data_folders()
        for folder in folders:
            if folder == name:
                return util_file.join_path(self.get_data_path(), name)
            
    def get_data_type(self, name):
        data_folder = data.DataFolder(name, self.get_data_path())
        data_type = data_folder.get_data_type()
        
        return data_type
        
    def get_data_folders(self):
        
        directory = self.get_data_path()
        
        return util_file.get_folders(directory)      
     
    def create_data(self, name, data_type):
        path = self.get_data_path()
        
        test_path = util_file.join_path(path, name)
        test_path = util_file.inc_path_name(test_path)
        name = util_file.get_basename(test_path)
        
        data_folder = data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        """
        code_name = 'import_%s' % name
        
        filepath = self.create_code(code_name, import_data = name)
        self.set_manifest(['%s.py' % code_name], append = True)
        """
        
        
        return data_folder.folder_path
    
    def import_data(self, name):
        
        path = self.get_data_path()
        
        data_folder = data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'import_data'):
            instance.import_data()
            
    def save_data(self, name):
        path = self.get_data_path()
        
        data_folder = data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'save'):
            instance.save()
    
    def rename_data(self, old_name, new_name):
                
        data_folder = data.DataFolder(old_name, self.get_data_path())
        #instance = data_folder.get_folder_data_instance()
        
        #instance.rename(new_name)
        print old_name, new_name
        
        return data_folder.rename(new_name)
    
    def delete_data(self, name):
        data_folder = data.DataFolder(name, self.get_data_path())
        
        
    
    #code ---
    
    def is_code_folder(self, name):
        
        path = self.get_code_folder(name)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
    
    def get_code_path(self):
        return self._get_path(self.code_folder_name)
    
    def get_code_folder(self, name):
    
        folders = self.get_code_folders()
        for folder in folders:
            if folder == name:
                return util_file.join_path(self.get_code_path(), name)

    def get_code_folders(self):
        directory = self.get_code_path()
        
        return util_file.get_folders(directory)  

    def get_code_type(self, name):
    
        data_folder = data.DataFolder(name, self.get_code_path())
        data_type = data_folder.get_data_type()
        return data_type
    
    def get_code_files(self, basename = False):
        directory = self.get_code_path()
        
        folders = util_file.get_folders(directory)
        
        files = []
        
        for folder in folders:
            
            data_folder = data.DataFolder(folder, directory)
            
            data_instance = data_folder.get_folder_data_instance()
            
            if data_instance:

                file_path = data_instance.get_file()

                if not basename:
                    files.append(file_path)
                if basename:
                    files.append(util_file.get_basename(file_path))

        return files
    
    def get_code_file(self, name):
        
        data_folder = data.DataFolder(name, self.get_code_path())
        
        data_instance = data_folder.get_folder_data_instance()
        
        if data_instance:
            filepath = data_instance.get_file()
            return filepath
        
    def create_code(self, name, data_type = 'script.python', inc_name = False, import_data = None):
        
        
        path = self.get_code_path()
        
        if inc_name:
            test_path = util_file.join_path(path, name)
            
            if util_file.is_dir(test_path):
                test_path = util_file.inc_path_name(test_path)
                name = util_file.get_basename(test_path)
        
        
        
        data_folder = data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        
        data_instance = data_folder.get_folder_data_instance()
        
        if name == 'manifest':
            data_instance.create()
            return
    
        if import_data:
            data_instance.set_lines(['process = None','','def main():',"    process.import_data('%s')" % import_data])
        if not import_data:
            data_instance.set_lines(['process = None','','def main():','    return'])
    
        data_instance.create()
    
        filename = data_instance.get_file()
        
        self.set_manifest(['%s.py' % name], append = True)
    
        
        return filename 
        
    def rename_code(self, old_name, new_name):
        
        code_folder = data.DataFolder(old_name, self.get_code_path())
        code_folder.rename(new_name)
        
        instance = code_folder.get_folder_data_instance()
        
        file_name = instance.get_file()
        file_name = util_file.get_basename(file_name)
                
        return file_name
        
    def delete_code(self, name):
        
        util_file.delete_dir(name, self.get_code_path())
        
        
    #--- manifest
        
    def get_manifest_folder(self):
        
        code_path = self.get_code_path()
        return util_file.join_path(code_path, 'manifest')
        
    def get_manifest_file(self):
        
        manifest_path = self.get_manifest_folder()
        
        return util_file.join_path(manifest_path, self.process_data_filename)
        

    def get_manifest_scripts(self, basename = True):
        
        manifest_file = self.get_manifest_file()
        
        if not manifest_file:
            return
        
        if not util_file.is_file(manifest_file):
            return
        
        files = self.get_code_files(False)
        
        scripts, states = self.get_manifest()
        
        if basename:
            return scripts
        
        if not basename:
            
            found = []
            
            for script in scripts:
                
                
                
                for filename in files:
                    
                    if filename.endswith(script):
                        
                        found.append(filename)
                        break
            
            return found
    
    def set_manifest(self, scripts, states = [], append = False):
        
        manifest_file = self.get_manifest_file()
        
        lines = []
        
        script_count = len(scripts)
        if states:
            state_count = len(states)
        if not states:
            state_count = 0
        
        for inc in range(0, script_count):
            
            if scripts[inc] == 'manifest.py':
                continue
            
            if inc > state_count-1:
                state = False
                
            if inc < state_count:
                state = states[inc]
            
            line = '%s %s' % (scripts[inc], state)
            lines.append(line)
                 
        util_file.write_lines(manifest_file, lines, append = append)
        
    
        
    def get_manifest(self):
        
        manifest_file = self.get_manifest_file()
        
        lines = util_file.get_file_lines(manifest_file)
        
        if not lines:
            return
        
        scripts = []
        states = []
        
        for line in lines:
            split_line = line.split()
            if len(split_line):
                scripts.append(split_line[0])
                
            if len(split_line) == 2:
                states.append(eval(split_line[1]))
                
            if len(split_line) == 1:
                states.append(False)
                
        return scripts, states
        
    
    #--- run
    
    def load(self, name):
        self._set_name(name)
        
    def add_part(self, name):
        part_process = Process(name)
        
        path = util_file.join_path(self.directory, self.process_name)
        
        part_process.set_directory(path)
        part_process.create()
        
    def create(self):
        return self._create_folder()
        
    def delete(self):
        util_file.delete_dir(self.process_name, self.directory)
        
    
        
    def rename(self, new_name):
        
        split_name = new_name.split('/')
        
        if util_file.rename( self.get_path(), split_name[-1]):
            
            self._set_name(new_name)
            
            
            return True
            
        return False
    
    def run_script(self, script):
                
        self._center_view()
        name = util_file.get_basename(script)
        path = util_file.get_parent_path(script)
        
        if self.external_code_path:
            if not self.external_code_path in sys.path:
                sys.path.append(self.external_code_path)
            
        module = util_file.load_python_module(name, path)
        
        if type(module) == str:
            return module
        
        if not module:
            return
        
        if hasattr(module, 'process'):
            module.process = self
        
        status = None  
        try:
            if hasattr(module, 'main'):
                module.main()
                
            if not hasattr(module, 'main'):
                if type(module) == str or type(module) == unicode:
                    status = module
                
        except Exception:
            status = traceback.format_exc()
            
        return status
               
    def run(self):
           
        if util.is_in_maya():
            cmds.file(new = True, f = True)
 
        scripts = self.get_manifest_scripts(False)
        
        for script in scripts:
            self.run_script(script)

                
            
def get_default_directory():
    if util.is_in_maya():
        return util_file.join_path(util_file.get_user_dir(), 'process_manager')
    if not util.is_in_maya():
        return util_file.join_path(util_file.get_user_dir(), 'documents/process_manager')
    
def copy_process_data(source_process, target_process, data_name, replace = False):
    
    data_type = source_process.get_data_type(data_name)
    
    data_folder_path = None
      
    if target_process.is_data_folder(data_name):
        
        data_folder_path = target_process.get_data_folder(data_name)
        
        other_data_type = target_process.get_data_type(data_name)
        
        if data_type != other_data_type:
            if replace:
                target_process.delete_data(data_name)
                
                copy_process_data(source_process, target_process, data_name)
                return
    
    if not target_process.is_data_folder(data_name):
        data_folder_path = target_process.create_data(data_name, data_type)
        
    path = source_process.get_data_path()
    data_folder = data.DataFolder(data_name, path)

    instance = data_folder.get_folder_data_instance()
    if not instance:
        return

    filepath = instance.get_file()
    
    basename = util_file.get_basename(filepath)
    
    destination_directory = util_file.join_path(data_folder_path, basename)
    
    if util_file.is_file(filepath):
        copied_path = util_file.copy_file(filepath, destination_directory)
    if util_file.is_dir(filepath):
        copied_path = util_file.copy_dir(filepath, destination_directory)
      
    version = util_file.VersionFile(copied_path)
    version.save('Copied from %s' % filepath)
              
            
def copy_process_code(source_process, target_process, code_name, replace = False):
    
    data_type = source_process.get_code_type(code_name)
    
    code_folder_path = None
    
    if target_process.is_code_folder(code_name):
        
        code_folder_path = target_process.get_code_folder(code_name)
        code_file = util_file.get_basename( target_process.get_code_file(code_name) )
        
        code_folder_path = util_file.join_path(code_folder_path, code_file)
        
        other_data_type = target_process.get_code_type(code_name)
        
        if data_type != other_data_type:
            if replace:
                target_process.delete_code(code_name)
                
                copy_process_code(source_process, target_process, code_name)
                            
                return
    
    if not target_process.is_code_folder(code_name):
        code_folder_path = target_process.create_code(code_name, data_type)
    
    
    path = source_process.get_code_path()
    data_folder = data.DataFolder(code_name, path)
    
    instance = data_folder.get_folder_data_instance()
    if not instance:
        return
    
    filepath = instance.get_file()
    
    destination_directory = code_folder_path
    
    if util_file.is_file(filepath):
        copied_path = util_file.copy_file(filepath, destination_directory)
    if util_file.is_dir(filepath):
        copied_path = util_file.copy_dir(filepath, destination_directory)
      
    version = util_file.VersionFile(copied_path)
    version.save('Copied from %s' % filepath)