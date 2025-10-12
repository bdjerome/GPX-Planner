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
  - Can select every KM, Half, Quarter
  - [x] Custom inputs (Distance, Nickname)
    - Try to parse waypoints from input gpx files and store these
  - Will need to pass as a dict to MapVisualizer
- Allow user to input start time of race
  - Add new columns to final_df that display what time runner will get to each marker
- More customization to route (reverse loops)


#Future Improvements
- Add image of map to the pdf output (have matplotlib might need selenium workaround)
- Graphical outputs so users understand how fatigue decay is affecting performance (same with hill adjustment)
- Ability to add cutoff times to custom markers 
- More experimentation and understanding of pace functions (VO2, decay)
- Add negative split possibility to pace calculation
- Create documentation for everything (Youtube Tutorial Video?) need to link in app 
- Customer feedback area (where will this go? Google sheets and email notification ?)
- Website metric tracking (how to do for free PostHog ?)
- Upload multiple gpx files and weave together
- Find a solution to no elevation given (use 3rd party api's ?)
- Donation button

