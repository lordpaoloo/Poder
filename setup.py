import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine-tuning.
build_exe_options = {
    "packages": [
        "os", 
        "sys", 
        "PyQt5", 
        "selenium", 
        "bs4", 
        "pandas",
        "re",
        "pickle",
        "time",
        "typing",
        "datetime",
        "unicodedata"
    ],
    "excludes": ["tkinter"],
    "include_files": ["resources/", "modules/"]  # Include additional files like resources and modules
}

# Base is set to "Win32GUI" for a GUI application, or None for a console application.
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Poder",
    version="0.1",
    description="A powerful tool to collect publicly available data from social media platforms.",
    options={"build_exe": build_exe_options},
    executables=[Executable("Ui.py", base=base, icon="resources/app_icon.ico")]
)
