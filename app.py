import streamlit as st
import pandas as pd
from pace_planner import GPXAnalyzer, PaceCalculator, MapVisualizer

def main():
    st.title("GPX Pace Planner 🏃‍♂️")
    st.write("Upload a GPX file and analyze your race pace strategy!")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a GPX file", type=['gpx'])
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with open("temp_route.gpx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Configuration options
        loops = st.sidebar.number_input("Number of loops", min_value=1, max_value=5, value=2)
        base_pace = st.sidebar.number_input("Base pace (min/km)", min_value=3.0, max_value=15.0, value=6.2, step=0.1)
        
        # Analysis options
        st.sidebar.subheader("Analysis Options")
        enable_decay = st.sidebar.checkbox("Enable fatigue decay", value=True)
        enable_hills = st.sidebar.checkbox("Enable hill adjustments", value=True)
        
        if st.button("Analyze Route"):
            with st.spinner("Processing GPX file..."):
                try:
                    # Initialize analyzer
                    analyzer = GPXAnalyzer("temp_route.gpx")
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
                    
                    # Display results
                    st.success("Analysis complete!")
                    
                    # Show summary statistics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_distance = analyzer.final_df['total_distance'].max()
                        st.metric("Total Distance", f"{total_distance:.2f} km")
                    
                    with col2:
                        avg_pace = analyzer.final_df['pace'].mean()
                        st.metric("Average Pace", f"{avg_pace:.2f} min/km")
                    
                    with col3:
                        finish_time = analyzer.final_df['cumulative_time_hms'].iloc[-1]
                        st.metric("Estimated Finish Time", finish_time)
                    
                    # Display pace data
                    st.subheader("Kilometer Splits")
                    km_data = analyzer.final_df[analyzer.final_df['is_km_marker'] == 1][
                        ['km_number', 'total_distance', 'pace', 'grade', 'cumulative_time_hms']
                    ].head(10)
                    st.dataframe(km_data)
                    
                    # Create and display map
                    st.subheader("Route Map")
                    
                    map_viz = MapVisualizer(analyzer.final_df)
                    map_viz.create_base_map()
                    map_viz.add_kilometer_markers()
                    map_viz.save_map("route_map.html")
                    
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
                    
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
    
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