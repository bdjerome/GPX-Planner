import streamlit as st

def main():
    st.title("📚 GPX Pace Planner Tutorial")
    st.markdown("---")

    st.page_link("app.py", label="**:blue[Click Here to Return to App]**")
    
    # Getting Started Section
    _col1, _col2, _col3 = st.columns([1,6,1])
    with _col2:
        st.header("Getting Started")
        st.markdown("""

                    GPX Pace planner was created to tackle the niche yet significant challenge of race planning faced by endurance athletes.
                    Traditionally race planning tools are non-existent or fall short when it comes to accounting for the complexities of elevation changes,
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
    st.header("⚙️ Advanced Functions")
    
    # Advanced features explanation
    adv_col1, adv_col2 = st.columns(2)
    
    with adv_col1:
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
    
    with adv_col2:
        st.subheader("⏱️ Fatigue Decay Modeling")
        st.markdown("""
        **Realistic Performance Degradation**
        
        Models how your pace naturally slows over distance:
        
        - **Progressive Slowdown**: Gradual pace increase over time with increased decay after the halfway point
        - Utilizing a piecewise logarithmic decay function for fatigue modeling
        
        *Particularly useful for ultra-marathons and long trail races.*
        """)

        #add adjustable graph
        st.slider(min_value=0.0, max_value=100.0, step=1.0, label="Example Race Distance (km)")

        # Placeholder for fatigue decay graph
        
        st.subheader("📊 Pace Analysis")
        st.markdown("""
        **Comprehensive Performance Metrics**
        
        Detailed analysis of your planned performance:
        
        - **Split-by-Split**: Kilometer or mile breakdown
        - **Cumulative Times**: Running total at each point
        - **Grade Impact**: See elevation effect on each segment
        - **Buffer Analysis**: Time margins for cutoff points
        - **Visual Charts**: Pace and elevation profiles
        
        *All data exportable to professional PDF reports.*
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
