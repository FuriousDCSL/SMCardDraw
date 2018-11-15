from PIL import Image
import datetime
import sys
import json
import os.path
import glob
import io
import random

from PyQt5.QtWidgets import QWidget, QMainWindow, QApplication, QStyleFactory,\
    QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, \
    QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QSplitter, QGraphicsView, \
    QButtonGroup, QGridLayout, QAction, QSizePolicy, QFileDialog, QDialog, \
    QGraphicsScene, QGraphicsView, QErrorMessage, QGraphicsScale, \
    QGraphicsItem, QListWidget, QCheckBox, QRadioButton, QFrame, \
    QListWidgetItem, QMessageBox, QProgressBar, QScrollArea, QGroupBox, \
    QSpacerItem, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PyQt5.QtGui import QIcon, QPixmap, QPen, QBrush, QTransform, QColor, \
    QPainter, QPalette, QFont
from PyQt5.QtCore import QSize,Qt, QRect, QPointF, QTimer, pyqtSignal, pyqtSlot

GRAPHICS_DIR = 'graphics/'
DATA_DIR = 'data/'
ERROR_LOG = 'error_log.txt'

def errorLog(msg):
    with io.open(ERROR_LOG, encoding = 'utf-8', mode = 'a') as errorLogFile:
        errorLogFile.write(msg+'\n')
    print(msg)

