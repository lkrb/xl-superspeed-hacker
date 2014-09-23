#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#############################################################################
#
# Copyright (C) 2014 lkrb.
# No rights reserved.
#
#############################################################################


from PyQt4 import QtCore, QtGui
import json
import os
import re
import sqlite3
import sys

DEFAULT_PATH = (
    u"C:/Program Files (x86)/Thunder Network"
    "/Thunder/Profiles/TaskDb.dat")


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Window(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        browseButton = QtGui.QPushButton(u"浏览...")
        browseButton.clicked.connect(self.browse)
        refreshButton = QtGui.QPushButton(u"刷新")
        refreshButton.clicked.connect(self.refresh)
        hackButton = QtGui.QPushButton(u"Hack!")
        hackButton.clicked.connect(self.hack)

        self.fileComboBox = QtGui.QComboBox()
        self.fileComboBox.setEditable(False)
        self.fileComboBox.addItem(DEFAULT_PATH)
        self.fileComboBox.setSizePolicy(
            QtGui.QSizePolicy.Preferred,
            QtGui.QSizePolicy.Preferred)
        self.fileComboBox.currentIndexChanged.connect(self.load_users_and_data)
        self.userIdComboBox = QtGui.QComboBox()
        self.userIdComboBox.setEditable(False)
        self.userIdComboBox.setSizePolicy(
            QtGui.QSizePolicy.Preferred,
            QtGui.QSizePolicy.Preferred)
        self.userIdComboBox.currentIndexChanged.connect(self.refresh)

        fileLabel = QtGui.QLabel(u"任务信息文件:")
        userIdLabel = QtGui.QLabel(u"用户ID:")
        tasksLabel = QtGui.QLabel(u"高速通道任务列表:")
        self.statusLabel = QtGui.QLabel()
        aboutLabel = QtGui.QLabel(
            u'By <a href="https://github.com/lkrb">lkrb</a>')
        aboutLabel.setTextFormat(QtCore.Qt.RichText)
        aboutLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        aboutLabel.setOpenExternalLinks(True)

        self.createTasksTable()

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(refreshButton)
        buttonsLayout.addWidget(hackButton)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(fileLabel, 0, 0)
        mainLayout.addWidget(self.fileComboBox, 0, 1)
        mainLayout.addWidget(browseButton, 0, 2)
        mainLayout.addWidget(userIdLabel, 1, 0)
        mainLayout.addWidget(self.userIdComboBox, 1, 1)
        mainLayout.addWidget(tasksLabel, 2, 0)
        mainLayout.addWidget(self.tasksTable, 3, 0, 1, 3)
        mainLayout.addWidget(self.statusLabel, 4, 0)
        mainLayout.addWidget(aboutLabel, 5, 0, 1, 0)
        mainLayout.addLayout(buttonsLayout, 5, 0, 1, 3)
        self.setLayout(mainLayout)

        icon = QtGui.QIcon(resource_path('icon.ico'))
        self.setWindowIcon(icon)

        self.setWindowTitle(u"渣雷高速通道解禁工具 v0.1")
        self.resize(700, 500)

        self.load_users_and_data()

    def browse(self):
        file = QtGui.QFileDialog.getOpenFileName(
            self, u"选择任务信息文件",
            self.fileComboBox.currentText(),
            u"Sqlite数据库文件 (*.dat)")

        if file:
            if self.fileComboBox.findText(file) == -1:
                self.fileComboBox.addItem(file)
            self.fileComboBox.setCurrentIndex(self.fileComboBox.findText(file))

            self.load_users_and_data()

    def load_users_and_data(self):
        user_list = []
        try:
            filename = unicode(self.fileComboBox.currentText())
        except:
            self.statusLabel.setText(u"路径有误")
            return

        if not os.path.isfile(filename):
            self.statusLabel.setText(u"指定的文件不存在或打开失败")
            return

        try:
            conn = sqlite3.connect(filename)
            c = conn.cursor()
            pat = re.compile(u'AccelerateTaskMap(\d+)_superspeed_1_1')
            for item in c.execute(
                    u'SELECT name FROM sqlite_master WHERE type = "table"'):
                m = pat.match(item[0])
                if m is not None:
                    user_list.append(m.group(1))
            conn.close()
        except Exception as e:
            self.statusLabel.setText(u"文件解析失败 %r" % e)
            conn.close()
            return

        self.userIdComboBox.clear()
        for user in user_list:
            if self.userIdComboBox.findText(user) == -1:
                self.userIdComboBox.addItem(user)
        if user_list:
            self.userIdComboBox.setCurrentIndex(0)
            self.refresh()

    def refresh(self):
        self.task_list = {}
        self.showTasks()
        try:
            userid = unicode(self.userIdComboBox.currentText())
        except:
            self.statusLabel.setText(u"用户ID有误")
            return

        try:
            filename = unicode(self.fileComboBox.currentText())
        except:
            self.statusLabel.setText(u"路径有误")
            return

        if not os.path.isfile(filename):
            self.statusLabel.setText(u"指定的文件不存在或打开失败")
            return

        try:
            conn = sqlite3.connect(filename)
            c = conn.cursor()
            tablename = u'AccelerateTaskMap%s_superspeed_1_1' % userid
            for item in c.execute(
                    u'SELECT LocalTaskId,UserData FROM %s' % tablename):
                c2 = conn.cursor()
                c2.execute(
                    u'SELECT Name FROM TaskBase WHERE TaskId = %d' % item[0])
                taskid = item[0]
                task = c2.fetchone()
                if task is None:
                    continue
                taskname = task[0]
                result = json.loads(str(item[1]))['Result']
                if taskid not in self.task_list or result != 0:
                    self.task_list[taskid] = (taskname, result)
            conn.close()
        except Exception as e:
            self.statusLabel.setText(u"文件解析失败 %r" % e)
            conn.close()
            return

        self.showTasks()

    def hack(self):
        try:
            filename = unicode(self.fileComboBox.currentText())
        except:
            self.statusLabel.setText(u"路径有误")
            return

        try:
            userid = unicode(self.userIdComboBox.currentText())
        except:
            self.statusLabel.setText(u"用户ID有误")
            return

        if not os.path.isfile(filename):
            self.statusLabel.setText(u"指定的文件不存在或打开失败")
            return

        try:
            conn = sqlite3.connect(filename)
            c = conn.cursor()
            tablename = u'AccelerateTaskMap%s_superspeed_1_1' % userid
            for k, v in self.task_list.items():
                if v[1] == 0:
                    continue
                for item in c.execute(
                        u'SELECT UserData,LocalSubFileIndex FROM %s '
                        'WHERE LocalTaskId = %d' % (tablename, k)):
                    c2 = conn.cursor()
                    jsondata = json.loads(str(item[0]))
                    jsondata['Result'] = 0
                    buf = buffer(json.dumps(jsondata))
                    query = (u"UPDATE %s SET UserData = (?) "
                             "WHERE LocalTaskId = %d AND "
                             "LocalSubFileIndex = %d" % (tablename,
                                                         k, item[1]))
                    b = sqlite3.Binary(buf)
                    c2.execute(query, (b, ))

            conn.commit()
            conn.close()
        except Exception as e:
            self.statusLabel.setText(u"文件解析失败 %r" % e)
            conn.close()
            return

        self.refresh()

    def showTasks(self):
        self.tasksTable.clearContents()
        self.tasksTable.setRowCount(0)
        errorcount = 0
        for k, v in self.task_list.items():
            taskNameItem = QtGui.QTableWidgetItem(v[0])
            taskNameItem.setFlags(taskNameItem.flags() ^
                                  QtCore.Qt.ItemIsEditable)

            if v[1] == 0:
                statusItem = QtGui.QTableWidgetItem(u"正常")
                statusItem.setTextColor(QtGui.QColor('green'))
            else:
                statusItem = QtGui.QTableWidgetItem(u"禁用")
                statusItem.setTextColor(QtGui.QColor('red'))
                errorcount += 1
            statusItem.setFlags(statusItem.flags() ^ QtCore.Qt.ItemIsEditable)

            row = self.tasksTable.rowCount()
            self.tasksTable.insertRow(row)
            self.tasksTable.setItem(row, 0, taskNameItem)
            self.tasksTable.setItem(row, 1, statusItem)

        self.statusLabel.setText(u"找到%d个任务，%d个高速通道被禁用" %
                                 (len(self.task_list.keys()), errorcount))

    def createTasksTable(self):
        self.tasksTable = QtGui.QTableWidget(0, 2)
        self.tasksTable.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)

        self.tasksTable.setHorizontalHeaderLabels((u"文件名", u"状态"))
        self.tasksTable.horizontalHeader().setResizeMode(
            0, QtGui.QHeaderView.Stretch)
        self.tasksTable.verticalHeader().hide()
        self.tasksTable.setShowGrid(False)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
