Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Projetos\DeliveryControl"
WshShell.Run "pythonw main.py", 0, False