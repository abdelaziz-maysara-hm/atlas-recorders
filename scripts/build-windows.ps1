$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path dist | Out-Null

function Build-App($name, $script, $extraArgs) {
  Write-Host "Building $name"
  $args = @(
    "--noconfirm", "--clean", "--onedir", "--windowed",
    "--name", $name,
    "--collect-all", "customtkinter",
    "--distpath", "build_out"
  ) + $extraArgs + @($script)
  python -m PyInstaller @args
  $out = "build_out/$name"
  if (-not (Test-Path $out)) { throw "missing $out" }
  Compress-Archive -Path $out -DestinationPath "dist/${name}_Win.zip" -Force
}

Build-App "Atlas_Capture" "windows/capture/atlas_capture.py" @()
Build-App "Atlas_Clip" "windows/clip/atlas_clip.py" @()
Build-App "Atlas_PDF" "windows/pdf/atlas_pdf.py" @("--collect-all", "pypdf")
Build-App "Atlas_Sound_Recorder" "windows/sound/atlas_sound_recorder.py" @(
  "--collect-all", "sounddevice",
  "--collect-all", "soundfile",
  "--collect-all", "numpy"
)
Build-App "Atlas_Screen_Recorder" "windows/screen/atlas_screen_recorder.py" @()

$screenDir = "build_out/Atlas_Screen_Recorder"
if (Test-Path "windows/screen/ffmpeg.exe") {
  Copy-Item "windows/screen/ffmpeg.exe" -Destination $screenDir
} elseif (Test-Path "ffmpeg.exe") {
  Copy-Item "ffmpeg.exe" -Destination $screenDir
}
Compress-Archive -Path $screenDir -DestinationPath "dist/Atlas_Screen_Recorder_Win.zip" -Force

Get-ChildItem dist
