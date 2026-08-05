Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d ""C:\Users\harshal\OneDrive\Desktop\antigravityProjects\algoTradingSetup"" && .\venv\Scripts\python.exe scripts\scheduler.py", 0, False
