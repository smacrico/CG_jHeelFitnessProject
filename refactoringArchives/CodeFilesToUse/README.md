# jHeelFitnessProject

This repository contains the source code and documentation for the jHeel Fitness Project. The project aims to provide a comprehensive fitness tracking application with features such as workout logging, progress tracking, and personalized fitness plans.

## Features
- Workout logging
- Progress tracking
- Personalized fitness plans
- User authentication and profiles

## Installation
1. Clone the repository
    ```bash
    git clone https://github.com/SteliosDev/jHeelFitnessProject.git
    ```
2. Navigate to the project directory
    ```bash
    cd jHeelFitnessProject
    ```
3. Install dependencies
    ```bash
    npm install
    ```

## Usage
1. Start the application
    ```bash
    npm start
    ```
2. Open your browser and navigate to `http://localhost:3000`

## Contributing
Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the `LICENSE.md` file for details.




## scripts explain :

### ###########################################
### #################### Garmin main scripts###
### ###########################################

##### rebuild db
& C:/Python312/python.exe C:/Python312/Scripts c:/Users/stma/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0/LocalCache/local-packages/Python311/Scripts/garmindb_cli.py --rebuild_db
##### backup all db
& C:/Python312/python.exe C:/Python312/Scripts/ c:/Users/stma/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0/LocalCache/local-packages/Python311/Scripts/garmindb_cli.py --backup
& C:/Python312/python.exe C:/Python312/Scripts/ c:/Users/stma/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0/LocalCache/local-packages/Python311/Scripts/garmindb_cli.py --all --download --import --analyze
& C:/Python312/python.exe C:/Python312/Scripts/garmindb_cli.py --all --download --import --analyze --latest
##### main script to download all latest data
& C:/Python312/python.exe C:/Python312/Scripts/garmindb_cli.py --all --download --import --analyze --latest

### BH lab
# doenload data from Garmin

& C:/Python312/python.exe C:/Python312/Scripts/garmindb_cli.py --all --download --import --analyze --latest
1. GarminDB -  export all data to Artemis DB, creating tables :
    garmmin
    garmin_activities
    garmin_monitoring
    garmin_summary
    garmin

    ==> fit files and more input are created Under HealthData folder in user's profile

2. jHeel_plugin v3.0 : -> export Dev Fields in table Artemistbl_Prod
    & C:/Python312/python.exe "c:/SteliosDev/stmaDEVs/jheel/jHeelFitnessProject/runAnalysis/jHeel_plugin v3.0.py"
    Artemistbl_Prod

3. & C:/Python312/python.exe "c:/SteliosDev/stmaDEVs/jheel/jHeelFitnessProject/runAnalysis/createRunAnalDB.py"
    creates RuningAnalysis DB dn table :
    runing_sessions (is created by selected run data drom DB.Artemis. Artemistbl_Prod)

3.  & C:/Python312/python.exe "C:/SteliosDev/stmaDEVs/jheel/jHeelFitnessProject/runAnalysis/RunningAnalysis_v40.py"
    Visuals for Run data from DB.RunningAnalysis.runnin_sessions table
    creates training_log table : (data used from visualizations)
    calculate scores and Run parameters : (print only)

4. jHeel_plugin_v4.1fbbHRV : -> reads fitFiles and export fb data HRV related to Artemis_HRV DB and creates tables:
    Artemistbl41
    hrv_sessions
    hrv_records


5. HRV DataAnalysis