# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from collections import OrderedDict
import json
import sys
import os
import shutil
import imp
import traceback
import getpass
import string
import re
import datetime
import subprocess
import tempfile
import threading
import stat
import ast

import util

import time

from vtool import logger
log = logger.get_logger(__name__) 

def get_permission(filepath):
    
    if os.access(filepath, os.R_OK | os.W_OK | os.X_OK ):
        return True
    
    try:
        log.info('Getting file permission: %s' % filepath)
        os.chmod(filepath, 0775)
        return True
    except:
                
        #util.warning('Failed to get elevated permission on %s' % filepath)
        return False

def get_vetala_version():
    
    filepath = get_vetala_directory()
    version_filepath = join_path(filepath, 'version.txt')
    
    if not is_file(version_filepath):
        return
    
    version_lines = get_file_lines(version_filepath)
    
    if not version_lines:
        return ''
    
    split_line = version_lines[0].split(':')
    
    if not split_line > 1:
        return ''
    
    version = split_line[1]
    version = version.strip()
    
    return 'BETA  ' + version

def get_vetala_directory():
    
    filepath = util.get_env('VETALA_PATH')
    filepath = fix_slashes(filepath)
    return filepath


class ProcessLog(object):
    
    def __init__(self, path):
        
        self.log_path = path
        
        self.log_path = create_dir('.log', self.log_path)
        
        date_and_time = get_date_and_time()
        
        self.log_path = create_dir('log_' % date_and_time, self.log_path)
    
        temp_log_path = util.get_env('VETALA_TEMP_LOG')
    
        util.set_env('VETALA_KEEP_TEMP_LOG', 'True')
        
        if not temp_log_path:
            util.set_env('VETALA_TEMP_LOG', self.log_path)
        
    def record_temp_log(self, name, value):
    
        if util.get_env('VETALA_KEEP_TEMP_LOG') == 'True':
            value = value.replace('\t', '  ')
            
            create_file('%s.txt' % name, self.log_path)
            

    def end_temp_log(self):
        util.set_env('VETALA_KEEP_TEMP_LOG', 'False')
        util.set_env('VETAL_TEMP_LOG', '')
        

class WatchDirectoryThread(threading.Thread):
    """
    Not developed fully.
    """
    
    def __init__(self):
        super(WatchDirectoryThread, self).__init__()

    def run(self, directory): 
        import time
        path_to_watch = "."
        before = dict ([(f, None) for f in os.listdir (path_to_watch)])
        
        while 1:
            time.sleep (10)
            
            after = dict ([(f, None) for f in os.listdir (path_to_watch)])
            
            added = [f for f in after if not f in before]
            removed = [f for f in before if not f in after]
    
            if added: util.show("Added: ", ", ".join (added))
            if removed: util.show("Removed: ", ", ".join (removed))
            
            before = after

class FileManager(object):
    """
    Convenience to deal with file write/read.
    
    Args:
        filepath (str): Path to the file to work on.
        skip_warning (bool): Wether to print warnings out or not.
    """
    
    def __init__(self, filepath, skip_warning = False):
        
        self.filepath = filepath
        self.skip_warning = skip_warning 
        if not skip_warning:
            self.warning_if_invlid_path('path is invalid: %s' % self.filepath)
                
        self.open_file = None       

    def read_file(self):
        """
        Start read the file.
        """
        if not self.skip_warning:
            self.warning_if_invalid_file('file is invalid')
        
        try:
            self.open_file = open(self.filepath, 'r')
        except:
            pass
        
    def write_file(self):
        """
        Start write the file.
        """
        if not self.skip_warning:
            self.warning_if_invalid_file('file is invalid')
        
        #if get_permission(self.filepath):
        
        try:
            self.open_file = open(self.filepath, 'w')
        except:
            'Failed to write to file: %s. Check permissions' % self.filepath
        
    def append_file(self):
        """
        Start append file.
        """
        if not self.skip_warning:
            self.warning_if_invalid_file('file is invalid')
        self.open_file = open(self.filepath, 'a')       
    
    def close_file(self):
        """
        Close file.
        """
        if self.open_file:
            self.open_file.close()
        
    def get_open_file(self):
        """
        Get open file object.
        """
        return self.open_file()
        
    def warning_if_invalid_folder(self, warning_text):
        """
        Check if folder is invalid and raise and error.
        """
        if not is_dir(self.filepath):
            raise NameError(warning_text)
    
    def warning_if_invalid_file(self, warning_text):
        """
        Check if file is invalid and raise and error.
        """
        if not is_file(self.filepath):
            raise NameError(warning_text)
        
    def warning_if_invlid_path(self, warning_text):
        """
        Check if path to file is invalid and raise error.
        """
        dirname = get_dirname(self.filepath)
        
        if not is_dir(dirname):
            raise UserWarning(warning_text)

class ReadFile(FileManager):
    """
    Class to deal with reading a file.
    """
    
    def __init__(self, filename, skip_warning = False):
        super(ReadFile, self).__init__(filename, skip_warning)        
        self.open_file = None
    
    def _get_lines(self):
        
        try:
            lines = self.open_file.read()
        except:
            return []
        
        return get_text_lines(lines)
        
        
    
    def read(self ):
        """
        Read the file.
        
        Returns:
            list: A list of file lines.
        """
        
        self.read_file()
        
        lines = self._get_lines()
        
        self.close_file()
        
        return lines

class WriteFile(FileManager):
    def __init__(self, filepath, skip_warning = False):
        super(WriteFile, self).__init__(filepath, skip_warning)
        
        self.filepath = filepath
        self.open_file = None
        
        self.append = False
        
    def write_file(self):
        """
        Write file. Basically creates the file if it doesn't exist.
        If set_append is True than append any lines to the file instead of replacing.
        """
        if self.append:
            self.append_file()
            
        if not self.append:
            super(WriteFile, self).write_file()
        
    def set_append(self, bool_value):
        """
        Append new lines to end of document instead of replace.
        
        Args:
            bool_value (bool)
        """
        self.append = bool_value
        
    def write_line(self, line):
        """
        Write a single line to the file.
        
        Args:
            line (str): The line to add to the file.
        """
        

        self.write_file()
        try:
            self.open_file.write('%s\n' % line)
        except:
            pass
        self.close_file()
        
    def write_json(self, data):
        self.write_file()
        try:
            json.dump(data, self.open_file,indent=4, sort_keys=True)
        except:
            pass
        self.close_file()
        
                
    def write(self, lines, last_line_empty = True):
        """
        Write the lines to the file.
        
        Args:
            lines (list): A list of lines. Each entry is a new line in the file.
            last_line_empty (bool): Wether or not to add a line after the last line.
        """
        self.write_file()
        
        try:
            inc = 0
            for line in lines:
    
                if inc == len(lines)-1 and not last_line_empty:
                    self.open_file.write(str('%s' % line))
                    break
                
                self.open_file.write(str('%s\n' % line))
                
                inc+= 1
        except:
            util.show( 'Could not write to file %s' % self.filepath )
            
        self.close_file()

