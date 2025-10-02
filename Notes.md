#This file stores notes I have and to-do lists 


#TODO
- Organize repo with folders for any saved information 
- Fix the TODO's in pace_planner.py 
- Make streamlit app prettier
  - Move title to top left 
  - Give better descriptions
  - Convert sidebar to st.form and have analyze button be the trigger there 
  - Make output look nice (map as first thing seen, then metrics, then table)
     - Maybe add some distinction like st.bar so you know you are seeing the output
     - Output df needs to have everything shown if not be scrollable
     - Output to downloadable pdf file
- Give more user choice for marker setup 
  - Can select every KM, Half, Quarter
  - Custom inputs (Distance, Nickname)
  - Will need to pass as a dict to MapVisualizer
  - This will also need to get passed to pace calculator so we know how long to each custom marker
- Allow user to input start time of race
  - Add new columns to final_df that display what time runner will get to each marker
- More customization to route (reverse loops)


#Future Improvements
- Ability to add cutoff times to custom markers 
- More experimentation and understanding of pace functions (VO2, decay)
- Create documentation for everything (Youtube Tutorial Video?) need to link in app 
- Customer feedback area (where will this go? Google sheets and email notification ?) 
- Upload multiple gpx files and weave together
- Donation button

