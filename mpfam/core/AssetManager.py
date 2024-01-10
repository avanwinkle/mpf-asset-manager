from datetime import datetime
import logging
import os
import pickle
import re
import shutil
import sys
import tempfile
from zipfile import ZipFile

# Requires: pysoundfile (via pip)
import soundfile as sf
import mpfam
from mpfam.core.AssetTree import AssetTree
from mpfam.core.RequiredAssets import RequiredAssets

class AssetManager():
    """Master class for managing audio and video assets."""

    def __init__(self, verbose=False):
        """Initialize and find sources."""
        mpfam_path = os.path.abspath(os.path.join(mpfam.__path__[0],
                                                     os.pardir))
        self.machine_configs = None
        self.machine_assets = None
        self.source_media = None
        self._analysis = None
        self._paths = { "source_path": None, "machine_path": None }
        self._config_file_path = os.path.join(mpfam_path, ".mpfam_config")
        self.cache_file_name = "mpfam_cache"

        self.log = logging.getLogger()
        self.log.addHandler(logging.StreamHandler(sys.stdout))
        self.log.setLevel("DEBUG" if verbose else "INFO")
        self._get_config_path("source_path")
        self._get_config_path("machine_path")

        self.conversion_root_folder = os.path.join(self.machine_path, "mpfam_resample")
        self.conversion_originals_folder = os.path.join(self.conversion_root_folder, "originals")
        self.conversion_converted_folder = os.path.join(self.conversion_root_folder, "converted")
        self.converted_media = None

    def _get_cache_path(self):
        return os.path.join(tempfile.gettempdir(), self.cache_file_name)

    def _write_to_cache(self, data):
        with open(self._get_cache_path(), 'wb') as f:
            pickle.dump(data, f)

    def clear_cache(self):
        """Remove cached asset tree, if it exists."""
        try:
            os.remove(self._get_cache_path())
            self.log.info("Cache file removed")
        except Exception as e:
            self.log.warning("Unable to remove cache file: {}".format(e))

    def _load_machine_configs(self, refresh=False):
        if refresh or not self.machine_configs:
            self.log.info("  Loading config files...")
            self.machine_configs = RequiredAssets(self.machine_path, self.log)

    def _load_source_media(self, refresh=False):
        self.log.info("  Looking for source media cache...")
        try:
            with open(self._get_cache_path(), 'rb') as f:
                self.source_media = pickle.load(f)
                stamp = os.path.getmtime(self._get_cache_path())
                self.log.info("    - Cache found from {}".format(
                              datetime.fromtimestamp(stamp).strftime("%b %d %Y %H:%M:%S")))
        except Exception as e:
            self.log.warning("    - Could not load cache file:\n        {}".format(e))

        if refresh or not self.source_media:
            self.log.info("  Loading media files from source folder...")
            self.source_media = AssetTree(self._paths["source_path"], self.log)

            self.log.info("   - creating cache of source media...")
            self._write_to_cache(self.source_media)

        if refresh or not self.converted_media:
            try:
                os.stat(self.conversion_converted_folder)
                self.log.info("  Loading converted media files...")
                self.converted_media = AssetTree(self.conversion_converted_folder, self.log)
            except(FileNotFoundError):
                self.log.info("  No converted media files found.")

    def _load_machine_assets(self, refresh=False):
        if refresh or not self.machine_assets:
            self.log.info("  Loading assets from machine folder {}...".format(self._paths["machine_path"]))
            self.machine_assets = AssetTree(self._paths["machine_path"], self.log, paths_to_exclude=[
                self.exports_path, self.conversion_originals_folder, self.conversion_converted_folder])

    def refresh(self):
        """Re-traverse the configs and asset folders."""
        self._load_machine_configs(refresh=True)
        self._load_source_media(refresh=True)
        self._load_machine_assets(refresh=True)

    def _set_config_path(self, path_type):
        """Define the path to look for media assets."""
        target = "media source" if path_type == "source_path" else "MPF machine"
        # Use print instead of log because this requires explicit user input and shouldn't be muted
        print("Set path to your {} folder:".format(target))
        rawpath = input(">> ").strip()
        # Store full paths, not relative
        if "~" in rawpath:
            root = os.environ.get('HOME') or os.environ.get('USERPROFILE')
            if not root:
                raise OSError("Unable to find home path in environment.")
            self._paths[path_type] = rawpath.replace("~", root)
        else:
            self._paths[path_type] = rawpath
        with open(self._config_file_path, 'wb') as f:
            config = {
                "source_path": self._paths["source_path"],
                "machine_path": self._paths["machine_path"]
            }
            pickle.dump(config, f)
        self.clear_cache()
        return self._paths[path_type]

    def _get_config_path(self, path_type):
        if not self._paths[path_type]:
            try:
                with open(self._config_file_path, 'rb') as f:
                    config = pickle.load(f)
                    self._paths["source_path"] = config.get("source_path")
                    self._paths["machine_path"] = config.get("machine_path")
                if not self._paths[path_type] or not os.stat(self._paths[path_type]):
                    raise FileNotFoundError()
            except(FileNotFoundError):
                self.log.info("Unable to read {}.".format(path_type))
                self._set_config_path(path_type)
            try:
                os.stat(self._paths[path_type])
            except(FileNotFoundError):
                target = "source media" if path_type == "source_path" else "MPF machine"
                self.log.info("MPF Asset Manager requires a path to your {} folder.".format(target))
                self.log.info("Path not found: '{}'\nExiting...".format(self._paths[path_type]))
                sys.exit()
        return self._paths[path_type]

    @property
    def source_path(self):
        return self._paths["source_path"]

    def set_source_path(self):
        return self._set_config_path("source_path")

    @property
    def machine_path(self):
        return self._paths["machine_path"]
    @property
    def exports_path(self):
        return os.path.join(self._paths["machine_path"], "mpfam_exports")

    def parse_machine_assets(self, write_mode=False, force_update=False, export_only=False):
        """Main method for mapping assets to config files and updating (if write-mode)."""
        self.log.info("\nMPF Asset Manager [{}]".format(
            "EXPORT ONLY" if export_only else "WRITE MODE" if write_mode else "READ-ONLY"))
        self.log.info("----------------------------------------------------")
        self.log.info("Parsing machine configs, assets, and source media:")
        self._load_machine_configs()
        self._load_machine_assets()
        self._load_source_media()
        matchedfilescount = 0

        self._analysis = {
            'found': [],
            'missing': [],
            'available': {},
            'unavailable': [],
            'misplaced': {},  # Key: expected file path; Value: current/wrong file path
            'orphaned': [],
            'duplicated': [],
            'sounds': {}  # Key: sound file name; Value: sound object
        }

        self.log.info("\nComparing current file tree to config assets:")

        dupes = self.machine_assets.get_duplicates()
        # First, look through all the files that exist in the mode folders to find orphaned, misplaced, and duplicate
        for __idx, filename in enumerate(self.machine_assets.get_files()):
            filepath = self.machine_assets.get_file_path(filename)
            mode = self.machine_configs.find_requiring_mode(filename)
            # If this file is not required by any configs
            if not mode:
                self._analysis['orphaned'].append(filepath)
            else:
                expectedpath = "{}/modes/{}/sounds/{}/{}".format(
                    self.machine_path,
                    self.machine_configs.get_mode_parent(mode.name),
                    mode.find_track_for_sound(filename),
                    filename
                    )
                if filepath != expectedpath:
                    self.log.info("{} is in the wrong place. Expected {}".format(filepath, expectedpath))
                    self._analysis['misplaced'][expectedpath] = filepath
                elif filename in dupes:
                    # The expected path is for the ONE mode that legit requires this file
                    for dupepath in dupes[filename]:
                        if expectedpath != dupepath and dupepath not in self._analysis['duplicated']:
                            self._analysis['duplicated'].append(dupepath)
                else:
                    matchedfilescount += 1
                    self.log.debug("Matched {} in node {}".format(filename, mode.name))

        allconfigs = self.machine_configs.get_all_configs()

        for mode, modesounds in allconfigs.items():
            for track, sounds in modesounds.by_track().items():
                for sound in sounds:
                    if sound in self._analysis['sounds']:
                        self.log.error("ERROR: Sound file '{}' in mode {} also exists in mode {}".format(
                              sound, mode, self._analysis['sounds'][sound]['mode']))
                        return
                    modepath = "{}/modes/{}/sounds/{}/".format(
                        self.machine_path,
                        self.machine_configs.get_mode_parent(mode),
                        track
                    )
                    sourcepath = None
                    exists = False
                    expectedpath = "{}{}".format(modepath, sound)
                    try:
                        # To force an update, don't "find" any files
                        if force_update:
                            raise FileNotFoundError
                        exists = os.stat(expectedpath)
                        self._analysis['found'].append(sound)
                    except(FileNotFoundError):
                        # Is this file misplaced? Are we planning on moving it?
                        if expectedpath in self._analysis['misplaced']:
                            pass
                        else:
                            self._analysis['missing'].append(sound)
                            try:
                                sourcepath = self.source_media.get_file_path(sound)
                                self._analysis['available'][expectedpath] = sourcepath
                            except(ValueError):
                                self._analysis['unavailable'].append(sound)

                    self._analysis['sounds'][sound] = {"mode": mode,
                                                       "modepath": modepath,
                                                       "sourcepath": sourcepath,
                                                       "exists": exists}

        self.log.info("  Found {} assets defined across {} config files.".format(
                      len(self._analysis['sounds']), len(allconfigs)))
        self.log.info("   - {} files correctly accounted for".format(
                      len(self._analysis['found'])))
        if self._analysis['misplaced']:
            self.log.info("   - {} misplaced files{}".format(
                          len(self._analysis['misplaced']), " will be moved" if write_mode else ""))
        if self._analysis['duplicated']:
            self.log.info("   - {} duplicate files{}".format(
                          len(self._analysis['duplicated']), " will be removed" if write_mode else ""))
        if self._analysis['orphaned']:
            self.log.info("   - {} orphaned files{}".format(
                          len(self._analysis['orphaned']), " will be removed" if write_mode else ""))
        if self._analysis['available']:
            self.log.info("   - {} missing files available {}".format(
                          len(self._analysis['available']), "and copied" if write_mode else "for copy"))
            for filename, sourcepath in self._analysis['available'].items():
                self.log.debug("    : {} -> {}".format(sourcepath, filename))
        if self._analysis['unavailable']:
            self.log.info("   - {} files missing and unavailable".format(
                          len(self._analysis['unavailable'])))

    def cleanup_machine_assets(self, write_mode=False, force_update=False):
        """Method to actually move/copy/delete asset files from MPF mode folders."""
        if not self._analysis:
            self.parse_machine_assets(write_mode=write_mode, force_update=force_update)

        files_changed = 0

        if self._analysis['orphaned']:
            self.log.info(("Removing {} orphaned files:" if write_mode else "{} orphaned files to remove").format(
                          len(self._analysis["orphaned"])))
            for orphan in self._analysis['orphaned']:
                self.log.info(" - {}".format(orphan))
                if write_mode:
                    os.remove(orphan)
                    files_changed += 1
        if self._analysis['duplicated']:
            self.log.info(("Removing {} duplicate files..." if write_mode else "{} duplicate files to remove").format(
                          len(self._analysis["duplicated"])))
            for orphan in self._analysis['duplicated']:
                self.log.info(" - {}".format(orphan))
                if write_mode:
                    os.remove(orphan)
                    files_changed += 1
        if self._analysis['misplaced']:
            self.log.info(("Moving {} misplaced files..." if write_mode else "{} misplaced files will be moved").format(
                          len(self._analysis["misplaced"])))
            for expectedpath, filepath in self._analysis['misplaced'].items():
                self.log.info(" - {} -> {}".format(filepath, expectedpath))
                if write_mode:
                    os.makedirs(expectedpath.rsplit("/", 1)[0], mode=0o755, exist_ok=True)
                    os.rename(filepath, expectedpath)
                    files_changed += 1
        if self._analysis['available']:
            self.log.info(("Copying {} new files..." if write_mode else "{} new files will be copied").format(
                          len(self._analysis["available"])))
            original_umask = os.umask(0)
            for idx, availitem in enumerate(self._analysis['available'].items()):
                dst = availitem[0]
                src = availitem[1]
                self.log.debug(" - {}/{}: {} -> {}".format(idx + 1, len(self._analysis['available']), src, dst))
                # Ensure the target directory exists
                if write_mode:
                    os.makedirs(dst.rsplit("/", 1)[0], mode=0o755, exist_ok=True)
                    shutil.copy2(src, dst)
                    files_changed += 1
            os.umask(original_umask)

        if self._analysis['unavailable']:
            self.log.info("\nWARNING: {} file{} could not be found:".format(
                          len(self._analysis['unavailable']), "" if len(self._analysis['unavailable']) == 1 else "s"))
            for filename in self._analysis['unavailable']:
                self.log.warning(" - {} ({})".format(filename, self._analysis['sounds'][filename]['mode']))

        # Any previous analysis is no longer valid
        if write_mode:
            videocount = self._copy_video_assets(export=False)
            self._analysis = None
            self.log.info("\nMachine copy and cleanup complete! {} audio file{} and {} video file{} changed.".format(
                files_changed or "No",
                "" if files_changed == 1 else "s",
                videocount or "no",
                "" if videocount == 1 else "s"))
        else:
            self.log.info("\nSimulation complete, no files changed.")

    def export_machine_assets(self, saveAsZip=False):
        """Batch output all assets within MPF folders to a single folder for compression/backup."""
        if not self._analysis:
            self.parse_machine_assets(export_only=True)

        count = 0
        size = 0
        zipFile = None
        if saveAsZip:
            zipfilename = "{}{}".format(self.exports_path, ".zip")
            zipFile = ZipFile(zipfilename, mode='w')
        else:
            os.makedirs(self.exports_path, mode=0o755, exist_ok=True)

        for filename in self._analysis['found']:
            sound = self._analysis['sounds'][filename]
            path = "{}{}".format(sound['modepath'], filename)
            if saveAsZip:
                zipFile.write(path, filename)
            else:
                shutil.copy2(path, "{}/{}".format(self.exports_path, filename))
            size += sound['exists'].st_size
            count += 1

        videocount = self._copy_video_assets(export=True, zipFile=zipFile)

        # Dump the readme too, to have instructions handy on the in-cabinet controller
        readme_filename = "_README.txt"
        readme_text = """
Exported by MPF Asset Manager (mpfam). To populate
these files into your machine's mode folders, run:

    mpfam update

and set your media source folder to this directory.

If you don't have mpfam on this computer, you can
install it via:

    pip install mpf-am

For more information, visit
https://github.com/avanwinkle/mpf-asset-manager
        """

        if saveAsZip:
            zipFile.writestr(readme_filename, readme_text)
        else:
            text = open(os.path.join(self.exports_path, readme_filename), mode="w")
            text.write(readme_text)
            text.close()

        self.log.info("\nExport complete: {} audio files, {} MB (plus {} videos)".format(
                      count, round(size / 100000) / 10, videocount))

    def analyze_sample_rates(self, mode=None):
        """Assess all sound files to determine sample rates."""
        if not self._analysis:
            write_mode = mode == "import"
            export_only = mode == "export"
            self.parse_machine_assets(write_mode=write_mode, export_only=export_only)
        if mode == "export":
            os.makedirs(self.conversion_originals_folder, mode=0o755, exist_ok=True)
            os.makedirs(self.conversion_converted_folder, mode=0o755, exist_ok=True)

        rates = {}
        mostCommonRate = None
        leastCommonFiles = []

        self.log.info("\nAnalyzing sample rates for {} files...".format(len(self._analysis['sounds'])))

        if mode != "import":
            for filename in self._analysis['found']:
                sound = self._analysis['sounds'][filename]
                path = "{}{}".format(sound['modepath'], filename)
                data, samplerate = sf.read(path)
                if samplerate not in rates:
                    rates[samplerate] = {"count": 0, "files": []}
                rates[samplerate]["count"] += 1
                rates[samplerate]["files"].append(path)

            self.log.info("\nAnalysis complete:")
            for rank, rankedRate in enumerate(sorted(rates.keys(), key=lambda x: rates[x]["count"], reverse=True)):
                self.log.info("  {}: {} files".format(rankedRate, rates[rankedRate]["count"]))
                if rank == 0:
                    mostCommonRate = rankedRate
                else:
                    leastCommonFiles += rates[rankedRate]["files"]

        if mode == "export":
            text = open("{}/RatesAnalysis.txt".format(self.conversion_root_folder), mode="w")
            text.write("\n".join(leastCommonFiles))
            text.close()
            self.log.info("\n{} files are not {} Hz, see mpfam_resample/RatesAnalysis.txt for details.".format(
                len(leastCommonFiles), mostCommonRate))

            for filename in leastCommonFiles:
                shutil.copy2(filename, "{}/{}".format(self.conversion_originals_folder, filename.split("/").pop()))
            self.log.info("\n - Those files have been copied to {}\n".format(self.conversion_originals_folder))
            self.log.info(" - If you batch process them into {},\n".format(self.conversion_converted_folder) +
                          "   MPF Asset Manager will import them to their correct mode folders when you call:\n\n" +
                          "      mpfam resample --import")

        elif mode == "import":
            self.log.info("\nCopying converted files back into mode folders...")

            # It's possible that no converted files existed when MPFAM started.
            self.converted_media = None
            self._load_source_media()
            count = 0
            for filename in self.converted_media.get_files():
                source_path = "{}/{}".format(self.conversion_converted_folder, filename)
                sound = self._analysis['sounds'][filename]
                dest_path = "{}{}".format(sound['modepath'], filename)

                self.log.debug("{} -> {}".format(source_path, dest_path))
                # Make a backup of the original
                shutil.move(dest_path, re.sub(r'\.([A-Za-z0-9]+)$', '.original.\g<1>', dest_path))
                shutil.copy2(source_path, dest_path)
                count += 1
            self.log.info("Successfully copied {} converted files into their mode folders".format(count))

    def _copy_video_assets(self, export=True, zipFile=None):
        videoroot = os.path.join(self.machine_path, "videos")
        exportroot = os.path.join(self.source_path, "videos")
        count = 0

        if export:
            src = videoroot
            dst = exportroot
        else:
            src = exportroot
            dst = videoroot

        # Ensure the destination folder exists
        if not zipFile:
            os.makedirs(dst, mode=0o755, exist_ok=True)
        for path, dirs, files in os.walk(src):
            for filename in files:
                # Ignore hidden files
                if filename[0] == ".":
                    continue
                target = os.path.join(dst, filename)
                # Always copy on export, but not import
                do_copy = export
                try:
                    os.stat(target)
                except(FileNotFoundError):
                    do_copy = True

                if do_copy:
                    srcfilepath = os.path.join(src, filename)
                    if zipFile:
                        zipFile.write(srcfilepath, os.path.join("videos", filename))
                    else:
                        shutil.copy2(srcfilepath, target)
                    count += 1
        return count