class VersionFile(object):
    """
    Convenience to version a file or folder.
    
    Args:
        filepath (str): The path to the file to version.
    """
    
    def __init__(self, filepath):
        self.filepath = filepath

        if filepath:

            self.filename = get_basename(self.filepath)
            self.path = get_dirname(filepath)
        
        self.version_folder_name = '.version'
        self.version_name = 'version'
        self.version_folder = None
        self.updated_old = False
        

            
            
        
    def _prep_directories(self):
        self._create_version_folder()
        self._create_comment_file()
        
        
    def _create_version_folder(self):
        
        self.version_folder = create_dir(self.version_folder_name, self.path)
        
    def _create_comment_file(self):
        self.comment_file = create_file('comments.txt', self.version_folder)
        
    def _increment_version_file_name(self):
        
        path = join_path(self.version_folder, self.version_name + '.1')
        
        return inc_path_name(path)
        
    def _default_version_file_name(self):
        
        if not self.version_name:
            return
        
        version_folder = self._get_version_folder()
        path = join_path(version_folder, self.version_name + '.default')
        
        return path
        
    def _get_version_path(self, version_int):
        path = join_path(self._get_version_folder(), self.version_name + '.' + str(version_int))
        
        return path
    
    def _get_version_number(self, filepath):
        
        version_number = util.get_end_number(filepath)
        
        return version_number
        
    def _get_version_folder(self):
        if is_file(self.filepath):
            dirname = get_dirname(self.filepath)
            path = join_path(dirname, self.version_folder_name)
        else:
            path = join_path(self.filepath, self.version_folder_name)
        
        return path
    
    def _get_comment_path(self):
        folder = self._get_version_folder()
        
        filepath = None
        
        if folder:
            filepath = join_path(folder, 'comments.txt')
            
        return filepath
            
    def _save(self, filename):
        
        self._create_version_folder()
        self._create_comment_file()
        
        if is_dir(self.filepath):
            copy_dir(self.filepath, filename)
        if is_file(self.filepath):
            copy_file(self.filepath, filename)
  
    def save_comment(self, comment = None, version_file = None, ):
        """
        Save a comment to a log file.
        
        Args:
            comment (str)
            version_file (str): The corresponding version file.
        """
         
        
        version = version_file.split('.')
        if version:
            version = version[-1]
        
        user = getpass.getuser()
        
        if not comment:
            comment = '-'
        
        comment.replace('"', '\"')
        
        comment_file = WriteFile(self.comment_file)
        comment_file.set_append(True)
        comment_file.write(['version = %s; comment = "%s"; user = "%s"' % (version, comment, user)])
        comment_file.close_file()
            
    def save(self, comment = None):
        """
        Save a version.
        
        Args:
            comment (str): The comment to add to the version.
        
        Returns:
            str: The new version file name
        """
        
        self._prep_directories()
        
        if not comment == None:
            comment.replace('\n', '   ')
            comment.replace('\r', '   ')
        if comment == None:
            comment = ' '
        
        inc_file_name = self._increment_version_file_name()
        
        self._save(inc_file_name)
            
        self.save_comment(comment, inc_file_name)
        
        return inc_file_name
    
    def save_default(self):
        
        self._prep_directories()
        
        filename = self._default_version_file_name()
        
        if filename:
            self._save(filename)
        else:
            util.warning('Could not save default.')
        
        return filename
    
    def has_default(self):
        
        if not self.version_name:
            return False
        
        filename = self._default_version_file_name()
        if is_file(filename):
            return True
        
        return False
    
    def has_versions(self):
        
        version_folder = self._get_version_folder()
        
        if exists(version_folder):
            return True
        
    def get_count(self):
        
        versions = self.get_version_numbers()
        
        if versions:
            return len(versions)
        else:
            return 0
        
        
        
    def set_version_folder(self, folder_path):
        """
        Set the folder where the version folder should be created.
        
        Args:
            folder_path (str): Full path to where the version folder should be created.
        """
        self.path = folder_path
        
    def set_version_folder_name(self, name):
        """
        Set the name of the version folder.
        
        Args:
            name (str)
        """
        self.version_folder_name = name
        
    def set_version_name(self, name):
        """
        Set the version name.
        
        Args:
            name (str): The name of the version.
        """
        self.version_name = name
        
    
        
    def get_version_path(self, version_int):
        """
        Get the path to a version.
        
        Args:
            version_int (int): The version number.
            
        Returns:
            str: The path to the version.
        """
        return self._get_version_path(version_int)
        
    def get_version_comment(self, version_int):
        """
        Get the version comment.
                
        Args:
            version_int (int): The version number.
            
        Returns:
            str: The version comment.
        """
        comment, user = self.get_version_data(version_int)
        return comment
    
    def get_organized_version_data(self):
        """
        Returns:
            version, comment, user, file_size, modified, version_file
        """
        versions = self.get_versions(return_version_numbers_also = True)
        
        if not versions:
            return
        
        if versions:
            version_paths = versions[0]
            version_numbers = versions[1] 
        
        filepath = self._get_comment_path()

        if not filepath:
            return []
        
        datas = []
        
        if is_file(filepath):
            
            read = ReadFile(filepath)
            lines = read.read()
            

            
            
            
            for line in lines:
                
                line_info_dict = {}    
                version = None
                comment = None
                user = None
                file_size = None
                modified = None
                
                split_line = util.split_line(line, ';')
                
                for sub_line in split_line:
                    
                    assignment = util.split_line(sub_line, '=') 
                    
                    if assignment and assignment[0]:
                        
                        name = assignment[0].strip()
                        value = assignment[1].strip()
                    
                        line_info_dict[name] = value
                
                if not line_info_dict.has_key('version'):
                    continue
                
                version = int(line_info_dict['version'])
                    
                if not int(line_info_dict['version']) in version_numbers:
                    continue
                
                if line_info_dict.has_key('comment'):
                    comment = line_info_dict['comment']
                    comment = comment[1:-1]
                if line_info_dict.has_key('user'):
                    user = line_info_dict['user']
                    user = user[1:-1]
                
                keys = version_paths.keys()
                
                version_file = version_paths[(version)]
                version_file = join_path(self.filepath, '%s/%s' % (self.version_folder_name, version_file))
                
                file_size = get_filesize(version_file)
                modified = get_last_modified_date(version_file)
                
                datas.append([version, comment, user, file_size, modified, version_file])
                
        return datas
        
    
    def get_version_data(self, version_int):
        """
        Get the version data.  Comment and user.
                
        Args:
            version_int (int): The version number.
            
        Returns:
            tuple: (comment, user)
        """
        filepath = self._get_comment_path()

        if not filepath:
            return None, None
        
        if is_file(filepath):
            
            read = ReadFile(filepath)
            lines = read.read()
            
            version = None
            comment = None
            user = None
            
            for line in lines:
                
                start_index = line.find('"')
                if start_index > -1:
                    end_index = line.find('";')
                    
                    subpart = line[start_index+1:end_index]
                    
                    subpart = subpart.replace('"', '\\"')
                    
                    line = line[:start_index+1] + subpart + line[end_index:]
                
                try:
                    exec(line)
                except:
                    pass
                
                if version == version_int:
                    
                    return comment, user
                
        return None, None
    
    def get_version_numbers(self):
        
        version_folder = self._get_version_folder()
        
        files = get_files_and_folders(version_folder)
        
        if not files:
            return
        
        number_list = []
            
        for filepath in files: 
            
            if not filepath.startswith(self.version_name):
                continue
            
            split_name = filepath.split('.')
            
            if split_name[1] == 'json':
                continue
            
            if split_name[1] == 'default':
                continue
            
            if not len(split_name) == 2:
                continue
            
            number = int(split_name[1])
            
            number_list.append(number)
        
        number_list.sort()
         
        return number_list
    
    def get_versions(self, return_version_numbers_also = False):
        """
        Get filepaths of all versions.
        
        Returns:
            list: List of version filepaths.
        """
        
        version_folder = self._get_version_folder()
        
        files = get_files_and_folders(version_folder)
        
        if not files:
            return None
        
        number_list = []
        pass_files = []
            
        for filepath in files: 
            
            if not filepath.startswith(self.version_name):
                continue
            
            split_name = filepath.split('.')
            
            if not len(split_name) == 2:
                continue
            
            number = int(split_name[1])
            
            number_list.append(number)
            pass_files.append(filepath)
            
        
        if not pass_files:
            return
        
        quick_sort = util.QuickSort(number_list)
        quick_sort.set_follower_list(pass_files)
        pass_files = quick_sort.run()
        
        
        
        
        pass_dict = {}
        
        for inc in range(0, len(number_list)):
            pass_dict[pass_files[0][inc]] = pass_files[1][inc]
        
        if not return_version_numbers_also:
            return pass_dict
        if return_version_numbers_also:
            return pass_dict, pass_files[0]
    
    def get_latest_version(self):
        """
        Get the filepath to the latest version.
        
        Returns:
            str: Filepath to latest version.
        """
        versions = self.get_versions()
        
        latest_version = versions[-1]
        
        return join_path(self.filepath, '%s/%s' % (self.version_folder_name, latest_version))

    def get_default(self):
        filename = self._default_version_file_name()
        
        return filename
       
