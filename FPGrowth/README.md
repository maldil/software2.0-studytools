**INPUT** : You can use this script to generate associate rules for multiple ML libraries and cascading library updates.
        
        1. Use the output of https://github.com/maldil/software2.0-studytools/blob/master/DetectingMLLibraries/main_library_detector.py that contain all the ML libraries in each project. 
  
**OUPUT** : 

        1. Associate rules for confidance = 0.5 and minSupport 0.1
     

**Usage** : 

        1. You have to install apache spark (guidance = https://spark.apache.org/docs/latest/)
        2. Define the variable FILE_PATH in the main_fp_growth.py
        3. Use the command `spark-submit` main_fp_growth.py` to generate assosiation rules

