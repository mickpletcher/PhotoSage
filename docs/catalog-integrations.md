# Catalog Integrations

PhotoSage never opens or edits a Lightroom Classic, Capture One, or Apple Photos
catalog database. Every integration exports/copies media to a separate folder and
creates a preview manifest. Apply remains a separate reviewed action.

## Shared safety rules

1. Back up the catalog and originals.
2. Export to a new, separate working directory.
3. Do not point PhotoSage at a live catalog package, cache, or database.
4. Create and inspect a preview manifest.
5. Approve the proposed names.
6. Apply only inside the export directory.
7. Reimport or relink through the catalog application's supported workflow.

Running PhotoSage against exported copies does not rename originals held inside a
managed catalog. Whether metadata and edits are preserved depends on the export
settings of the catalog application.

## Lightroom Classic

The plug-in is located at:

```text
integrations/lightroom/PhotoSage.lrplugin
```

Install it through Lightroom Classic's Plug-in Manager. The PhotoSage export
service renders selected files into an export directory and invokes a preview.
It does not apply renames.

Before first use, confirm `photosage` is available to the Lightroom process. A
terminal-only virtual environment may not be visible to Lightroom. Prefer the
signed CLI executable or add the installed command to the user PATH, then restart
Lightroom.

Validate with a small temporary catalog and two non-sensitive images. Confirm an
export is created, a manifest is written, the originals and catalog are unchanged,
and no apply happens automatically.

See [Lightroom Integration](lightroom-integration.md) for installation,
configuration, workflow, and rollback details.

## Capture One

The helper is:

```text
integrations/capture-one/Invoke-PhotoSagePreview.ps1
```

Create a Capture One process recipe that exports originals and required XMP
sidecars to a dedicated folder. Invoke the helper after export:

```powershell
powershell.exe -NoProfile -File "C:\Path\To\Invoke-PhotoSagePreview.ps1" -ExportFolder "C:\PhotoSage\CaptureOneExport"
```

The folder must already exist. The script recursively rejects `.cocatalog`
content and Capture One `Cache` or `Settings` paths. It then runs:

```powershell
photosage lightroom-process --input C:\PhotoSage\CaptureOneExport --preview
```

Despite the command's historical name, it processes an external export folder
and does not require a Lightroom catalog.

Test the process recipe without a post-processing action first. Then run the
helper manually. Confirm the resulting manifest is preview-only before attaching
the helper to automation.

If PowerShell execution policy blocks the script, use the organization's approved
script signing or deployment method. Do not weaken machine-wide policy just for
this integration.

## Apple Photos

The AppleScript is:

```text
integrations/apple-photos/ExportSelectionToPhotoSage.applescript
```

Run it on macOS through Script Editor or an approved Automator/Shortcuts wrapper.
The script:

1. Prompts for an export directory.
2. Reads the current Photos selection.
3. Exports originals to that directory.
4. Runs `photosage preview` against the exported files.
5. Reports that no files were renamed.

The shell environment used by AppleScript must be able to find `photosage` via
`/usr/bin/env`. GUI-launched macOS applications often have a smaller PATH than an
interactive terminal. Install PhotoSage into a standard executable location or
adapt the local script to an explicit trusted path.

Grant Photos automation permission only to the application running the script.
The script does not modify the Photos library, but the exported originals can
contain full metadata.

## Applying and returning results

Review and apply the exported directory through normal PhotoSage commands. Then
import the renamed copies as new assets or use the catalog application's supported
relink workflow. Do not edit catalog database files to substitute new paths.

When XMP sidecars are part of the workflow, verify each media/sidecar pair before
reimport. See [Recovery and Review](recovery-and-review.md).

## Troubleshooting

| Problem | Check |
| --- | --- |
| Integration cannot find PhotoSage | Run `photosage --help` in the environment visible to the catalog app. Use an explicit installed path if required. |
| No manifest appears | Run the equivalent preview command manually and check the configured manifest directory. |
| Capture One helper rejects the folder | Export to a clean directory outside `.cocatalog`, `Cache`, and `Settings` paths. |
| AppleScript says there is no selection | Select one or more assets in Photos before running it. |
| Metadata or edits are missing | Correct the catalog export recipe; PhotoSage only receives what was exported. |
| Reimport creates duplicates | Decide whether the workflow creates copies or relinks existing assets before applying names. |
| Sidecar collision occurs | Stop, compare both sidecars, and generate a new preview after resolving the export layout. |
