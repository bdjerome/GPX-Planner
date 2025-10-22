import streamlit as st

def main():
    st.title("📚 GPX Pace Planner Tutorial")
    st.markdown("---")
    
    # Getting Started Section
    st.header("🚀 Getting Started")
    st.markdown("""
    **Write your getting started paragraph here.** This section will provide an overview of what GPX Pace Planner does 
    and guide new users through their first experience with the application. You can explain the basic concept, 
    what users need to get started, and what they can expect to achieve with the tool.
    """)
    
    st.markdown("---")
    
    # Video layout in columns for nice formatting
    video_col1,video_col2, video_col3 = st.columns(3)
    
    with video_col1:
        pass
    
    with video_col2:
        st.subheader("📹 Getting Started Guide")
        st.markdown("*Quick walkthrough of the basic features*")
        # Placeholder for video - replace with actual video URL when ready
        st.info("**Video URL**: Add your video URL here using st.video('your_video_url')")
        # st.video("your_video_url_here")

    with video_col3:
        pass
    
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
        
        - **Uphill**: Pace slows based on gradient percentage
        - **Downhill**: Pace increases (with safety limits)
        - **Customizable**: Adjust sensitivity to match your running style
        - **Grade Calculation**: Uses GPS elevation data for accuracy
        
        *Perfect for trail races and hilly courses where maintaining even effort is more important than even pace.*
        """)
        
        st.subheader("� Custom Markers")
        st.markdown("""
        **Strategic Waypoints and Checkpoints**
        
        Add important points along your route:
        
        - **Aid Stations**: Track water and fuel stops
        - **Checkpoints**: Race timing points and milestones  
        - **Cutoff Times**: Set time limits with buffer calculations
        - **Personal Notes**: Reminders for strategy or terrain
        - **Interactive Editing**: Click on map or use data table
        
        *Essential for race planning and execution strategy.*
        """)
    
    with adv_col2:
        st.subheader("⏱️ Fatigue Decay Modeling")
        st.markdown("""
        **Realistic Performance Degradation**
        
        Models how your pace naturally slows over distance:
        
        - **Progressive Slowdown**: Gradual pace increase over time
        - **Customizable Rate**: Adjust based on your endurance level
        - **Distance Scaling**: More pronounced effect on longer routes
        - **Realistic Predictions**: Better finish time estimates
        
        *Particularly useful for ultra-marathons and long trail races.*
        """)
        
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
    - **General Questions**: Check the FAQ section above
    
    **Created by Brandon Jerome** | GPX Pace Planner
    """)

if __name__ == "__main__":
    main()
