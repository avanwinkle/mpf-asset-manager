MPF Asset Sound Manager
=======================

Asset Manager automates the population of media assets into the mode folders of
a Mission Pinball game. It will copy new files, reorganized moved files, cleanup
unused files, and warn of missing and duplicated files.

### Purpose
MPF is designed to store assets in subfolders of the modes that use them. 
Changing MPF configs to move assets to another mode requires the asset files
to be moved as well—which can be a tedious process.

MPF Asset Manager automates the process by reading the MPF config files, 
mapping all the assets in the project folder, and moving the assets into the
correct mode folders. It will also delete assets that are no longer referenced,
and warn the user if any config files reference assets that can't be found.

### Media Source Folders
For pinball machines pulling media assets from an external source, e.g. a video
game rip, MPF Asset Manager allows the game designer to reference asset files
in the external source folder. MPF Asset Manager will copy the asset files from
the source folder to the corresponding mode folders, and can constantly update
their locations as the configs change.

### Export and Import
Assets can take a lot of hard disk space, and are often excluded from code
repositories. When moving a pinball game from one computer to another, cloning
the repo is the optimal method but that leaves the new machine without any
assets. 

MPF Asset Manager can export all of a game's asset files (from every subfolder)
into a single folder that can be copied to the new machine. On the new machine,
MPF Asset Manager can user that folder as the media source folder and instantly
copy the assets into the correct mode subfolders.


Usage:
-------------

1. MPF Asset Manager is run with the following command:
    ```mpfam```

2. If you have not run Asset Manager before you will be prompted to enter
    the location of your source media folder. Asset Manager remembers the
    path, so it's recommended to choose a permanent location.

2. If you have not run Asset Manager before, you will also be prompted to
    enter the location of your MPF project (where you run `mpf` from).

That's it!


Interactive Mode:
-----------------

You can run Asset Manager interactively with the basic command:
    ```mpfam```

Interactive mode contains the following features:

1. Update Assets
> The default function of Sound Manager. Will copy and move media files,
> remove unused files, and report any missing/duplicate assets.

2. Analyze machine and audio
> Read-only behavior. Performs the same analysis as the update routine,
> but does not write or delete any files.

3. Set media source folder
> Set or change the folder containing the Mass Effect 2 extracted audio
> files.

4. Refresh configs and files
> Reloads the MPF modes and configurations. Useful if Sound Manager is
> kept running while config changes are saved.

5. Clear cached media source tree
> Refreshes the source media files. For performance reasons, the source
> asset folder tree is cached. If any source assets are moved, renamed,
> or added, a refresh may be necessary.

*Note: On startup, Sound Manager will log whether it's referencing cached
asset files or building a new cache.*

Command Line Mode:
------------------

You can perform Asset Manager functions directly from the command line. The
most common commands are:

```
mpfam update        // Synchronize all asset files to their proper location

mpfam sim           // Simulate an update and display what would be changed, 
                    // but don't make any changes.

mpfam export        // Export all assets from the machine folder
```

For the full list of commands, run `mpfam --help`