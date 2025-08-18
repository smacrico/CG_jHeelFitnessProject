######################################
########### personal laptop Runs######
###### MSBuddyFitnessApp #############
######################################

### Garmin DownLoad Latest ###########
& C:/Python313/python.exe C:/Python313/Scripts/garmindb_cli.py --all --download --import --analyze --latest

& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject/GarminParse_PlugIn/jHeel_plugin v5.1.py"








### Run Analysis
#2
& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject/Apex_RunAnalyzer/runAnalysis/scripts/createRunAnalDB.py"

#3 RunAnalysis ###

& C://Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject/Apex_RunAnalyzer/runAnalysis/scripts/RunningAnalysis_v6.0.py"
& C://Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject/Apex_RunAnalyzer/runAnalysis/scripts/RunningAnalysis_v50.py"



    #interactive DashBoard - Run Analysis
   
    streamlit run scripts/app.py


    #interactive DashBoard - Garmin Health Data
   
    streamlit run app/main.py


#4 HRV Analysis

& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject/MSBuddy_FitnessApp/HRV_DWH/scripts/HRV_datawarehouse.py"

& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject/MSBuddy_FitnessApp/HRV_DWH/scripts/HRV_dwhAnalytics_v2.py"


    #interactive DashBoard - HRV data analysis
    streamlit run hrv_streamlit_dashboard.py