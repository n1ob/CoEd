# CoEd
This app is a toolbox to handle FreeCAD Sketcher constraints. It's still work in progress in some areas.
* Based on FreeCAD v0.19
* co_main.py uses an embedded FreeCAD.
* coed.FCMacro.py is meant to be used as FreeCAD macro.
## Features
* Re-sizable floating window witch can be expanded from a compact view to access addition functionality 
* Select elements in the sketch an see relevant constraints in the app
* Select constraints in the app and see relevant elements in the sketch
* Inline toggle driving flag, if appropriate
* Inline toggle virtual flag
* Inline toggle active flag
* Inline modify constraint expression with enhanced beginner friendly completer
* Inline rename constraint
* Show Geo Index/Id defining the constraint, using 1 based index to be inline with UI naming, the type is char encoded for better readability 
* Filter for different types of constraints, selection only showing constraint types actually present in the sketch
* Normal, Construction and External elements are color coded
* Delete constraints
* Create coincident constraints based on a tolerance value.
* Create horizontal/vertical constraints based on a tolerance value.
* Create radius constraint, current or fixed value
* Create X/Y constraints on elements
* Create equal constraints based on a tolerance value.
* Create parallel constraints based on a tolerance value.
* Display open vertices
* Display various textual information about the sketch content in xml format with syntax highlighting
* Various configuration options
