"""Sound asset manager for MPF."""
from mpfam.core import AssetManager

from datetime import datetime
import sys

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
        7e - export uncommon sample files
        7i - import converted sample files

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
        elif selection == "7e":
            manager.analyze_sample_rates(mode="export")
        elif selection == "7i":
            manager.analyze_sample_rates(mode="import")
        elif selection == "8":
            manager.cleanup_machine_assets(write_mode=True, force_update=True)
        elif selection == "0" or not selection:
            running = False


def launch():
    """Primary method: do something."""
    args = sys.argv[1:]
    verbose = "-v" in args
    write_mode = "-w" in args
    export_zip = "-z" in args

    manager = AssetManager.AssetManager(verbose=verbose)

    if not manager.source_path:
        print("ERROR: Source media not found. Exiting.")
        return
    elif not manager.machine_path:
        print("Error: Machine path not found, Exiting.")
        return

    if not args or args[0] == "-i":
        interactive(manager)
        return

    if args[0] == "help" or "-h" in args[0]:
        args = None

    valid_arg = None
    if args:
        starttime = datetime.now()
        valid_arg = True
        if args[0] == "analyze" or args[0] == "analyse":
            manager.parse_machine_assets(write_mode=write_mode)
        elif args[0] == "sim" or args[0] == "simulate":
            manager.cleanup_machine_assets(write_mode=False)
        elif args[0] == "update":
            manager.cleanup_machine_assets(write_mode=True)
        elif args[0] == "clear":
            manager.clear_cache()
        elif args[0] == "export":
            manager.export_machine_assets(saveAsZip=export_zip)
        elif args[0] == "resample" or args[0] == "sample":
            mode = "export" if "--export" in args else "import" if "--import" in args else None
            manager.analyze_sample_rates(mode=mode)
        else:
            valid_arg = False

        if valid_arg:
            endtime = datetime.now()
            manager.log.info("\nOperation complete in {:.2f} seconds".format((endtime - starttime).total_seconds()))
            return

    print("""
---Mission Pinball Asset File Script---

Use this script to copy audio files from your source media folder into the
corresponding MPF Pinball mode folders, move files from old mode folders to
new ones, and export all assets from the machine folder.

Options:
    sim -  Print analysis of config files and source folder with summary of
                    files to move/copy/remove. No changes are made.

    update - Copy all audio files referenced in configs from the source folder
                    to the appropriate modes/(name)/sounds/(track) folders,
                    and remove all audio files not referenced in config files

    export - Export the asset files from the MPF mode folders to a single folder
                    for easy transfer to a machine without the complete source
                    asset folder.

    clear - Clear cached source media tree. Necessary if the source media files
                    have changed.

    resample - Inspect all audio files and generate a report of the sample rates.
                    Useful to determine ideal target sample rate for conversion
                    of all audio assets, which improves MPF performance.

        Optional arguments for resample:
        --------------------------------
        --export:   Create a new folder with copies of all assets that are not
                    the most common sample rate. Ideal for running a batch
                    conversion process in the audio program of your choice.

        --import:   Replace existing machine assets with the normalized assets
                    from the batch conversion process. All original asset files
                    are are preserved with an \".original\" extension.

    clear -  Clear cached directory trees (use when source media files change)

Flags:
    -v    - Verbose mode
    -z    - Save as zip file (when exporting)
Usage:
>> mpfam [sim|update|export|clear|resample] [-v]
""")

    if valid_arg is False:
        print("ERROR: Unknown command '{}'.".format(args[0]))
