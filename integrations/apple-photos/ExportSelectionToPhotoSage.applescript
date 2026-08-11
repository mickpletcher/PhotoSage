set destinationFolder to choose folder with prompt "Choose an empty PhotoSage export folder"
tell application "Photos"
    set selectedItems to selection
    if (count of selectedItems) is 0 then error "Select at least one photo or video in Photos."
    export selectedItems to destinationFolder with using originals
end tell
set destinationPath to POSIX path of destinationFolder
do shell script "/usr/bin/env photosage preview --input " & quoted form of destinationPath
display dialog "PhotoSage created a review manifest. No files were renamed." buttons {"OK"}