class SettingsFile(object):
    
    def __init__(self):
        self.directory = None
        self.filepath = None
        
        self.settings_dict = {}
        self.optional_dict = {}
        self.settings_order = []
        self.write = None 
        self._has_json = None
        self._has_permission = False
    
    def _get_json_file(self):
        directory = get_dirname(self.filepath)
        
        if not self.filepath:
            return
        
        name = get_basename_no_extension(self.filepath)
        
        filename=name+'.json'
        
        if not self._has_json:
            filepath = create_file(filename, directory)
        else:
            filepath = join_path(directory, filename)
        
        #if not filepath:
        #    test_path = join_path(directory, name+'.json')
            
        #    if is_file(test_path):
        #        filepath = test_path
        
        
        return filepath
    
    def _has_json_file(self):
        
        if self._has_json != None:
            return self._has_json
        
        if not self.filepath:
            return False
        
        directory = get_dirname(self.filepath)
        name = get_basename_no_extension(self.filepath)
        
        filepath = join_path(directory, name + '.json')
        
        if exists(filepath):
            return True
        else:
            return False
    
    def _read(self):
        
        if not self.filepath:
            return
        
        lines = get_file_lines(self.filepath)
        
        if not lines:
            return
        
        self.settings_dict = {}
        self.settings_order = []
        
        for line in lines:
            if not line:
                continue
            
            split_line = line.split('=')
            
            name = split_line[0].strip()
            
            value = split_line[-1]
            
            if not value:
                continue
            
            value = fix_slashes(value)
            
            try:
                value = eval( str(value) )
            except:
                value = str(value)
            
            self.settings_dict[name] = value
            self.settings_order.append(name)
            
    def _read_json(self):
        
        filepath = self._get_json_file()
        
        if not filepath:
            return
        
        self.filepath = filepath
        
        data = None
        
        try:
            data = OrderedDict(get_json(filepath))
        except:
            self.settings_order = []
            self.settings_dict = {}
            return
        
        self.settings_order = data.keys()
        self.settings_dict = data
        
    def _update_old(self, filename):
        
        directory = self.directory
    
        if filename == 'data.json':
            old = join_path(directory, 'data.type')
            if is_file(old):
                self.filepath = old
                
        if filename == 'options.json':
            old_options = join_path(directory, 'options.txt')
            if is_file(old_options):
                self.filepath = old_options
        
        if filename == 'settings.json':
            old_settings = join_path(directory, 'settings.txt')
            if is_file(old_settings):
                self.filepath = old_settings
                            
        if not filename.endswith('.json'):
            old = join_path(directory, filename)
            
            if is_file(old):
                self.filepath = old    
        
        self._read()
        self._write_json()       

    def _get_permission(self, filepath):
        if not self._has_permission:
            get_permission(filepath)
            self._has_permission = True
            
    def _write(self):
        
        self._write_json()
        
        """
        #this is now deprecated, writing to json takes over
        lines = []
        
        
        
        for key in self.settings_order:
            value = self.settings_dict[key]
            
            if type(value) == str or type(value) == unicode:
                value = '"%s"' % value
            
            #if value == None:
            #    value = "None"
            
            line = '%s = %s' % (key, str(value))
            
            lines.append(line)
        
        write = WriteFile(self.filepath)
        
        try:
            write.write(lines)
        except:
            
            time.sleep(.1)
            write.write(lines)
        """

    def _write_json(self):
        
        filepath = self._get_json_file()
        
        if not filepath:
            return
        
        self._get_permission(filepath)
        
        write = WriteFile(filepath, skip_warning=True)
        
        out_list = []
        
        for key in self.settings_order:
            value = self.settings_dict[key]
            
            out_list.append([key, value])
            
        out_data = OrderedDict(out_list)
        
            
        #write.write_json(out_list)
        write.write_json(out_data.items())
    
    def set(self, name, value):
        
        log.debug('Set setting %s %s' % (name, value))
                
        self.settings_dict[name] = value
        
        if not name in self.settings_order:
            self.settings_order.append(name)
        
        
        self._write()
    
    def get(self, name):
        
        if name in self.settings_dict:
            return self.settings_dict[name]
    
    def has_setting(self, name):
        
        if not self.settings_dict.has_key(name):
            return False
        
        return True
    
    def has_settings(self):
        
        if self.settings_order:
            return True
        
        return False
    
    def get_settings(self):
        
        log.debug('Get settings')
        
        found = []
        
        for setting in self.settings_order:
            
            found.append( [setting, self.settings_dict[setting]] )
            
        return found
    
    def get_file(self):
        return self.filepath
    
    def clear(self):
        
        self.settings_dict = {}
        self.settings_order = []
        
        self._write()
    
    def reload(self):
        
        self._read_json()
    
    def set_directory(self, directory, filename = 'settings.json'):
        self.directory = directory
        
        #eventually after a lot of testing, can add a statement to delete old settings/data files
        
        self.filepath = join_path(self.directory, filename)
        
        self._has_json = self._has_json_file()
        
        if not self._has_json:
            self._update_old(filename)
                        
        self._read_json()
        #self._read()
        
        return self.filepath

class ControlNameFromSettingsFile(util.ControlName):
    
    def __init__(self, directory = None):
        
        super(ControlNameFromSettingsFile, self).__init__()
        
        if directory:
            self.set_directory(directory)
        
    
    def set_directory(self, directory, filename = 'settings.json'):
        
        self.directory = directory
         
        
        settings_inst = SettingsFile()
        settings_inst.set_directory(directory, filename)
        
        self._settings_inst = settings_inst
        
        control_order = settings_inst.get('control_name_order')
        
        if control_order: 
            self.control_order = control_order
        
        self.control_alias = settings_inst.get('control_alias')
        self.left_alias = settings_inst.get('control_left')
        self.right_alias = settings_inst.get('control_right')
        self.center_alias = settings_inst.get('control_center')
        
        
        if not self.control_alias:
            self.control_alias = 'CNT'
        if not self.left_alias:
            self.left_alias = 'L'
        if not self.right_alias:
            self.right_alias = 'R'
        if not self.center_alias:
            self.center_alias = 'C'
        
        self.control_uppercase = settings_inst.get('control_uppercase')
        
        if self.control_uppercase == None:
            self.control_uppercase = True
         
    def set(self, name, value):
        
        if name == 'control_name_order':
            self.control_order = value
            if self._settings_inst:
                self._settings_inst.set(name, value)
        
        if name == 'control_alias':
            self.control_alias = str(value)
            if self._settings_inst:
                self._settings_inst.set(name, value)
                
        if name == 'control_left':
            self.left_alias = value
            if self._settings_inst:
                self._settings_inst.set(name, value)

        if name == 'control_right':
            self.right_alias = value
            if self._settings_inst:
                self._settings_inst.set(name, value)

        if name == 'control_center':
            self.center_alias = value
            if self._settings_inst:
                self._settings_inst.set(name, value)
        
        if name == 'control_uppercase':
            self.control_uppercase = value
            if self._settings_inst:
                self._settings_inst.set(name, value)

class FindUniquePath(util.FindUniqueString):
    
    def __init__(self, directory):
        
        if not directory:
            directory = get_cwd()
        
        self.parent_path = self._get_parent_path(directory)
        basename = get_basename(directory)
        
        super(FindUniquePath, self).__init__(basename)
        
    def _get_parent_path(self, directory):
        return get_dirname(directory)
    
    def _get_scope_list(self):
        return get_files_and_folders(self.parent_path)
    
    def _search(self):
        
        end_number = self._get_number()
        
        self.increment_string = self.test_string
        
        unique = False
        
        scope = self._get_scope_list()
        
        numbers = []
        filtered_scope = []
        
        if scope:
            
            if len(scope) > 1:
                for thing in scope:
                    
                    number = util.get_end_number(thing)
                    if number:
                        self._format_string(number)
                        
                        if thing == self.increment_string:
                            numbers.append( number )
                            filtered_scope.append(thing)
                
                sort = util.QuickSort(numbers)
                numbers = sort.run()
        
        if numbers:
            end_number = numbers[-1]
            self._format_string(end_number)
        
        inc = 0
        
        while not unique:
            
            if inc > 10000:
                break
            
            inc += 1
            
            if not scope:
                unique = True
                continue
            
            if not self.increment_string in scope:
                unique = True
                continue
            
            if self.increment_string in scope:
                
                if not end_number:
                    end_number = 1
                else:
                    end_number += 1
                    
                self._format_string(end_number)
                
                continue
        
        return join_path(self.parent_path, self.increment_string)

