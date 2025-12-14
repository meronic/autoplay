# app.py

# Main application entry point
import os
import sys
from PyQt5 import QtWidgets, QtGui

# Application modules
import core
import ui

# Main function
def main():
    
    cfg_path = os.path.join(core.BASE_DIR, "config.json")
    cfg = core.load_config(cfg_path)

    app = QtWidgets.QApplication(sys.argv)
    ui.setup_app_style(app)

    win = ui.MainWindow(cfg)

    icon_file = cfg.get("ui", {}).get("icon_file", "icon.png")
    icon_path = os.path.join(core.BASE_DIR, icon_file)
    if os.path.exists(icon_path):
        win.setWindowIcon(QtGui.QIcon(icon_path))

    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
