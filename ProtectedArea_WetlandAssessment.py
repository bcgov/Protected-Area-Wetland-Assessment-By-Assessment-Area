'''

	Wetlands Protected Area Analysis Tier 1 Skeena East ESI
	Created By: Jesse Fraser
	June 8th 2020

	Goal:
Calculates the total protected area as well as wetland protected area and compares them.

'''
#Possibly needed imports
#import win32com.client, win32api
import sys, string, os, time, win32com.client, datetime, win32api, arcpy, arcpy.mapping , csv
#import  wml_library_arcpy_v3 as wml_library
from arcpy import env

arcpy.env.overwriteOutput = True
import sys, string, os, time , datetime, arcpy, arcpy.mapping , csv


#make sure the spatial extension is working
try:
    arcpy.CheckOutExtension("Spatial")
    from arcpy.sa import *
    from arcpy.da import *
except:
    arcpy.AddError("Spatial Extension could not be checked out")
    os.sys.exit(0)
#Set the time stamp
time = time.strftime("%y%m%d")


#Input Wetland Complex dataset
wetland_complex_input = arcpy.GetParameterAsText(0)
#wetland_complex_input = r"V:\srm\smt\Workarea\ArcProj\P17_Skeena_ESI\Data\Values\Wetlands\BaseData\WetlandsBase.gdb\Wetlands_Restart_190911\ESI_basic_Wetland_Complexes_190912"

#Protecte Area input
protectedAreas = arcpy.GetParameterAsText(1)
#protectedAreas = r"V:\srm\smt\Workarea\ArcProj\P17_Skeena_ESI\Data\Values\Wetlands\T1.5\DesignatedLands\SSAF_FWAau_NoHarvest_2018_200408.shp"

#Assessment Unit Input
AU = arcpy.GetParameterAsText(2)
#AU = r"V:\srm\smt\Workarea\ArcProj\P17_Skeena_ESI\Data\ESI_Data.gdb\AU\SSAF_fwaAU_Watersheds"

#Save Location Folder
output_save = arcpy.GetParameterAsText(3)
#output_save = r"V:\srm\smt\Workarea\ArcProj\P17_Skeena_ESI\Data\Values\Wetlands\T1"

#AU Unique ID Field
au_ID = arcpy.GetParameterAsText(4)
#au_ID = r"WATERSHED_FEATURE_ID"

#create geodatabase to work out of
save_gdb = "Wet_Protected_" + time
arcpy.CreateFileGDB_management(output_save, save_gdb)
output_gdb = output_save + r"\Wet_Protected_" + time + r".gdb"

#copy the wetland complex into the new gdb
working_au = output_gdb + r"\au_" + time
arcpy.CopyFeatures_management(AU, working_au)
'''
working_wet = output_gdb + r"\wet_" + time
test1 = arcpy.CopyFeatures_management(wetland_complex_input, working_wet)
print test1
working_prot = output_gdb + r"\prot_" + time
test2 = arcpy.CopyFeatures_management(protectedAreas, working_prot)
print test2
'''

#create Assessment Unit layer to query
arcpy.MakeFeatureLayer_management(working_au,"au_lyr")
lyr_au = arcpy.mapping.Layer("au_lyr")

#create wetland layer to query
arcpy.MakeFeatureLayer_management(wetland_complex_input,"wet_lyr")
lyr_wet = arcpy.mapping.Layer("wet_lyr")

#create protected layer to query
arcpy.MakeFeatureLayer_management(protectedAreas,"prot_lyr")
lyr_prot = arcpy.mapping.Layer("prot_lyr")

#get the  name 
desc = arcpy.Describe(wetland_complex_input)
#Get name to add FID query
#Also protect from shapefile inputs
if desc.name[-4:] == ".shp":
	wetland_name = desc.name[:-4]
else:
	wetland_name = desc.name
#get the name 
desc = arcpy.Describe(protectedAreas)
#Get name to add FID query
if desc.name[-4:] == ".shp":
	protected_name = desc.name[:-4]
else:
	protected_name = desc.name


#Create FID queries
prot_FID = r"FID_" + protected_name
wet_FID = r"FID_" + wetland_name

print wet_FID
print prot_FID

#get the areafield name to avoid geometry vs shape issue (Thanks you Carol Mahood)
desc = arcpy.Describe(lyr_au)
geomField = desc.shapeFieldName
areaFieldName = str(geomField) + "_Area"

#Make a Union feature to query for values
working_union = output_gdb + r"\wet_au_Union_" + time
arcpy.Union_analysis([working_au, protectedAreas, wetland_complex_input], working_union)

#get the areafield name to avoid geometry vs shape issue (Thanks you Carol Mahood)
fc = working_union
desc = arcpy.Describe(fc)
geomField = desc.shapeFieldName
union_areaFieldName = str(geomField) + "_Area"

#create Wetland layer to query
arcpy.MakeFeatureLayer_management(working_union,"union_lyr")
lyr_union = arcpy.mapping.Layer("union_lyr")


