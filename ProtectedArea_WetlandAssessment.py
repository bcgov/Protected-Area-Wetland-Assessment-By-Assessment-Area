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

#Protecte Area input
protectedAreas = arcpy.GetParameterAsText(1)
#Assessment Unit Input
AU = arcpy.GetParameterAsText(2)

#Save Location Folder
output_save = arcpy.GetParameterAsText(3)

#AU Unique ID Field
au_ID = arcpy.GetParameterAsText(4)

#create geodatabase to work out of
save_gdb = "Wet_Protected_" + time
arcpy.CreateFileGDB_management(output_save, save_gdb)
output_gdb = output_save + r"\Wet_Protected_" + time + r".gdb"

#copy the wetland complex into the new gdb
working_au = output_gdb + r"\au_" + time
arcpy.CopyFeatures_management(AU, working_au)

#create Assessment Unit layer to query
arcpy.MakeFeatureLayer_management(AU,"au_lyr")
lyr_au = arcpy.mapping.Layer("au_lyr")

#add fields to working wetland feature
protected_Area = "AU_protected_area"
arcpy.AddField_management(lyr_au, protected_Area, "DOUBLE")
perc_prot = "Perc_AU_Protected"
arcpy.AddField_management(lyr_au, perc_prot, "DOUBLE")
wetland_Area = "AU_wetland_area"
arcpy.AddField_management(lyr_au, wetland_Area, "DOUBLE")
perc_Wetland = "Perc_AU_Wetlands"
arcpy.AddField_management(lyr_au, perc_Wetland, "DOUBLE")
prot_wet_area = "AU_Protected_wetland_area"
arcpy.AddField_management(lyr_au, prot_wet_area, "DOUBLE")
perc_AU_Wetland_prot = "Perc_AU_Protected_Wetlands"
arcpy.AddField_management(lyr_au, perc_AU_Wetland_prot, "DOUBLE")
perc_Wetland_prot = "Perc_Wetlands_Protected"
arcpy.AddField_management(lyr_au, perc_Wetland_prot, "DOUBLE")

#get the areafield name to avoid geometry vs shape issue (Thanks you Carol Mahood)
desc = arcpy.Describe(lyr_au)
geomField = desc.shapeFieldName
areaFieldName = str(geomField) + "_Area"

sumwetland_Area = 0
sumprotected_Area = 0
sumwetland_protected_Area = 0

num_done = 0
#Make a Union feature to query for values
working_union = output_gdb + r"\wet_au_Union_" + time
arcpy.Union_analysis([lyr_au, wetland_complex_input, protectedAreas], working_union)

#create Wetland layer to query
arcpy.MakeFeatureLayer_management(working_union,"union_lyr")
lyr_union = arcpy.mapping.Layer("union_lyr")

#get the areafield name to avoid geometry vs shape issue (Thanks you Carol Mahood)
desc = arcpy.Describe(lyr_union)
geomField = desc.shapeFieldName
union_areaFieldName = str(geomField) + "_Area"
		
#Iterate through AUs to clip protected area and wetlands
with arcpy.da.UpdateCursor(lyr_au, [au_ID, protected_Area, wetland_Area, prot_wet_area, perc_prot, perc_Wetland, perc_AU_Wetland_prot, areaFieldName, perc_Wetland_prot]) as cursor:
	for test in cursor:
		str_test = str(test[0])[:-2]
		
		#Make sure the Assessment unit is the only feature being red 
		lyr_au.definitionQuery = au_ID + r" = " + str_test
		
		#create a cursor to look inside union
		cursor2 = arcpy.SearchCursor(lyr_union)		
		
		''' Protected in AU '''
		# Def Query for given AU Protected Area
		lyr_uniondefinitionQuery =
		 
		#Iterate through each feature to get the total area
		for test2 in cursor2:
			sumprotected_Area = test2.getValue(union_areaFieldName) + sumprotected_Area
		'''  End   '''
		
		''' Wetlands in  AU '''
				
		# Def Query for given AU Wetland Area
		lyr_uniondefinitionQuery =
		
		#Iterate through each feature to get the total area 
		for test2 in cursor2:
			sumwetland_Area = test2.getValue(union_areaFieldName) + sumwetland_Area
		
		
		''' End '''
		
		''' Wetlands Protected '''
				
		# Def Query for given AU Protected Wetland Area
		lyr_uniondefinitionQuery =
		
		#Iterate through each feature to get the total area 
		for test2 in cursor2:
			sumwetland_protected_Area = test2.getValue(it_protectedWetland_AU_areaFieldName) + sumwetland_protected_Area
		

		''' End '''

		test[1] = sumprotected_Area
		test[2] = sumwetland_Area
		test[3] = sumwetland_protected_Area
		cursor.updateRow(test)
		
		test[4] = (test[1]/test[7])*100
		test[5] = (test[2]/test[7])*100
		test[6] = (test[3]/test[7])*100
		test[8] = (test[3]/test[2])*100
		
		cursor.updateRow(test)
		
		lyr_au.definitionQuery = ""
		num_done = num_done + 1
		print "Done Section: " + str(num_done)