class ParsePython(object):
    """
    This needs to be replaced by something that uses the AST instead.
    """
    def __init__(self, filepath):
        
        self.filepath = filepath
        
        self.main_scope = PythonScope('main')
        self.main_scope.set_indent(0)
        
        self.last_scope = self.main_scope
        self.last_parent_scope = self.main_scope
        
        self.scope_types = ['class', 'def'] 
        self.logic_scope_types = ['if', 'elif', 'else', 'while']
        self.try_scope_types = ['try','except','finally']
        
        self.indents = []
        self.current_scope_lines = []
        
        
        self._parse()
        
        
    def _set_scope(self, scope):
        
        self.last_scope.set_scope_lines(self.current_scope_lines)
        self.current_scope_lines = []
        self.last_scope = scope
        
    def _parse(self):
        
        lines = []
        
        if is_file(self.filepath):
            lines = get_file_lines(self.filepath)
        
        for line in lines:

            strip_line = line.strip()
            
            if not strip_line:
                continue
            
            indent = 0
            
            match = re.search('^ +(?=[^ ])', line)
            
            if match:
                indent = len(match.group(0))
 
            if self.indents:
                last_indent = self.indents[-1]
                
                if indent < last_indent:            
                    pass
        
            self.find_scope_type(strip_line, indent)
            
            self.current_scope_lines.append(line)
            
    def find_scope_type(self, line, indent):
            
        for scope_type in self.scope_types:
            match = re.search('%s(.*?):' % scope_type, line)
            
            if not match:
                continue
            
            scope_line = match.group(0)
            
            match = re.search('(?<=%s)(.*?)(?=\()' % scope_type, scope_line)
            
            if not match:
                continue
            
            scope_name = match.group(0)
            scope_name = scope_name.strip()
            
            match = re.search('\((.*?)\)', scope_line)
            
            if not match:
                continue
            
            scope_bracket = match.group()
            
            parent_scope = self.main_scope
            
            if self.indents:
            
                if indent > self.indents[-1]:
                    parent_scope = self.last_scope
                
                if indent == self.indents[-1]:
                    parent_scope = self.last_parent_scope
                
                if indent < self.indents[-1]:
                    
                    if indent == 0:
                        parent_scope == self.main_scope
                    
                    if indent > 0:
                        parent_indent = self.last_scope.parent.indent
                        parent_scope = self.last_scope.parent
                        
                        #need to go up the scope until finding a matching indent
                        """
                        while parent_indent != indent:
                            
                            parent_indent = self.last_scope.parent.indent
                            parent_scope = self.last_scope.parent
                        """
                    
            sub_scope = PythonScope(scope_name)
            sub_scope.set_bracket(scope_bracket)
            sub_scope.set_parent(parent_scope)   
            sub_scope.set_indent(indent)
            sub_scope.set_scope_type(scope_type)         
            
            self.last_parent_scope = parent_scope
            self.last_scope = sub_scope
            self.indents.append(indent)
            
            return True
        
        return False
            
class PythonScope(object):
    
    def __init__(self, name):
        
        self.name = name
        self.parent = None
        self.children = []
        
        self.bracket_string = '()'
        self.docstring = ''
        self.scope_lines = []
        self.scope_type = ''
        
        self.indent = None
        
    def set_scope_type(self, scope_type_name):
        self.scope_type = scope_type_name
        
    def set_bracket(self, bracket_string):
        
        self.bracket_string = bracket_string
    
    def set_scope_lines(self, lines):
        self.scope_lines = lines

    def set_parent(self, parent_scope):
        self.parent = parent_scope
        parent_scope.set_child(self)
    
    def set_child(self, child_scope):
        self.children.append(child_scope)
        
    def set_indent(self, indent):
        self.indent = indent
    
    

#---- get


def get_basename(directory):
    """
    Get the last part of a directory name. If the name is C:/goo/foo, this will return foo.
    
    Args:
        directoroy(str): A directory path.
        
    Returns:
        str: The last part of the directory path.
    """
    
    if directory:
        return os.path.basename(directory)

def get_basename_no_extension(filepath):
    """
    Get the last part of a directory name. If the name is C:/goo/foo.py, this will return foo.
    
    Args:
        directoroy(str): A directory path.
        
    Returns:
        str: The last part of the directory path, without any extensions.
    """
    
    if not filepath:
        return
    
    basename = get_basename(filepath)
    
    new_name = remove_extension(basename)
    
    return new_name

def get_dirname(directory):
    """
    Given a directory path, this will return the path above the last thing in the path.
    If C:/goo/foo is give, C:/goo will be returned.
    
    Args:
        directory (str): A directory path. 
        
    Returns:
        str: The front portion of the path.
    """
    try:
        return os.path.dirname(directory)
    except:
        return False

def get_user_dir():
    """
    Get the path to the user directory.
    
    Returns:
        str: The path to the user directory.
    """
    return fix_slashes( os.path.expanduser('~') )

def get_temp_dir():
    """
    Get path to the temp directory.
    
    Returns:
        str: The path to the temp directory.
    """
    return fix_slashes( tempfile.gettempdir() ) 

def get_cwd():
    """
    Get the current working directory.
    
    Returns:
        str: The path to the current working directory.
    """
    return os.getcwd()

def get_files(directory):
    """
    Get files found in the directory.
    
    Args:
        directory (str): A directory path.
    
    Returns:
        list: A list of files in the directory.
    """
    
    files = os.listdir(directory)
    
    found = []
    
    for filename in files:
        
        file_path = join_path(directory, filename)
    
        if is_file(file_path):
            found.append(filename)
    
    return found

def get_folders_without_prefix_dot(directory, recursive = False, base_directory = None):
    
    if not exists(directory):
        return
    
    found_folders = []
    
    folders = get_folders(directory)
    
    if not base_directory:
        base_directory = directory
    
    for folder in folders:
        
        if folder == 'version':
            version = VersionFile(directory)
            if version.updated_old:
                continue
        
        if folder.startswith('.'):
            continue

        folder_path = join_path(directory, folder)
        
        folder_name = os.path.relpath(folder_path,base_directory)
        folder_name = fix_slashes(folder_name)
        
        found_folders.append(folder_name)
        
        if recursive:
            sub_folders = get_folders_without_prefix_dot(folder_path, recursive, base_directory)
            
        found_folders += sub_folders
         
    """
    os.walk was slower... it was retrieving everything... folders and files...
    for root, dirs, files in os.walk(directory):
        
        for folder in dirs:
            
            if folder == 'version':
            
                version = VersionFile(root)
                
                if version.updated_old:
                    continue
            
            if folder.startswith('.'):
                continue
            
            folder_name = join_path(root, folder)
            
            folder_name = os.path.relpath(folder_name,directory)
            folder_name = fix_slashes(folder_name)
            
            found_folders.append(folder_name)
        
        if not recursive:
            break
    """
     
    return found_folders

def get_folders(directory, recursive = False):
    """
    Get folders found in the directory.
    
    Args:
        directory (str): A directory path.
    
    Returns:
        list: A list of folders in the directory.
    """
    
    found_folders = []

    if not recursive:
        files = None
        
        try:
            files = os.listdir(directory)
        except:
            return found_folders
        
        if not files:
            return found_folders
        
        for filename in files:
            
            folder_name = join_path(directory, filename)
            if is_dir(folder_name):
                folder_name = os.path.relpath(folder_name,directory)
                folder_name = fix_slashes(folder_name)
            
                found_folders.append(folder_name)
    
    if recursive:
        try:
            for root, dirs, files in os.walk(directory):
                
                for folder in dirs:
                    
                    folder_name = join_path(root, folder)
                    
                    folder_name = os.path.relpath(folder_name,directory)
                    folder_name = fix_slashes(folder_name)
                    
                    found_folders.append(folder_name)
        except:
            return found_folders
            
    
    
    return found_folders           

