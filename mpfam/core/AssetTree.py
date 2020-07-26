import os
import re

SOUND_REGEX = 'ogg|wav|mp3|flac|aac'

class AssetTree(object):
    """Class to traverse source asset tree and return file information for assets in the MPF machine and mode folders."""

    def __init__(self, fileroot, log, paths_to_exclude=[]):
        """Initialize: traverse the asset files path and map asset filenames."""
        # Most efficient way: two arrays in parallel?
        self._soundfiles, self._soundpaths = [], []
        self._originalfiles, self._originalpaths = [], []
        for path, __dirs, files in os.walk(fileroot):
            # Don't look in the exports folder!
            if path in paths_to_exclude:
                continue
            for filename in files:
                if re.search(r'\.(' + SOUND_REGEX + ')$', filename):
                    if re.search(r'\.original\.(' + SOUND_REGEX + ')$', filename):
                        self._originalfiles.append(filename)
                        self._originalpaths.append(path)
                    else:
                        if filename in self._soundfiles:
                            log.info("File {} found in {} but also in {}".format(
                                  filename, path, self._soundpaths[self._soundfiles.index(filename)]))
                        self._soundfiles.append(filename)
                        self._soundpaths.append(path)

    def get_file_path(self, filename):
        """Return the path of the first occurrance of a filename."""
        idx = self._soundfiles.index(filename)
        return os.path.join(self._soundpaths[idx], filename)

    def get_duplicates(self):
        """Return a mapping of assets with filenames appearing in multiple mode folders."""
        dupes = {}
        for idx, filename in enumerate(self._soundfiles):
            if self._soundfiles.index(filename) != idx:
                if filename not in dupes:
                    # Add the first instance from before we knew it was a dupe
                    dupes[filename] = [os.path.join(self._soundpaths[self._soundfiles.index(filename)], filename)]
                dupes[filename].append(os.path.join(self._soundpaths[idx], filename))
        return dupes

    def get_files(self):
        """Return the mapping of asset files to their containing mode folders."""
        return self._soundfiles

