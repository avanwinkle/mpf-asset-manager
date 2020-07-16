"""Sound asset manager for MPF."""
from classes.AssetManager import AssetManager

from datetime import datetime
import io
import logging
import os
import pickle
import re
import sys
import tempfile

def interactive(manager):
    """Interactive shell mode."""
    running = True
    while running:
        print("""
MPF Asset Manager
===============================
    Machine Folder: {}
    Source Folder:  {}
===============================

    1. Update assets (copy & prune)

    2. Analyze machine and audio

    3. Set media source folder

    4. Refresh configs and files

    5. Clear cached media source tree

    6. Export assets

    7. Analyze sample rates (takes time)

    8. Force refresh of all files

    0. Exit this program
""".format(manager.machine_path, manager.source_path))
        selection = input(">> ")
        if selection == "1" or selection == "2":
            write_mode = selection == "1"
            manager.cleanup_machine_assets(write_mode=write_mode)
        elif selection == "3":
            manager.set_source_path()
        elif selection == "4":
            manager.refresh()
        elif selection == "5":
            manager.clear_cache()
        elif selection == "6":
            manager.export_machine_assets()
        elif selection == "7":
            manager.analyze_sample_rates()
        elif selection == "8":
            manager.cleanup_machine_assets(write_mode=True, force_update=True)
        elif selection == "0" or not selection:
            running = False


def main():
    """Primary method: do something."""
    args = sys.argv[1:]
    verbose = "-v" in args
    write_mode = "-w" in args

    manager = AssetManager(verbose=verbose)

    if not manager.source_path:
        print("ERROR: Source media not found. Exiting.")
        return
    elif not manager.machine_path:
        print("Error: Machine path not found, Exiting.")
        return

    if not args or args[0] == "-i":
        interactive(manager)
        return

    if args:
        starttime = datetime.now()
        if args[0] == "parse":
            manager.parse_machine_assets(write_mode=write_mode)
        elif args[0] == "copy":
            manager.cleanup_machine_assets(write_mode=write_mode)
        elif args[0] == "update":
            manager.cleanup_machine_assets(write_mode=True)
        elif args[0] == "clear":
            manager.clear_cache()
        elif args[0] == "export":
            manager.export_machine_assets()
        elif args[0] == "convert":
            mode = "export" if "--export" in args else "import" if "--import" in args else None
            manager.analyze_sample_rates(mode=mode)
        endtime = datetime.now()
        manager.log.info("\nOperation complete in {:.2f} seconds".format((endtime - starttime).total_seconds()))

        return

    print("""
---Mission Pinball Asset File Script---

Use this script to copy audio files from your source media folder into the
corresponding MPF Pinball mode folders.

Options:
    update - Copy all audio files referenced in configs from the source folder
                     to the appropriate modes/(name)/sounds/(track) folders, and remove
                     all audio files not referenced in config files

    parse -  Print analysis of config files and source folder with summary of
                     files to move/copy/remove

    export - Export the asset files from the MPF mode folders to a single folder,
                     for quick setup on a machine without the complete Mass Effect 2
                     extraction folder (i.e. the in-cabinet pinball controller).

    clear -  Clear cached directory trees (for use when source media files change)

Params:
    path_to_sounds - Path to the folder containing all the source audio files

Flags:
    -v    - Verbose mode
    -w    - Write mode

Usage:
>> python mpfam.py [copy|parse|clear] [<path_to_sounds>] [-v|-w]
""")


if __name__ == "__main__":
    main()
