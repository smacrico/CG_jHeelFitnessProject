######################################
########### personal laptop Runs######
######################################
& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/GarminParse_PlugIn/jHeel_plugin v5.1 dev.py"

### Run Analysis
#2
& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/Apex_RunAnalyzer/runAnalysis/createRunAnalDB.py"

#3 RunAnalysis ###
& C://Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/Apex_RunAnalyzer/runAnalysis/RunningAnalysis_v50.py"
& C://Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/Apex_RunAnalyzer/runAnalysis/RunningAnalysis_v6.0.py"

    #interactive DashBoard 
   
    streamlit run app.py


############# HRV Analysis

& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/MSBuddy_FitnessApp/HRV_DWH/HRV_datawarehouse.py"

& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/MSBuddy_FitnessApp/HRV_DWH/HRV_datawarehouse_V1.5.py"
& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/MSBuddy_FitnessApp/HRV_DWH/HRV_datawarehouse V1.9.py"

#unifiedScript
& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/MSBuddy_FitnessApp/HRV_DWH/HRV_datawarehouse V1.95.py"


############next scripts

& C:/Python313/python.exe "C:/smakrykoDev/GitHubRepos/CG_jHeelFitnessProject-1/MSBuddy_FitnessApp/HRV Patern Detection v1.0.py"

