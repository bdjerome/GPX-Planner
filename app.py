import streamlit as st
import pandas as pd
import datetime
from pace_planner import GPXAnalyzer, PaceCalculator, MapVisualizer
from misc_functions import convert_to_mph, convert_to_kmh, convert_to_km, convert_to_miles

def main():
    st.set_page_config(layout="wide")
    st.title("GPX Pace Planner 🏃‍♂️")
    st.write("Upload a GPX file and analyze your race pace strategy!")
    
    # Create two columns for Route Selection and Analysis Configuration
    main_col1, main_col2 = st.columns(2)
    
    # Route Selection (left column)
    with main_col1:
        st.subheader("Route Selection")
        route_source = st.radio("Choose route source:", ["Upload new file", "Use saved route"])
        
        selected_file_path = None
        
        if route_source == "Upload new file":
            uploaded_file = st.file_uploader("Choose a GPX file", type=['gpx'])
            if uploaded_file is not None:
                # Check if this is a different file than what we had before
                current_file_name = uploaded_file.name
                if ('last_uploaded_file' not in st.session_state or 
                    st.session_state.last_uploaded_file != current_file_name):
                    
                    # Clear previous analysis when file changes
                    if 'analysis_complete' in st.session_state:
                        del st.session_state.analysis_complete
                    if 'analyzer' in st.session_state:
                        del st.session_state.analyzer
                    if 'current_show_arrows' in st.session_state:
                        del st.session_state.current_show_arrows
                    
                    # Store the new file name
                    st.session_state.last_uploaded_file = current_file_name
                
                # Save uploaded file temporarily
                with open("temp_route.gpx", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                selected_file_path = "temp_route.gpx"
                st.success(f"File uploaded: {uploaded_file.name}")
        else:
            # Show saved routes
            import os
            saved_routes_dir = "saved_routes"
            if os.path.exists(saved_routes_dir):
                gpx_files = [f for f in os.listdir(saved_routes_dir) if f.endswith('.gpx')]
                if gpx_files:
                    selected_route = st.selectbox("Select a saved route:", gpx_files)
                    selected_file_path = os.path.join(saved_routes_dir, selected_route)
                    
                    # Check if this is a different saved route
                    if ('last_selected_route' not in st.session_state or 
                        st.session_state.last_selected_route != selected_route):
                        
                        # Clear previous analysis when route changes
                        if 'analysis_complete' in st.session_state:
                            del st.session_state.analysis_complete
                        if 'analyzer' in st.session_state:
                            del st.session_state.analyzer
                        if 'current_show_arrows' in st.session_state:
                            del st.session_state.current_show_arrows
                        
                        # Store the new route name
                        st.session_state.last_selected_route = selected_route
                        
                else:
                    st.warning("No saved routes found. Add GPX files to the 'saved_routes' folder.")
            else:
                st.error("Saved routes directory not found.")
    
    # Configuration form (right column)
    with main_col2:
        with st.form("pace_analysis_form"):
            st.subheader("Analysis Configuration")
            
            # Basic Settings Container
            with st.container():
                st.write("**Basic Settings**")
                form_col1, form_col2 = st.columns(2)
                
                with form_col1:
                    loops = st.number_input("Number of loops", min_value=1, max_value=5, value=1)
                    
                with form_col2:
                    # radio button defining if min/mile or min/km
                    pace_unit = st.radio("Pace unit:", ["min/km", "min/mile"])
            
            # Pace Settings Container
            with st.container():
                st.write("**Pace Configuration**")
                
                if pace_unit == "min/km":
                    pace_time = st.time_input("Base pace (min/km)", datetime.time(0, 6, 12))
                    # Use hour field as minutes, minute field as seconds
                    base_pace = pace_time.hour + (pace_time.minute / 60.0)
                else:  # min/mile
                    pace_time_miles = st.time_input("Base pace (min/mile)", datetime.time(0, 10, 0))
                    # Use hour field as minutes, minute field as seconds
                    pace_minutes = pace_time_miles.hour + (pace_time_miles.minute / 60.0)
                    base_pace = convert_to_kmh(pace_minutes)
            
            # Advanced Options Container
            with st.container():
                st.write("**Advanced Options**")
                adv_col1, adv_col2 = st.columns(2)
                
                with adv_col1:
                    enable_decay = st.checkbox("Enable fatigue decay", value=True)
                    
                with adv_col2:
                    enable_hills = st.checkbox("Enable hill adjustments", value=True)
            
            # Submit button
            st.markdown("---")
            submitted = st.form_submit_button("🚀 Analyze Route", disabled=(selected_file_path is None), use_container_width=True)
        
    # Process form submission
    if submitted and selected_file_path is not None:
        # Clear any previous session state data
        if 'analysis_complete' in st.session_state:
            del st.session_state.analysis_complete
        if 'analyzer' in st.session_state:
            del st.session_state.analyzer
        if 'current_show_arrows' in st.session_state:
            del st.session_state.current_show_arrows
            
        with st.spinner("Processing GPX file..."):
            try:
                # Initialize analyzer
                analyzer = GPXAnalyzer(selected_file_path)
                analyzer.load_gpx()
                analyzer.map_adjustment(loops=loops)
                analyzer.calculate_distances()
                analyzer.find_kilometer_markers()
                
                # Calculate pace
                pace_calc = PaceCalculator(analyzer, base_pace)
                pace_calc.calculate_pace(
                    distance=0, grade=0, total_distance=0,
                    decay=enable_decay, hill_mode=enable_hills
                )
                pace_calc.calculate_times()
                
                # Store results in session state
                st.session_state.analysis_complete = True
                st.session_state.analyzer = analyzer
                st.session_state.current_show_arrows = True  # Default value
                st.session_state.map_needs_regeneration = True  # Force map regeneration
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.session_state.analysis_complete = False
    
    # Display results if analysis is complete
    if st.session_state.get('analysis_complete', False):

        analyzer = st.session_state.analyzer
        
        # Display results
        st.success("Analysis complete!")
        
        # Unit toggle checkbox
        use_metric = st.checkbox("Use Metric Units", value=True)
        
        # Show summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate values once
        total_distance = analyzer.final_df['total_distance'].max()
        avg_pace = analyzer.final_df['pace'].mean()
        finish_time = analyzer.final_df['cumulative_time_hms'].iloc[-1]
        uphill, downhill = analyzer.gpx_parsed.get_uphill_downhill()
        total_elevation_gain = uphill * loops if uphill else 0
        
        with col1:
            if use_metric:
                st.metric("Distance", f"{total_distance:.2f} km", border=True)
            else:
                miles_total_distance = convert_to_miles(total_distance)
                st.metric("Distance", f"{miles_total_distance:.2f} miles", border=True)
        
        with col2:
            if use_metric:
                st.metric("Average Pace", f"{avg_pace:.2f} min/km", border=True)
            else:
                mph_avg_pace = convert_to_mph(avg_pace)
                st.metric("Average Pace", f"{mph_avg_pace:.2f} min/mile", border=True)

        with col3:
            st.metric("Estimated Duration", finish_time, border=True)
            
        with col4:
            if use_metric:
                st.metric("Elevation Gain", f"{total_elevation_gain:.0f} m", border=True)
            else:
                elevation_gain_ft = total_elevation_gain * 3.28084  # Convert meters to feet
                st.metric("Elevation Gain", f"{elevation_gain_ft:.0f} ft", border=True)
        
        # Display pace data
        st.subheader("Kilometer Splits")
        km_data = analyzer.final_df[analyzer.final_df['is_km_marker'] == 1][
            ['km_number', 'total_distance', 'pace', 'grade', 'cumulative_time_hms']
        ]
        st.dataframe(km_data)

        #may need to use on_change and save the updated df to session state
        #adding note column 
        #km_data['Notes'] = ''
        #TODO edited_df = st.data_editor(km_data, num_rows="fixed", disabled=[col for col in km_data.columns if col not 'Notes'], key='output_data_editor')
        
        # Create and display map
        st.subheader("Route Map")
        
        show_arrows = st.checkbox("Show directional arrows", value=True)
        
        # Regenerate map if checkbox state changed OR if new analysis was run
        if ('current_show_arrows' not in st.session_state or 
            st.session_state.current_show_arrows != show_arrows or
            st.session_state.get('map_needs_regeneration', False)):
            
            # Create map once
            map_viz = MapVisualizer(analyzer.final_df)
            map_viz.create_base_map()
            
            # Add markers based on user preference
            if show_arrows:
                map_viz.add_kilometer_markers_directional()
            else:
                map_viz.add_kilometer_markers()
            
            # Save map once
            map_viz.save_map("route_map.html")
            
            # Update session state
            st.session_state.current_show_arrows = show_arrows
            st.session_state.map_needs_regeneration = False  # Reset flag

        # Display map in Streamlit
        with open("route_map.html", "r") as f:
            map_html = f.read()
        st.components.v1.html(map_html, height=600)
        
        # Show elevation profile
        st.subheader("Elevation Profile")
        st.line_chart(analyzer.final_df[['total_distance', 'elevation']].set_index('total_distance'))
        
        # Show pace progression
        st.subheader("Pace Progression")
        st.line_chart(analyzer.final_df[['total_distance', 'pace']].set_index('total_distance'))
    
    elif submitted and selected_file_path is None:
        st.error("Please select a GPX file before analyzing!")
    
    else:
        st.info("Please upload a GPX file to get started.")
        
        # Show sample data or instructions
        st.subheader("How to use:")
        st.write("""
        1. Upload your GPX route file
        2. Configure the number of loops and your target pace
        3. Enable decay and hill adjustments as needed
        4. Click 'Analyze Route' to see your pace strategy!
        """)

if __name__ == "__main__":
    main()