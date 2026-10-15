# Import a built image into a Ghidra project per RTLPlayground doc/ghidra.md:
# skip 2-byte header, 0x10000 bytes, 8051 big endian, load at 0x0000.
param([Parameter(Mandatory)][string]$Bin,
      [string]$Ghidra = (Get-ChildItem 'D:\Claude projects\tools\ghidra_*' -Directory | select -First 1).FullName,
      [string]$Proj = 'D:\Claude projects\ghidra-proj')
$tmp = Join-Path $env:TEMP 'rtlp_code.bin'
$b = [IO.File]::ReadAllBytes($Bin)
[IO.File]::WriteAllBytes($tmp, $b[2..0x10001])
New-Item -ItemType Directory -Force $Proj | Out-Null
& "$Ghidra\support\analyzeHeadless.bat" $Proj rtlp -import $tmp -overwrite -processor '8051:BE:16:default' `
  -loader BinaryLoader -loader-baseAddr 0x0 -loader-blockName code
