import sys
import unittest
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide2.QtWidgets import QApplication, QWidget

from co_main import main_g
from co_config import Cfg
import Sketcher
from co_logger import xp, flow, file
# App.getDocument('Unbenannt').getObject('Sketch').delGeometries([0])
from co_observer import register, unregister

DOC = "Test"
SKETCH = "Sketch"


def add_geo(o: object, b: bool = False):
    App.getDocument(DOC).getObject(SKETCH).addGeometry(o, b)


def add_geo2(o: object):
    App.getDocument(DOC).getObject(SKETCH).addGeometry(o)


def set_dat(i: int, o: object):
    App.getDocument(DOC).getObject(SKETCH).setDatum(i, o)


def add_con(o: object):
    App.getDocument(DOC).getObject(SKETCH).addConstraint(o)


# todo test cases, test cases, test cases
class MyTest(unittest.TestCase):
    def setUp(self) -> None:
        print("setUp")
        self.app = QApplication()
        self.ex = QWidget()
        Gui.showMainWindow()
        App.newDocument(DOC)
        Gui.activeDocument().activeView().viewDefaultOrientation()
        Gui.ActiveDocument.ActiveView.setAxisCross(True)
        Gui.activateWorkbench("SketcherWorkbench")
        App.activeDocument().addObject('Sketcher::SketchObject', SKETCH)
        App.activeDocument().Sketch.Placement = App.Placement(App.Vector(0.000000, 0.000000, 0.000000),
                                                              App.Rotation(0.000000, 0.000000, 0.000000, 1.000000))
        App.activeDocument().Sketch.MapMode = "Deactivated"
        Gui.activeDocument().setEdit(SKETCH)
        self.ActiveSketch = App.getDocument(DOC).getObject(SKETCH)

    def testNew(self):
        add_geo(Part.LineSegment(App.Vector(-6.458662, 8.742734, 0), App.Vector(4.249124, -2.602964, 0)), False)
        add_geo(Part.LineSegment(App.Vector(10.000000, 10.000000, 0), App.Vector(5.297122, -3.000000, 0)), False)
        add_geo(Part.LineSegment(App.Vector(4.476952, -3.650960, 0), App.Vector(1.788612, -11.000000, 0)), False)
        # ! show the new stuff in the gui
        App.getDocument(DOC).recompute()
        self.ex = main_g(self.ActiveSketch, self.app)
        self.app.exec_()
        Cfg().save()
        # sys.exit()

    def testDisplayProps(self):
        print('App.activeDocument()', App.activeDocument())
        print('App.ActiveDocument', App.ActiveDocument)
        print('App.activeDocument().__class__', App.activeDocument().__class__)
        print('App.activeDocument().Name', App.activeDocument().Name)
        print('App.activeDocument().ActiveObject', App.activeDocument().ActiveObject)
        print('App.listDocuments()', App.listDocuments())
        ad: App.Document = App.activeDocument()

        s = App.activeDocument().ActiveObject
        print(s.__class__.__name__)
        print(type(s))
        print(str(s))
        print(str(s) == '<Sketcher::SketchObject>')
        print(ad.RootObjects)

        # print('App.activeDocument().Content', ad.Content)

        # d: dict = App.ConfigDump()
        # for key, value in d.items():
        #     print(key, ' = ', value)

        # if App.activeDocument().ActiveObject == '<Sketcher::SketchObject>':
        #     print('xxxx')

    def testConstraint(self):
        print("testConstraint")
        add_geo(Part.LineSegment(App.Vector(2.452832, 4.486332, 0), App.Vector(3.533459, 1.000000, 0)), False)
        add_geo(Part.LineSegment(App.Vector(2.582505, 5.307610, 0), App.Vector(7.466946, 6.000000, 0)), False)
        add_con(Sketcher.Constraint('Coincident', 1, 1, 0, 1))
        add_geo(Part.LineSegment(App.Vector(7.423720, 8.722394, 0), App.Vector(10.000000, 3.448930, 0)), False)
        add_con(Sketcher.Constraint('PointOnObject', 1, 2, 2))
        add_con(Sketcher.Constraint('Vertical', 0))
        add_con(Sketcher.Constraint('Horizontal', 1))
        add_geo(Part.LineSegment(App.Vector(9.498528, 9.000000, 0), App.Vector(12.740411, 2.281851, 0)), False)
        add_con(Sketcher.Constraint('Parallel', 2, 3))
        add_geo(Part.LineSegment(App.Vector(11.000000, 4.616008, 0), App.Vector(15.636494, 9.630122, 0)), False)
        add_con(Sketcher.Constraint('Perpendicular', 3, 4))
        add_geo(Part.Circle(App.Vector(4.484411, 3.362479, 0), App.Vector(0, 0, 1), 1.456771))
        add_con(Sketcher.Constraint('Radius', 5, 1.456771))
        set_dat(6, App.Units.Quantity('1.460000 mm'))
        add_con(Sketcher.Constraint('Tangent', 5, 1))
        add_geo(Part.LineSegment(App.Vector(15.000000, 5.394060, 0), App.Vector(21.000000, 3.000000, 0)), False)
        add_con(Sketcher.Constraint('Equal', 4, 6))
        add_geo(Part.LineSegment(App.Vector(16.630672, 2.281851, 0), App.Vector(19.000000, 6.690814, 0)), False)
        add_con(Sketcher.Constraint('Symmetric', 6, 1, 6, 2, 7))
        add_geo(Part.LineSegment(App.Vector(3.000000, 7.684991, 0), App.Vector(7.207594, 11.000000, 0)), False)
        add_con(Sketcher.Constraint('Block', 8))
        add_geo(Part.LineSegment(App.Vector(20.000000, 10.000000, 0), App.Vector(25.794397, 5.000000, 0)), False)
        add_con(Sketcher.Constraint('DistanceX', 9, 1, 7, 2, -0.920818))
        add_con(Sketcher.Constraint('DistanceY', 9, 1, 7, 2, -3.354052))
        add_con(Sketcher.Constraint('DistanceX', 9, 1, 9, 2, 5.794397))
        set_dat(13, App.Units.Quantity('5.790000 mm'))
        add_con(Sketcher.Constraint('DistanceY', 9, 2, 9, 1, 5.000000))
        set_dat(14, App.Units.Quantity('5.000000 mm'))
        add_con(Sketcher.Constraint('Distance', 4, 6.330670))
        set_dat(15, App.Units.Quantity('6.330000 mm'))
        add_geo(Part.Circle(App.Vector(10.449479, 15.508739, 0), App.Vector(0, 0, 1), 1.760755))
        add_con(Sketcher.Constraint('Diameter', 10, 3.521510))
        set_dat(16, App.Units.Quantity('3.520000 mm'))
        add_geo(Part.LineSegment(App.Vector(21.000000, 8.000000, 0), App.Vector(29.511757, 11.661702, 0)), False)
        add_con(Sketcher.Constraint('Angle', 9, 1, 11, 1, 1.118574))
        set_dat(17, App.Units.Quantity('64.090000 deg'))
        add_geo(Part.LineSegment(App.Vector(35.260696, 12.655880, 0), App.Vector(44.554100, 13.000000, 0)), False)
        add_geo(Part.LineSegment(App.Vector(38.000000, 15.508739, 0), App.Vector(42.652195, 10.000000, 0)), False)
        add_geo(Part.LineSegment(App.Vector(36.000000, 14.773911, 0), App.Vector(41.000000, 10.000000, 0)), False)
        add_con(Sketcher.Constraint('Coincident', 14, 2, 13, 2))
        add_con(Sketcher.Constraint('PointOnObject', 14, 2, 12))
        add_con(Sketcher.Constraint('SnellsLaw', 14, 2, 13, 2, 12, 0.150000000000))

        # ! show the new stuff in the gui
        App.getDocument(DOC).recompute()
        self.ex = main_g(self.ActiveSketch, self.app)
        self.app.exec_()
        Cfg().save()

    def testCoincident(self):
        add_geo(Part.LineSegment(App.Vector(-8.0, -5.0, 0.0), App.Vector( 4.0,  7.0, 0.0)), False)
        add_geo(Part.LineSegment(App.Vector( 5.0,  7.0, 0.0), App.Vector( 7.0, -8.0, 0.0)), False)
        add_geo(Part.LineSegment(App.Vector(-8.0, -6.0, 0.0), App.Vector( 7.0, -9.0, 0.0)), False)
        add_geo(Part.LineSegment(App.Vector( 4.0,  8.0, 0.0), App.Vector(20.0, 10.0, 0.0)), False)
        add_geo2(Part.Point(App.Vector(16.0, -5.0, 0.0)))
        # add_geo(Part.LineSegment(App.Vector(8.000000,8.000000,0),App.Vector(10.000000,10.000000,0)), False)
        # add_geo(Part.Point(App.Vector(9.000000,9.000000,0)), False)
        # add_con(Sketcher.Constraint('PointOnObject',2,1,1))
        # ! show the new stuff in the gui
        # self.ActiveSketch.Document.recompute()
        App.getDocument(DOC).recompute()
        register()
        self.ex = main_g(self.ActiveSketch, self.app)
        self.app.exec_()
        Cfg().save()

    def tearDown(self) -> None:
        file.close()
        print("tearDown")
        unregister()         # Uninstall the resident function
        App.closeDocument(DOC)

    # App.activeDocument() <Document object at 000001D763812470>
    # App.ActiveDocument <Document object at 000001D763812470>
    # App.activeDocument() <class 'App.Document'>
    # App.activeDocument().Name Test
    # App.activeDocument().ActiveObject <Sketcher::SketchObject>
    # App.listDocuments() {'Test': <Document object at 000001D763812470>}
    # AppDataSkipVendor  =  true
    # AppHomePath  =  C:/Program Files/FreeCAD 0.19/
    # AppIcon  =  freecad
    # AppTempPath  =  C:\ Users\red\AppData\Local\Temp\
    # BinPath  =  C:/Program Files/FreeCAD 0.19/bin\
    # BuildRepositoryURL  =  git://github.com/FreeCAD/FreeCAD.git releases/FreeCAD-0-19
    # BuildRevision  =  24291 (Git)
    # BuildRevisionBranch  =  releases/FreeCAD-0-19
    # BuildRevisionDate  =  2021/04/15 09:17:08
    # BuildRevisionHash  =  7b5e18a0759de778b74d3a5c17eba9cb815035ac
    # BuildVersionMajor  =  0
    # BuildVersionMinor  =  19
    # CopyrightInfo  =  © Juergen Riegel, Werner Mayer, Yorik van Havre and others 2001-2020
    #
    # CreditsInfo  =  FreeCAD wouldn't be possible without FreeCAD community.
    #
    # Debug  =  0
    # DocPath  =  C:/Program Files/FreeCAD 0.19/doc\
    # ExeName  =  FreeCAD
    # ExeVendor  =  FreeCAD
    # ExeVersion  =  0.19
    # LicenseInfo  =  FreeCAD is free and open-source software licensed under the terms of LGPL2+ license.
    #
    # LoggingConsole  =
    # LoggingFile  =
    # PATH  =  C:\ Users\red\PycharmProjects\FreeCad\venv\Scripts;C:\Program Files (x86)\Razer Chroma SDK\bin;C:\Program Files\Razer Chroma SDK\bin;C:\Program Files (x86)\Common Files\Oracle\Java\javapath;C:\Dev\openjdk-16\bin;C:\PROGRAM FILES\DELL\DW WLAN CARD;C:\WINDOWS\SYSTEM32;C:\WINDOWS;C:\WINDOWS\SYSTEM32\WBEM;C:\WINDOWS\SYSTEM32\WINDOWSPOWERSHELL\V1.0\;C:\PROGRAM FILES (X86)\NVIDIA CORPORATION\PHYSX\COMMON;C:\Program Files\WIDCOMM\Bluetooth Software\;C:\Dev\apache-maven-3.3.9\bin;C:\Dev\Go\bin;C:\Program Files\nodejs\;C:\Program Files\Microsoft SQL Server\130\Tools\Binn\;C:\Program Files (x86)\Windows Kits\10\Windows Performance Toolkit\;C:\Program Files\Microsoft\Web Platform Installer\;C:\Program Files\Microsoft SQL Server\120\Tools\Binn\;C:\WINDOWS\system32;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;C:\Program Files\NVIDIA Corporation\NVIDIA NvDLISR;C:\Program Files (x86)\Intel\Intel(R) Management Engine Components\DAL;C:\Program Files\Intel\Intel(R) Management Engine Components\DAL;C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;C:\Users\red\AppData\Local\atom\bin;C:\Users\red\AppData\Roaming\npm;C:\Program Files\Docker Toolbox;C:\Users\red\AppData\Local\Microsoft\WindowsApps;C:\Users\red\AppData\Local\Microsoft\WindowsApps;C:\Users\red\AppData\Local\Microsoft\WindowsApps;C:\Program Files\dotnet\;C:\Program Files\PuTTY\;C:\Program Files\Git\cmd;C:\Program Files\FreeCAD 0.19\bin;C:\Program Files\FreeCAD 0.19\lib;C:\Users\red\AppData\Local\Programs\Python\Python39\Scripts\;C:\Users\red\AppData\Local\Programs\Python\Python39\;C:\Users\red\AppData\Local\atom\bin;C:\Users\red\AppData\Roaming\npm;C:\Program Files\Docker Toolbox;C:\Users\red\AppData\Local\Microsoft\WindowsApps;C:\Users\red\AppData\Local\GitHubDesktop\bin;C:\Program Files\JetBrains\PyCharm Community Edition 2021.1.3\bin;
    # PYTHONPATH  =  C:\ Users\red\Documents\GitHub\freecad-stubs\freecad_stubs_gen;C:\Users\red\PycharmProjects\FreeCad;C:\Users\red\Documents\FreeCAD\Macros\coed;C:\Users\red\AppData\Roaming\FreeCAD\Mod\MyScripts;C:\Program Files\JetBrains\PyCharm Community Edition 2021.1.3\plugins\python-ce\helpers\pycharm
    # PythonSearchPath  =  C:\ Users\red\Documents\GitHub\freecad-stubs\freecad_stubs_gen;C:\Users\red\PycharmProjects\FreeCad;C:\Users\red\Documents\FreeCAD\Macros\coed;C:\Users\red\AppData\Roaming\FreeCAD\Mod\MyScripts;C:\Program Files\JetBrains\PyCharm Community Edition 2021.1.3\plugins\python-ce\helpers\pycharm;C:\Program Files\FreeCAD 0.19\bin\python38.zip;C:\Program Files\FreeCAD 0.19\bin\DLLs;C:\Program Files\FreeCAD 0.19\bin\lib;C:\Program Files\FreeCAD 0.19\bin
    # RunMode  =
    # SplashScreen  =  freecadsplash
    # SystemParameter  =  C:\ Users\red\AppData\Roaming\FreeCAD\system.cfg
    # UserAppData  =  C:\ Users\red\AppData\Roaming\FreeCAD\
    # UserHomePath  =  C:\ Users\red\Documents
    # UserParameter  =  C:\ Users\red\AppData\Roaming\FreeCAD\user.cfg
    # Verbose  =

    # <Document SchemaVersion="4" ProgramVersion="0.19R24291 (Git)" FileVersion="1">
    #     <Properties Count="15" TransientCount="3">
    #         <_Property name="FileName" type="App::PropertyString" status="50331648"/>
    #         <_Property name="Tip" type="App::PropertyLink" status="33554433"/>
    #         <_Property name="TransientDir" type="App::PropertyString" status="50331649"/>
    #         <Property name="Comment" type="App::PropertyString">
    #             <String value=""/>
    #         </Property>
    #         <Property name="Company" type="App::PropertyString">
    #             <String value=""/>
    #         </Property>
    #         <Property name="CreatedBy" type="App::PropertyString">
    #             <String value=""/>
    #         </Property>
    #         <Property name="CreationDate" type="App::PropertyString" status="16777217">
    #             <String value="2021-08-20T02:09:38Z"/>
    #         </Property>
    #         <Property name="Id" type="App::PropertyString">
    #             <String value=""/>
    #         </Property>
    #         <Property name="Label" type="App::PropertyString" status="1">
    #             <String value="Test"/>
    #         </Property>
    #         <Property name="LastModifiedBy" type="App::PropertyString">
    #             <String value=""/>
    #         </Property>
    #         <Property name="LastModifiedDate" type="App::PropertyString" status="16777217">
    #             <String value="Unknown"/>
    #         </Property>
    #         <Property name="License" type="App::PropertyString" status="1">
    #             <String value="All rights reserved"/>
    #         </Property>
    #         <Property name="LicenseURL" type="App::PropertyString" status="1">
    #             <String value="http://en.wikipedia.org/wiki/All_rights_reserved"/>
    #         </Property>
    #         <Property name="Material" type="App::PropertyMap">
    #             <Map count="0">
    #             </Map>
    #         </Property>
    #         <Property name="Meta" type="App::PropertyMap">
    #             <Map count="0">
    #             </Map>
    #         </Property>
    #         <Property name="ShowHidden" type="App::PropertyBool" status="1">
    #             <Bool value="false"/>
    #         </Property>
    #         <Property name="TipName" type="App::PropertyString" status="83886080">
    #             <String value=""/>
    #         </Property>
    #         <Property name="Uid" type="App::PropertyUUID" status="16777217">
    #             <Uuid value="84809aae-60ff-4370-bd91-2cc3345fd5b7"/>
    #         </Property>
    #     </Properties>
    #     <Objects Count="1" Dependencies="1">
    #         <ObjectDeps Name="Sketch" Count="0"/>
    #         <Object type="Sketcher::SketchObject" name="Sketch" id="3376" />
    #     </Objects>
    #     <ObjectData Count="1">
    #         <Object name="Sketch" Extensions="True">
    #             <Extensions Count="1">
    #                 <Extension type="Part::AttachExtension" name="AttachExtension">
    #                 </Extension>
    #             </Extensions>
    #             <Properties Count="16" TransientCount="0">
    #                 <Property name="AttacherType" type="App::PropertyString" status="8">
    #                     <String value="Attacher::AttachEnginePlane"/>
    #                 </Property>
    #                 <Property name="AttachmentOffset" type="App::PropertyPlacement" status="8">
    #                     <PropertyPlacement Px="0" Py="0" Pz="0" Q0="0" Q1="0" Q2="0" Q3="1" A="0" Ox="0" Oy="0" Oz="1"/>
    #                 </Property>
    #                 <Property name="Constraints" type="Sketcher::PropertyConstraintList">
    #                     <ConstraintList count="0">
    #                     </ConstraintList>
    #                 </Property>
    #                 <Property name="ExpressionEngine" type="App::PropertyExpressionEngine" status="67108864">
    #                     <ExpressionEngine count="0">
    #                     </ExpressionEngine>
    #                 </Property>
    #                 <Property name="ExternalGeometry" type="App::PropertyLinkSubList">
    #                     <LinkSubList count="0">
    #                     </LinkSubList>
    #                 </Property>
    #                 <Property name="FullyConstrained" type="App::PropertyBool" status="218103808">
    #                     <Bool value="true"/>
    #                 </Property>
    #                 <Property name="Geometry" type="Part::PropertyGeometryList" status="8192">
    #                     <GeometryList count="0">
    #                     </GeometryList>
    #                 </Property>
    #                 <Property name="Label" type="App::PropertyString" status="134217728">
    #                     <String value="Sketch"/>
    #                 </Property>
    #                 <Property name="Label2" type="App::PropertyString" status="67108992">
    #                     <String value=""/>
    #                 </Property>
    #                 <Property name="MapMode" type="App::PropertyEnumeration">
    #                     <Integer value="0"/>
    #                 </Property>
    #                 <Property name="MapPathParameter" type="App::PropertyFloat" status="8">
    #                     <Float value="0"/>
    #                 </Property>
    #                 <Property name="MapReversed" type="App::PropertyBool" status="8">
    #                     <Bool value="false"/>
    #                 </Property>
    #                 <Property name="Placement" type="App::PropertyPlacement" status="8388608">
    #                     <PropertyPlacement Px="0" Py="0" Pz="0" Q0="0" Q1="0" Q2="0" Q3="1" A="0" Ox="0" Oy="0" Oz="1"/>
    #                 </Property>
    #                 <Property name="Shape" type="Part::PropertyPartShape">
    #                 </Property>
    #                 <Property name="Support" type="App::PropertyLinkSubList">
    #                     <LinkSubList count="0">
    #                     </LinkSubList>
    #                 </Property>
    #                 <Property name="Visibility" type="App::PropertyBool" status="648">
    #                     <Bool value="true"/>
    #                 </Property>
    #             </Properties>
    #         </Object>
    #     </ObjectData>
    # </Document>
    #

    # <Constrain Name="" Type="1" Value="0" First="1" FirstPos="1" Second="0" SecondPos="1" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="13" Value="0" First="1" FirstPos="2" Second="2" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="3" Value="0" First="0" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="2" Value="0" First="1" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="4" Value="0" First="2" FirstPos="0" Second="3" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="10" Value="0" First="3" FirstPos="0" Second="4" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="11" Value="1.46" First="5" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="10" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="5" Value="0" First="5" FirstPos="0" Second="1" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="12" Value="0" First="4" FirstPos="0" Second="6" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="14" Value="0" First="6" FirstPos="1" Second="6" SecondPos="2" Third="7" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="17" Value="0" First="8" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="7" Value="-0.920818" First="9" FirstPos="1" Second="7" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="8" Value="-3.35405" First="9" FirstPos="1" Second="7" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="7" Value="5.79" First="9" FirstPos="1" Second="9" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="8" Value="5" First="9" FirstPos="2" Second="9" SecondPos="1" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="6" Value="6.33" First="4" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="18" Value="3.52" First="10" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="10" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="9" Value="1.11858" First="9" FirstPos="1" Second="11" SecondPos="1" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="1" Value="0" First="14" FirstPos="2" Second="13" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="13" Value="0" First="14" FirstPos="2" Second="12" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
    # <Constrain Name="" Type="16" Value="0.15" First="14" FirstPos="2" Second="13" SecondPos="2" Third="12" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
