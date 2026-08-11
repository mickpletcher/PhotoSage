[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Container })]
    [string]$ExportFolder
)

$catalogEntries = Get-ChildItem -LiteralPath $ExportFolder -Recurse -Force -ErrorAction Stop |
    Where-Object { $_.Name -like '*.cocatalog' -or $_.FullName -match '[\\/]CaptureOne[\\/](Cache|Settings)' }
if ($catalogEntries) {
    throw 'Capture One catalog content detected. Export images to a separate process-recipe folder.'
}

& photosage lightroom-process --input $ExportFolder --preview
if ($LASTEXITCODE -ne 0) {
    throw "PhotoSage preview failed with exit code $LASTEXITCODE"
}
