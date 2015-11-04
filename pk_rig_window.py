import maya.cmds as cmds
import maya.mel as mel

import maya.OpenMayaUI as apiUI
import pysideuic
import xml.etree.ElementTree as xml
from cStringIO import StringIO
from shiboken import wrapInstance
from PySide import QtGui, QtCore


def getMayaWindow():
	ptr = apiUI.MQtUtil.mainWindow()
	if ptr is not None:
		return wrapInstance(long(ptr),QtGui.QWidget)

def loadUiType(uiFile):
	parsed = xml.parse(uiFile)
	widget_class = parsed.find('widget').get('class')
	form_class = parsed.find('class').text

	with open(uiFile, 'r') as f:
		o = StringIO()
		frame = {}

		pysideuic.compileUi(f, o, indent=0)
		pyc = compile(o.getvalue(), '<string>', 'exec')
		exec pyc in frame

		form_class = frame['Ui_%s'%form_class]
		base_class = eval('QtGui.%s'%widget_class)
	return form_class, base_class 


characters = []
currentCharacter = ""
characterRoot = ""

modules = []
modulesData = {}

currentModule = ""
currentModuleRoot = ""

listExample_form, listExample_base = loadUiType('C://Users//Pavel//Dropbox//Animacord//pk_rig.ui')

