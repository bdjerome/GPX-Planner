import streamlit as st
import pandas as pd
import datetime
from pace_planner import GPXAnalyzer, PaceCalculator, MapVisualizer
from misc_functions import convert_to_mph, convert_to_kmh, convert_to_km,\
    convert_to_miles, dynamic_input_data_editor, generate_gpx_analysis_pdf \
        , merge_custom_markers, plotly_elevation_plot, plotly_pace_plot, calculate_time_difference

def main():
    st.set_page_config(
        page_title="GPX Pace Planner", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    st.title("GPX Pace Planner")
    st.write("Upload a GPX file, analyze your race pace strategy, and optionally generate a pdf report!")

    st.page_link("pages/tutorial.py", label="**:blue[Click Here to View Tutorial]**")

    # with st.expander(label='Usage Instructions', expanded=True):
    #     # Show sample data or instructions
    #     st.subheader("How to use:")
    #     st.markdown("""
    #                 1. Upload or select a saved GPX route file
    #     2. Configure the number of loops and your target pace
    #     3. Enter the time your race starts
    #     4. Optionally
    #         - Alter pace by enabling fatigue decay and hill adjustments as needed
    #         - Input custom markers with nicknames (aid stations, planned meetups, etc.)
    #     4. Click 'Analyze Route' to see your pace strategy!
    #                 """)
    
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
                    if 'km_notes' in st.session_state:
                        del st.session_state.km_notes
                    
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
                        if 'km_notes' in st.session_state:
                            del st.session_state.km_notes
                        
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
                
                # Single time input that works for both units
                pace_time = st.time_input("Base pace (min:sec)", datetime.time(6, 12, 0))
                race_start = st.time_input("Race start time", None, step=300)
            
            # Advanced Options Container
            with st.container():
                st.write("**Advanced Options**")
                adv_col1, adv_col2 = st.columns(2)
                
                with adv_col1:
                    enable_decay = st.checkbox("Enable fatigue decay", value=True)
                    
                with adv_col2:
                    enable_hills = st.checkbox("Enable hill adjustments", value=True)

            with st.expander("Custom Marker Configuration"):
                st.write("Add custom markers at specific distances with nicknames and optional cutoff times. These will be used for output in the pace table.")
                st.write("E.g., Distance: 5.0, Nickname: Water Station, Cutoff Time: 10:00:00")
                # Data editor for custom markers
                custom_marker_distance_type = st.checkbox("Using KM markers?", value=True)
                custom_marker_data = st.data_editor(pd.DataFrame(columns=["Distance", "Nickname","Cutoff Time"]), num_rows="dynamic", use_container_width=True)
            
            # Submit button
            st.markdown("---")
            submitted = st.form_submit_button("🚀 Analyze Route", disabled=(selected_file_path is None), use_container_width=True)
        
    # Process form submission
    if submitted and selected_file_path is not None:
        # Process pace input outside form to avoid reset issues
        pace_minutes = pace_time.hour + (pace_time.minute / 60.0)
        # Convert to km/h if needed (our internal format is always min/km)
        if pace_unit == "min/mile":
            base_pace = convert_to_kmh(pace_minutes)
        else:
            base_pace = pace_minutes
            
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
                    decay=enable_decay, hill_mode=enable_hills
                )
                pace_calc.calculate_times()
                pace_calc.calculate_clock_times(race_start)

                # Merge custom markers if provided
                if not custom_marker_data.empty and len(custom_marker_data) > 0:
                    analyzer.final_df = merge_custom_markers(
                        analyzer.final_df, 
                        custom_marker_data, 
                        use_km_markers=custom_marker_distance_type
                    )
                    
                    # Calculate cutoff buffer if cutoff times exist
                    if 'cutoff_time_formatted' in analyzer.final_df.columns:
                        analyzer.final_df['cutoff_buffer_minutes'] = analyzer.final_df.apply(calculate_time_difference, axis=1)
                
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
        total_elevation_loss = downhill * loops if downhill else 0
        
        with col1:
            if use_metric:
                st.metric("Total Distance", f"{total_distance:.2f} km", border=True)
            else:
                miles_total_distance = convert_to_miles(total_distance)
                st.metric("Total Distance", f"{miles_total_distance:.2f} miles", border=True)

        #dummy var creation so pdf function works
        pace_minutes = 0
        pace_seconds = 0

        with col2:
            if use_metric:
                # Convert pace to minutes:seconds format
                pace_minutes = int(avg_pace)
                pace_seconds = int((avg_pace - pace_minutes) * 60)
                st.metric("Average Pace", f"{pace_minutes}:{pace_seconds:02d} min/km", border=True)
            else:
                mph_avg_pace = convert_to_mph(avg_pace)
                pace_minutes = int(mph_avg_pace)
                pace_seconds = int((mph_avg_pace - pace_minutes) * 60)
                st.metric("Average Pace", f"{pace_minutes}:{pace_seconds:02d} min/mile", border=True)

        with col3:
            st.metric("Estimated Duration", finish_time, border=True)
            
        with col4:
            if use_metric:
                st.metric("Elevation Gain/Loss", f"{total_elevation_gain:.0f}/{total_elevation_loss:.0f} m", border=True)
            else:
                elevation_gain_ft = total_elevation_gain * 3.28084  # Convert meters to feet
                elevation_loss_ft = total_elevation_loss * 3.28084
                st.metric("Elevation Gain/Loss", f"{elevation_gain_ft:.0f}/{elevation_loss_ft:.0f} ft", border=True)

        # Display pace data - use custom markers if they exist, otherwise use km markers
        st.subheader("Pace Data")
        
        # Check if custom markers exist
        has_custom_markers = 'custom_marker' in analyzer.final_df.columns and \
                           analyzer.final_df['custom_marker'].str.strip().ne('').any()

        # Rounding KM column to 1 decimal place
        analyzer.final_df['total_distance'] = analyzer.final_df['total_distance'].round(1)
        
        # Always get first and last rows (start and finish points)
        first_row = analyzer.final_df.iloc[[0]].copy()
        last_row = analyzer.final_df.iloc[[-1]].copy()

        
        if has_custom_markers:
            #changing output to show cutoff times if they exist
            if 'cutoff_buffer_minutes' in analyzer.final_df.columns:
                # Display custom markers data with cutoff buffer
                marker_data = analyzer.final_df[
                    (analyzer.final_df['is_km_marker'] == 1) & 
                    (analyzer.final_df['custom_marker'].str.strip() != '')
                ][['km_number', 'total_distance', 'pace', 'grade', 'cumulative_time_hms','clock_time', 'custom_marker','cutoff_time_formatted', 'cutoff_buffer_minutes']].copy()

            else:
                # Display custom markers data without cutoff times
                marker_data = analyzer.final_df[
                    (analyzer.final_df['is_km_marker'] == 1) & 
                    (analyzer.final_df['custom_marker'].str.strip() != '')
                ][['km_number', 'total_distance', 'pace', 'grade', 'cumulative_time_hms','clock_time', 'custom_marker']].copy()
                
            # Add marker labels to start and finish rows
            first_row['custom_marker'] = 'START'
            last_row['custom_marker'] = 'FINISH'
            
            # Ensure START and FINISH rows have cutoff columns if they exist in marker_data
            if 'cutoff_time_formatted' in marker_data.columns:
                if 'cutoff_time_formatted' not in first_row.columns:
                    first_row['cutoff_time_formatted'] = pd.NA
                if 'cutoff_time_formatted' not in last_row.columns:
                    last_row['cutoff_time_formatted'] = pd.NA
                    
            if 'cutoff_buffer_minutes' in marker_data.columns:
                if 'cutoff_buffer_minutes' not in first_row.columns:
                    first_row['cutoff_buffer_minutes'] = pd.NA
                if 'cutoff_buffer_minutes' not in last_row.columns:
                    last_row['cutoff_buffer_minutes'] = pd.NA
            
            # Combine all data: start + markers + finish
            km_data = pd.concat([first_row, marker_data, last_row], ignore_index=True)
            
            # Sort by distance first, then by marker priority (START/FINISH over custom markers)
            # Create a priority column for sorting: START=1, FINISH=1, custom markers=2
            km_data['_sort_priority'] = km_data['custom_marker'].apply(
                lambda x: 1 if x in ['START', 'FINISH'] else 2
            )
            km_data = km_data.sort_values(['total_distance', '_sort_priority']).reset_index(drop=True)
            
            # Remove duplicates based on total_distance, keeping first (which will be START/FINISH due to priority)
            km_data = km_data.drop_duplicates(subset=['total_distance'], keep='first')
            
            # Clean up the temporary sort column
            km_data = km_data.drop('_sort_priority', axis=1)
            
            # Rename custom_marker column to something more user-friendly
            km_data = km_data.rename(columns={'custom_marker': 'Marker'})
        else:
            # Display regular km markers
            marker_data = analyzer.final_df[analyzer.final_df['is_km_marker'] == 1][
                ['km_number', 'total_distance', 'pace', 'grade', 'cumulative_time_hms', 'clock_time']
            ].copy()
            
            # Add marker column for consistency and label start/finish
            first_row['Marker'] = 'START'
            last_row['Marker'] = 'FINISH'
            marker_data['Marker'] = ''  # Empty marker for regular km points
            
            # Ensure START and FINISH rows have cutoff columns if they exist in original data
            if 'cutoff_time_formatted' in analyzer.final_df.columns:
                if 'cutoff_time_formatted' not in first_row.columns:
                    first_row['cutoff_time_formatted'] = pd.NA
                if 'cutoff_time_formatted' not in last_row.columns:
                    last_row['cutoff_time_formatted'] = pd.NA
                if 'cutoff_time_formatted' not in marker_data.columns:
                    marker_data['cutoff_time_formatted'] = pd.NA
                    
            if 'cutoff_buffer_minutes' in analyzer.final_df.columns:
                if 'cutoff_buffer_minutes' not in first_row.columns:
                    first_row['cutoff_buffer_minutes'] = pd.NA
                if 'cutoff_buffer_minutes' not in last_row.columns:
                    last_row['cutoff_buffer_minutes'] = pd.NA
                if 'cutoff_buffer_minutes' not in marker_data.columns:
                    marker_data['cutoff_buffer_minutes'] = pd.NA
            
            # Combine all data: start + markers + finish
            km_data = pd.concat([first_row, marker_data, last_row], ignore_index=True)
            
            # Sort by distance first, then by marker priority (START/FINISH over empty strings)
            # Create a priority column for sorting: START=1, FINISH=1, empty=2
            km_data['_sort_priority'] = km_data['Marker'].apply(
                lambda x: 1 if x in ['START', 'FINISH'] else 2
            )
            km_data = km_data.sort_values(['total_distance', '_sort_priority']).reset_index(drop=True)
            
            # Remove duplicates based on total_distance, keeping first (which will be START/FINISH due to priority)
            km_data = km_data.drop_duplicates(subset=['total_distance'], keep='first')
            
            # Clean up the temporary sort column
            km_data = km_data.drop('_sort_priority', axis=1)
        
        # Helper function to convert pace to MM:SS format
        def format_pace(pace_float):
            minutes = int(pace_float)
            seconds = int((pace_float - minutes) * 60)
            return f"{minutes}:{seconds:02d}"
        
        # Apply unit conversion for display if needed
        if not use_metric:
            # Create converted display columns (preserve original data)
            km_data['distance_display'] = km_data['total_distance'].apply(convert_to_miles).round(1)
            km_data['pace_display'] = km_data['pace'].apply(lambda x: format_pace(convert_to_mph(x)))

            # Start with base columns for imperial
            display_columns = ['distance_display', 'pace_display', 'grade', 'cumulative_time_hms', 'clock_time']
            column_renames = {
                'distance_display': 'Miles',
                'pace_display': 'Pace (min/mile)',
                'grade': 'Grade (%)',
                'cumulative_time_hms': 'Duration',
                'clock_time': 'Clock Time'
            }
            
            # Add Marker column if it exists
            if 'Marker' in km_data.columns:
                display_columns.append('Marker')
                
            # Add cutoff time columns if they exist
            if 'cutoff_time_formatted' in km_data.columns:
                display_columns.extend(['cutoff_time_formatted', 'cutoff_buffer_minutes'])
                column_renames.update({
                    'cutoff_time_formatted': 'Cutoff Time',
                    'cutoff_buffer_minutes': 'Cutoff Buffer (min)'
                })

        else:
            # Create formatted pace for metric display
            km_data['pace_display'] = km_data['pace'].apply(format_pace)
            
            # Start with base columns for metric
            display_columns = ['total_distance', 'pace_display', 'grade', 'cumulative_time_hms', 'clock_time']
            column_renames = {
                'total_distance': 'KM',
                'pace_display': 'Pace (min/km)',
                'grade': 'Grade (%)',
                'cumulative_time_hms': 'Duration',
                'clock_time': 'Clock Time'
            }
            
            # Add Marker column if it exists
            if 'Marker' in km_data.columns:
                display_columns.append('Marker')
                
            # Add cutoff time columns if they exist
            if 'cutoff_time_formatted' in km_data.columns:
                display_columns.extend(['cutoff_time_formatted', 'cutoff_buffer_minutes'])
                column_renames.update({
                    'cutoff_time_formatted': 'Cutoff Time',
                    'cutoff_buffer_minutes': 'Cutoff Buffer (min)'
                })

        # Create display dataframe with appropriate columns
        km_data_display = km_data[display_columns].copy()
        if column_renames:
            km_data_display = km_data_display.rename(columns=column_renames)
        
        # Initialize or update notes in session state
        if 'km_notes' not in st.session_state:
            st.session_state.km_notes = [''] * len(km_data_display)
        
        # Ensure notes list matches current data length
        if len(st.session_state.km_notes) != len(km_data_display):
            # Preserve existing notes when possible, pad with empty strings for new entries
            old_notes = st.session_state.km_notes.copy()
            st.session_state.km_notes = [''] * len(km_data_display)
            for i in range(min(len(old_notes), len(st.session_state.km_notes))):
                st.session_state.km_notes[i] = old_notes[i]
        
        # Add notes column to display dataframe
        km_data_display['Notes'] = st.session_state.km_notes
        
        # Create data editor using the dynamic wrapper function
        edited_df = dynamic_input_data_editor(
            km_data_display, 
            key='output_data_editor',
            num_rows="fixed", 
            disabled=[col for col in km_data_display.columns if col != 'Notes'], 
            use_container_width=True,
            hide_index=True
        )
        
        # Update session state with the edited notes
        st.session_state.km_notes = edited_df['Notes'].tolist()
        
        # PDF Download Section
        st.markdown("---")
        col_download1, col_download2 = st.columns([1, 3])
        
        with col_download1:
            # Get route name (use uploaded file name or "Saved Route")
            if 'last_uploaded_file' in st.session_state:
                route_name = st.session_state.last_uploaded_file.replace('.gpx', '')
            elif 'last_selected_route' in st.session_state:
                route_name = st.session_state.last_selected_route.replace('.gpx', '')
            else:
                route_name = "GPX Route"
            
            try:
                # Prepare PDF data with original columns plus notes
                pdf_data = km_data.copy()
                pdf_data['Notes'] = st.session_state.km_notes
                
                # Generate PDF
                pdf_buffer = generate_gpx_analysis_pdf(
                    analyzer=analyzer,
                    km_data=pdf_data,  # Use original data with all columns
                    total_distance=total_distance,
                    pace_minutes=pace_minutes,
                    pace_seconds=pace_seconds,
                    finish_time=finish_time,
                    total_elevation_gain=total_elevation_gain,
                    use_metric=use_metric,
                    route_name=route_name
                )
                
                # Single download button that generates and downloads
                st.download_button(
                    label="📄 Generate & Download PDF Report",
                    data=pdf_buffer.getvalue(),
                    file_name=f"{route_name}_pace_analysis.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
        
        with col_download2:
            st.info("💡 Click to generate and download your complete pace analysis report with all data, metrics, and notes.")
        
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
        elevation_plot = plotly_elevation_plot(analyzer, total_elevation_gain)
        if elevation_plot:
            st.plotly_chart(elevation_plot)
        else:
            st.write("No elevation data available to display.")

        # Show pace progression
        st.subheader("Pace Progression")
        pace_plot = plotly_pace_plot(analyzer)
        if pace_plot:
            st.plotly_chart(pace_plot)
        else:
            st.write("No elevation data available to display.")
    
    elif submitted and selected_file_path is None:
        st.error("Please select a GPX file before analyzing ")
    else:
        st.info("Please select a GPX file before analyzing!")


if __name__ == "__main__":
    main()