def get_files_and_folders(directory):
    """
    Get files and folders found in the directory.
    
    Args:
        directory (str): A directory path.
    
    Returns:
        list: A list of files and folders in the directory.
    """
    
    try:
        files = os.listdir(directory)
    except:
        files = []
    
    return files

def get_folders_date_sorted(directory):
    """
    Get folders date sorted found in the directory.
    
    Args:
        directory (str): A directory path.
    
    Returns:
        list: A list of folders date sorted in the directory.
    """
    mtime = lambda f: os.stat(os.path.join(directory, f)).st_mtime

    return list(sorted(os.listdir(directory), key = mtime))

def get_files_date_sorted(directory, extension = None):
    """
    Get files date sorted found in the directory.
    
    Args:
        directory (str): A directory path.
    
    Returns:
        list: A list of files date sorted in the directory.
    """    
    if not extension:
        files = get_files(directory)
        
    if extension:
        files = get_files_with_extension(extension, directory)
    
    mtime = lambda f: os.stat(os.path.join(directory, f)).st_mtime
    
    return list(sorted(files, key = mtime))
        

def get_latest_file_at_path(path):
    
    files = get_files_date_sorted(path)
    
    if files:
        filepath = join_path(path, files[-1])
        return filepath

def get_latest_file(file_paths, only_return_one_match = True):
    
    last_time = 0
    times = {}
    
    for file_path in file_paths:
        
        mtime = os.stat(file_path).st_mtime
        
        if not times.has_key(mtime):
            times[mtime] = []
            
        times[mtime].append(file_path)
        
        if mtime > last_time:
            last_time = mtime
    
    if not times.keys():
        return
    
    if only_return_one_match:
        return times[mtime][0]
    
    if not only_return_one_match:
        return times[mtime]


def get_files_with_extension(extension, directory, fullpath = False):
    """
    Get files that have the extensions.
    
    Args:
        extension (str): eg. .py, .data, etc.
        directory (str): A directory path.
        fullpath (bool): Wether to returh the filepath or just the file names.
    
    Returns:
        list: A list of files with the extension.
    """
    found = []
    
    
    try:
        objects = os.listdir(directory)
    except:
        return found
    
    for filename_and_extension in objects:
        filename, found_extension = os.path.splitext(filename_and_extension)
        if found_extension == '.%s' % extension:
            if not fullpath:
                found.append(filename_and_extension)
            if fullpath:
                found.append(join_path(directory, filename_and_extension))
            
    return found

def get_size(path, round_value = 2):
    
    size = 0
    
    if is_dir(path):
        size = get_folder_size(path, round_value)
    if is_file(path):
        size = get_filesize(path, round_value)

    return size 

def get_filesize(filepath, round_value = 2):
    """
    Get the size of a file.
    
    Args:
        filepath (str)
        
    Retrun
        float: The size of the file specified by filepath.
    """
    
    size = os.path.getsize(filepath)
    size_format = round( size * 0.000001, round_value )

    return size_format

def get_folder_size(path, round_value = 2, skip_names = []):
    """
    skip_names will skip folders and files that have the same name specified in skip_names list.
    """
    size = 0
    
    skip_names = util.convert_to_sequence(skip_names)
    
    for root, dirs, files in os.walk(path):
        
        root_name = get_basename(root)
        if root_name in skip_names:
            continue
        
        for name in files:
            
            if name in skip_names:
                
                continue
            
            size += get_filesize( join_path(root, name), round_value )
            
    return size

def get_date():
    
    date_value = datetime.datetime.now()
    year = date_value.year
    month = date_value.month
    day = date_value.day
    
    return '%s_%s_%s' % (year,month,day)

def get_date_and_time():
    date_value = datetime.datetime.now()
    year = date_value.year
    month = date_value.month
    day = date_value.day
    
    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = date_value.second
    
    second = str( int(second) )
    
    if len(hour) == 1:
        hour = '0'+hour
    if len(minute) == 1:
        minute = '0'+minute
    if len(second) == 1:
        second = second + '0'

    return '%s_%s_%s__%s_%s_%s' % (year,month,day,hour,minute,second)

def get_last_modified_date(filepath):
    """
    Get the last date a file was modified.
    
    Args:
        filepath (str)
        
    Returns:
        str: A formatted date and time.
    """
    
    mtime = os.path.getmtime(filepath)
    
    date_value = datetime.datetime.fromtimestamp(mtime)
    year = date_value.year
    month = date_value.month
    day = date_value.day
    
    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = date_value.second
    
    second = str( int(second) )
    
    if len(hour) == 1:
        hour = '0'+hour
    if len(minute) == 1:
        minute = '0'+minute
    if len(second) == 1:
        second = second + '0'

    return '%s-%s-%s  %s:%s:%s' % (year,month,day,hour,minute,second)
    
def get_user():
    """
    Get the current user.
    
    Returns:
        str: The name of the current user.
    """
    return getpass.getuser()
    
def get_file_text(filepath):
    """
    Get the text directly from a file. One long string, no parsing.
    
    """
    lines = []
    open_file = None
    
    try:
        open_file = open(filepath, 'r')    
        lines = open_file.read()
        open_file.close()
    except:
        if open_file:
            open_file.close()
    
    return lines

def get_file_lines(filepath):
    """
    Get the text from a file.
    
    Args:
        filepath (str): The filename and path.
    
    Returns:
        str
    """
    read = ReadFile(filepath, skip_warning=True)
    
    return read.read()

def get_json(filepath):
    
    with open(filepath) as json_file:
        data = json.load(json_file)
        
    return data

def get_text_lines(text):
    """
    Get the text from a file. Each line is stored as a different entry in a list.
    
    Args:
        text (str): Text from get_file_lines
        
    Returns:
        list
    """
    text = text.replace('\r', '')
    lines = text.split('\n')
        
    return lines
    

def exists(directory):
    
    if not directory:
        return False
    
    if os.path.exists(directory):
        return True
    else:
        return False
    
def is_dir(directory):
    """
    Returns: 
        bool
    """
        
    if not directory:
        return False
        
    log.debug('is directory: %s' % directory)
        
    try:
        mode = os.stat(directory)[stat.ST_MODE]
        if stat.S_ISDIR(mode):
            return True
    except:
        return False
    
    
def is_file(filepath):
    """
    Returns: 
        bool
    """
     
    if not filepath:
        return False
    
    log.debug('is file: %s' % filepath)
    
    try:
        mode = os.stat(filepath)[stat.ST_MODE]
        if stat.S_ISREG(mode):
            return True
        
    except:
        return False
    
    
    

def is_file_in_dir(filename, directory):
    """
    
    Args:
        filename (str): Filename including path.
        directory (str): Directory name including path.
    
    Returns:
        bool: Wether the file is in the directory.
    """
    
    log.debug('is file in directory')
    filepath = join_path(directory, filename)
    
    return os.path.isfile(filepath)

def is_same_date(file1, file2):
    """
    Check if 2 files have the same date.
    
    Args:
        file1 (str): Filename including path.
        file2 (str): Filename including path.
        
    Returns: 
        bool
    """
    
    if file1 == None and file2 != None:
        return False
    
    if file1 == None and file2 == None:
        return True
    
    if file1 != None and file == None:
        return False
    
    date1 = os.path.getmtime(file1)
    date2 = os.path.getmtime(file2)
    
    if date1 == None and date2 == None:
        return True
    
    if date1 != None and date2 != None:
        value = date1 - date2
        
        if abs(value) < 0.01:
            return True
    
    if date1 == None and date2 != None:    
        return False
    
    if date1 != None and date2 == None:
        return False
    


def is_same_text_content(file1, file2):
    
    text1 = get_file_text(file1)
    text2 = get_file_text(file2)
    
    if text1 == text2:
        return True
    
    return False

def inc_path_name(directory, padding = 0):
    """
    Add padding to a name if it is not unique.
    
    Args:
        directory (str): Directory name including path.
        padding (int): Where the padding should start.
        
    Returns:
        str: The new directory with path.
    """
    unique_path = FindUniquePath(directory)
    unique_path.set_padding(padding) 
    
    return unique_path.get()

