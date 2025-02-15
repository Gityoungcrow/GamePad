import sys
import sqlite3
from os import name

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem, QMessageBox
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.uic import loadUi


class SnakeGame(QDialog):
    def init(self):
        super().init()
        super(SnakeGame, self).init()
        loadUi('snake.ui', self)



class MyApp(QMainWindow):
    def init(self):
        super().init()
        uic.loadUi('gamepad.ui', self)  # Загружаем дизайн

        self.pushButton.clicked.connect(self.SnakeGame)


    def snakegame(self):
        mood_page = SnakeGame()
        mood_page.exec()


if name == 'main':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec())