import sys
from PyQt6.QtWidgets import QApplication
from model import ImageModel
from view import MainWindow
from controller import Controller


def main() -> None:
    app = QApplication(sys.argv)

    model = ImageModel()
    view = MainWindow()
    controller = Controller(model, view)

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
