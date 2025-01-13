$DIRECTORY = (Get-Item .).FullName

Write-Output $DIRECTORY
Set-Location $DIRECTORY

Unblock-File -Path .\.venv\Scripts\Activate.ps1

.\.venv\Scripts\activate.ps1

Unblock-File -Path .\API_KEY.ps1

if (Test-Path .\API_KEY.ps1) {
    .\API_KEY.ps1
}

py SummarizeTaxTable.py