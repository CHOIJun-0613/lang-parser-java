cd .. 
call .venv\Scripts\activate
cmd /c "python -m csa.cli.main analyze --db-object --clean"
cd commands
echo [���� ���丮] : %cd%
pause