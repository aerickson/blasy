import os
import configparser
from pathlib import Path

class PluginFileLocator:
    """
    Locate plugins in the filesystem by looking for .plugin files and extracting info.
    """

    def __init__(self, plugin_info_ext="plugin"):
        self.plugin_info_ext = plugin_info_ext
        self.plugin_places = []
        self.recursive = True

    def setPluginPlaces(self, directories_list):
        if isinstance(directories_list, str):
            raise ValueError("Expected a list of directories, not a string")
        self.plugin_places = directories_list

    def disableRecursiveScan(self):
        self.recursive = False

    def locatePlugins(self):
        """
        Walk through plugin places and look for plugins.
        Returns a list of (info_file_path, plugin_module_path, info_dict)
        """
        candidates = []
        for directory in map(os.path.abspath, self.plugin_places):
            if not os.path.isdir(directory):
                continue
            if self.recursive:
                walker = os.walk(directory)
            else:
                walker = [(directory, [], os.listdir(directory))]
            for dirpath, _, filenames in walker:
                for filename in filenames:
                    if filename.endswith(f".{self.plugin_info_ext}"):
                        info_file_path = os.path.join(dirpath, filename)
                        info_dict = self._parse_plugin_info(info_file_path)
                        if not info_dict:
                            continue
                        module_path = os.path.join(dirpath, info_dict.get("module", ""))
                        candidates.append((info_file_path, module_path, info_dict))
        return candidates

    def _parse_plugin_info(self, info_file_path):
        parser = configparser.ConfigParser()
        try:
            parser.read(info_file_path)
        except Exception:
            return None
        if not parser.has_section("Core"):
            return None
        info = {}
        for key in parser["Core"]:
            info[key.lower()] = parser["Core"][key]
        # Optionally add documentation fields
        if parser.has_section("Documentation"):
            for key in parser["Documentation"]:
                info[key.lower()] = parser["Documentation"][key]
        return info

class PluginFileAnalyzerWithInfoFile:
    """
    Analyzer for plugins described by a textual description file (INI format).
    """

    def __init__(self, extensions="plugin"):
        # Accept a string or tuple of extensions
        if isinstance(extensions, str):
            extensions = (extensions,)
        self.extensions = tuple(ext.lstrip('.') for ext in extensions)

    def is_valid_plugin(self, filename):
        """
        Check if the file has a valid plugin info file extension.
        """
        return any(filename.endswith(f".{ext}") for ext in self.extensions)

    def get_infos_dict_from_plugin(self, dirpath, filename):
        """
        Extract plugin info from the info file.
        Returns a dict with at least 'name' and 'module'.
        """
        info_file_path = os.path.join(dirpath, filename)
        parser = configparser.ConfigParser()
        try:
            parser.read(info_file_path)
        except Exception:
            return None

        if not parser.has_section("Core"):
            return None

        info = {}
        for key in parser["Core"]:
            info[key.lower()] = parser["Core"][key]

        # Optionally add documentation fields
        if parser.has_section("Documentation"):
            for key in parser["Documentation"]:
                info[key.lower()] = parser["Documentation"][key]

        # Ensure required fields
        if "name" not in info or "module" not in info:
            return None

        # Add the path to the module
        info["path"] = os.path.join(dirpath, info["module"])
        return info