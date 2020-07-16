from mpf.core.utility_functions import Util

class ModeAssets(object):
    """Class to parse a mode's config file and find asset file definitions."""

    def __init__(self, mode_name=None):
        """Initialize."""
        self._dict = {}
        self._tracks = []
        self._files = []
        self._pool_tracks = {}
        self.name = mode_name

    def parse_config(self, mode_config):
        """Parse a yaml config file and create mappings for required assets."""
        if not mode_config.get('sounds'):
            return self

        for sound_pool in mode_config.get('sound_pools', {}).values():
            for soundname in Util.string_to_list(sound_pool['sounds']):
                if soundname in self._pool_tracks and self._pool_tracks[soundname] != sound_pool['track']:
                    print("ERROR: Sound {} exists in multiple pools/tracks in config {}".format(soundname, self.name))
                    return
                try:
                    self._pool_tracks[soundname] = sound_pool['track']
                except KeyError:
                    raise AttributeError("Sound pool '{}'' has no track".format(soundname))

        for soundname, sound in mode_config['sounds'].items():
            self._add_sound(sound, pool_track=self._pool_tracks.get(soundname))

    def _add_sound(self, sound_dict, pool_track=None):
        """Add a sound mapping for an asset file identified in the config."""
        filename = sound_dict['file']
        # If a track is explicitly defined, use it
        if 'track' in sound_dict and sound_dict['track']:
            trackname = sound_dict['track']
        # If this sound is in a sound pool with a track, use that
        elif pool_track:
            trackname = pool_track
        # Mass Effect 2 Pinball defaults:
        elif filename.startswith('en_us_'):
            trackname = 'voice'
        elif filename.startswith('mus_'):
            trackname = 'music'
        else:
            trackname = 'unknown'

        self._add_track(trackname)
        self._files.append(filename)
        self._dict[trackname].append(filename)

    def find_track_for_sound(self, filename):
        """Identify the track requested for the filename (to know its folder)."""
        for trackname, sounds in self._dict.items():
            if filename in sounds:
                return trackname

    def _add_track(self, trackname):
        if trackname not in self._tracks:
            self._tracks.append(trackname)
            self._dict[trackname] = []

    def all(self):
        """Return all the files in the config."""
        return self._files

    def by_track(self):
        """Return all the files mapped by their track name."""
        return self._dict

    def __repr__(self):
        """String repr."""
        return "<ModeSounds '{}': {} files>".format(self.name, len(self))

    def __len__(self):
        """Length is the number of files."""
        return len(self._files)

