$DIRECTORY = (Get-Item .).FullName

echo $DIRECTORY
cd $DIRECTORY

Unblock-File -Path .\.venv\Scripts\Activate.ps1

.\.venv\Scripts\activate.ps1

Unblock-File -Path .\API_KEY.ps1

if (Test-Path .\API_KEY.ps1) {
    .\API_KEY.ps1
}

py SummarizeTaxTable.py