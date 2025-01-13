$DIRECTORY = (Get-Item .).FullName

echo $DIRECTORY
cd $DIRECTORY

Unblock-File -Path .\.venv\Scripts\Activate.ps1

.\.venv\Scripts\activate.ps1

py SummarizeTaxTable.py