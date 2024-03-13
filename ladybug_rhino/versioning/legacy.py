"""Functions for updating from Legacy to LBT."""
import os

try:
    import System.Drawing
except ImportError:
    raise ImportError("Failed to import System.")

try:
    import Rhino
    import Grasshopper
    import Grasshopper.Kernel as gh
except ImportError:
    raise ImportError("Failed to import Grasshopper.")

from ..grasshopper import give_warning
from .userobject import UO_FOLDER, FOLDER_MAP

LBT_UO_FOLDERS = (
    'ladybug_grasshopper',
    'honeybee_grasshopper_core',
    'honeybee_grasshopper_radiance',
    'honeybee_grasshopper_energy',
    'dragonfly_grasshopper'
)

# the comments in the dictionaries below note whether there are plans for
# a possible better component to map the legacy one to in the future
LADYBUG_MAP = {
    "Ladybug_Render View": ["LB Capture View", None],
    "Ladybug_Import CEC Photovoltaics Module": ["HB Photovoltaic Properties", "A better replacement may be available in the future."],  # possible better future
    "Ladybug_Outdoor Comfort Calculator": ["LB UTCI Comfort", None],
    "Ladybug_Real Time Radiation Analysis": ["LB Real Time Incident Radiation", None],
    "Ladybug_Draft Discomfort": ["LB Ankle Draft", "The original Fanger draft model is no longer endorsed by ASHRAE-55.\nUse ankle draft instead."],
    "Ladybug_Simplified Photovoltaics Module": ["HB Photovoltaic Properties", "Used with the new 'HB Generation Loads' component."],
    "Ladybug_PMV Comfort Parameters": ["LB PMV Comfort Parameters", None],
    "Ladybug_Photovoltaics Performance Metrics": ["HB Generation Loads", None],
    "Ladybug_Solar Water Heating Surface": [None, "Coming Soon to HB-Energy!"],  # SOON!
    "Ladybug_Legend Parameters": ["LB Legend Parameters", None],
    "Ladybug_MRT Calculator": ["Multiplication", "Native Grasshopper multiplication does effectively\nthe same as the Legacy component."],
    "Ladybug_Bioclimatic Chart": ["LB Psychrometric Chart", None],
    "Ladybug_PV SWH System Size": [None, "Coming Soon to HB-Energy!"],  # SOON!
    "Ladybug_Design Day Sky Model": ["LB Cumulative Sky Matrix", "Get Clear Sky Radiation from the 'LB Import STAT' component."],
    "Ladybug_Mesh Threshold Selector": ["LB Mesh Threshold Selector", None],
    "Ladybug_Shading Mask_II": ["LB Sky Mask", None],
    "Ladybug_Psychrometric Chart": ["LB Psychrometric Chart", "Note that the 'LB PMV Polygon' is a separate\ncomponent that plots the comfort polygon."],
    "Ladybug_Import Ground Temp": [None, "Coming Soon!"],  # SOON!
    "Ladybug_Import Sandia Photovoltaics Module": ["HB Photovoltaic Properties", "A better replacement may be available in the future."],  # possible better future
    "Ladybug_Wind Boundary Profile": ["LB Wind Profile", None],
    "Ladybug_Wind Speed Calculator": ["LB Wind Speed", None],
    "Ladybug_Passive Strategy List": ["LB Passive Strategies", "More passive strategies are planned for the future."], # possible better future
    "Ladybug_SunriseSunset": ["LB Day Solar Information", None],
    "Ladybug_CDD_HDD": ["LB Degree Days", None],
    "Ladybug_Pedestrian Wind Comfort": [None, "No plans to replace. Never made it out of WIP.\nDid not have a clear relationship to other components."],
    "Ladybug_PMV Comfort Calculator": ["LB PMV Comfort", None],
    "Ladybug_Ladybug": [None, "No longer needed in LBT as all core functions\nlive outside Grasshopper with your installation."],
    "Ladybug_SolarFan": [None, "Coming Soon!"],  # SOON!
    "Ladybug_Import epw": ["LB Import EPW", None],
    "Ladybug_View From Sun": ["LB View From Sun", None],
    "Ladybug_Separate By Normal": ["LB Filter by Normal", "Note the _orientation input of the new component\nhas changed since Legacy."],
    "Ladybug_GenCumulativeSkyMtx": ["LB Cumulative Sky Matrix", "This LBT component also does what\nLegacy Ladybug_selectSkyMtx did."],
    "Ladybug_Shading Parameters List": ["HB Facade Parameters", None],
    "Ladybug_Radiation Calla Dome": ["LB Radiation Dome", None],
    "Ladybug_F2C": ["LB To SI", "The 'LB To SI' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Analysis Period": ["LB Analysis Period", None],
    "Ladybug_Average Data": ["LB Time Interval Operation", None],
    "Ladybug_Branch Data": ["PartitionList", "Native GH 'Partition List' w/ Size of 24 is best for days.\nSee ladybug-core SDK for data collection group_by_month()."],
    "Ladybug_Surface Hourly Solar": ["LB Directional Solar Irradiance", None],
    "Ladybug_Capture View": ["LB Capture View", None],
    "Ladybug_Set Rhino Sun": ["LB Set Rhino Sun", None],
    "Ladybug_Open EPW And STAT Weather Files": ["LB Download Weather", None],
    "Ladybug_Surface View Analysis": ["LB View Factors", None],
    "Ladybug_fly": [None, "No plans to update.\nColibri components in TTToolbox plugin are much better."],
    "Ladybug_SolarEnvelopeBasic": ["LB Solar Envelope", None],
    "Ladybug_Cone Of Vision": [None, "No plans to update as similar workflows can be\nachieved with native Grasshopper components."],
    "Ladybug_Location Finder": ["LB Construct Location", "Legacy component was dependent on Google Maps API,\nwhich has become paid."],
    "Ladybug_Import Location": ["LB Import Location", None],
    "Ladybug_Cold Water Temperature": [None, "Coming Soon to HB-Energy!"],  # SOON!
    "Ladybug_Shading Mask": ["LB Sky Mask", None],
    "Ladybug_Line Chart": ["LB Monthly Chart", "Hourly data on 'LB Monthly Chart' is often clearer than Legacy 'Line Chart'.\nNative GH 'Quick Graph' is also similar.\nOr use Excel and get more customization."],
    "Ladybug_Create Legend": ["LB Create Legend", None],
    "Ladybug_Update File": ["LB Sync Grasshopper File", None],
    "Ladybug_Beaufort Ranges": [None, "Beaufort scale was developed for naval vessels\nand is not recommended for pedestrian comfort.\nLawson's criteria is better."],
    "Ladybug_DOY_HOY": ["LB Calculate HOY", None],
    "Ladybug_Texture Maker": [None, "The Human plugin does a better job with texture mapping."],
    "Ladybug_Generate Mesh": ["LB Generate Point Grid", None],
    "Ladybug_Import stat": ["LB Import STAT", None],
    "Ladybug_selectSkyMtx": [None, "No longer needed as the 'LB Cumulative Sky Matrix'\ncomponent does everything."],
    "Ladybug_Humidity Ratio Calculator": ["LB Humidity Metrics", None],
    "Ladybug_Sunlight Hours Analysis": ["LB Direct Sun Hours", None],
    "Ladybug_Clothing Function": ["LB Clothing by Temperature", None],
    "Ladybug_3D Chart": ["LB Hourly Plot", None],
    "Ladybug_L2G": ["LB To IP", "The 'LB To IP' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Mesh-To-Hatch": ["LB Mesh to Hatch", None],
    "Ladybug_Outdoor Solar Temperature Adjustor": ["LB Outdoor Solar MRT", None],
    "Ladybug_Wind Rose": ["LB Wind Rose", None],
    "Ladybug_Solar Water Heating System": [None, "Coming Soon to HB-Energy!"],  # SOON!
    "Ladybug_Cfm2M3s": ["LB To SI", "The 'LB To SI' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Activities Met List": ["LB Activities Met List", None],
    "Ladybug_CombineSolarEnvelopes": [None, "Can be done with native Grasshopper\n'Deconstruct Mesh' and sorting components."],
    "Ladybug_Window Downdraft": [None, "Legacy model was very simple/limited and\nit's unclear if it should be ported to LBT."],
    "Ladybug_Sun_Shades_Calculator": ["LB Shade Benefit", "Use 'LB Shade Benefit' with 'LB Mesh Threshold Selector'\nto get shade geometry that blocks all sun vectors."],
    "Ladybug_Orient to Camera": ["LB Orient to Camera", None],
    "Ladybug_Export Ladybug": ["LB Export UserObject", None],
    "Ladybug_Monthly Bar Chart": ["LB Monthly Chart", None],
    "Ladybug_Comfort Shade Benefit Evaluator": ["LB Thermal Shade Benefit", None],
    "Ladybug_Create LB Header": ["LB Construct Header", None],
    "Ladybug_Construct Time": ["LB Calculate HOY", "Decimal HOYs are supported throughout LBT and minute is now an input on 'LB Calculate HOY'."],
    "Ladybug_uSI2uIP": ["LB Unit Converter", "The 'LB Unit Converter' converts individual values.\nTo convert data collections use the 'LB To IP' component."],
    "Ladybug_ShadingDesigner": ["LB Shade Benefit", "Use 'LB Shade Benefit' with 'LB Mesh Threshold Selector'\nto get shade geometry that blocks all sun vectors.\nUse 'HB LouverShades' to generate louvers."],
    "Ladybug_Photovoltaics Surface": ["HB Shade", "Assign PV properties to the Shade geometry\n with 'HB Photovoltaic Properties' component."],
    "Ladybug_Separate data": ["LB Deconstruct Data", None],
    "Ladybug_SolarFanBasic": [None, "Coming Soon!"],  # SOON!
    "Ladybug_Tilt And Orientation Factor": [None, "No longer needed as new PV components use detailed\nShade geometry in an EnergyPlus simulation."],
    "Ladybug_Wh2BTU": ["LB To IP", "The 'LB To IP' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Radiation Rose": ["LB Radiation Rose", None],
    "Ladybug_Bounce from Surface": ["LB Surface Ray Tracing", None],
    "Ladybug_Shadow Study": ["LB Set Rhino Sun", None],
    "Ladybug_Open STAT File": ["File Path", "Right-click the native Grasshopper 'File Path' component\nand choose 'Select one existing file'."],
    "Ladybug_SunPath": ["LB SunPath", None],
    "Ladybug_uIP2uSI": ["LB Unit Converter", "The 'LB Unit Converter' converts individual values.\nTo convert data collections use the 'LB To SI' component."],
    "Ladybug_Passive Strategy Parameters": ["LB Passive Strategy Parameters", "This gets plugged into the 'LB PMV Polygon' component."],
    "Ladybug_Body Characteristics": ["LB PET Body Parameters", None],
    "Ladybug_BTUft2Whm": ["LB To SI", "The 'LB To SI' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Radiation Analysis": ["LB Incident Radiation", None],
    "Ladybug_Sunpath Shading": ["HB Generation Loads", "Detailed shading calculations now happen with EnergyPlus\nin the 'HB Generation Loads' component."],
    "Ladybug_SolarEnvelope": ["LB Solar Envelope", None],
    "Ladybug_Clothing List": ["Clothing List", None],
    "Ladybug_True North": ["LB Magnetic to True North", None],
    "Ladybug_Search": [None, "Consult the search-able online docs of the components for similar functionality.\nhttps://discourse.ladybug.tools/pub/lbt-grasshopper-doc"],
    "Ladybug_Update Ladybug": ["LB Versioner", None],
    "Ladybug_Solar Water Heating Performance Metrics": [None, "Coming Soon to HB-Energy!"],  # SOON!
    "Ladybug_WetBulbTemp": ["LB Humidity Metrics", None],
    "Ladybug_Adaptive Comfort Chart": ["LB Adaptive Chart", None],
    "Ladybug_Kmz Generator": [None, "Legacy component was dependent on Google Maps API,\nwhich has become paid."],
    "Ladybug_View Analysis": ["LB View Percent", "For studying whether an set of points is visible,\nuse 'LB Visibility Percent' instead of 'LB View Percent'."],
    "Ladybug_Residential Hot Water": ["HB Service Hot Water", "See also HB-Energy Program Types for a variety of\nservice hot water demand profiles."],
    "Ladybug_North": ["LB Compass", None],
    "Ladybug_Forward Raytracing": ["LB Surface Ray Tracing", None],
    "Ladybug_Commercial Public Apartment Hot Water": ["HB Service Hot Water", "See also HB-Energy Program Types for a variety of\nservice hot water demand profiles."],
    "Ladybug_Set the View": ["LB Set View", None],
    "Ladybug_DC to AC derate factor": ["HB Electric Load Center", "The 'Electric Load Center' component uses the PVWatts inverter\nperformance curve implemented in E+ to convert DC to AC."],
    "Ladybug_Thermal Comfort Indices": ["LB PET Comfort", "For thermal comfort indices other than PET,\nsee the 'LB Thermal Indices' component."],
    "Ladybug_Countour Mesh": [None, "Coming soon with support for contour curves only\n(colored mesh between curves is unreliable)."],  # SOON!
    "Ladybug_Solar Water Heating System Detailed": [None, "Coming Soon to HB-Energy!"],  # SOON!
    "Ladybug_Gradient Library": ["LB Color Range", None],
    "Ladybug_Steady State Surface Temperature": [None, "Coming Soon!"],  # SOON!
    "Ladybug_Construct Location": ["LB Construct Location", None],
    "Ladybug_Adaptive Comfort Parameters": ["LB Adaptive Comfort Parameters", None],
    "Ladybug_Decompose Location": ["LB Deconstruct Location", None],
    "Ladybug_view Rose": ["LB View Rose", None],
    "Ladybug_Orientation Study Parameters": [None, "Use the native Grasshopper 'Rotate' component with\nsliders and record components to run orientation studies."],
    "Ladybug_rIP2rSI": ["LB Unit Converter", "The 'LB Unit Converter' converts individual values.\nTo convert data collections use the 'LB To SI' component."],
    "Ladybug_Open EPW Weather File": ["File Path", "Right-click the native Grasshopper 'File Path' component\nand choose 'Select one existing file'."],
    "Ladybug_Terrain Generator": ["LB Construct Location", "Legacy component was dependent on Google Maps API,\nwhich has become paid."],
    "Ladybug_C2F": ["LB To IP", "The 'LB To IP' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_ms2mph": ["LB To IP", "The 'LB To IP' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Radiant Asymmetry Discomfort": ["LB Radiant Asymmetry", None],
    "Ladybug_Adaptive Comfort Calculator": ["LB Adaptive Comfort", None],
    "Ladybug_lux2ft-cd": ["LB Unit Converter", "The 'LB Unit Converter' converts individual values.\nTo convert data collections use the 'LB To IP' component."],
    "Ladybug_download EPW Weather File": ["LB EPWmap", None],
    "Ladybug_Day_Month_Hour": ["LB HOY to DateTime", None],
    "Ladybug_CDH_HDH": ["LB Degree Days", None],
    "Ladybug_Colored Sky Visualizer": [None, "Coming Soon!"],  # SOON!
    "Ladybug_BTU2Wh": ["LB To SI", "The 'LB To SI' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Sky Dome": ["LB Sky Dome", None],
    "Ladybug_Ankle Draft Discomfort": ["LLB Ankle Draft", None],
    "Ladybug_Recolor Mesh": ["LB Spatial Heatmap", None],
    "Ladybug_M3s2Cfm": ["LB To IP", "The 'LB To IP' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."],
    "Ladybug_Comfort Mannequin": [None, "There may be a future component for radiant thermal studies\nof human geometry that may use the mannequin geometry."],
    "Ladybug_Whm2BTUft": ["LB To IP", "The 'LB To IP' component converts units of data collections.\nTo convert individual values, use the 'LB Unit Converter'."]
}

HONEYBEE_MAP = {
    "Honeybee_Lookup Daylighting Folder": [None, "No longer needed as most HB-Radiance result-parsing components\naccept the root of the result folder."],
    "Honeybee_Set Zone Properties": ["HB Set Multiplier", "All Room geometry attributes are now always computed from the geometry.\nThe only set-able properties are the multiplier and whether the floor area is excluded."],
    "Honeybee EP context Surfaces": ["HB Shade", None],
    "Honeybee_IES Custom Lamp": [None, "Coming Soon!"],  # SOON!
    "Honeybee_PerimeterCoreZoning": ["HB Rooms by Orientation", None],
    "Honeybee_Generate Cumulative Sky": ["HB Cumulative Radiation", "Recipe components now also run the Radiance simulation."],
    "Honeybee_Seasonal Schedule": ["HB Seasonal Schedule", None],
    "Honeybee_Radiance Trans Material By Color": ["HB Translucent Modifier 3", "Use the native Grasshopper 'Split ARGB' component\nto convert colors to an input for the new component."],
    "Honeybee_Surface Data Based On Type": ["HB Face Result by Type", None],
    "Honeybee_Read EP HVAC Result": ["HB Read Custom Result", "It is now recommended that HVAC outputs be requested one-by-one\nand loaded with the 'Custom Result' component.\nThis avoids long result-parsing times for thousands of HVAC nodes."],  # possible better version
    "Honeybee_Masses2Zones": ["HB Room from Solid", None],
    "Honeybee_IES Project": [None, "Coming Soon!"],  # SOON!
    "Honeybee_SplitBuildingMass2Floors": ["DF Building from Solid", "Workflows for generating full-building energy models from\nmassing or footprints are now in the Dragonfly tab."],
    "Honeybee_Create EP Plenum": ["HB Plenum", None],
    "Honeybee_infORventPerArea Calculator": ["HB Apply Absolute Load Values", "Absolute flow rates of infiltration and ventilation are now\nspecified with 'HB Apply Absolute Load Values.'\nBlower door flow rate conversions can be done with the\n'HB Blower Pressure Converter' component."],
    "Honeybee_Ambient Resolution": ["HB Ambient Resolution", None],
    "Honeybee_Generate Test Points": ["LB Generate Point Grid", "Gridded mesh and point generation is now\nall done with a single Ladybug component."],
    "Honeybee_Generate Standard CIE Sky": ["HB CIE Standard Sky", None],
    "Honeybee_Microclimate Map Analysis": [None, "No longer needed as each of the thermal mapping\nrecipe components also runs the simulation."],
    "Honeybee_Decompose Based On Boundary Condition": ["HB Faces by BC", "The 'HB Faces by BC' component returns the Face objects organized by BC.\nIf you are only seeking to visualize the boundary conditions,\nuse the 'HB Visualize by BC' component."],
    "Honeybee_EnergyPlus Glass Material": ["HB Glass Modifier", None],
    "Honeybee_Set Radiance Materials": ["HB Apply ModifierSet", "ModifierSets are now used to specify Radiance materials by type and BC.\nCreate a ModifierSet with the 'HB ModifierSet' component."],
    "Honeybee_Radiance Metal Material By Color": ["HB Metal Modifier 3", "Use the native Grasshopper 'Split ARGB' component\nto convert colors to an input for the new component."],
    "Honeybee_Vertical Sky Component": ["HB Sky View", "Set cloudy_sky option to True and use vertically-oriented\ngeometry with the 'HB Sky View' recipe to get VSC\nas described by the UK BRE."],
    "Honeybee_AskMe": [None, "No longer needed as this is better done with our search-able online component docs.\nhttps://discourse.ladybug.tools/pub/lbt-grasshopper-doc"],
    "Honeybee_Set EP Zone Construction": ["HB Apply ConstructionSet", "ConstructionSets are now used to specify constructions by type and BC.\nCreate a ConstructionSet with the 'HB ConstructionSet' component."],
    "Honeybee_EnergyPlus Construction": ["HB Opaque Construction", "Note that there are now separate components for 'HB Opaque Construction'\nand 'HB Window Construction.'"],
    "Honeybee_Set EnergyPlus Zone Thresholds": ["HB Apply Setpoint Values", "Note that daylight control setpoints are now specified\non a separate 'HB Apply Daylight Control' component."],
    "Honeybee_IntersectMasses": ["HB Intersect Solids", "The new 'HB Intersect Solids' component can accept either\nBrep geometries or entire Honeybee Rooms."],
    "Honeybee_Generate Average Sky": ["HB Custom Sky", "Recreating the original 'Average Sky' behavior is possible by deconstructing\nEPW radiation data and averaging values to feed into the 'HB Custom Sky.'"],
    "Honeybee_Call from EP Construction Library": ["HB Search Constructions", None],
    "Honeybee_simple_Inverter": ["HB Electric Load Center", "The new 'Electric Load Center' component uses the PVWatts inverter\nperformance curve to convert DC to AC."],
    "Honeybee_Zone Attribute List": ["HB Room Attributes", None],
    "Honeybee_Constant Schedule": ["HB Constant Schedule", None],
    "Honeybee_R-Value With Air Films": ["HB Deconstruct Construction", "The 'U-Factor' outputs of the 'HB Deconstruct Construction' component\ninclude air films while the 'R-value' outputs do not."],
    "Honeybee_orientHBGlz": ["HB Facade Parameters", None],
    "Honeybee_Read DS Result for a point": ["HB Annual Results to Data", "Time series results are now loaded to data collections.\nThere will be one data collection per point."],
    "Honeybee_Therm Material": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Generate EP Output": ["HB Simulation Output", "Simulation Output now gets connected to the 'HB Simulation Parameter'\ncomponent instead of the OpenStudio component."],
    "Honeybee_Get Zone EnergyPlus Loads": ["HB Color Room Attributes", "The 'HB Color Room Attributes' component both visualizes and returns\nthe loads assigned to rooms. Use the 'HB Room Energy Attributes'\ncomponent to see all available loads."],
    "Honeybee_Visualize Microclimate Map": ["HB Visualize Thermal Map", None],
    "Honeybee_Make Adiabatic By Type": ["HB Adiabatic by Type", "For more customized assignment of Adiabatic boundary conditions,\nthe 'HB Properties by Guide Surface' can alternatively be used."],
    "Honeybee_Annual Daylight Simulation": ["HB Annual Daylight", "Recipe components now also run the Radiance simulation."],
    "Honeybee_Import WINDOW Glz System": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Surface Attribute List": ["HB Face Attributes", None],
    "Honeybee_PET Analysis Recipe": [None, "Coming Soon!"],  # SOON!
    "Honeybee_Therm Material to EnergyPlus Material": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Read HVAC Sizing": ["HB Read HVAC Sizing", None],
    "Honeybee_OpenFileDirectory": ["LB Open Directory", None],
    "Honeybee_Radiance BSDF Material": ["HB BSDF Modifier", None],
    "Honeybee Lighting Density Calculator": [None, "Most factors that relate LPD to illuminance targets are now\nincorporated into daylight control schedules, such as those in\nthe 'HB Daylight Control Schedule' or the 'HB Apply Daylight Control' components."],
    "Honeybee_AddEarthtube": [None, "Coming Soon!"],  # SOON!
    "Honeybee_Set Loads And Schedules": ["HB Apply ProgramType", "Use the 'HB Search Programs' component to see a\nfull list of currently-supported programs."],
    "Honeybee_IES Luminaire": [None, "Coming Soon!"],  # SOON!
    "Honeybee_Daily Schedule": ["HB Gene Pool to Day Schedule", None],
    "Honeybee_Custom Radiant Environment": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Generator_PV": ["HB Photovoltaic Properties", "Photovoltaic properties are now always assigned to\nShades, which represent the PV geometry."],
    "Honeybee_Separate conditioned and unconditioned zones": ["HB Rooms by Attribute", "Use the 'HB Room Energy Attributes' component to select\nthe attribute name for 'Is Conditioned.'"],
    "Honeybee_addHBGlz": ["HB Add Subface", "The 'HB Add Subface' component does not accept Breps\nand raw geometry must be first processed through the\n'HB Aperture' or 'HB Door' component."],
    "Honeybee_PMV Comfort Analysis Recipe": ["HB PMV Comfort Map", "Recipe components now also run the simulation."],
    "Honeybee_Read RAD Result": [None, "No longer needed as there are several components for parsing\nannual results from the root of the result folder."],
    "Honeybee_Radiance Metal Material": ["HB Metal Modifier", None],
    "Honeybee_Convert IMG": ["HB HDR to GIF", "GIF is currently the only supported conversion type.\nMore can be added upon request on our forum."],
    "Honeybee_Get or Set HB Object Name": ["HB Set Identifier", "The identifier is the unique name of the object used for simulation."],
    "Honeybee_Find Non-Convex": [None, "No longer needed as all complications from concave geometry\nin simulation engines are automatically resolved."],
    "Honeybee_Radiance Opaque Material": ["HB Opaque Modifier", None],
    "Honeybee_generationsystem": ["HB Electric Load Center", "The 'HB Electric Load Center' component already\nincludes the properties of the inverter."],
    "Honeybee_Generate Sky With Certain Illuminance level": ["HB Certain Illuminance", None],
    "Honeybee_Set EP Surface Construction": ["HB Apply Opaque Construction", "For applying child constructions, use the\n'HB Apply Window Construction' component."],
    "Honeybee_DSParameters": ["HB Radiance Parameter", "Daysim is no longer used in the LBT plugin.\nAll parameters are native Radiance parameters."],
    "Honeybee_Decompose EnergyPlus Schedule": ["HB Deconstruct Schedule", None],
    "Honeybee_ Run Energy Simulation": ["HB Annual Loads", "The 'HB Annual Loads' component runs an optimized EnergyPlus simulation\nthat is designed for only returning monthly heating/cooling/electric loads."],
    "Honeybee_MSH2RAD": ["HB Shade", "Plug Rhino Meshes into this component to have it keep the geometry\nin an optimized mesh format for simulation."],
    "Honeybee_Read_generation_system_results": ["HB Read Generation Result", None],
    "Honeybee_Search EP Construction": ["HB Search Constructions", None],
    "Honeybee_Mirror Honeybee": ["HB Mirror Modifier", None],
    "Honeybee_Outdoor Comfort Analysis Recipe": ["HB UTCI Comfort Map", "Recipe components now also run the simulation."],
    "Honeybee_Dump Honeybee Objects": ["HB Dump Objects", "Both Honeybee Models (geometry) and energy/radiance objects\ncan be dumped to files."],
    "Honeybee_Re-run OSM": ["HB Run OSM", None],
    "Honeybee_HVAC Cooling Details": [None, "No longer used as options for HVAC customization live on\nthe components that assign the HVAC template."],
    "Honeybee_OpenStudio to gbXML": ["HB Dump gbXML", None],
    "Honeybee_Set EP Air Flow": ["HB Window Opening", "The 'HB Window Opening' component is for air flow resulting from operable windows.\,For assigning fan-driven air flow that is separate from the HVAC system,\nuse the 'HB Fan Ventilation' component."],
    "Honeybee_Decompose EP Material": ["HB Deconstruct Material", None],
    "Honeybee_Import THERM XML": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Separate Zones By Program": ["HB Rooms by Attribute", "Use the 'HB Room Energy Attributes' component to select\nthe attribute name for 'Program.'"],
    "Honeybee_Solve Adjacencies": ["HB Solve Adjacency", None],
    "Honeybee_Skylight Based on Ratio": ["HB Skylights by Ratio", None],
    "Honeybee_Get EnergyPlus Schedules": ["HB Deconstruct ProgramType", "Deconstruct the individual load objects out of the 'HB Deconstruct ProgramType'\ncomponent to get both the load values and schedules in the program."],
    "Honeybee_Load OpenStudio Measure": ["HB Load Measure", None],
    "Honeybee_Select by Type": ["HB Faces by Type", "The 'HB Faces by Type' component returns the Face objects organized by type.\nIf you are only seeking to visualize the face types,\nuse the 'HB Visualize by Type' component."],
    "Honeybee_EnergyPlus Opaque Material": ["HB Opaque Material", None],
    "Honeybee_Set EP Zone Interior Construction": ["HB Interior Construction Subset", "Plug the 'HB Interior Construction Subset' component into the\n'HB ConstructionSet' component to assign interior constructions to Rooms\nusing the 'HB Apply ConstructionSet' component."],
    "Honeybee_Re-run IDF": ["HB Run IDF", None],
    "Honeybee_Run Daylight Simulation": [None, "No longer needed as each of the Radiance recipe\ncomponents also runs the simulation."],
    "Honeybee_Call from Radiance Library": ["HB Search Modifiers", None],
    "Honeybee_Radiance Trans Material": ["HB Translucent Modifier", None],
    "Honeybee_Add to EnergyPlus Library": ["HB Dump Objects", "Write energy objects to files in the sub-folders of\n'AppData\Roaming\ladybug_tools\standards' to add them to\nyour permanent user library."],
    "Honeybee_createHBZones": ["HB Room", None],
    "Honeybee_Assembly Uvalue": ["HB Deconstruct Construction", "If the window constructions plugged into the 'HB Deconstruct Construction'\ncomponent have a frame, this will be included in the output\nU-Factor and R-Value."],
    "Honeybee_ChangeHBObjName": ["HB Set Identifier", "The identifier is the unique name of the object used for simulation."],
    "Honeybee_Glare Analysis": ["HB Glare Postprocess", None],
    "Honeybee_Radiance Opaque Material By Color": ["HB Opaque Modifier 3", "Use the native Grasshopper 'Split ARGB' component\nto convert colors to an input for the new component."],
    "Honeybee_Daysim Occupancy Generator Based On List": ["HB Fixed Interval Schedule", "Note that energy schedules can be used as input for the\n'HB Annual Daylight' occupancy."],
    "Honeybee_Read All the Hourly Results from Annual Daylight Study": ["HB Annual Results to Data", "By default, 'HB Annual Results to Data' reads all results but individual\npoints can be used to only import some sensors."],
    "Honeybee_Decompose Based On Type": ["HB Faces by Type", "The 'HB Faces by Type' component returns the Face objects organized by type.\nIf you are only seeking to visualize the face types,\nuse the 'HB Visualize by Type' component."],
    "Honeybee_Separate Zones By Orientation": ["HB Rooms by Orientation", None],
    "Honeybee_Radiance Materials Info": [None, "No longer needed as the text representation of Radiance\nmodifiers shows all relevant info."],
    "Honeybee_Read Annual Result I": ["HB Annual Daylight Metrics", None],
    "Honeybee_ListZonePrograms": ["HB Search Programs", None],
    "Honeybee_createHBSrfs": ["HB Face", None],
    "Honeybee_Energy Shade Benefit Evaluator": ["HB Load Shade Benefit", "The new 'HB Load Shade Benefit' performs all calculations,\nincluding running the EnergyPlus simulation under the hood\n to get the loads."],
    "Honeybee_Make Adiabatic": [None, "No longer needed as adiabatic boundary conditions can be assigned when\nfirst creating the 'HB Face' or they can be applied using the\n'HB Properties by Guide Surface' component."],
    "Honeybee_Set Exposure for HDR": ["HB Adjust HDR", None],
    "Honeybee_bldgPrograms": ["HB Building Programs", None],
    "Honeybee_Read Microclimate Matrix": ["HB Read Thermal Matrix", None],
    "Honeybee_Visualise_Honeybeegeneration_cashflow": [None, "No plans are in place to port this component to LBT\nunless we find a way to make it generic for different\nenergy conservation strategies."],
    "Honeybee_HVAC Air Details": ["HB All-Air HVAC", "No longer used as options for HVAC customization live on\nthe components that assign the HVAC template."],
    "Honeybee_Read THERM Result": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Extrude Windows": ["HB Extruded Border Shades", None],
    "Honeybee_Daysim Electrical Lighting Use": ["HB Daylight Control Schedule", "The recommended workflow is to apply the schedule from the 'HB Daylight Control Schedule'\nto an energy simulation to get the final lighting energy use."],
    "Honeybee_ExportEPC": [None, "EPC is deprecated and there are no plans to update this component."],
    "Honeybee_Generate Dark Sky": ["HB Certain Illuminance", "Plug in a zero for the sky illuminance value\nto make a completely dark sky."],
    "Honeybee_Label Zones": ["HB Label Rooms", None],
    "Honeybee_Convert TIF to HDR": [None, "There are currently no plans to translate between TIF and HDR\nunless this is requested on the forum."],
    "Honeybee_Balance Temperature Calculator": ["HB Balance Temperature", None],
    "Honeybee_Create Therm Polygons": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Apply OpenStudio Measure": ["HB Run OSW", "Measures are typically assigned with the 'HB Model to OSM' component\nbut incorporating them into and OpenStudio Workflow (OSW)\nJSON will allow you to run them with the 'HB Run OSW' component."],
    "Honeybee_Label Zone Surfaces": ["HB Label Faces", None],
    "Honeybee_Radiance Mirror Material": ["HB Mirror Modifier", None],
    "Honeybee_Read Annual Result II": ["HB Annual Daylight Metrics", None],
    "Honeybee_Adaptive Comfort Analysis Recipe": ["HB Adaptive Comfort Map", "Recipe components now also run the simulation."],
    "Honeybee_Honeybee": [None, "No longer needed in LBT as all core functions\nlive outside Grasshopper with your installation."],
    "Honeybee_Separate Zones By Floor": ["HB Rooms by Floor Height", None],
    "Honeybee_Glazing based on ratio": ["HB Apertures by Ratio", None],
    "Honeybee_Refine Daylight Simulation": [None, "Not feasible given the optimized way that the\nnew Radiance recipes are parallelized."],
    "Honeybee_ShadowPar": ["HB Shadow Calculation", None],
    "Honeybee_Search EP Schedule Library": ["HB Search Schedules", None],
    "Honeybee_Daysim Shading State": ["HB Dynamic State", None],
    "Honeybee_Advanced Dynamic Shading Recipe": ["HB Dynamic Aperture Group", None],
    "Honeybee_Image Based Simulation": ["HB Point-In-Time View-Based", "Recipe components now also run the simulation."],
    "Honeybee_DecomposeHBZone": ["HB Deconstruct Object", None],
    "Honeybee_FalseColor": ["HB False Color", None],
    "Honeybee_gbXML to Honeybee": ["HB Load gbXML OSM IDF", None],
    "Honeybee_Create Therm Boundaries": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Matrix to Data Tree": ["LB Deconstruct Matrix", None],
    "Honeybee_HVACSystemsList": ["HB All-Air HVAC Templates", "Note that the LBT plugin has 3 separate HVAC system dropdown components:\nAll-Air, DOAS, and HeatCool."],
    "Honeybee_Energy Simulation Par": ["HB Simulation Parameter", None],
    "Honeybee_Indoor View Factor Calculator": [None, "No longer needed as view factor calculations happen within each\nthermal map recipe simulation (using Radiance)."],
    "Honeybee_Daysim Occupancy Generator": ["HB Weekly Schedule", "Note that energy schedules can be used as input for the\n'HB Annual Daylight' occupancy."],
    "Honeybee_Set EnergyPlus Zone Schedules": ["HB Apply Room Schedules", None],
    "Honeybee_Read EP Result": ["HB Read Room Energy Result", None],
    "Honeybee_Lookup EnergyPlus Folder": [None, "No longer needed as practically all EnergyPlus simulation results\nnow live in a single SQL file."],
    "Honeybee_EnergyPlus Window Air Gap": ["HB Window Gap Material", None],
    "Honeybee_Import WINDOW IDF Report": ["HB Window Construction", "A more appropriate component that imports from IDF will be coming soon."],  # SOON!
    "Honeybee_Radiance Glass Material": ["HB Glass Modifier", None],
    "Honeybee_Annual Schedule": ["HB Weekly Schedule", None],
    "Honeybee_Watch The Sky": ["HB Visualize Sky", None],
    "Honeybee_Thermal Autonomy Analysis": [None, "No longer needed as all thermal mapping components compute\nThermal Comfort Percent (TCP) of occupied hours\nas part of the simulation."],
    "Honeybee_Import rad": ["HB Check Scene", "The 'HB Check Scene' component offers a better way to check\n thatgeometry has been correctly translated to Radiance.\nAn importer from RAD to Honeybee may be added in the future\nto assist in model creation / interoperability."],
    "Honeybee_Radiance Glass Material By Color": ["HB Glass Modifier 3", "Use the native Grasshopper 'Split ARGB' component\nto convert colors to an input for the new component."],
    "Honeybee_EnergyPlus Window Material": ["HB Window Material", None],
    "Honeybee_Normalize Data by Floor Area": ["HB Normalize by Floor Area", None],
    "Honeybee_Color Surfaces by EP Result": ["HB Color Faces", None],
    "Honeybee_Load Honeybee Objects": ["HB Load Objects", "Both Honeybee Models (geometry) and energy/radiance objects\ncan be loaded from files."],
    "Honeybee_EnergyPlus Window Shade Generator": ["HB Louver Shades", "When simulating blinds as part of a window construction,\nuse the 'HB Window Construction Shade' component\ninstead of 'HB Louver Shades.'"],
    "Honeybee_RADParameters": ["HB Radiance Parameter", None],
    "Honeybee_Generate Climate Based Sky": ["HB Climatebased Sky", None],
    "Honeybee_Create CSV Schedule": ["HB Fixed Interval Schedule", None],
    "Honeybee_Decompose EP Construction": ["HB Deconstruct Construction", None],
    "Honeybee_Surface Data Based On Type Detailed": ["HB Face Result by Type", None],
    "Honeybee_Rotate Honeybee": ["HB Rotate", None],
    "Honeybee_Set EnergyPlus Zone Loads": ["HB Apply Load Values", None],
    "Honeybee_Generate Zone Test Points": ["HB Sensor Grid from Rooms", None],
    "Honeybee_Import dgp File": ["HB Glare Postprocess", "The postprocessing of HDR files for glare is fast enough that\nit's easiest to just run this again on top of the HDR file."],
    "Honeybee_Convert HDR to TIF": ["HB HDR to GIF", "GIF is currently the only supported conversion type.\nMore can be added upon request on our forum."],
    "Honeybee_Radiance Mirror Material By Color": ["HB Mirror Modifier 3", "Use the native Grasshopper 'Split ARGB' component\nto convert colors to an input for the new component."],
    "Honeybee_Customize EnergyPlus Objects": [None, "Customization of IDF text that is this specific is better done with\nnative Grasshopper text-editing components and the additional strings\ninput on the energy simulation components."],
    "Honeybee_Scale Honeybee": ["HB Scale", None],
    "Honeybee_Daysim Glare Control Recipe": ["HB Aperture Group Schedule", None],
    "Honeybee_Read Hourly Results from Annual Daylight Study": ["HB Annual Average Values", None],
    "Honeybee_Export To OpenStudio": ["HB Model to OSM", None],
    "Honeybee_Color Zones by EP Result": ["HB Color Rooms", None],
    "Honeybee_Daysim shading group sensors": ["HB Aperture Group Schedule", None],
    "Honeybee_Daylight Factor Simulation": ["HB Daylight Factor", None],
    "Honeybee_IES Luminaire Zone": [None, "Coming Soon!"],  # SOON!
    "Honeybee_Conceptual Dynamic Shading Recipe": ["HB Automatic Aperture Group", None],
    "Honeybee_Get EnergyPlus Loads": ["HB Deconstruct ProgramType", "Deconstruct the individual load objects out of the 'HB Deconstruct ProgramType'\ncomponent to get both the load values and schedules in the program."],
    "Honeybee_Write THERM File": [None, "It's unknown whether Therm will be ported to LBT\ngiven the known limitations/bugs of it's closed source meshing\nand exclusive reliance on Windows."],  # uncertain
    "Honeybee_Remove Glazing": ["HB Apertures by Ratio", "Set the ratio to zero to have the 'HB Apertures by Ratio'\ncomponent remove all windows."],
    "Honeybee_Move Honeybee": ["HB Move", None],
    "Honeybee_EnergyPlus Shade Material": ["HB Shade Material", None],
    "Honeybee_Condensation calculator": [None, "There are no plans to port this component over as it is very specific to THERM."],  # uncertain
    "Honeybee_Generate Custom Sky": ["HB Custom Sky", None],
    "Honeybee_Call from EP Schedule Library": ["HB Search Schedules", None],
    "Honeybee_Get Zone EnergyPlus Schedules": ["HB Color Room Attributes", "The 'HB Color Room Attributes' component both visualizes and returns\nthe schedules assigned to rooms. Use the 'HB Room Energy Attributes'\ncomponent to see all available schedules."],
    "Honeybee_Update Honeybee": ["LB Versioner", None],
    "Honeybee_Make Adiabatic by Name": ["HB Properties by Guide Surface", "The 'HB Properties by Guide Surface' provides a better level of control\nwhen making just a few Faces of a whole Room adiabatic."],
    "Honeybee_HVAC Heating Details": [None, "No longer used as options for HVAC customization live on\nthe components that assign the HVAC template."],
    "Honeybee_Construct Energy Balance": ["HB Thermal Load Balance", None],
    "Honeybee_SplitFloor2ThermalZones": ["HB Straight Skeleton", "The 'HB Straight Skeleton' component is more reliable than\nits legacy counterpart but works from flat floor plates instead of solids."],
    "Honeybee_Read EP Surface Result": ["HB Read Face Result", None],
    "Honeybee_Import idf": ["HB Load gbXML OSM IDF", None],
    "Honeybee_Thermally Bridged EP Construction": [None, "There are no plans to port this component over as it is very specific to THERM."],  # uncertain
    "Honeybee_Assign HVAC System": ["HB All-Air HVAC", "Note that the LBT plugin has 3 separate components\nfor applying HVAC system templates: All-Air, DOAS, and HeatCool."],
    "Honeybee_Convert HDR to GIF": ["HB HDR to GIF", None],
    "Honeybee_Glazing Parameters List": ["HB Facade Parameters", None],
    "Honeybee_Import Pts File": ["ReadFile", "The native Grasshopper 'Read File' component can read pts files,\nwhich are easily processed with native GH text components."],  # SOON!
    "Honeybee_Create EP Ground": ["HB Ground", None],
    "Honeybee_Read EP Custom Result": ["HB Read Custom Result", None],
    "Honeybee_Convert EnergyPlus Schedule to Values": ["HB Schedule to Data", None],
    "Honeybee_Daysim Annual Profiles": ["HB Imageless Annual Glare", "Daysim is no longer used by LBT but the 'HB Imageless Annual Glare' recipe\ndoes a much better job estimating the glare levels that the\nlegacy 'Annual Profiles' tried to report."],
    "Honeybee_Add Internal Mass to Zone": ["HB Internal Mass", None],
    "Honeybee_EnergyPlus NoMass Opaque Material": ["HB Opaque Material No Mass", None],
    "Honeybee_Set EP Zone Underground Construction": ["HB Ground Construction Subset", "Plug the 'HB Ground Construction Subset' component into the\n'HB ConstructionSet' component to assign ground constructions to Rooms\nusing the 'HB Apply ConstructionSet' component."],
    "Honeybee_Grid Based Simulation": ["HB Point-In-Time Grid-Based", "Recipe components now also run the simulation."],
    "Honeybee_Simulation Control": ["HB Simulation Control", None],
    "Honeybee_Lighting control Recipe": ["HB Daylight Control Schedule", None],
    "Honeybee_Add to Radiance Library": ["HB Dump Objects", "Write Radiance objects to files in the sub-folders of\n'AppData\Roaming\ladybug_tools\standards' to add them to\nyour permanent user library."],
    "Honeybee_Read Result Dictionary": ["HB Read Result Dictionary", None]
}


def insert_new_user_object(user_object, component, doc):
    """Insert a new user object next to an existing component in the Grasshopper doc.

    Args:
        user_object: A Grasshopper user object component instance.
        component: The outdated component where the userobject will be inserted
            next to.
        doc: The Grasshopper document object.
    """
    # use component to find the location
    x = component.Attributes.Pivot.X + 30
    y = component.Attributes.Pivot.Y - 20
    user_object.Attributes.Pivot = System.Drawing.PointF(x, y)
    # insert the new one
    doc.AddObject(user_object, False, 0)


def insert_new_native_gh_component(new_comp_id, component, doc):
    """Insert a new native Grasshopper component in the Grasshopper doc.

    Args:
        new_comp_id: The GUID of the native grasshopper component to be inserted.
        component: The outdated component where the userobject will be inserted
            next to.
        doc: The Grasshopper document object.
    """
    # create the new component instance
    comp_instance = Grasshopper.Instances.ComponentServer.EmitObject(new_comp_id)
    comp_instance.CreateAttributes()
    # use component to find the location
    x = component.Attributes.Pivot.X + 30
    y = component.Attributes.Pivot.Y - 20
    comp_instance.Attributes.Pivot = System.Drawing.PointF(x, y)
    # insert the new one
    doc.AddObject(comp_instance, False)


def mark_component(doc, component, note=None):
    """Put a circular red group around a component and label it with a note.

    Args:
        doc: The Grasshopper document object.
        component: A Grasshopper component object on the canvas to be circled.
        note: Text for the message to be displayed on the circle.
    """
    grp = gh.Special.GH_Group()
    grp.CreateAttributes()
    grp.Border = gh.Special.GH_GroupBorder.Blob
    grp.AddObject(component.InstanceGuid)
    grp.Colour = System.Drawing.Color.IndianRed  # way to pick a racist color name, .NET
    if note:
        grp.NickName = note
    else:
        grp.NickName = 'Legacy Component!'
    doc.AddObject(grp, False)
    return True


def suggest_new_component(component, updating_component):
    """Drop a suggested LBT component on the canvas for an input Legacy LB+HB component.

    This includes circling the component in red if it is a Legacy component,
    adding the a message to this red circle (if applicable), identifying the
    suggested LBT component in the LADYBUG_MAP and HONEYBEE_MAP (if it exists),
    and dropping an instance of the new LBT component next to the Legacy component.

    Args:
        component: A Grasshopper legacy component object on the canvas for which
            a LBT component will be suggested.
        updating_component: An object for the component that is doing the updating.
            This will be used to give warnings and access the Grasshopper doc.
            Typically, this can be accessed through the ghenv.Component call.
    """
    # identify the correct user object sub-folder to which the component belongs
    comp_name_str = str(component.Name)
    if comp_name_str.startswith('Ladybug'):
        try:
            new_comp_name, msg = LADYBUG_MAP[comp_name_str]
        except KeyError:  # not an official Legacy Ladybug component
            warning = 'Failed to identify "{}" as a legacy component.'.format(
                comp_name_str)
            give_warning(updating_component, warning)
            return warning
    elif comp_name_str.startswith('Honeybee'):
        try:
            new_comp_name, msg = HONEYBEE_MAP[comp_name_str]
        except KeyError:  # not an official Legacy Ladybug component
            warning = 'Failed to identify "{}" as a legacy component.'.format(
                comp_name_str)
            give_warning(updating_component, warning)
            return warning
    else:  # unidentified plugin; see if we can find it in the root
        return  # not a Legacy component at all

    # get the document
    doc = updating_component.OnPingDocument()
    # define the callback function and update the solution
    def call_back(document):
        component.ExpireSolution(False)

    doc.ScheduleSolution(2, gh.GH_Document.GH_ScheduleDelegate(call_back))

    # circle the component in red
    mark_component(doc, component, msg)

    # if there's a suggested component, loop drop it in the canvas
    if new_comp_name is not None:
        ghuser_file = '%s.ghuser' % new_comp_name
        for lbt_uo_f in LBT_UO_FOLDERS:
            fp = os.path.join(UO_FOLDER, lbt_uo_f, 'user_objects', ghuser_file)
            if os.path.isfile(fp):
                uo = gh.GH_UserObject(fp).InstantiateObject()
                insert_new_user_object(uo, component, doc)
                break
        else:  # no installed LBT component was found
            # check to see if there's a native GH component
            new_component = Rhino.NodeInCode.Components.FindComponent(new_comp_name)
            if new_component is not None:
                new_comp_id = new_component.ComponentGuid
                insert_new_native_gh_component(new_comp_id, component, doc)
            elif new_comp_name == 'File Path':
                new_comp_id = System.Guid('06953bda-1d37-4d58-9b38-4b3c74e54c8f')
                insert_new_native_gh_component(new_comp_id, component, doc)
            else:  # no replacement component was found; give a warning
                warning = 'Failed to find the installed component for "{}", which ' \
                    'is the suggested update for "{}".'.format(new_comp_name, comp_name_str)
                give_warning(updating_component, warning)
                return warning

    return 'Successfully suggested update for %s.' % component.Name
