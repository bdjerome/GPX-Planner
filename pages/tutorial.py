import streamlit as st
import pandas as pd
import numpy as np

from misc_functions import convert_to_mph, convert_to_kmh, convert_to_km,\
    convert_to_miles, dynamic_input_data_editor, generate_gpx_analysis_pdf \
        , merge_custom_markers, plotly_elevation_plot, plotly_pace_plot, calculate_time_difference

from pace_planner import speed_calculation

def main():
    st.title("GPX Pace Planner Tutorial")
    st.markdown("---")

    st.page_link("app.py", label="**:blue[Click Here to Return to App]**")
    
    # Getting Started Section
    _col1, _col2, _col3 = st.columns([1,6,1])
    with _col2:
        st.header("Getting Started")
        st.markdown("""

                    GPX Pace planner was created to tackle the niche yet significant challenge of race planning faced by endurance athletes.
                    Current race planning tools are non-existent or fall short when it comes to accounting for the complexities of elevation changes,
                    fatigue over long distances, and the need for crew/families to support athletes at various points along the route.
                    GPX Pace Planner fills this gap by providing a comprehensive solution that integrates GPS data,
                    pacing algorithms, and user configured parameters. The end result is a comprehensive tool that outputs 
                    important strategy details in a simple and easy to understand format.
        """, width=700)
    
    st.markdown("---")
    
    # Video layout - using wider columns for larger video display
    video_col1, video_col2, video_col3 = st.columns([0.5, 9, 0.5])
    
    with video_col2:
        st.subheader("📹 Getting Started Guide")
        st.markdown("*Quick walkthrough of the basic features*")
        # Video with larger display size - using container width
        st.video("notes/GPX_tutorial.mp4", start_time=0)
    
    st.markdown("---")
    
    # Advanced Functions Section
    st.header("Advanced Functions")
    
    # Advanced features explanation
    adv_col1, adv_col2 = st.columns([0.7, 0.3])
    
    with adv_col1:
        st.warning("Both the Hill Adjustment and Fatigue Decay functions were created by me based on what felt right, but I am in the process of finding research papers or references for further improvement.")
        st.subheader("🏔️ Hill Adjustments")
        st.markdown("""
        **Automatic Pace Correction for Elevation**
        
        The hill adjustment feature automatically modifies your pace based on elevation changes:
        
        - **Grade Calculation**: 
            - Determine grade per km segment
            - Multiply grade with a factor to slow pace uphill
                - If grade > 20 then factor is 0.12 otherwise 0.08
            - Add the calculated slowdown to the base pace for uphill segments
        - **Downhill**: Base pace is unaffected
        - **GPS Elevation Data**: Requires GPS elevation data to meaningfully adjust pace, if no elevation data is present no adjustments are made.
        
        *Perfect for trail races and hilly courses where maintaining even effort is more important than even pace.*
        """)
        # Create example trail profile with random elevation changes
        distances = list(range(1, 26))  # 1km to 25km
        base_pace_example = 6.0
        
        # Generate random elevation profile using normal distribution
        np.random.seed(42)  # Fixed seed for consistent demo
        
        # Create dramatic trail profile: big climb, steep descent, level running
        elevations = []
        for km in distances:
            if km <= 8:
                # Big climb: 0m to 600m over first 8km
                elevation = (km / 8) * 600
            elif km <= 12:
                # Steep descent: 600m down to 100m over 4km
                descent_progress = (km - 8) / 4  # 0 to 1
                elevation = 600 - (descent_progress * 500)  # Drop 500m
            else:
                # Level running: stay around 100m with small variations
                base_elevation = 100
                # Add small random variations for realism
                variation = np.random.normal(0, 10)  # Small variations around 100m
                elevation = base_elevation + variation
                # Keep within reasonable bounds
                elevation = max(80, min(120, elevation))
            
            elevations.append(elevation)
        
        # Calculate grades (elevation change per km)
        grades = []
        for i, km in enumerate(distances):
            if i == 0:
                grade = 0  # Start with 0 grade
            else:
                elev_change = elevations[i] - elevations[i-1]
                grade = (elev_change / 1000) * 100  # Grade as percentage
            grades.append(grade)
        
        # Create DataFrame for trail race example
        hill_df = pd.DataFrame({
            'total_distance': distances,
            'elevation_m': elevations,
            'elevation_ft': [e * 3.28084 for e in elevations],  # Convert to feet for display
            'grade': grades,
            'pace_flat': [base_pace_example] * len(distances),
            'pace_hills': [speed_calculation(base_pace_example, d, g, 25, decay=False, hill_mode=True) 
                          for d, g in zip(distances, grades)]
        })
        
        # Create combined elevation and pace plot
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Create subplots with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Elevation Profile", "Pace Adjustment"),
            vertical_spacing=0.25,
            row_heights=[0.4, 0.6]
        )
        
        # Add elevation profile (top plot)
        fig.add_trace(
            go.Scatter(
                x=hill_df['total_distance'], 
                y=hill_df['elevation_m'],
                mode='lines+markers',
                name='Elevation',
                line=dict(color='green', width=3),
                marker=dict(size=6),
                fill='tonexty',
                fillcolor='rgba(0,128,0,0.2)'
            ),
            row=1, col=1
        )
        
        # Add flat pace line (bottom plot)
        fig.add_trace(
            go.Scatter(
                x=hill_df['total_distance'], 
                y=hill_df['pace_flat'],
                mode='lines',
                name='Flat Terrain Pace',
                line=dict(color='blue', dash='dash', width=2)
            ),
            row=2, col=1
        )
        
        # Add hill-adjusted pace line (bottom plot)
        fig.add_trace(
            go.Scatter(
                x=hill_df['total_distance'], 
                y=hill_df['pace_hills'],
                mode='lines+markers',
                name='Hill-Adjusted Pace',
                line=dict(color='red', width=3),
                marker=dict(size=6)
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            height=500,
            showlegend=True,
            plot_bgcolor='white',
            title_text="Hill Adjustment Example 25km Race: Elevation vs Pace Impact"
        )
        
        # Update x-axes
        fig.update_xaxes(title_text="Distance (km)", showgrid=True, gridcolor='lightgrey')
        
        # Update y-axes
        fig.update_yaxes(title_text="Elevation (m)", showgrid=True, gridcolor='lightgrey', row=1, col=1)
        fig.update_yaxes(title_text="Pace (min/km)", showgrid=True, gridcolor='lightgrey', row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)

        #-----------------------------------------------------
        st.subheader("⏱️ Fatigue Decay Modeling")
        st.markdown("""
        **Realistic Performance Degradation**
        
        Models how your pace naturally slows over distance:
        
        - **Progressive Slowdown**: Gradual pace increase over time with increased decay after the halfway point
        - Utilizing a piecewise logarithmic decay function for fatigue modeling
        
        *Particularly useful for ultra-marathons and long trail races.*
        """)

        #add adjustable graph
        ex_distance = st.slider(min_value=0.0, max_value=100.0, value = 10.0, step=1.0, label="Example Race Distance (km)")

        # Fatigue decay graph
        if ex_distance > 0:
            fatigue_df = pd.DataFrame([i for i in range(1, int(ex_distance)+1)], columns=['total_distance'])

            fatigue_df['pace'] = fatigue_df.apply(
                lambda row: speed_calculation(6.0, row['total_distance'], 0, ex_distance, decay=True, hill_mode=False), axis=1
            )

            pace_plot = plotly_pace_plot(fatigue_df, use_metric=True)
            if pace_plot:
                st.plotly_chart(pace_plot, use_container_width=True)
            else:
                st.info("Set a distance greater than 0 to see the fatigue decay model")
        else:
            st.info("Set a distance greater than 0 to see the fatigue decay model")

    #-----------------------------------------------------
    st.subheader("📍 Custom Markers")
    st.markdown("""
    **Strategic Waypoints and Checkpoints**
    
    Add important points along your route:
    
    - **Aid Stations or Checkpoints**: Track fuel stops, milestones, and timing points
    - **Nicknames**: Custom labels for easy identification
    - **Cutoff Times**: Optionally set time limits for buffer calculations in the output
        - Time must be in HH:MM:SS 24 hour format so 00:00:00-24:00:00

    *Essential for race planning and execution strategy especially if Pacers or Crew are involved.*
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    ### 💡 Need More Help?
    
    - **Issues or Bugs**: Report them through the GitHub repository
    - **Feature Requests**: Submit suggestions for new functionality
    
    **Created by Brandon Jerome** | GPX Pace Planner
    """)

if __name__ == "__main__":
    main()
