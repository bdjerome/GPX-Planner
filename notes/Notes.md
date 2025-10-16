#This file stores notes I have and to-do lists 


#TODO
- [x] Organize repo with folders for any saved information 
- [x] Fix the TODO's in pace_planner.py 
- Make streamlit app prettier
  - [x] Move title to top left 
  - Give better descriptions
  - [x] Convert sidebar to st.form and have analyze button be the trigger there 
  - [x] Radio button above Base Pace defining if min/mile or min/km
  - [x] convert pace input from integer input to time input
  - Make output look nice (metrics,then map, then table, then graphs)
     - [x] Add st.checkbox above map for inclusion of arrows or not
     - [x] Add legend for the map
     - [x] For metric outputs show metric units and freedom units
     - Maybe add some distinction like st.bar so you know you are seeing the output
     - [x] Output df needs to have everything shown if not be scrollable and have note section
     - [x] Output to downloadable pdf file
- Give more user choice for marker setup 
  - [x] Custom inputs (Distance, Nickname)
  - [x] Automatically add Start and Finish points to the output table
  - In output table what is grade # displaying ?
- [x] Allow user to input start time of race
  - [x] Add new columns to final_df that display what time runner will get to each marker
- [x] update elevation output graph 
- [x] update pace progression output graph 
- [x] Move how to use to top of page
- Wrap text in pdf notes column if needed (would generating as excel be easier)


#Future Improvements
- Add elevation drop
- Create documentation for everything (Youtube Tutorial Video?) need to link in app 
- Customer feedback area (where will this go? Google sheets and email notification ?)
- Website metric tracking (how to do for free PostHog ?)
- Graphical outputs so users understand how fatigue decay is affecting performance (same with hill adjustment)
- Ability to add cutoff times to custom markers 
- Give more user choice for marker setup 
  - Can select every KM, Half, Quarter
    - Try to parse waypoints from input gpx files and store these
  - Will need to pass as a dict to MapVisualizer
- More experimentation and understanding of pace functions (VO2, decay)
- Add image of map to the pdf output (have matplotlib might need selenium workaround)
- More customization to route creation 
  - Reverse Loops
  - Add negative split possibility to pace calculation
- Upload multiple gpx files and weave together
- Find a solution to no elevation given (use 3rd party api's ?)
- Donation button

