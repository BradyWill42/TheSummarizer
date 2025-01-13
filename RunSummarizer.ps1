$DIRECTORY = (Get-Item .).FullName

Write-Output $DIRECTORY
Set-Location $DIRECTORY

if (Test-Path .\.venv\Scripts\Activate.ps1) {
	Unblock-File -Path .\.venv\Scripts\Activate.ps1
	.\.venv\Scripts\activate.ps1
} else {
	Write-Output "Virtual Environment Script does not exist or failed"
}

if (Test-Path .\API_KEY.ps1) {
	Unblock-File -Path .\API_KEY.ps1
	.\API_KEY.ps1
} else {
	Write-Output "API_KEY.ps1 Missing"
	pause
}

py SummarizeTaxTable.py