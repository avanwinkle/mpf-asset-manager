from mpf.file_interfaces.yaml_roundtrip import YamlRoundtrip

from mpfam.core.ModeAssets import ModeAssets

import io
import os

class RequiredAssets(object):
    """Class object to parse, return, and query mode config files."""

    def __init__(self, machine_path, log):
        """Initialize: create config mappings and walk config files."""
        self._allconfigs = {}  # Key: mode/config name, Value: ModeSounds object
        self._childconfigs = {}  # Key: mode/config name, Value: ModeSounds object
        self._sounds_by_filename = {}  # Key: array of filenames, Value: ModeSounds object
        self._source = None
        self._allsoundfiles = []
        # Track modes that are imported into parent modes, so we don't scan them twice
        self._configparents = {}  # Key: child config name, Value: parent config

        loader_roundtrip = YamlRoundtrip()
        for path, __dirs, files in os.walk(os.path.join(machine_path, 'modes')):
            for filename in files:
                if filename.endswith('.yaml'):
                    configfilename = filename[:-5]
                    with io.open('{}/{}'.format(path, filename), 'r', encoding='utf-8') as f:
                        source = f.read()
                    conf = loader_roundtrip.process(source)
                    sounds = ModeAssets(configfilename, log)
                    sounds.parse_config(conf)
                    if len(sounds) > 0:
                        self._allconfigs[configfilename] = sounds

                    for importedconfigname in conf.get('config', []):
                        self._configparents[importedconfigname[:-5]] = configfilename

        # Wait until all configs have been imported, because load order is unpredictable
        for configfilename in self._configparents:
            if configfilename in self._allconfigs:
                self._childconfigs[configfilename] = self._allconfigs[configfilename]
                # TODO: Allow the sounds to exist in their child modes and zip up to parents later
                # Commenting this line after the YamlParser change stopped importing child yaml sounds
                # del self._allconfigs[configfilename]

    def get_all_configs(self):
        """Return all configs mapped by the MPF machine project."""
        return self._allconfigs

    def get_mode_parent(self, modename):
        """If the mode is a child mode, return the parents path."""
        name = modename
        while name in self._configparents:
            name = self._configparents[name]
        return name

    def find_requiring_mode(self, filename):
        """For a given asset filename, find the mode that includes that filename in its config file."""
        # So we only have to do this once, make all of the sound files in a Mode into an array key
        if not self._sounds_by_filename:
            for sounds in self._allconfigs.values():
                for soundname in sounds.all():
                    self._sounds_by_filename[soundname] = sounds
                    self._allsoundfiles.append(soundname)

        # Easiest check: is this file required _anywhere_ ?
        if filename not in self._allsoundfiles:
            return None

        # Next check: find which mode requires it
        for filelist in self._sounds_by_filename:
            if filename in filelist:
                return self._sounds_by_filename[filelist]

    def __len__(self):
        """Get the length of config files."""
        return len(self._allconfigs)