class PkRigWindow(listExample_form, listExample_base):
	
	def __init__(self, parent=getMayaWindow()):
		super(PkRigWindow, self).__init__(parent)
		self.setupUi(self)

		self.create_connections()
		self.create_menus()
		
		
		# initial state
		self.updateCharacters()
		self.mainPage_stackedWidget.setCurrentIndex(0)
		self.character_comboBox.setCurrentIndex(0)
		
		self.select_character()
		
	def create_menus(self):
		
		self.rigTemplate_menu = QtGui.QMenu()
		self.rigTemplate_menu.addAction(self.actionReset_Rig)
		self.rigTemplate_menu.addAction(self.actionLoad_Template)
		self.rigTemplate_menu.addAction(self.actionSave_Template)
		self.rigTemplate_toolBut.setMenu(self.rigTemplate_menu)
		
		self.moduleTemplate_menu = QtGui.QMenu()
		self.moduleTemplate_menu.addAction(self.actionReset_Module)
		self.moduleTemplate_menu.addAction(self.actionLoad_Module_Template)
		self.moduleTemplate_menu.addAction(self.actionSave_Module_Template)
		self.moduleTemplate_toolBut.setMenu(self.moduleTemplate_menu)
		
		self.addModule_menu = QtGui.QMenu()
		self.addModule_menu.addAction(self.actionGlobal)
		self.addModule_menu.addAction(self.actionLimb)
		self.addModule_menu.addAction(self.actionShoulder)
		self.addModule_menu.addAction(self.actionSpine)
		self.addModule_toolBut.setMenu(self.addModule_menu)
		
	def create_connections(self):
		# modes
		self.editCharacter_button.clicked.connect(self.editCharacter)
		self.editModules_button.clicked.connect(self.editModules)
		self.editSkin_button.clicked.connect(self.editSkin)
		
		# Character Buttons
		self.newCharacter_button.clicked.connect(self.create_character)
		self.characterRename_button.clicked.connect(self.rename_character)
		self.characterDelete_button.clicked.connect(self.remove_character)
		
		# Module Main
		self.moduleSelect_button.clicked.connect(self.select_moduleRoot)
		self.moduleRename_button.clicked.connect(self.rename_module)
		self.moduleDelete_button.clicked.connect(self.remove_module)
		
		# Module Connections
		self.setParentModule_button.clicked.connect(self.choose_parent_module)
		self.setPosersParent_button.clicked.connect(self.editConnections_setPosersParent)
		self.setControlsParent_button.clicked.connect(self.editConnections_setControlsParent)
		self.setEndPoserParent_button.clicked.connect(self.editConnections_setEndPoserParent)
		self.resetConnections_button.clicked.connect(self.editConnections_resetConnections)
		
		self.character_comboBox.currentIndexChanged.connect(self.select_character)
		self.modules_listWidget.currentItemChanged.connect(self.select_module)
		
		self.actionNew_Rig.triggered.connect(self.create_character)
		
		# Create module
		self.actionGlobal.triggered.connect(lambda: self.create_module("global"))
		self.actionShoulder.triggered.connect(lambda: self.create_module("shoulder"))
		self.actionLimb.triggered.connect(lambda: self.create_module("limb"))
		self.actionSpine.triggered.connect(lambda: self.create_module("spine"))
	
	
	
	# Main Buttons ------------------------------------------------------
	
	def editCharacter(self):
		if self.editCharacter_button.isChecked() :
			self.mainPage_stackedWidget.setCurrentIndex(0)
			self.editModules_button.setChecked(False)
			self.editSkin_button.setChecked(False)
		
			for m in modules:
				cmds.hide(m+":posers")
				cmds.showHidden(m+":controls")
				cmds.setAttr(m+":skinJoints.template", 0)

		else:
			self.editCharacter_button.setChecked(True)
				
	def editModules(self):
		if self.editModules_button.isChecked() :
			self.mainPage_stackedWidget.setCurrentIndex(1)
			self.editCharacter_button.setChecked(False)
			self.editSkin_button.setChecked(False)
			
			self.update_modules_list()
			
			for m in modules:
				cmds.showHidden(m+":posers")
				cmds.hide(m+":controls")
				#cmds.setAttr(m+":skinJoints.template", 1)

		else:
			self.editModules_button.setChecked(True)

	def editSkin(self):
		if self.editSkin_button.isChecked() :
			self.mainPage_stackedWidget.setCurrentIndex(2)
			self.editCharacter_button.setChecked(False)
			self.editModules_button.setChecked(False)
			
			for m in modules:
				cmds.showHidden(m+":posers")
				cmds.hide(m+":controls")

		else:
			self.editSkin_button.setChecked(True)
			
			
	# Character ---------------------------------------------------------
	
	def create_character(self):
		global characters
		
		# new rig dialog
		text, ok = QtGui.QInputDialog.getText(self, 'New Rig Dialog', 'Enter character name:')

		if ok and text != "":
			# create main group
			rigRoot = cmds.group(empty=True, n=text+"_main")
			
			# add attributes
			cmds.addAttr(rigRoot, longName='type', dataType='string')
			cmds.setAttr(rigRoot+".type", "pkRig_root", type="string", lock=True)
			
			cmds.addAttr(rigRoot, longName='charName', dataType='string')
			cmds.setAttr(rigRoot+".charName", text, type="string", lock=True)			

		self.updateCharacters()
		
		# select new character from menu
		self.character_comboBox.setCurrentIndex(self.character_comboBox.findText(text))
		
	def select_character(self):
		global currentCharacter, characterRoot

		currentCharacter = self.character_comboBox.currentText()
		self.characrerName_lineEdit.setText(currentCharacter)

		# get character group
		all = cmds.ls(transforms=True)
		for o in all:
			if cmds.attributeQuery("type", node=o, exists=True):
				if cmds.getAttr(o+".type") == "pkRig_root":
					name = cmds.getAttr(o+".charName")
					if name == currentCharacter:
						characterRoot = o

	def rename_character(self):
		newCharacterName, ok = QtGui.QInputDialog().getText(self, 'Rename Character', 'Enter character name:', QtGui.QLineEdit.Normal, currentCharacter)

		if ok and newCharacterName != "":

			# rename char group
			cmds.rename(characterRoot, newCharacterName+"_main")

			# edit attr
			cmds.setAttr(newCharacterName+"_main.charName", lock=False)	
			cmds.setAttr(newCharacterName+"_main.charName", newCharacterName, type="string", lock=True)	

			# update list
			self.updateCharacters()

			# select new character from menu
			self.character_comboBox.setCurrentIndex(self.character_comboBox.findText(newCharacterName))			

	def remove_character(self):
		cmds.delete(characterRoot)
		self.updateCharacters()

	def updateCharacters(self):
		global characters
		
		characters = []
		
		all = cmds.ls(transforms=True)
		
		for o in all:
			if cmds.attributeQuery("type", node=o, exists=True):
				if cmds.getAttr(o+".type") == "pkRig_root":
					name = cmds.getAttr(o+".charName")
					characters.append(name)
					
		# fill char menu by acc
		self.character_comboBox.clear()
		self.character_comboBox.addItems(characters)
		self.character_comboBox.setCurrentIndex(len(characters)-1)
		
		# disable buttons if not any rigs
		if len(characters) == 0:
			self.rig_frame.setEnabled(False)
		else:
			self.rig_frame.setEnabled(True)
		
		
		
	# Module ------------------------------------------------------------
		
	def create_module(self, moduleType):
		# new module dialog
		moduleName, ok = QtGui.QInputDialog().getText(self, 'Add ' + moduleType + ' Module', 'Enter module name:', QtGui.QLineEdit.Normal, moduleType)

		if ok and moduleName != "":

			# If module with name is exist
			if cmds.objExists(moduleName+":main"):
				QtGui.QMessageBox.information(self, "Warning", "This module is exist.")
			else:
				# add module to list
				item = QtGui.QListWidgetItem(moduleName)
				self.modules_listWidget.addItem(item)
				self.modules_listWidget.setCurrentItem(item)
				
				# import module  
				cmds.file("G:/Projects New/AnimaCord/pk_rig/%s/%s_rig.mb" %(moduleType,moduleType), r=True, type="mayaBinary", namespace=moduleName)
				cmds.file("G:/Projects New/AnimaCord/pk_rig/%s/%s_rig.mb" %(moduleType,moduleType), importReference=True )
				cmds.parent(moduleName+":main", characterRoot)
				
				# set module name
				cmds.setAttr(moduleName+":main.moduleName", moduleName, type="string")
				
				cmds.hide(moduleName+":controls")
				cmds.select(moduleName+":main_poser")
				
				self.update_modules_list()
				
	def select_module(self, curr, prev):
		global currentModule, currentModuleRoot

		try: 
			currentModule = curr.text() 

			self.moduleName_lineEdit.setText(currentModule)

			childs = cmds.listRelatives(characterRoot) or []

			for o in childs:
				if cmds.attributeQuery("moduleType", node=o, exists=True):
					n = cmds.getAttr(o+".moduleName")
					if n == curr.text():
						type = cmds.getAttr(o+".moduleType")
						self.moduleName_label.setText("Type: " + type)
						currentModuleRoot = o
		except:
			pass
		
		self.fillModuleConnections()
		
	def rename_module(self):
		global modules, currentModule
		
		# new module dialog
		newModuleName, ok = QtGui.QInputDialog().getText(self, 'Rename Module', 'Enter module name:', QtGui.QLineEdit.Normal, currentModule)		

		if ok and newModuleName != "":
			
			cmds.namespace( set=':' )
			cmds.namespace( add=newModuleName )
			cmds.namespace( mv=(currentModule, newModuleName) )
			cmds.namespace( rm=currentModule )
			
			currentModule = newModuleName
			
			cmds.setAttr(currentModule+":main.moduleName", currentModule, type="string")
			
			self.update_modules_list()
	
	def remove_module(self):

		childs = cmds.listRelatives(characterRoot) or []
		#print currentModule

		for o in childs:
			if cmds.attributeQuery("moduleType", node=o, exists=True):
				n = cmds.getAttr(o+".moduleName")
				if n == currentModule:
					cmds.parent(currentModule+":main", w=True)
					cmds.namespace( set=':' )
					cmds.namespace( rm=currentModule, deleteNamespaceContent=True )

		self.update_modules_list()
		
	def select_moduleRoot(self):

		childs = cmds.listRelatives(characterRoot) or []

		for o in childs:
			if cmds.attributeQuery("moduleType", node=o, exists=True):
				n = cmds.getAttr(o+".moduleName")
				if n == currentModule:
					cmds.select(o)		




	def update_modules_list(self):
		global modules, modulesData
		
		modules = []
		modulesData = {}
		
		try:
			childs = cmds.listRelatives(characterRoot)

			for o in childs:
				
				if cmds.attributeQuery("moduleType", node=o, exists=True):
					# get module parametes
					mName = cmds.getAttr(o+".moduleName")
					mRoot = o
					mType = cmds.getAttr(o+".moduleType")
					
					# save module data
					modulesData[mName] = [mRoot, mType]
					# and modules list
					modules.append(mName)
					
					
		except:
			childs = []
		
		self.modules_listWidget.clear()
		self.modules_listWidget.addItems(modules)
		item = self.modules_listWidget.item(0)
		self.modules_listWidget.setCurrentItem(item)
		
	def choose_parent_module(self):
		
		# Copy modules list without current module
		ms = modules[:]
		ms.remove(currentModule)
		
		parentModule, ok = QtGui.QInputDialog().getItem(self, 'Set Parent Module', 'Choose parent module:', ms)		
		
		if ok and parentModule != "":
			# set text
			self.parentModule_lineEdit.setText(parentModule)
			# make connections
			self.editConnections_setPosersParent(parentModule)
			

	def fillModuleConnections(self):
		# hide add connection (maybe unused current module)
		self.end_poser_inCon_frame.setVisible(0)
		
		# get all "_inCon" attrs
		inAttrs = self.getInputAttrs(currentModuleRoot)
		
		# if add attr exist, show his connection
		for attr in inAttrs:
			if attr == "end_poser_inCon":
				self.end_poser_inCon_frame.setVisible(1)

			
		
		
		
	def editConnections_setPosersParent(self, parentModule=""):
		
		# Is connect manually, parent is selected object
		if parentModule == "" :
			sel = cmds.ls(sl=True)
			if len(sel) == 1:
				parent = sel[0]
		# else, find parent from coonection in module root object
		else:
			parentRoot =  modulesData[parentModule][0]
			parent = cmds.listConnections( parentRoot + '.posersParent_inCon', d=False, s=True )[0]
			
			
		# set text 2
		self.posersParent_lineEdit.setText(parent)

		
	def editConnections_setControlsParent(self):
		
		sel = cmds.ls(sl=True)
		
		if len(sel) == 1:
			self.controlsParent_lineEdit.setText(sel[0])
	
	def editConnections_setEndPoserParent(self):
		
		sel = cmds.ls(sl=True)
		
		if len(sel) == 1:
			self.endPoserParent_lineEdit.setText(sel[0])
	
	def editConnections_resetConnections(self):
		pass
		
	def getInputAttrs(self, obj):
		
		inAttrs = []
		
		try:
			attrs = cmds.listAttr( obj, userDefined=True)
		except:
			attrs = []
		
		for attr in attrs:
			if "_inCon" in attr:
				inAttrs.append(attr)

		return inAttrs
	

if __name__ == "__main__":
	import pk_rig_window
	reload(pk_rig_window)
	
	try:
		conn.close()
		conn.deleteLater()
		del(conn)
	except:
		pass
	
	conn = pk_rig_window.PkRigWindow()
	conn.show()