def open_browser(filepath):
    """
    Open the file browser to the path specified. Currently only works in windows.
    
    Args:
        filepath (str): Filename with path.
        
    """
    
    if util.is_windows():
        os.startfile(filepath)
        
    if util.is_linux():
        try:
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, filepath])  

        except:
            os.system("gnome-terminal --working-directory=%s" % filepath)

def remove_extension(path):
    
    dot_split = path.split('.')
    
    new_name = path
    
    if len(dot_split) > 1:
        new_name = string.join(dot_split[:-1], '.')
    
    return new_name

def get_common_path(path1, path2):
    
    path1 = fix_slashes(path1)
    path2 = fix_slashes(path2)
    
    split_path1 = path1.split('/')
    split_path2 = path2.split('/')
    
    first_list = split_path1
    second_list = split_path2

    
    found = []
        
    for inc in range(0, len(first_list)):
        
        if len(second_list) <= inc:
            break
        
        if first_list[inc] == second_list[inc]:
            found.append(first_list[inc])
            
        if first_list[inc] != second_list[inc]:
            break
        
    found = string.join(found, '/')
    
    return found

def remove_common_path(path1, path2):
    """
    Given path1 = pathA/pathB
    and path2 = pathA/pathC
    
    or path1 = pathA
    and path2 = pathA/pathC
    
    return pathC
    """

    
    path1 = fix_slashes(path1)
    path2 = fix_slashes(path2)
    
    split_path1 = path1.split('/')
    split_path2 = path2.split('/')
    
    skip = True
    new_path = []
    
    for inc in range(0, len(split_path2)):
        
        if skip:
            if len(split_path1) > inc:
                if split_path1[inc] != split_path2[inc]:
                    skip = False
                    
            if (len(split_path1)-1) < inc:
                skip = False
                
        if not skip:
            new_path.append(split_path2[inc])

    new_path = string.join(new_path, '/')
    
    return new_path

def remove_common_path_simple(path1, path2):
    """
    This just subtracts a string that is the same at the beginning.
    path1 gets subtracted from path2
    """
    
    if not path2:
        return ''
    
    value = path2.find(path1)
    sub_part = None
    
    if value > -1 and value == 0:
        sub_part = path2[len(path1):]
        
    if sub_part:
        if sub_part.startswith('/'):
            sub_part = sub_part[1:]
        
    return sub_part
    
def get_installed_programs():
    """
    Not working at all, very hacky
    """
    if util.is_windows():
        #this is a hack for now.
        
        import _winreg
        uninstall_dir = 'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
        
        uninstall  = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, uninstall_dir)
        
        try:
            inc = 0
            while 1:
                name, value, type = _winreg.EnumValue(uninstall, inc)
                
                inc += 1
                
        except WindowsError:
            pass
        
        get_files(uninstall_dir)

def get_comments(comment_directory, comment_filename = None):
    """
    Get the comments from a comments.txt file.
    
    Args:
        comment_directory (str): Directory where the comments.txt file lives.
        comment_filename (str): The name of the comment file. By default comments.txt
        
    Returns:
        dict: comment dict, keys are filename, and value is (comment, user) 
    """
    
    if not comment_filename:
        comment_file = join_path(comment_directory, 'comments.txt')
    if comment_filename:
        comment_file = join_path(comment_directory, comment_filename)
    
    if not comment_file:
        return
    
    comments = {}
    
    if is_file(comment_file):
        read = ReadFile(comment_file)
        lines = read.read()
        
        filename = None
        comment = None
        user = None
        
        for line in lines:  

            exec(line)                            
            
            if comment_filename:
                if comment_filename == filename:
                    return comment, user
            
            comments[ filename ] = [ comment, user ]

    return comments

def get_default_directory():
    if util.is_in_maya():
        return join_path(get_user_dir(), 'process_manager')
    if not util.is_in_maya():
        return join_path(get_user_dir(), 'documents/process_manager')

def get_vetala_settings_inst():
    
    vetala_settings = util.get_env('VETALA_SETTINGS')
    
    if not vetala_settings:
        vetala_settings = get_default_directory()
    
    settings = SettingsFile()
    settings.set_directory(vetala_settings)
    
    return settings

  
#---- edit

def fix_slashes(directory):
    """
    Fix slashes in a path so the are all /
    
    Returns:
        str: The new directory path.
    """
    
    if not directory:
        return
    
    directory = directory.replace('\\','/')
    
    
    if not directory.find('https://') > -1:
        directory = directory.replace('//', '/')
    
    return directory

def set_windows_slashes(directory):
    """
    Set all the slashes in a name so they are all \
    
    Returns:
        str: The new directory path.
    """
    
    directory = directory.replace('/', '\\')
    directory = directory.replace('//', '\\')
    
    return directory
    
def join_path(directory1, directory2):
    """
    Append directory2 to the end of directory1
    
    Returns:
        str: The combined directory path.
    """
    if not directory1 or not directory2:
        return
    
    directory1 = fix_slashes( directory1 )
    directory2 = fix_slashes( directory2 )
    
    path = '%s/%s' % (directory1, directory2)
    
    path = fix_slashes( path )
    
    return path

    

def rename(directory, name, make_unique = False):
    """
    Args:
        directory (str): Full path to the directory to rename.
        name (str): The new name.
        make_unique (bool): Wether to add a number to the name to make it unique, if needed.
        
    Retrun
        str: The path of the renamed folder, or False if rename fails. 
    """
    
    basename = get_basename(directory)
    
    if basename == name:
        return
    
    parentpath = get_dirname(directory)
    
    renamepath = join_path(parentpath, name)
    
    if make_unique:
        renamepath = inc_path_name(renamepath)
        
    if exists(renamepath):
        return False

    try:
        
        get_permission(directory)
        
        message = 'rename: ' + directory + '   to   ' + renamepath
        util.show( message)
        
        os.rename(directory, renamepath)
    except:
        time.sleep(.1)
        try:
            os.rename(directory, renamepath)
        except:
            util.error(traceback.format_exc())
            return False
    
    return renamepath

def move(path1, path2):
    """
    Move the folder or file pointed to by path1 under the directory path2
    
    Args:
        path1 (str): File or folder including path.
        path2 (str): Path where path1 should move to.
        
    Returns:
        bool: Wether the move was successful.
    """
    try:
        
        shutil.move(path1, path2)
    except:
        util.warning('Failed to move %s to %s' % (path1, path2))
        return False
    
    return True

def comment(filepath, comment, comment_directory):
    """
    Add a comment to comments.txt
    
    Args:
        filepath (str): Filename and path of the file that is being commented about.
        comment (str): The comment
        comment_directoyr (str): Directory where the comments.txt file should be saved. 
    """
    comment_file = create_file('comments.txt', comment_directory)
    
    version = get_basename(filepath)
    
    user = getpass.getuser()
    
    if not comment:
        comment = '-'
    
    comment_file = WriteFile(comment_file)
    comment_file.set_append(True)
    comment_file.write(['filename = "%s"; comment = "%s"; user = "%s"' % (version, comment, user)])
    comment_file.close_file()
    

def write_lines(filepath, lines, append = False):
    """
    Write a list of text lines to a file. Every entry in the list is a new line.
    
    Args:
        filepath (str): filename and path
        lines (list): A list of text lines. Each entry is a new line.
        append (bool): Wether to append the text or if not replace it.
    
    """
    write_file = WriteFile(filepath)
    write_file.set_append(append)
    write_file.write(lines)
    

def write_replace(filepath, stuff_to_write):
    
    open_file = open(filepath, 'w')
    
    try:
        open_file.write(stuff_to_write)
    except:
        util.warning( 'Could not write: %s' %  stuff_to_write)
    
    open_file.close()
    

#---- create

def create_dir(name, directory = None, make_unique = False):
    """
    Args:
        name (str): The name of the new directory.
        make_unique (bool): Wether to pad the name with a number to make it unique. Only if the name is taken.
        
    Returns:
        str: The folder name with path. False if create_dir failed.
    """
    
    if directory == None:
        full_path = name
    
    if not name:
        full_path = directory
    
    if name and directory:    
        full_path = join_path(directory, name)
         
    if make_unique:
        full_path = inc_path_name(full_path)   
    
    if is_dir(full_path):
        return full_path
       
    try:
        os.makedirs(full_path)
    except:
        return False
    
    get_permission(full_path)
    
    return full_path           
    