class ImageTextDialog(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.parent=parent
        self.initUI()

    def initUI(self):
        topLayout=QHBoxLayout()
        topLayout.setContentsMargins(0,0,0,0)
        self.textIn = QLineEdit()
        self.fileDialogIn = QPushButton('...')
        self.fileDialogIn.setFocusPolicy(Qt.ClickFocus)
        self.fileDialogIn.clicked.connect(self.getFile)
        self.fileDialogIn.setMaximumWidth(20)  #DEBUG need to change this to  dynamic instead of static at some point
        topLayout.addWidget(self.textIn,3)
        topLayout.addWidget(self.fileDialogIn,1)
        self.setLayout(topLayout)

    def getFile(self, rootFolder):
        fileName = QFileDialog.getOpenFileName(self,'Select Song Image',self.songFolder, 'Images (*.png *.jpg)')
        if fileName[0]=='':
            return
        self.textIn.setText(fileName[0])
        self.parent.updateImageFile(fileName[0])

    def setText(self,text):
        self.textIn.setText(text)

    def setFolder(self,folder):
        self.songFolder = folder


class PacksPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent =parent
        self.initUI()

    def initUI(self):
        topLayout=QVBoxLayout()
        self.setLayout(topLayout)
        self.formLayout = QFormLayout()
#        self.songsRootFolderSelect = FileTextDialog(self)
#        self.formLayout.addRow(QLabel('Songs Root Folder'), self.songsRootFolderSelect)
        topLayout.addLayout(self.formLayout)
        self.list = QListWidget()
        active_color = self.palette().brush(QPalette.Active, QPalette.Highlight).color().name()
        self.list.setStyleSheet('QListWidget:item:selected:!active { background: %s; }' % active_color)

        self.list.currentItemChanged.connect(self.currentItemChanged)
        topLayout.addWidget(self.list)

    def currentItemChanged(self, item):
        if item != None:
            self.parent.packSelect(item.text())


    def update(self, packs):
        self.list.clear()
        for pack in packs:
            self.list.addItem(pack['name'])
        self.packUpdate(packs)

    def packUpdate(self, packs):
        for i in range(self.list.count()):
            for pack in packs:
                if pack['name']==self.list.item(i).text():
                    if 'excluded' in pack.keys() and pack['excluded'] == 'true':
                        self.list.item(i).setForeground(QBrush(Qt.gray))
                    else:
                        self.list.item(i).setForeground(QBrush(Qt.black))

class PackInfoPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        topLayout=QVBoxLayout()
        self.setLayout(topLayout)
        formLayout = QFormLayout()
        self.packLabel = QLabel()
        formLayout.addRow(self.packLabel)
        self.excludePack = QCheckBox('Exclude Pack')
        self.excludePack.stateChanged.connect(self.excludedClicked)
        formLayout.addRow(self.excludePack)
        self.itgRB = QRadioButton('ITG difficulty Rating')
        self.ddrRB = QRadioButton('DDR original difficulty Rating')
        self.ddrXRB = QRadioButton('DDR X scale difficulty Rating')
        self.itgRB.clicked.connect(self.itgRBClicked)
        self.ddrRB.clicked.connect(self.ddrRBClicked)
        self.ddrXRB.clicked.connect(self.ddrXRBClicked)
        self.group =QButtonGroup()
        self.group.addButton(self.itgRB)
        self.group.addButton(self.ddrRB)
        self.group.addButton(self.ddrXRB)
        formLayout.addRow(self.itgRB)
        formLayout.addRow(self.ddrRB)
        formLayout.addRow(self.ddrXRB)
        self.list = QListWidget()
        active_color = self.palette().brush(QPalette.Active, QPalette.Highlight).color().name()
        self.list.setStyleSheet('QListWidget:item:selected:!active { background: %s; }' % active_color)
        self.list.currentItemChanged.connect(self.currentItemChanged)
        topLayout.addLayout(formLayout)
        topLayout.addWidget(self.list)

    def selectPack(self,packs,packName):
        self.packLabel.setText(packName)
        self.packName = packName
        self.list.clear()
        for pack in packs:
            if pack['name'] == packName:
                self.pack = pack
                if 'excluded' in pack.keys() and pack['excluded'] == 'true':
                    self.excludePack.setChecked(True)
                else:
                    self.excludePack.setChecked(False)
                if 'difficulty_scale' in self.pack.keys() and self.pack['difficulty_scale'] != 'unset':
                    if self.pack['difficulty_scale'] == 'ddr':
                        self.ddrRB.setChecked(True)
                    elif self.pack['difficulty_scale'] == 'ddrx':
                        self.ddrXRB.setChecked(True)
                    elif self.pack['difficulty_scale'] == 'itg':
                        self.itgRB.setChecked(True)
                else:
                    self.pack['difficulty_scale'] = 'unset'
                    self.group.setExclusive(False)
                    self.ddrRB.setChecked(False)
                    self.ddrXRB.setChecked(False)
                    self.itgRB.setChecked(False)
                    self.group.setExclusive(True)


                for song in pack['songs']:
                    title = QListWidgetItem(song['title'])
                    self.list.addItem(title)
                    if ('excluded' in song.keys() and song['excluded'] == 'true') or self.pack['excluded'] == 'true':
                        title.setForeground(QBrush(Qt.gray))

    # def updateSong(self,songInfo):
    #     self.excludedClicked(False)
        # if songInfo['excluded'] == 'true' or self.pack['excluded'] == 'true':
        #     self.list.findItems(songInfo['title'], Qt.MatchExactly)[0].setForeground(QBrush(Qt.gray))
        # else:
        #     self.list.findItems(songInfo['title'], Qt.MatchExactly)[0].setForeground(QBrush(Qt.black))

    def ddrRBClicked(self, signal):
        self.pack['difficulty_scale'] = 'ddr'
        self.packUpdate()
    def itgRBClicked(self, signal):
        self.pack['difficulty_scale'] = 'itg'
        self.packUpdate()
    def ddrXRBClicked(self, signal):
        self.pack['difficulty_scale'] = 'ddrx'
        self.packUpdate()

    def excludedClicked(self, signal):
        if self.excludePack.isChecked():
            self.excludePack.setChecked(True)
            self.pack['excluded'] = 'true'
            for i in range(self.list.count()):
                self.list.item(i).setForeground(QBrush(Qt.gray))
        else:
            self.pack['excluded'] = 'false'
            self.excludePack.setChecked(False)
            for i in range (self.list.count()):
                for song in self.pack['songs']:
                    if self.list.item(i).text() ==song['title']:
                        if 'excluded' in song.keys() and song['excluded'] == 'true':
                            self.list.item(i).setForeground(QBrush(Qt.gray))
                        else:
                            self.list.item(i).setForeground(QBrush(Qt.black))


        self.packUpdate()

    def packUpdate(self):
        self.parent.packUpdate(self.pack)

    def currentItemChanged(self, item):
        if item != None:
            for i in range(self.list.count()):
                self.list.item(i).setBackground(QBrush(Qt.white))
            item.setBackground(QBrush(Qt.blue))
            self.parent.songSelect(self.packName, item.text())

def parseSMFile(songFileName):
    #errorLog('Parsing SM file: '+songFileName)
    with io.open (songFileName, encoding ='utf-8', errors='ignore') as smFile:
        rawData = smFile.readlines()
    stripComments = []
    for line in rawData:
        stripComments.append(line.split('//')[0])
    smText = ''
    for line in stripComments:
        smText+=line
    smParsed = smText.split(';')
    smStr=[]
    for cmd in smParsed:
        smStr.append(cmd.strip())
    smDict = {}

    notesSingleDict = {}
    notesDoubleDict = {}

    for line in smStr:
        if line[1:6].upper() != 'NOTES':
            splitLine = line.split('#')
            if len(splitLine)>1:
                splitLine = splitLine[1].split(':',1)
            if len(splitLine)>1:
                smDict[splitLine[0].lower()] = splitLine[1]

        else:
            notes = line.split(':')
            if (notes[1].lower().strip() == 'dance-single'):
                notesSingleDict[notes[3].lower().strip()]=notes[4].strip()
            if (notes[1].lower().strip() == 'dance-double'):
                notesDoubleDict[notes[3].lower().strip()]=notes[4].strip()
    smDict['single'] = notesSingleDict
    smDict['double'] = notesDoubleDict
    return smDict



def parseSSCFile(songFileName):
    #errorLog('SSC parsing: '+ songFileName)
    with io.open (songFileName, encoding ='utf-8', errors='ignore') as smFile:
        rawData = smFile.readlines()
    stripComments = []
    for line in rawData:
        stripComments.append(line.split('//')[0])
    smText = ''
    for line in stripComments:
        smText+=line
    smParsed = smText.split('#NOTEDATA:')


    notesSingleDict = {}
    notesDoubleDict = {}
    smDict ={}
    for line in smParsed[0].strip().split(';'):
        line = line.strip().split('#')
        if len(line)>1:
            line = line[1]
            line = line.split(':')
            smDict[line[0].lower()]=line[1]
    for chart in smParsed[1:]:
        lines = chart.strip().split(';')
        chartDifficulty = ''
        chartMeter = ''
        chartType = ''
        for line in lines:
            line = line.strip().split('#')
            if len(line)>1:
                line = line[1]
                line = line.split(':')
                if line[0].lower()=='stepstype':
                    chartType = line[1].lower()
                elif line[0].lower() == 'difficulty':
                    chartDifficulty = line[1].lower()
                elif line[0].lower() == 'meter':
                    chartMeter = line[1]
        if chartType.split('-')[1].lower() == 'single':
            notesSingleDict[chartDifficulty]=chartMeter
        else:
            notesDoubleDict[chartDifficulty]=chartMeter

    smDict['single'] = notesSingleDict
    smDict['double'] = notesDoubleDict
    return smDict

    return {}

def parseDWIFile(songFileName):
    #errorLog('DWI parsing '+ songFileName)
    with io.open (songFileName, encoding ='utf-8', errors='ignore') as dwiFile:
        rawData = dwiFile.readlines()
    stripComments = []
    for line in rawData:
        stripComments.append(line.split('//')[0])
    dwiText = ''
    for line in stripComments:
        dwiText+=line
    dwiParsed = dwiText.split(';')
    dwiStr=[]
    for cmd in dwiParsed:
        dwiStr.append(cmd.strip())
    parsedData = {}
    singleDict = {}
    doubleDict = {}
    for cmd in dwiStr:
        if len(cmd)>0:
            cmd = cmd.split('#')[1]
            cmd = cmd.split(':')
            if cmd[0].lower() == 'bpm':
                parsedData['displaybpm']= cmd[1]
            elif cmd[0].lower() == 'single':
                if cmd[1].lower()=='maniac':
                    singleDict['hard'] = cmd[2]
                if cmd[1].lower()=='another':
                    singleDict['medium'] = cmd[2]
                if cmd[1].lower()=='basic':
                    singleDict['easy']=cmd[2]
                if cmd[1].lower()=='smaniac':
                    singleDict['challenge']=cmd[2]
            elif cmd[0].lower() == 'double':
                if cmd[1].lower()=='maniac':
                    doubleDict['hard'] = cmd[2]
                if cmd[1].lower()=='another':
                    doubleDict['medium'] = cmd[2]
                if cmd[1].lower()=='basic':
                    doubleDict['easy']=cmd[2]
            else:
                parsedData[cmd[0].lower()]=cmd[1]
    parsedData['single']=singleDict
    parsedData['double']=doubleDict
    parsedData['difficulty_scale']='ddr'
    return parsedData

def parseSongFile(song):
    smFilename = ''
    sscFilename = ''
    dwiFilename = ''


    for file in os.listdir(song):
        (base, ext) = os.path.splitext(file)
        #errorLog(base+"\t"+ext)
        if ext.lower() == '.sm':
            smFilename = os.path.join(song,file)
        if ext.lower() == '.ssc':
            sscFilename = os.path.join(song,file)
        if ext.lower() == '.dwi':
            dwiFilename = os.path.join(song,file)


    if smFilename != '':
        parsedData = parseSMFile(smFilename)
    elif sscFilename != '':
        parsedData = parseSSCFile(sscFilename)
    elif dwiFilename != '':
        parsedData = parseDWIFile(dwiFilename)
    else:
        errorLog ('ERROR: no song file: '+ song)
        parsedData = {}
        return parsedData
    parsedData['folder']= song

    return parsedData

def parseDisplayBPM(bpms):
    bpms = bpms.split(':')
    lowBpm =9999
    highBpm = 0
    for bpm in bpms:
        if bpm =='*':
            return bpm
        bpm = int(float(bpm))
        if bpm < lowBpm:
            lowBpm = bpm
        if bpm > highBpm:
            highBpm = bpm
    lowBpm = int(lowBpm)
    highBpm = int(highBpm)
    if lowBpm == highBpm:
        return str(lowBpm)
    else:
        return str(lowBpm)+'-'+str(highBpm)

def parseSongBPMS(bpms):
    bpms = bpms.split(',')
    stripBpms = []
    for bpm in bpms:
        stripBpms.append(int(float(bpm.split('=')[1])))
    lowBpm =9999
    highBpm = 0
    for bpm in stripBpms:
        bpm = int(float(bpm))
        if bpm < lowBpm:
            lowBpm = bpm
        if bpm > highBpm:
            highBpm = bpm
    lowBpm = int(lowBpm)
    highBpm = int(highBpm)
    if lowBpm == highBpm:
        return str(lowBpm)
    else:
        return str(lowBpm)+'-'+str(highBpm)

def parsePack(packFolder):
    songs = []
    pack = {}

    pack['name']=os.path.split(packFolder)[1]
    pack['folder']=packFolder
    pack['excluded']='false'
    pack['difficulty_scale']='itg'
    for song in os.listdir(packFolder):
        if os.path.isdir(os.path.join(packFolder,song)):
            parsedData = parseSongFile(os.path.join(packFolder,song))
            if parsedData != {}:
                if 'banner' in parsedData.keys():
                    (base, ext) = os.path.splitext(parsedData['banner'])
                    if ext.lower() == '.png' or ext.lower == '.jpg':
                        image = getImage(parsedData,['jacket', 'json', 'banner' ,'background'])
                    else:
                        image = getImage(parsedData,['jacket', 'banner','background'])

                else:
                    image = getImage(parsedData,['banner','jacket','background'])
                parsedData['banner'] = image
                parsedData['excluded'] = 'false'
                parsedData['difficulty_scale'] = 'pack'
                songs.append(parsedData)
    pack['songs']=songs
    return pack

class CardGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.rows =[]
        self.layout=QGridLayout()
        self.setLayout(self.layout)

    def addRow(self,row):
        for i in range(len(self.rows)):
            self.layout.removeItem(self.rows[i])

        self.rows.append(row)

        i=0
        for row in reversed(self.rows):
#            self.layout.setRowMinimumHeight(i,200)
            self.layout.addLayout(row,i,0)
            i +=1

class Card(QWidget):
    def __init__(self):
        super().__init__()
        self.mouseReleaseEvent = self.clicked


        self.initUI()

    def initUI(self):
        self.layout =QGridLayout()
        self.layout.addItem(QSpacerItem(10,10),0,0)
        self.layout.addItem(QSpacerItem(10,10),5,5)
        self.formLayout = QFormLayout()
        self.layout.addLayout(self.formLayout,1,1,4,4,Qt.AlignCenter)
        self.veto = QFrame()
        self.veto.setFrameShape(QFrame.Box)
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(.5)
        self.veto.setGraphicsEffect(effect)
        self.veto.setStyleSheet('border: 5px ; border-radius: 20px; background-color: gray')
        self.vetoed = False
        self.setLayout(self.layout)

    def setColor(self, color):
        self.color = QFrame()
        self.color.setFrameShape(QFrame.Box)
        self.color.setStyleSheet('border: 5px ; border-radius: 20px; background-color: '+color)
        self.layout.addWidget(self.color,0,0,-1,-1)

    def setVeto(self, vetoed):
        self.vetoed = vetoed
        if vetoed:
            self.layout.addWidget(self.veto,0,0,-1,-1)
            self.veto.show()
        else:
            self.layout.removeWidget(self.veto)
            self.veto.hide()

    def clicked(self,event):
        if self.vetoed:
            self.setVeto(False)
        else:
            self.setVeto(True)

    def setBackground(self, imageName):
        label = QLabel()
        label.setPixmap(QPixmap(imageName).scaledToWidth(150))
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(.75)
        label.setGraphicsEffect(effect)
        self.layout.addWidget(label,1,1,4,4,Qt.AlignCenter)

    def setTitle(self,title):
        self.title = title
        label = QLabel(title)
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(4)
        effect.setColor(Qt.black)
        effect.setXOffset(1)
        effect.setYOffset(1)
        label.setGraphicsEffect(effect)
        label.setStyleSheet('color: white')
        label.setWordWrap(True)
        label.setFont(QFont('SanSerif',16,QFont.Bold))
        self.formLayout.addRow(label)

    def setSubTitle(self, subTitle):
        if subTitle != '':
            label = QLabel(subTitle)
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(4)
            effect.setColor(Qt.black)
            effect.setXOffset(1)
            effect.setYOffset(1)
            label.setGraphicsEffect(effect)
            label.setStyleSheet('color: white')
            label.setWordWrap(True)
            label.setFont(QFont('SanSerif',12))
            self.formLayout.addRow(label)

    def setTitleTranslit(self,titletranslit):
        if titletranslit != '':
            label = QLabel(titletranslit)
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(4)
            effect.setColor(Qt.black)
            effect.setXOffset(1)
            effect.setYOffset(1)
            label.setGraphicsEffect(effect)
            label.setStyleSheet('color: white')
            label.setWordWrap(True)
            label.setFont(QFont('SanSerif',12))
            self.formLayout.addRow(label)

    def setArtist(self,artist):
        label = QLabel(artist)
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(4)
        effect.setColor(Qt.black)
        effect.setXOffset(1)
        effect.setYOffset(1)
        label.setGraphicsEffect(effect)
        label.setStyleSheet('color: white')
        label.setFont(QFont('SanSerif',14, QFont.Bold))
        label.setWordWrap(True)
        self.formLayout.addRow(label)

    def setStyleMeter(self,style,scale, meter):
        label1 = QLabel(style)
        effect1 = QGraphicsDropShadowEffect()
        effect1.setBlurRadius(4)
        effect1.setColor(Qt.black)
        effect1.setXOffset(1)
        effect1.setYOffset(1)
        label1.setGraphicsEffect(effect1)
        label1.setStyleSheet('color: white')
        label1.setFont(QFont('SanSerif',12, QFont.Bold))
        label1.setWordWrap(True)
        label2 = QLabel(meter)
        effect2 = QGraphicsDropShadowEffect()
        effect2.setBlurRadius(4)
        effect2.setColor(Qt.black)
        effect2.setXOffset(2)
        effect2.setYOffset(2)
        label2.setGraphicsEffect(effect2)
        label2.setStyleSheet('color: white')
        label2.setFont(QFont('SanSerif',12, QFont.Bold))
        label2.setWordWrap(True)
        label3 = QLabel(scale)
        effect3 = QGraphicsDropShadowEffect()
        effect3.setBlurRadius(4)
        effect3.setColor(Qt.black)
        effect3.setXOffset(1)
        effect3.setYOffset(1)
        label3.setGraphicsEffect(effect3)
        label3.setStyleSheet('color: white')
        label3.setFont(QFont('SanSerif',12, QFont.Bold))
        label3.setWordWrap(True)
        rowLayout = QHBoxLayout()
        rowLayout.addWidget(label1)
        rowLayout.addWidget(label3)
        rowLayout.addWidget(label2)
        self.formLayout.addRow(rowLayout)


    def setFolder(self,folder):
        label = QLabel(os.path.split(folder)[1])
        label.setStyleSheet('color: white')
        label.setWordWrap(True)
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(4)
        effect.setColor(Qt.black)
        effect.setXOffset(1)
        effect.setYOffset(1)
        label.setGraphicsEffect(effect)
        label.setFont(QFont('SanSerif',12, QFont.Bold))
        self.formLayout.addRow(label)

# card.setColor (color)
# card.setBackground(song['banner'])
# card.setTitle(song['title'])
# if 'subtitle' in song.keys():
#     card.setSubTitle(song['subtitle'])
# if 'titletranslit' in song.keys():
#     card.setTitleTranslit('titletranslit'])
# if 'artist' in song.keys():
#     card.setArtist(song['artist'])
# card.setFolder(song['folder'])
# row.addWidget(card)
# self.drawnCards.addRow(row)


class CardDrawPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.topLayout=QVBoxLayout()
        self.setLayout(self.topLayout)
        self.inputLayout =QFormLayout()
        self.inputhbox =QHBoxLayout()
        self.input1 = QFormLayout()
        self.input2 = QFormLayout()


        self.numDraw = QSpinBox()
        self.numDraw.setValue(5)
        self.input1.addRow(QLabel('Number to draw: '),self.numDraw)
        self.input1.addRow(QLabel(''))
        self.ddrUse = QCheckBox()
        self.ddrUse.setChecked(True)
        self.input1.addRow(QLabel('Difficulty level DDR: '), self.ddrUse)
        self.ddrMax = QSpinBox()
        self.ddrMax.setValue(10)
        self.input1.addRow(QLabel('Upper Bound (inclusive): '), self.ddrMax)
        self.ddrMin = QSpinBox()
        self.ddrMin.setValue(8)
        self.input1.addRow(QLabel('Lower Bound (inclusive): '), self.ddrMin)
        self.input1.addRow(QLabel(''))
        self.ddrXUse = QCheckBox()
        self.ddrXUse.setChecked(True)
        self.input1.addRow(QLabel('Difficulty level DDR X Scale: '),self.ddrXUse)
        self.ddrXMax = QSpinBox()
        self.ddrXMax.setValue(14)
        self.input1.addRow(QLabel('Upper Bound (inclusive): '), self.ddrXMax)
        self.ddrXMin = QSpinBox()
        self.ddrXMin.setValue(10)
        self.input1.addRow(QLabel('Lower Bound (inclusive): '), self.ddrXMin)
        self.input1.addRow(QLabel(''))
        self.itgUse =QCheckBox()
        self.itgUse.setChecked(True)
        self.input1.addRow(QLabel('Difficulty level ITG: '), self.itgUse)
        self.itgMax = QSpinBox()
        self.itgMax.setValue(10)
        self.input1.addRow(QLabel('Upper Bound (inclusive): '), self.itgMax)
        self.itgMin = QSpinBox()
        self.itgMin.setValue(8)
        self.input1.addRow(QLabel('Lower Bound (inclusive): '), self.itgMin)

        self.input1.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.inputhbox.addLayout(self.input1)

        self.style = QComboBox()
        self.style.addItem('Single')
        self.style.addItem('Double')
        self.input2.addRow(QLabel('Style: '), self.style)
        self.input2.addRow(QLabel(''))
        self.input2.addRow(QLabel('Difficulties: '))
        self.input2.addRow(QLabel(''))
        self.beginner = QCheckBox()
        self.input2.addRow(QLabel('\tBeginner '), self.beginner)
        self.basic = QCheckBox()
        self.input2.addRow(QLabel('\tBasic '), self.basic)
        self.difficult = QCheckBox()
        self.input2.addRow(QLabel('\tDifficult '), self.difficult)
        self.expert = QCheckBox()
        self.expert.setChecked(True)
        self.input2.addRow(QLabel('\tExpert '), self.expert)
        self.challenge = QCheckBox()
        self.challenge.setChecked(True)
        self.input2.addRow(QLabel('\tChallenge '), self.challenge)
        self.edit = QCheckBox()
        self.input2.addRow(QLabel('\tEdit '), self.edit)

        #self.input2.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.inputhbox.addLayout(self.input2)

        self.inputLayout.addRow(self.inputhbox)

        # self.wtTop = QFormLayout()
        # self.useweighted = QCheckBox()
        # self.wtTop.addRow(QLabel('Use Weighted '), self.useweighted)
        # self.weights = QHBoxLayout()
        # self.weights.addWidget(QLabel('WT1: '))
        # self.weights.addWidget(QLabel('WT2: '))
        # self.weights.addWidget(QLabel('WT3: '))
        # self.weights.addWidget(QLabel('WT4: '))
        # self.weights.addWidget(QLabel('WT5: '))
        # self.wtTop.addRow(self.weights)
        # self.inputLayout.addRow(self.wtTop)

        self.drawButton = QPushButton('Draw')
        self.drawButton.clicked.connect(self.drawCards)
        self.inputLayout.addRow(self.drawButton)
        self.drawnCards = CardGrid()
        self.drawnCardsScroll =QScrollArea()
#        self.drawnCardsWidget =QWidget()
#        self.drawnCardsWidget.setLayout(self.drawnCards)
        self.drawnCardsScroll.setWidget(self.drawnCards)
        self.topLayout.addLayout(self.inputLayout)
        self.drawnCardsScroll.setWidgetResizable(True)
        self.topLayout.addWidget(self.drawnCardsScroll)
        #self.topLayout.addWidget(self.drawnCards)

    def drawCardsNaive(self):

#        self.drawnCards.setStyleSheet('QLabel{background-color: white}')

        packs = self.parent.getPacks()
        matchingSongs = []
        difficulties =[]
        if self.beginner.isChecked():
            difficulties.append('beginner')
        if self.basic.isChecked():
            difficulties.append('easy')
        if self.difficult.isChecked():
            difficulties.append('medium')
        if self.expert.isChecked():
            difficulties.append('hard')
        if self.challenge.isChecked():
            difficulties.append('challenge')
        if self.edit.isChecked():
            difficulties.append('edit')

        style = self.style.currentText().lower()
        for pack in packs:
            for song in pack['songs']:
                #print('Pack: ', pack['name'],' excluded: ', pack['excluded'], 'song: ', song['title'], 'excluded: ', song['excluded'])
                if song['excluded'] == 'true' or pack['excluded'] == 'true':
                    pass
                else:
                    for difficulty in difficulties:
                        if (song['difficulty_scale'] == 'itg' or pack['difficulty_scale'] == 'itg') and self.itgUse.isChecked():
                            if difficulty in song[style].keys() and int(song[style][difficulty]) in range(self.itgMin.value(),self.itgMax.value()+1):
                                song['draw_diff']=difficulty
                                song['folder']=pack['folder']
                                song['folder_diff']=pack['difficulty_scale']
                                matchingSongs.append(song)
                        if (song['difficulty_scale'] == 'ddr' or pack['difficulty_scale'] == 'ddr')and self.ddrUse.isChecked():
                            if difficulty in song[style].keys() and int(song[style][difficulty]) in range(self.ddrMin.value(),self.ddrMax.value()+1):
                                song['draw_diff']=difficulty
                                song['folder']=pack['folder']
                                song['folder_diff']=pack['difficulty_scale']
                                matchingSongs.append(song)
                        if (song['difficulty_scale'] == 'ddrx' or pack['difficulty_scale'] == 'ddrx') and self.ddrXUse.isChecked():
                            if difficulty in song[style].keys() and int(song[style][difficulty]) in range(self.ddrXMin.value(),self.ddrXMax.value()+1):
                                song['draw_diff']=difficulty
                                song['folder']=pack['folder']
                                song['folder_diff']=pack['difficulty_scale']
                                matchingSongs.append(song)
        numSongs =len(matchingSongs)
        row = QHBoxLayout()
        for i in range(self.numDraw.value()):
            if numSongs >1:
                draw = random.randint(0,numSongs-1)
            elif numSongs == 1:
                draw = 0
            else:
                continue
            
            print(len(matchingSongs)," ",draw)
            song =matchingSongs[draw]
            del matchingSongs[draw]
            numSongs = len(matchingSongs)
            card  = Card()
            #button.setMinimumSize(QSize(0,150))
            #button.
            if song['draw_diff'] == 'beginner':
                color='lightblue'
            if song['draw_diff'] == 'easy':
                color='yellow'
            if song['draw_diff'] == 'medium':
                color='darkred'
            if song['draw_diff'] == 'hard':
                color='green'
            if song['draw_diff'] == 'challenge':
                color='purple'
            if song['draw_diff'] == 'edit':
                color='gray'
            card.setColor (color)
            card.setBackground(song['banner'])
            card.setTitle(song['title'])
            if 'subtitle' in song.keys():
                card.setSubTitle(song['subtitle'])
            if 'titletranslit' in song.keys():
                card.setTitleTranslit(song['titletranslit'])
            if 'artist' in song.keys():
                card.setArtist(song['artist'])
            card.setStyleMeter(self.style.currentText(),song['folder_diff'], song[style][song['draw_diff']])
            card.setFolder(song['folder'])
            #card.setVeto(True)
            row.addWidget(card)
        self.drawnCards.addRow(row)

    def drawCards(self):
        self.drawCardsNaive()

class SongInfoPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        topLayout=QVBoxLayout()
        self.setLayout(topLayout)
        formLayout = QFormLayout()
        self.excludeSong = QCheckBox('Exclude Song')
        self.excludeSong.stateChanged.connect(self.excludedClicked)
        formLayout.addRow(self.excludeSong)
        self.itgRB = QRadioButton('ITG difficulty Rating')
        self.ddrRB = QRadioButton('DDR original difficulty Rating')
        self.ddrXRB = QRadioButton('DDR X scale difficulty Rating')
        self.packRB = QRadioButton('Default to pack difficulty Rating')
        self.itgRB.clicked.connect(self.itgRBClicked)
        self.ddrRB.clicked.connect(self.ddrRBClicked)
        self.ddrXRB.clicked.connect(self.ddrXRBClicked)
        self.packRB.clicked.connect(self.packRBClicked)
        formLayout.addRow(self.packRB)
        formLayout.addRow(self.itgRB)
        formLayout.addRow(self.ddrRB)
        formLayout.addRow(self.ddrXRB)

        self.songTitle = QLabel()
        self.songTitleTranslit = QLabel()
        self.songSubTitle = QLabel()
        self.songSubTitleTranslit = QLabel()
        self.songArtist = QLabel()
        self.songArtistTranslit = QLabel()
        self.songBPM = QLabel()
        self.songGenre = QLabel()
        self.songSingleBeginner = QLabel()
        self.songSingleBasic = QLabel()
        self.songSingleDifficult = QLabel()
        self.songSingleExpert = QLabel()
        self.songSingleChallenge = QLabel()
        self.songSingleEdit = QLabel()
        self.songDoubleBeginner = QLabel()
        self.songDoubleBasic = QLabel()
        self.songDoubleDifficult = QLabel()
        self.songDoubleExpert = QLabel()
        self.songDoubleChallenge = QLabel()
        self.songDoubleEdit = QLabel()
        self.songGraphicSelect = ImageTextDialog(self)
        self.songGraphic = QLabel()

        formLayout.addRow(QLabel('Title:'), self.songTitle)
        formLayout.addRow(QLabel('Title Translit:'), self.songTitleTranslit)
        formLayout.addRow(QLabel('SubTitle:'), self.songSubTitle)
        formLayout.addRow(QLabel('SubTitle Translit:'), self.songSubTitleTranslit)
        formLayout.addRow(QLabel('Artist:'), self.songArtist)
        formLayout.addRow(QLabel('Artist Translit:'), self.songArtistTranslit)
        formLayout.addRow(QLabel('BPM:'), self.songBPM)
        formLayout.addRow(QLabel('Genre:'), self.songGenre)
        formLayout.addRow(QLabel('Graphic:'), self.songGraphicSelect)
        formLayout.addRow(self.songGraphic)
        formLayout.addRow(QLabel('Single: '))
        formLayout.addRow(QLabel('Beginner:'), self.songSingleBeginner)
        formLayout.addRow(QLabel('Basic:'), self.songSingleBasic)
        formLayout.addRow(QLabel('Difficult:'), self.songSingleDifficult)
        formLayout.addRow(QLabel('Expert:'), self.songSingleExpert)
        formLayout.addRow(QLabel('Challenge:'), self.songSingleChallenge)
        formLayout.addRow(QLabel('Edit:'), self.songSingleEdit)
        formLayout.addRow(QLabel('Double:'))
        formLayout.addRow(QLabel('Beginner:'), self.songDoubleBeginner)
        formLayout.addRow(QLabel('Basic:'), self.songDoubleBasic)
        formLayout.addRow(QLabel('Difficult:'), self.songDoubleDifficult)
        formLayout.addRow(QLabel('Expert:'), self.songDoubleExpert)
        formLayout.addRow(QLabel('Challenge:'), self.songDoubleChallenge)
        formLayout.addRow(QLabel('Edit:'), self.songDoubleEdit)

        topLayout.addLayout(formLayout)

    def packRBClicked(self, signal):
        self.songInfo['difficulty_scale'] = 'pack'
        self.songUpdate()
    def ddrRBClicked(self, signal):
        self.songInfo['difficulty_scale'] = 'ddr'
        self.songUpdate()
    def itgRBClicked(self, signal):
        self.songInfo['difficulty_scale'] = 'itg'
        self.songUpdate()
    def ddrXRBClicked(self, signal):
        self.songInfo['difficulty_scale'] = 'ddrx'
        self.songUpdate()

    def excludedClicked(self, signal):
        if self.excludeSong.isChecked():
            self.songInfo['excluded'] = 'true'
        else:
            self.songInfo['excluded'] = 'false'
        self.songUpdate()

    def selectSong(self, pack, songName):
        self.packName = pack['name']
        for song in pack['songs']:
            if songName == song['title']:
                self.songInfo = song
        if 'title' in self.songInfo.keys():
            title = self.songInfo['title']
            self.songTitle.setText(title)
        if 'titletranslit' in self.songInfo.keys():
            self.songTitleTranslit.setText(self.songInfo['titletranslit'])
        if 'subtitle' in self.songInfo.keys():
            self.songSubTitle.setText(self.songInfo['subtitle'])
        if 'subtitletranslit' in self.songInfo.keys():
            self.songSubTitleTranslit.setText(self.songInfo['subtitletranslit'])
        if 'artist' in self.songInfo.keys():
            self.songArtist.setText(self.songInfo['artist'])
        if 'artisttranslit' in self.songInfo.keys():
            self.songArtistTranslit.setText(self.songInfo['artisttranslit'])
        if 'genre' in self.songInfo.keys():
            self.songGenre.setText(self.songInfo['genre'])
        if 'displaybpm' in self.songInfo.keys():
            self.songBPM.setText(parseDisplayBPM(self.songInfo['displaybpm']))
        else:
            self.songBPM.setText(parseSongBPMS(self.songInfo['bpms']))

        if 'excluded' in self.songInfo.keys() and self.songInfo['excluded'] =='true':
            self.excludeSong.setChecked(True)
        else:
            self.excludeSong.setChecked(False)
            self.songInfo['excluded'] = 'false'
            self.songUpdate()

        if 'difficulty_scale' in self.songInfo.keys():
            self.setDifficultyScale(self.songInfo['difficulty_scale'])
        else:
            self.setDifficultyScale('pack')
            self.songInfo['difficulty_scale'] = 'pack'
            self.songUpdate()
        self.songGraphicSelect.setText(self.songInfo['banner'])
        self.songGraphic.setPixmap(QPixmap(self.songInfo['banner']).scaledToWidth(200))
        self.songGraphicSelect.setFolder(self.songInfo['folder'])

        if 'single' in self.songInfo.keys():
            if 'beginner' in self.songInfo['single'].keys():
                self.songSingleBeginner.setText(self.songInfo['single']['beginner'])
            else:
                self.songSingleBeginner.setText('')

            if 'easy' in self.songInfo['single'].keys():
                self.songSingleBasic.setText(self.songInfo['single']['easy'])
            else:
                self.songSingleBasic.setText('')
            if 'medium' in self.songInfo['single'].keys():
                self.songSingleDifficult.setText(self.songInfo['single']['medium'])
            else:
                self.songSingleDifficult.setText('')
            if 'hard' in self.songInfo['single'].keys():
                self.songSingleExpert.setText(self.songInfo['single']['hard'])
            else:
                self.songSingleExpert.setText('')
            if 'challenge' in self.songInfo['single'].keys():
                self.songSingleChallenge.setText(self.songInfo['single']['challenge'])
            else:
                self.songSingleChallenge.setText('')
            if 'edit' in self.songInfo['single'].keys():
                self.songSingleEdit.setText(self.songInfo['single']['edit'])
            else:
                self.songSingleEdit.setText('')
        if 'double' in self.songInfo.keys():
            if 'beginner' in self.songInfo['double'].keys():
                self.songDoubleBeginner.setText(self.songInfo['double']['beginner'])
            else:
                self.songDoubleBeginner.setText('')
            if 'easy' in self.songInfo['double'].keys():
                self.songDoubleBasic.setText(self.songInfo['double']['easy'])
            else:
                self.songDoubleBasic.setText('')
            if 'medium' in self.songInfo['double'].keys():
                self.songDoubleDifficult.setText(self.songInfo['double']['medium'])
            else:
                self.songDoubleDifficult.setText('')
            if 'hard' in self.songInfo['double'].keys():
                self.songDoubleExpert.setText(self.songInfo['double']['hard'])
            else:
                self.songDoubleExpert.setText('')
            if 'challenge' in self.songInfo['double'].keys():
                self.songDoubleChallenge.setText(self.songInfo['double']['challenge'])
            else:
                self.songDoubleChallenge.setText('')
            if 'edit' in self.songInfo['double'].keys():
                self.songDoubleEdit.setText(self.songInfo['double']['edit'])
            else:
                self.songDoubleEdit.setText('')

    def setDifficultyScale(self, scale):
        if scale == 'pack':
            self.packRB.setChecked(True)
        elif scale == 'itg':
            self.itgRB.setChecked(True)
        elif scale == 'ddr':
            self.ddrRB.setChecked(True)
        elif scale == 'ddrx':
            self.ddrXRB.setChecked(True)


    def songUpdate(self):
        self.parent.songUpdate(self.packName, self.songInfo)

    def updateImageFile(self,imageName):
        self.songInfo['banner'] = imageName
        self.songGraphic.setPixmap(QPixmap(imageName).scaledToWidth(200))
        self.songUpdate()

def getImage(songJson, imagePref):

    bannerExt=['-bn','-banner','_bn','_banner','banner','bn','']
    jacketExt=['-jacket','-jk','_jacket','_jk','jacket','jk']
    bgExt=['-bg','-background','_bg','_background','bg','background']

    song = songJson['folder']

    (root,tail) = os.path.split(song)
    images = []
    for file in os.listdir(song):
        (base, ext) = os.path.splitext(file)

        if ext.lower() == '.png' or ext.lower() == '.jpg':
            images.append(file) #, os.path.getsize(os.path.join(root,song,file))))


    for pref in imagePref:
        if pref == 'json':
            if os.path.isfile(os.path.join(song,songJson['banner'])):
                return os.path.join(song, songJson['banner'])
#            errorLog("Banner missing trying fallback "+tail)

        if pref =='jacket':
            for image in images:
                (base,ext) = os.path.splitext(image)
                if base.lower() == 'jacket':
                    return os.path.join(song,image)
                if base.lower() == 'jk':
                    return os.path.join(song,image)
                for ext in jacketExt:
                    if base.lower() == tail.lower()+ext:
                        return os.path.join(song,image)
        if pref =='banner':
            for image in images:
                (base,ext) = os.path.splitext(image)
                if base.lower() == 'banner':
                    return os.path.join(song,image)
                if base.lower() == 'bn':
                    return os.path.join(song,image)
                for ext in bannerExt:
                    if base.lower() == tail.lower()+ext:
                        return os.path.join(song,image)
        if pref =='background':
            for image in images:
                (base,ext) = os.path.splitext(image)
                if base.lower() == 'background':
                    return os.path.join(song,image)
                if base.lower() == 'bg':
                    return os.path.join(song,image)
                for ext in bgExt:
                    if base.lower() == tail.lower()+ext:
                        return os.path.join(song,image)

    filesize = -1
    imagename = ''
    for image in images:

        size = os.path.getsize (os.path.join(song,image))
        if filesize == -1:
            filesize = size
            imagename = image
        elif size < filesize:
            filesize = size
            imagename = image
    if filesize == -1:
        return os.path.join(GRAPHICS_DIR,'BannerNotFound.png')

    return os.path.join(song,imagename)

class ScraperMainPanel(QWidget):
    def __init__(self,songsJson):
        super().__init__()
        self.jsonOutFile = ''
        self.initUI(songsJson)

    def initUI(self,songsJson):
        self.topLayout = QHBoxLayout()
        self.topLayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.topLayout)
        self.mainPanel = QSplitter()

        self.packsPanel = PacksPanel(self)
        self.packInfoPanel = PackInfoPanel(self)
        self.songInfoPanel = SongInfoPanel(self)
        self.mainPanel.addWidget(self.packsPanel)
        self.mainPanel.addWidget(self.packInfoPanel)
        self.mainPanel.addWidget(self.songInfoPanel)
        self.topLayout.addWidget(self.mainPanel)



    def packSelect(self, pack):
        self.packInfoPanel.selectPack(self.packs,pack)

    def songSelect (self, packName, songName):

        for pack in self.packs:
            if packName == pack['name']:
                    self.songInfoPanel.selectSong(pack, songName)

    def buildJson(self,parent,rootFolder):
        self.packs = []
        fileNames = os.listdir(rootFolder)
        parent.setPBMin(0)
        parent.setPBMax(len(fileNames))
        parent.showPB()
        for fileName in fileNames:
            parent.incPB()
            if os.path.isdir(os.path.join(rootFolder,fileName)):
                self.packs.append(parsePack(os.path.join(rootFolder,fileName)))
        self.packSelect(self.packs[0]['name'])
        self.packsPanel.update(self.packs)
        parent.hidePB()

    def loadJson(self):
        self.packs = []
        fileName = QFileDialog.getOpenFileName(self, 'Select JSON file', '', 'JSON Files (*.json)')
        if fileName[0] != '':
            with io.open(fileName[0], encoding='utf-8') as jsonFile:
                self.packs = json.load(jsonFile)
                self.jsonOutFile = fileName[0]

        self.packSelect(self.packs[0]['name'])
        self.packsPanel.update(self.packs)

    def saveAsJson(self):
        filename = QFileDialog.getSaveFileName(self, 'Save Json as...', '.', 'Json file (*.json)')
        if filename[0] != '':
            with io.open(filename[0], encoding = 'utf-8', mode = 'w') as jsonOut:
                json.dump(self.packs,jsonOut, sort_keys=True, indent=2)
                self.jsonOutFile = filename[0]
        else:
            msg =QMessageBox()
            msg.setText('File Not Saved!')
            msg.exec()
    def saveJson(self):
        if self.jsonOutFile == '':
            self.saveAsJson()
        else:
            with io.open(self.jsonOutFile, encoding='utf-8', mode ='w') as jsonOut:
                json.dump(self.packs, jsonOut, sort_keys=True, indent=2)

    def songUpdate(self,packName, songInfo):
        songs = []
        for pack in self.packs:
            if pack['name'] == packName:
                for song in pack['songs']:
                    if songInfo['folder'] == song['folder']:
                        songs.append(songInfo)
                    else:
                        songs.append(song)
                pack['songs'] = songs
        self.packInfoPanel.excludedClicked(False)

    def packUpdate(self, packInfo):
        packs = []
        for pack in self.packs:
            if packInfo['name'] == pack['name']:
                packs.append(packInfo)
            else:
                packs.append(pack)
        self.packs = packs
        self.packsPanel.packUpdate(packs)

    def exportImages(self, parent, fileName):
        assetPacks = []
        parent.setPBMin(0)
        parent.setPBMax(len(self.packs))
        parent.showPB()
        for pack in self.packs:
            parent.incPB()
            if pack['excluded'] != 'true':
                (root,tail) = os.path.split(pack['folder'])
                if not os.path.exists(os.path.join(fileName,tail)):
                    os.mkdir(os.path.join(fileName,tail))
                pack['folder'] = tail
                songs =[]
                for song in pack['songs']:
                    if 'excluded' in song.keys() and song['excluded'] != 'true' or 'excluded' not in song.keys():

                        banner = Image.open(song['banner'])
                        (base,bannerFile) = os.path.split(song['banner'])
                        (bannerBase, bannerExt) = os.path.splitext(bannerFile)
                        ratio = 150.0 / float(banner.size[0])
                        banner = banner.resize((150, int(banner.size[1]*ratio)))
                        if banner.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', banner.size, 0xffffff )
                            background.paste(banner, banner.split()[-1])
                            banner = background
                        banner.convert('RGB').save(os.path.join(fileName,tail,bannerBase)+'.jpg', quality=90)
                        song['banner'] = os.path.join(tail,bannerBase+'.jpg')
                        songs.append(song)
                pack['songs'] = songs
                assetPacks.append(pack)
        with io.open(os.path.join(fileName,'StepMania.json'), encoding='utf-8', mode='w') as jsonOutFile:
            json.dump(assetPacks,jsonOutFile, sort_keys=True, indent=2)
        parent.hidePB()

    def getPacks(self):
        return self.packs

class ScraperMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Stepmania Scraper')
        self.status = self.statusBar()
        self.resize(1024,768)
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        self.setWindowIcon(QIcon(GRAPHICS_DIR+'sm.png'))
        self.mainPanel = QTabWidget()
        self.scraper = ScraperMainPanel('info.json')
        self.cardDraw = CardDrawPanel(self)
        self.mainPanel.addTab(self.scraper,'Scraper')
        self.mainPanel.addTab(self.cardDraw, 'Card Draw')
        self.progressBar = QProgressBar()
        self.progressBar.hide()
        self.status.addWidget(self.progressBar)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        newAct = QAction('&New',self)
        newAct.setShortcut('Ctrl+N')
        newAct.triggered.connect(self.newJson)
        openAct = QAction('&Open', self)
        openAct.setShortcut('Ctrl+O')
        openAct.triggered.connect(self.openJson)
        exportAct = QAction('Export for WebApp', self)
        exportAct.triggered.connect(self.exportImages)
        saveAct = QAction('&Save',self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.triggered.connect(self.saveJson)
        saveAsAct= QAction('Save &As...',self)
        saveAsAct.triggered.connect(self.saveAsJson)
        saveAsAct.setShortcut('Ctrl+Shit+S')
        settingsAct = QAction('Se&ttings',self)
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.quitApp)
        fileMenu.addAction(newAct)
        fileMenu.addAction(openAct)
        fileMenu.addSeparator()
        fileMenu.addAction(exportAct)
        fileMenu.addSeparator()
        fileMenu.addAction(saveAct)
        fileMenu.addAction(saveAsAct)
        fileMenu.addSeparator()
        fileMenu.addAction(settingsAct)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAct)

        helpMenu = menuBar.addMenu('&Help')
        helpAct = QAction('&Help', self)
        helpAct.setShortcut('F1')
        helpAct.triggered.connect(self.helpDialog)
        aboutAct = QAction('&About', self)
        helpMenu.addAction(helpAct)
        helpMenu.addSeparator()
        helpMenu.addAction(aboutAct)

        self.setCentralWidget(self.mainPanel)

        self.show()

    def getPacks(self):
        return self.scraper.getPacks()

    def exportImages(self, event):
        fileName = QFileDialog.getExistingDirectory(self, 'Select Assests folder','.')
        if fileName!='':
            self.scraper.exportImages(self, fileName)


    def newJson(self, event):
        fileName = QFileDialog.getExistingDirectory(self,'Select Songs Root Folder','c:/games/Stepmania 5.1/Songs')
        self.scraper.buildJson(self, fileName)


    def openJson(self, event):
        self.scraper.loadJson()

    def saveAsJson(self, event):
        self.scraper.saveAsJson()

    def saveJson(self, event):
        self.scraper.saveJson()
        self.status.showMessage('Saved')

    def quitApp(self):
        QApplication.quit()

    def helpDialog(self):
        print('help')

    def setPBMin(self, min):
        self.progressBar.setMinimum(min)

    def setPBMax(self, max):
        self.progressBar.setMaximum(max)

    def showPB(self):
        self.PBValue = 0
        self.progressBar.show()

    def incPB(self):
        self.PBValue += 1
        self.progressBar.setValue(self.PBValue)

    def hidePB(self):
        self.progressBar.hide()

def main():
    with io.open(ERROR_LOG, encoding = 'utf-8', mode = 'w') as errorLogFile:
        errorLogFile.write(str(datetime.datetime.now()))
    app = QApplication(sys.argv)

    SMScraper = ScraperMainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
