$DIRECTORY = (Get-Item .).FullName

echo $DIRECTORY
cd $DIRECTORY

.\.venv\Scripts\activate.ps1

py SummarizeTaxTable.py