def delete_dir(name, directory = None):
    """
    Delete the folder by name in the directory.
    
    Args:
        name (str): The name of the folder to delete.  Name can also be the full path, with no need to supply directory.
        directory (str): The dirpath where the folder lives.
        
    Returns:
        str: The folder that was deleted with path.
    """
    
    util.clean_file_string(name)
    
    full_path = name
    
    if directory:
        full_path = join_path(directory, name)
    
    if not exists(full_path):
            
        util.show('%s was not deleted. It does not exist.' % full_path)
        
        return full_path
    
    try:
        shutil.rmtree(full_path, onerror = delete_read_only_error)
    except:
        util.warning('Could not remove children of path %s' % full_path)  
    
    return full_path

def delete_read_only_error(action, name, exc):
    """
    Helper to delete read only files.
    """
    
    get_permission(name)
    action(name)
    

def refresh_dir(directory):
    """
    Delete everything in the directory.
    """
    
    base_name = get_basename(directory)
    dir_name = get_dirname(directory)
    
    if exists(directory):
        try:
            files = get_files(directory)
        except:
            files = []
        
        if files:
            for filename in files:
                delete_file(filename, directory)
            
        delete_dir(base_name, dir_name)
        
    if not exists(directory):
        create_dir(base_name, dir_name)

def create_file(name, directory = None, make_unique = False):
    """
    Args:
        name (str): The name of the new file. 
        make_unique (bool): Wether to pad the name with a number to make it unique. Only if the name is taken.
        
    Returns:
        str: The filename with path. False if create_dir failed.
    """
    
    if directory == None:
        directory = get_dirname(name)
        name = get_basename(name)
    
    
    name = util.clean_file_string(name)
    full_path = join_path(directory, name)
    
    if make_unique:
        full_path = inc_path_name(full_path)
        
    try:
        open_file = open(full_path, 'a')
        open_file.close()
    except:
        #turn on when troubleshooting
        #util.warning( traceback.format_exc() )
        return False
    
    get_permission(full_path)
    
    return full_path
    
def delete_file(name, directory):
    """
    Delete the file by name in the directory.
    
    Args:
        name (str): The name of the file to delete.
        directory (str): The dirpath where the file lives.
        
    Returns:
        str: The filepath that was deleted.
    """
    
    full_path = join_path(directory, name)
    
    if not is_file(full_path):
        
        util.show('%s was not deleted.' % full_path)
        
        return full_path
    
    try:
        get_permission(full_path)
    except:
        pass
    os.remove(full_path) 
    
    return full_path

def copy_dir(directory, directory_destination, ignore_patterns = []):
    """
    Copy the directory to a new directory.
    
    Args:
        directory (str): The directory to copy with path.
        directory_destination (str): The destination directory.
        ignore_patterns (list): Add txt, py or extensions to ingore them from copying. 
        Eg. if py is added to the ignore patterns list, all *.py files will be ignored from the copy.
        
    Returns:
        str: The destination directory
    """
    if not is_dir(directory):
        return        
    
    if not ignore_patterns:
        shutil.copytree(directory, 
                        directory_destination)        
    
    if ignore_patterns:
        shutil.copytree(directory, 
                        directory_destination, 
                        ignore = shutil.ignore_patterns(ignore_patterns) )
    
    
    
    return directory_destination
    
def copy_file(filepath, filepath_destination):
    """
    Copy the file to a new directory.
    
    Args:
        filepath (str): The file to copy with path.
        filepath_destination (str): The destination directory. 
        
    Returns:
        str: The destination directory
    """
    
    get_permission(filepath)
    
    shutil.copy2(filepath, filepath_destination)
    
    return filepath_destination

    
#---- python

def delete_pyc(python_script):
    """
    Delete the .pyc file the corresponds to the .py file
    """
    
    script_name = get_basename(python_script)
    
    if not python_script.endswith('.py'):
        util.warning('Could not delete pyc file for %s. Be careful not to run this command on files that are not .py extension.' % script_name)
        return
    
    compile_script = python_script + 'c'
            
    if is_file(compile_script):
        
        c_name = get_basename(compile_script)
        c_dir_name = get_dirname(compile_script)
        
        if not c_name.endswith('.pyc'):
            return
        
        delete_file( c_name, c_dir_name)

def remove_sourced_code(code_directory):

    found = []
    keys = sys.modules.keys()
    
    for key in keys:
        
        if not sys.modules.has_key(key):
            continue
        
        if sys.modules[key] and hasattr(sys.modules[key], '__file__'):
            if sys.modules[key].__file__ == code_directory:
                found.append(key)
                break
    
    for key in found:
        if sys.modules.has_key(key):
            sys.modules.pop(key)

def source_python_module(code_directory):
    
    get_permission(code_directory)
    
    try:
        try:
            remove_sourced_code(code_directory)
            
            fin = open(code_directory, 'r')
            import md5
            
            module_inst = imp.load_source(md5.new(code_directory).hexdigest(), code_directory, fin)
            
            return module_inst
        
        except:
            return traceback.format_exc()
        
        finally:
            try: fin.close()
            except: pass
            
    except ImportError:
        traceback.print_exc(file = sys.stderr)
        return None

def load_python_module(module_name, directory):
    """
    Load a module by name and return its instance.
    
    Args:
        module_name (str): The name of the module found in the directory.
        directory (str): The directory path where the module lives.
        
    Returns:
        module instance: The module instance. 
        With the module instance you can access programattically functions and attributes of the modules.
        
    """    
        
    full_path = join_path(directory, module_name)
            
    if not exists(full_path):
        return
    
    split_name = module_name.split('.')
    
    filepath, pathname, description = imp.find_module(split_name[0], 
                                                [directory])
    
    try:
        module = imp.load_module(module_name, 
                                 filepath, 
                                 pathname, 
                                 description)
        
    except:
        filepath.close()
        return traceback.format_exc()
    
    finally:
        if filepath:
            filepath.close()
    
    return module
        
#--- code analysis
        
def get_package_path_from_name(module_name, return_module_path = False):
    
    split_name = module_name.split('.')
    
    if len(split_name) > 1:
        sub_path = string.join(split_name[:-1], '/')
    else:
        sub_path = module_name
    
    paths = sys.path
    
    found_path = None
    
    for path in paths:
    
        test_path = join_path(path, sub_path)
        
        if exists(test_path):
            found_path = path
    
    if not found_path:
        return None
    
    test_path = found_path
    good_path = ''
    
    inc = 0
    
    for name in split_name:
        
        if inc == len(split_name)-1:
            if return_module_path:
                good_path = join_path(good_path, '%s.py' % name)
                break
        
        test_path = join_path(test_path, name)
        
        files = get_files_with_extension('py', test_path)
        
        if not files:
            continue
        
        if '__init__.py' in files:
            good_path = test_path
        
        if not '__init__.py' in files:
            return None
                
        inc += 1
    
    return good_path
    
def get_line_class_map(lines):
    
    for line in lines:
        
        line = str(line)
        
def get_line_imports(lines):
    """
    This needs to be replaced by AST stuff.
    """
    module_dict = {}
    
    for line in lines:
        
        line = str(line)
        
        split_line = line.split()
        split_line_count = len(split_line)
        
        for inc in range(0, split_line_count):
            
            module_prefix = ''
            
            if split_line[inc] == 'import':
                
                if inc > 1:
                    if split_line[inc-2] == 'from':
                        module_prefix = split_line[inc-1]
                
                if inc < split_line_count - 1:
                    
                    module = split_line[inc+1]
                    namespace = module
                    
                    if module_prefix:
                        module = '%s.%s' % (module_prefix, module)
                    
                    module_path = get_package_path_from_name(module, return_module_path=True)
                    
                    module_dict[namespace] = module_path
    
    return module_dict
                    