#add fields to working wetland feature
protected_Area = "AU_protected_area"
arcpy.AddField_management(lyr_au, protected_Area, "DOUBLE")
perc_prot = "Perc_ofAU_Protected"
arcpy.AddField_management(lyr_au, perc_prot, "DOUBLE")
wetland_Area = "AU_wetland_area"
arcpy.AddField_management(lyr_au, wetland_Area, "DOUBLE")
perc_Wetland = "Perc_ofAU_Wetlands"
arcpy.AddField_management(lyr_au, perc_Wetland, "DOUBLE")
prot_wet_area = "AU_Protected_wetland_area"
arcpy.AddField_management(lyr_au, prot_wet_area, "DOUBLE")
perc_AU_Wetland_prot = "Perc_ofAU_Protected_Wetlands"
arcpy.AddField_management(lyr_au, perc_AU_Wetland_prot, "DOUBLE")
perc_Wetland_prot = "Perc_ofWetlands_Protected_ByAU"
arcpy.AddField_management(lyr_au, perc_Wetland_prot, "DOUBLE")

sumwetland_Area = 0
sumprotected_Area = 0
sumwetland_protected_Area = 0
num_done = 0

#figure out what the AU ID field type is
fields = arcpy.ListFields(lyr_union, au_ID)
for field in fields:
	fieldType = field.type

#Iterate through AUs to clip protected area and wetlands
rows = arcpy.UpdateCursor(lyr_au)
for row in rows:
	
	sumwetland_Area = 0
	sumprotected_Area = 0
	sumwetland_protected_Area = 0
	wtrAU = row.getValue(au_ID)	
	
	#For codes that are numbers
	str_test = str(wtrAU)[:-2]
	
	
	''' Protected in AU '''
	# Def Query for given AU Protected Area - checking what field type is ID field
	if fieldType in ["Double", "Single", "Integer", "SmallInteger"]:
		lyr_union.definitionQuery = au_ID + r" = " + str_test + " AND " + prot_FID + " <> -1"
	else:
		lyr_union.definitionQuery = au_ID + r" = '" + wtrAU + "' AND " + prot_FID + " <> -1"
	
	with arcpy.da.UpdateCursor(lyr_union, [union_areaFieldName]) as cursor:		
		#Iterate through each feature to get the total area
		for test in cursor:
			sumprotected_Area = test[0] + sumprotected_Area
	'''  End   '''
	lyr_union.definitionQuery = ""
	''' Wetlands in  AU '''	
	
	# Def Query for given AU Wetland Area
	# Def Query for given AU Protected Area - checking what field type is ID field
	if fieldType in ["Double", "Single", "Integer", "SmallInteger"]:
		lyr_union.definitionQuery = au_ID + r" = " + str_test + " AND " + wet_FID + " <> -1"
	else:
		lyr_union.definitionQuery = au_ID + r" = '" + wtrAU + "' AND " + wet_FID + " <> -1"
	
	
	#Iterate through each feature to get the total area 
	with arcpy.da.UpdateCursor(lyr_union, [union_areaFieldName]) as cursor2:		
		#Iterate through each feature to get the total area
		for test2 in cursor2:
			sumwetland_Area = test2[0] + sumwetland_Area

	''' End '''
	lyr_union.definitionQuery = ""
		
	''' Wetlands Protected '''
	# Def Query for given AU Protected Wetland Area
	if fieldType in ["Double", "Single", "Integer", "SmallInteger"]:
		lyr_union.definitionQuery = au_ID + r" = " + str_test + " AND " + wet_FID + " <> -1" + " AND " + prot_FID + " <> -1"
	else:
		lyr_union.definitionQuery = au_ID + r" = '" + wtrAU + "' AND " + wet_FID + " <> -1" + " AND " + prot_FID + " <> -1"
	
	#Iterate through each feature to get the total area 
	with arcpy.da.UpdateCursor(lyr_union, [union_areaFieldName]) as cursor3:		
		#Iterate through each feature to get the total area
		for test3 in cursor3:
			sumwetland_protected_Area = test3[0] + sumwetland_protected_Area			
	''' End '''

	lyr_union.definitionQuery = ""
		
		#Populate the fields
	areaBig = row.getValue(areaFieldName)
	row.setValue(wetland_Area, sumwetland_Area)
	row.setValue(protected_Area, sumprotected_Area)
	row.setValue(prot_wet_area, sumwetland_protected_Area)
	
	
	test4 = (sumprotected_Area/areaBig)*100
	row.setValue(perc_prot, test4)
	
	test5 = (sumwetland_Area / areaBig)*100
	row.setValue(perc_Wetland, test5)
	
	test6 = (sumwetland_protected_Area / areaBig)*100
	row.setValue(perc_AU_Wetland_prot, test6)
	
	if sumwetland_Area > 0:
		test8 = (sumwetland_protected_Area/sumwetland_Area)*100
		row.setValue(perc_Wetland_prot, test8)
		
	else:
		row.setValue(perc_Wetland_prot, 0)
	rows.updateRow(row)
		
	lyr_au.definitionQuery = ""
	num_done = num_done + 1
	
	print "Done Section: " + str(num_done)
	print "Watershed ID: " + str_test
	
	sumwetland_Area = 0
	sumprotected_Area = 0
	sumwetland_protected_Area = 0
		
	

print "ALL DONE"
		