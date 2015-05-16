SegTracker
==========
Strava is a fitness application that allows users to compete against one another on "segments", which are essentially mini time trials over a certain stretch of road or trail.  This program allows users to compare their individual efforts on a specific segment over time by providing a line plot of their times, rolling average times, and median times, over a certain period.  

The following steps must be followed to run the program correctly:

1.  In `auth.py`, STRAVA\_CLIENT\_ID and STRAVA\_CLIENT\_SECRET must be replaced with a proper client id and secret, which can be obtained by registering a new application with Strava at http://www.strava.com/developers.

2.  This application will only work with the source version of web2py.  Web2py uses its own version of python so it is not possible to install the necessary libraries on the standard version.  
	
	Install the source version from here: (or from main site, source code version)
		http://www.web2py.com/examples/static/web2py_src.zip
	Extract the zip to wherever you would like this version stored.
	To open up web2py, use the command line and go to the web2py folder and type `python web2py.py`.  Then, import the application as "SegTracker".  Everything else will work as normal.
		
3.  Some of the libraries only work with Python 2.7. Unfortunately, this app is not compatible with Python 3. 
		If you do not already have 2.7 on your computer, you must download it from here:
			https://www.python.org/download/releases/2.7/
			
4.  You must install stravalib and pygal, two third-party modules for Python.  
	Follow the instructions at https://github.com/hozn/stravalib and http://pygal.org/download/.
	To sum up:
		Using the command line enter the following commands:
			`%cd Python2.7/Scripts`		(note that this is wherever you chose to install Python2.7)
			`%pip install stravalib`
			`%pip install pygal`

5.  You must have a Strava account with which to log in.  If you don't have a Strava account, contact me and I can provide a test account.


Main Features
-------------
* Displays a list of the user's activities (rides and runs), pulled from the Strava API, which can be updated with the "update" button or deleted with the "reset" button.
* For each activity, displays a list of each segment effort on the route and the user's time on that effort.
* For each segment, displays a graph showing all of the user's times on that segment, along with a rolling average and median on these times if there are 8 or more efforts.  The start date and end date of the graph can be changed to analyze a smaller subsection of activities.
* Shows basic information on the user and all activities, segments, and segment efforts.

Known Bugs
-------------
* When a timeframe is set for the segment times graph, the graph's mouse-over label system no longer functions.
* The lines between points do not display on Firefox for the time being, but this is expected to be fixed soon.  See [this reported bug](https://bugzilla.mozilla.org/show\_bug.cgi?id=1153106) for more details.

Test Data
-------------
Test data can be viewed by following the instructions in step 2 above (logging in and changing `default.py`), or via appadmin.  It does not make much sense to provide test cases, but this table shows some example times and the associated rolling average and the median, which should be equivalent to the data points that would appear on the graph of a segment with these times:

| Time | Rolling Average | Median |
|------|-----------------|--------|
| 5:02 | 5:43            | 5:02   |
| 6:24 | 5:25            | 5:43   |
| 4:48 | 5:20            | 5:02   |
| 4:47 | 4:55            | 4:55   |
| 5:10 | 5:11            | 5:02   |
| 5:35 | 5:15            | 5:06   |
| 4:59 | 5:05            | 5:02   |
| 4:41 | 4:51            | 5:01   |
| 4:52 | 4:47            | 4:59   |