def get_defined(module_path, name_only = False):
    """
    Get classes and definitions from the text of a module.
    """
    
    file_text = get_file_text(module_path)
    
    functions = []
    classes = []
    
    ast_tree = ast.parse(file_text, 'string', 'exec')
    
    for node in ast_tree.body:
        
        #if node:
            #yield( node.lineno, node.col_offset, 'goobers', 'goo')
        found_args_name = ''
        
        if isinstance(node, ast.FunctionDef):
            
            function_name = node.name
            
            if not name_only:
                function_name = get_ast_function_name_and_args(node)
                
            functions.append( function_name )
            
        if isinstance(node, ast.ClassDef):
            
            class_name = node.name + '()'
            
            for sub_node in node.body:
                if isinstance(sub_node, ast.FunctionDef):
                    
                    if sub_node.name == '__init__':
                        found_args = get_ast_function_args(sub_node)
                        if found_args:
                            found_args_name = string.join(found_args, ',')
                        if not found_args:
                            found_args_name = ''
                        class_name = '%s(%s)' % (node.name, found_args_name)
            
            classes.append(class_name)
            
    classes.sort()
    functions.sort()
            
    defined = classes + functions
            
    return defined

def get_defined_classes(module_path):
    
    file_text = get_file_text(module_path)
    
    defined = []
    defined_dict = {}
    
    if not file_text:
        return None, None
    
    ast_tree = ast.parse(file_text)
    
    for node in ast_tree.body:
        if isinstance(node, ast.ClassDef):
            defined.append(node.name)
            defined_dict[node.name] = node
            
    return defined, defined_dict

#--- ast

def get_ast_function_name_and_args(function_node):
    function_name = function_node.name
    
    found_args = get_ast_function_args(function_node)
    
    if found_args:
        found_args_name = string.join(found_args, ',')
    if not found_args:
        found_args_name = ''
    
    function_name = function_name + '(%s)' % found_args_name
    
    return function_name
        
def get_ast_function_args(function_node):
    
    found_args =[]
    
    if not function_node.args:
        return found_args
                
    defaults = function_node.args.defaults
    
    args = function_node.args.args
    
    args.reverse()
    defaults.reverse()
    inc = 0
    for arg in args:
        
        name = arg.id
        
        if name == 'self':
            continue
        
        default_value = None
        
        if inc < len(defaults):
            default_value = defaults[inc]
        
        if default_value:
            
            value = None
            
            if isinstance(default_value, ast.Str):
                value = "'%s'" % default_value.s
            if isinstance(default_value, ast.Name):
                value = default_value.id
            if isinstance(default_value, ast.Num):
                value = default_value.n
            
            if value:
                found_args.append('%s=%s' % (name, value))
            if not value:
                found_args.append(name)
        if not default_value:
            found_args.append(name)
            
        inc += 1
            
    found_args.reverse()
    
    return found_args


def get_ast_class_sub_functions(module_path, class_name):
    
    defined, defined_dict = get_defined_classes(module_path)

    if not defined:
        return

    if class_name in defined:
        class_node = defined_dict[class_name]
        
        parents = []
        
        bases = class_node.bases
        
        while bases:
            
            temp_bases = bases
            
            find_bases = []
            
            for base in temp_bases:
                
                class_name = None
                
                #there was a case where base was an attribute and had no id...
                #if hasattr(base, 'attr'):
                #    attr_name = base.attr
                
                if hasattr(base, 'id'):
                    class_name = base.id
                    
                if class_name and class_name in defined_dict:
                    parents.append(defined_dict[class_name])
                    
                    sub_bases = parents[-1].bases
                    if sub_bases:
                        find_bases += sub_bases
                            
            bases = find_bases
        
        functions = get_ast_class_members(class_node, parents)
        functions.sort()
        return functions

def get_ast_class_members(class_node, parents = [], skip_list = None):
    
    if skip_list == None:
        skip_list = []
    
    class_functions = []
    
    for node in class_node.body:
        
        if isinstance(node, ast.FunctionDef):
            
            name = node.name
            
            if skip_list:
                if name in skip_list:
                    continue
            
            skip_list.append(name)
            
            stuff = get_ast_function_name_and_args(node)
            
            if stuff.startswith('_'):
                continue
            stuff = stuff.replace('self', '')
            class_functions.append(stuff)
        
    found_parent_functions = []
        
    for parent in parents:
        
        
        parent_functions = get_ast_class_members(parent, skip_list = skip_list)
        found_parent_functions += parent_functions
        
    found_parent_functions += class_functions
        
    return found_parent_functions

def get_ast_assignment(text, line_number, assignment):
    
    text = str(text)
    
    if not text:
        return
    
    ast_tree = None
    
    try:
        ast_tree = ast.parse(text, 'string', 'exec')
    except:
        if not ast_tree:
            return
        
    line_assign_dict = {}
    
    value = None
    
    for node in ast.walk(ast_tree):
        
        if hasattr( node, 'lineno' ):
            current_line_number = node.lineno
            
            if current_line_number <= line_number:
                
                if isinstance(node, ast.ImportFrom):
                    
                    for name in node.names:
                        
                        full_name = node.module + '.' +  name.name
                        
                        value = ['import',full_name]
                        
                        if not name.asname:
                            line_assign_dict[name.name] = value
                        
                        if name.asname:
                            line_assign_dict[name.asname] = ['import', full_name]
                        
                if isinstance(node, ast.Assign):
                    
                    targets = []
                    
                    for target in node.targets:
                        if hasattr(target, 'id'):
                            targets.append( target.id )
                    
                    if hasattr(node.value, 'id'):
                        value = node.value.id
                        
                    if hasattr(node.value, 'func'):
                        value = []
                        if hasattr(node.value.func, 'value'):
                            #there was a case where func didn't have value...
                            if hasattr(node.value.func.value, 'id'):
                                
                                value.append( node.value.func.value.id )
                                value.append( node.value.func.attr )
                        
                    if targets:
                        for target in targets:
                            if value:
                                line_assign_dict[target] = value
            
            if current_line_number > line_number:
                continue
            
    return line_assign_dict

#--- applications

def maya_batch_python_file(python_file_path):

    dirpath = None
    
    if util.is_in_maya():
        dirpath = os.environ['MAYA_LOCATION']
    
    
    
    if not dirpath:
        util.warning('Could not find Maya.')
    

    mayapy_file = 'mayapy.exe'
    shell = False
    
    
    if util.is_linux():
        mayapy_file = 'mayapy'
        
    mayapy_path = '%s/bin/%s' % (dirpath,mayapy_file)
    
    util.show('Opening Maya Batch in directory: %s' % mayapy_path)
    
    command = [mayapy_path, python_file_path]
    if util.is_linux():
        command.insert(0, 'gnome-terminal')
    
    mayapy = subprocess.Popen([mayapy_path, python_file_path], shell = shell)

def launch_maya(version, script = None):
    """
    Needs maya installed. If maya is installed in the default directory, will launch the version specified.
    """
    if sys.platform == 'win32':
        path = 'C:\\Program Files\\Autodesk\\Maya%s\\bin\\maya.exe' % version
        
        if script:
            os.system("start \"maya\" \"%s\" -script \"%s\"" % (path, script))
        if not script:
            os.system("start \"maya\" \"%s\"" % path)
            
def launch_nuke(version, command = None):
    """
    Needs nuke installed. If nuke is installed in default path, it will launch the version specified.
    """
    if sys.platform == 'win32':
        split_version = version.split('v')
        
        nuke_exe_version = split_version[0]
        
        path = 'C:\\Program Files\\Nuke%s\\Nuke%s.exe' % (version, nuke_exe_version)
        
        if not is_file(path):
            new_version = split_version[0] + 'v4' 
            path = 'C:\\Program Files\\Nuke%s\\Nuke%s.exe' % (new_version, nuke_exe_version) 
        
        
        if command:
            os.system('start "nuke" "%s" "%s"' % (path, command))
        if not command:
            os.system('start "nuke" "%s"' % path)
    
def run_ffmpeg():
    """
    Needs ffmpeg installed. 
    """
    path = 'X:\\Tools\\ffmpeg\\bin\\ffmpeg.exe'
    
    os.system('start \"ffmpeg\" \"%s\"' % path)
    
