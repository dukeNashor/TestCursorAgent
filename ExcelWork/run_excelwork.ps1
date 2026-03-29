[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptDir

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }

    throw "未找到可用的 Python 解释器，请先安装 Python 3。"
}

$pythonCmd = Get-PythonCommand

if (-not $SkipInstall) {
    Write-Host "Installing dependencies from requirements.txt ..." -ForegroundColor Cyan
    & $pythonCmd[0] $pythonCmd[1..($pythonCmd.Length - 1)] -m pip install -r .\requirements.txt
}

Write-Host "Launching ExcelWork app ..." -ForegroundColor Green
& $pythonCmd[0] $pythonCmd[1..($pythonCmd.Length - 1)] .\lab_kpi_pyqt6_app.py
