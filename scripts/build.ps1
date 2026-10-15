# Build RTLPlayground for SWTG018AS-A V2.0 via Docker (Docker Desktop must be running).
param([string]$Src = 'D:\Claude projects\RTLPlayground', [string]$Machine = 'SWTG018AS_A_V_2_0')
docker build -q -t rtlplayground-dev $Src
docker run --rm -v "${Src}:/workspace" rtlplayground-dev make MACHINE=$Machine
Get-ChildItem "$Src\output\$Machine\*.bin"
