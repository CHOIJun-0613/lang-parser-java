cd .. 
call .venv\Scripts\activate
cmd /c "python -m csa.cli.main sequence --class-name UserController --project-name car-center-devlab --image-format svg"
cd commands
echo [���� ���丮] : %cd%
pause