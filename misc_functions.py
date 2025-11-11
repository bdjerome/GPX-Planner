
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import LineCollection
import plotly.express as px
import tempfile
import os

#convert pace between min/km and min/mile
def convert_to_mph(pace_min_per_km):
    """Convert pace from min/km to min/mile"""
    return pace_min_per_km * 1.60934

def convert_to_kmh(pace_min_per_mile):
    """Convert pace from min/mile to min/km"""
    return pace_min_per_mile / 1.60934

def convert_to_miles(km):
    """Convert kilometers to miles"""
    return km / 1.60934

def convert_to_km(miles):
    """Convert miles to kilometers"""
    return miles * 1.60934

def calculate_time_difference(row):
    """
    Calculate the difference between cutoff time and clock time in minutes.
    
    Args:
        row: DataFrame row containing 'cutoff_time_formatted' and 'clock_time' columns
    
    Returns:
        float: Difference in minutes (positive = arrive before cutoff, negative = arrive after cutoff)
        pd.NA: If either time is missing or invalid
    """
    if pd.notna(row['cutoff_time_formatted']) and pd.notna(row['clock_time']):
        try:
            # Parse clock_time string to time object if it's a string
            if isinstance(row['clock_time'], str):
                clock_time = datetime.datetime.strptime(row['clock_time'], "%H:%M:%S").time()
            else:
                clock_time = row['clock_time']
            
            cutoff_time = row['cutoff_time_formatted']
            
            # Convert both times to datetime for calculation (using arbitrary date)
            base_date = datetime.date.today()
            cutoff_datetime = datetime.datetime.combine(base_date, cutoff_time)
            clock_datetime = datetime.datetime.combine(base_date, clock_time)
            
            # Calculate difference in minutes
            diff_minutes = (cutoff_datetime - clock_datetime).total_seconds() / 60
            return round(diff_minutes, 1)
        except (ValueError, TypeError):
            return pd.NA
    return pd.NA

def create_static_map_image(analyzer_df, show_arrows=True, width_inches=8, height_inches=6):
    """
    Create a stylized PNG map image using matplotlib without axes or grid
    
    Args:
        analyzer_df: DataFrame from GPXAnalyzer with route data
        show_arrows: Boolean to show directional arrows or simple markers (currently uses circles)
        width_inches: Width of the image in inches
        height_inches: Height of the image in inches
    
    Returns:
        BytesIO: PNG image data as bytes
    """
    fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=150, facecolor='white')
    
    # Get the route coordinates
    lats = analyzer_df['latitude'].values
    lons = analyzer_df['longitude'].values
    
    # Create a gradient effect along the route
    points = np.array([lons, lats]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # Create colors that transition from blue to red along the route
    n_segments = len(segments)
    colors_gradient = plt.cm.viridis(np.linspace(0, 1, n_segments))
    
    # Create line collection with gradient colors
    lc = LineCollection(segments, colors=colors_gradient, linewidths=4, alpha=0.8)
    line = ax.add_collection(lc)
    
    # Add start marker (green circle)
    ax.scatter(lons[0], lats[0], c='#2ECC71', s=200, marker='o', 
              zorder=6, edgecolor='white', linewidth=3, alpha=0.9)
    
    # Add finish marker (red square) - only if different from start
    if len(lons) > 1 and (lons[0] != lons[-1] or lats[0] != lats[-1]):
        ax.scatter(lons[-1], lats[-1], c='#E74C3C', s=200, marker='s', 
                  zorder=6, edgecolor='white', linewidth=3, alpha=0.9)
    
    # Set equal aspect ratio and adjust bounds
    ax.set_aspect('equal')
    
    # Calculate bounds with minimal padding for a cleaner look
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    padding = max(lat_range, lon_range) * 0.05  # Reduced padding
    
    ax.set_xlim(min(lons) - padding, max(lons) + padding)
    ax.set_ylim(min(lats) - padding, max(lats) + padding)
    
    # Remove all axes, labels, ticks, and spines for a clean look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Set background color
    ax.set_facecolor('white')
    
    # Remove any margins
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close(fig)  # Clean up the figure
    
    return img_buffer

#wrapper function for st.data_editor to allow dynamic input data
def dynamic_input_data_editor(data, key, **_kwargs):
    """
    Like streamlit's data_editor but which allows you to initialize the data editor with input arguments that can
    change between consecutive runs. Fixes the problem described here: https://discuss.streamlit.io/t/data-editor-not-changing-cell-the-1st-time-but-only-after-the-second-time/64894/13?u=ranyahalom
    :param data: The `data` argument you normally pass to `st.data_editor()`.
    :param key: The `key` argument you normally pass to `st.data_editor()`.
    :param _kwargs: All other named arguments you normally pass to `st.data_editor()`.
    :return: Same result returned by calling `st.data_editor()`
    """
    changed_key = f'{key}_khkhkkhkkhkhkihsdhsaskskhhfgiolwmxkahs'
    initial_data_key = f'{key}_khkhkkhkkhkhkihsdhsaskskhhfgiolwmxkahs__initial_data'

    def on_data_editor_changed():
        if 'on_change' in _kwargs:
            args = _kwargs['args'] if 'args' in _kwargs else ()
            kwargs = _kwargs['kwargs'] if 'kwargs' in _kwargs else {}
            _kwargs['on_change'](*args, **kwargs)
        st.session_state[changed_key] = True

    if changed_key in st.session_state and st.session_state[changed_key]:
        data = st.session_state[initial_data_key]
        st.session_state[changed_key] = False
    else:
        st.session_state[initial_data_key] = data
    __kwargs = _kwargs.copy()
    __kwargs.update({'data': data, 'key': key, 'on_change': on_data_editor_changed})
    return st.data_editor(**__kwargs)

def generate_gpx_analysis_pdf(analyzer, km_data, total_distance, pace_minutes, pace_seconds, finish_time, 
                             total_elevation_gain, use_metric=True, route_name="GPX Route"):
    """
    Generate a PDF report of the GPX analysis results.
    
    Args:
        analyzer: GPXAnalyzer object with analysis results
        km_data: DataFrame with kilometer split data including notes
        total_distance: Total route distance
        avg_pace: Average pace
        finish_time: Estimated finish time
        total_elevation_gain: Total elevation gain
        use_metric: Boolean for metric vs imperial units
        route_name: Name of the route for the report title
    
    Returns:
        BytesIO object containing the PDF data
    """
    buffer = BytesIO()
    
    # Create custom page template with footer
    from reportlab.platypus import PageTemplate, Frame
    from reportlab.lib.enums import TA_CENTER
    
    def add_page_footer(canvas, doc):
        """Add footer to every page"""
        canvas.saveState()
        footer_text = "Generated by GPX Pace Planner. Created by Brandon Jerome"
        canvas.setFont('Helvetica', 8)
        canvas.setFillGray(0.5)  # Gray color for footer
        # Calculate center position and draw text
        text_width = canvas.stringWidth(footer_text, 'Helvetica', 8)
        canvas.drawString((A4[0] - text_width) / 2, 0.5*inch, footer_text)
        canvas.restoreState()
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.5*inch, rightMargin=0.5*inch, 
                           topMargin=0.75*inch, bottomMargin=1*inch)  # Increased bottom margin for footer
    
    styles = getSampleStyleSheet()
    story = []
    
    # Clean up NA values in cutoff columns before processing
    km_data = km_data.copy()  # Don't modify the original
    if 'cutoff_time_formatted' in km_data.columns:
        # Replace all NA variants with empty strings
        km_data['cutoff_time_formatted'] = km_data['cutoff_time_formatted'].apply(
            lambda x: '' if (x is pd.NA or pd.isna(x) or x == pd.NaT or 
                           (hasattr(x, '_instance') and str(x) == '<NA>')) else x
        )
    
    if 'cutoff_buffer_minutes' in km_data.columns:
        # Replace all NA variants with empty strings
        km_data['cutoff_buffer_minutes'] = km_data['cutoff_buffer_minutes'].apply(
            lambda x: '' if (x is pd.NA or pd.isna(x) or 
                           (hasattr(x, '_instance') and str(x) == '<NA>')) else x
        )
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph(f"GPX Pace Analysis Report", title_style))
    story.append(Paragraph(f"Route: {route_name}", styles['Heading2']))
    story.append(Spacer(1, 15))
    
    # Add Route Map right after title
    try:
        # Generate the stylized map image using matplotlib
        map_img_buffer = create_static_map_image(analyzer.final_df, show_arrows=True, width_inches=6, height_inches=3)
        
        # Create Image directly from BytesIO buffer (no temporary file needed)
        map_img_buffer.seek(0)  # Reset buffer position
        img = Image(map_img_buffer, width=4.5*inch, height=2.25*inch)
        
        # Center the image
        from reportlab.platypus import KeepTogether
        from reportlab.lib.enums import TA_CENTER
        
        # Create a table to center the image
        img_table = Table([[img]], colWidths=[4.5*inch])
        img_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(img_table)
        
    except Exception as e:
        # If map generation fails, add a note about it
        story.append(Paragraph(f"Route visualization unavailable", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Generation date
    date_str = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"Generated on: {date_str}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary Statistics Table
    story.append(Paragraph("Summary Statistics", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    if use_metric:
        distance_str = f"{total_distance:.2f} km"
        pace_str = f"{pace_minutes}:{pace_seconds:02d} min/km"
        elevation_str = f"{total_elevation_gain:.0f} m"
    else:
        miles_distance = convert_to_miles(total_distance)
        elevation_ft = total_elevation_gain * 3.28084
        distance_str = f"{miles_distance:.2f} miles"
        pace_str = f"{pace_minutes}:{pace_seconds:02d} min/mile"
        elevation_str = f"{elevation_ft:.0f} ft"
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Distance', distance_str],
        ['Average Pace', pace_str],
        ['Estimated Duration', finish_time],
        ['Elevation Gain', elevation_str]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Kilometer Splits Table
    story.append(Paragraph("Pace Splits", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Check which optional columns exist
    has_markers = 'Marker' in km_data.columns
    has_cutoff_time = 'cutoff_time_formatted' in km_data.columns
    has_cutoff_buffer = 'cutoff_buffer_minutes' in km_data.columns
    
    # Build dynamic headers based on available columns (removed KM column)
    headers = ['Distance', 'Pace', 'Grade (%)', 'Duration', 'Clock Time']
    
    if has_cutoff_time:
        headers.append('Cutoff Time')
    if has_cutoff_buffer:
        headers.append('Cutoff Buffer (min)')
    if has_markers:
        headers.append('Marker')
    
    headers.append('Notes')
    splits_data = [headers]
    
    for _, row in km_data.iterrows():
        km_num = f"{row['km_number']:.0f}"
        
        if use_metric:
            distance = f"{row['total_distance']:.2f} km"
        else:
            distance_miles = convert_to_miles(row['total_distance'])
            distance = f"{distance_miles:.2f} mi"
        
        # Use pace_display if available, otherwise fall back to formatted pace
        if 'pace_display' in row and pd.notna(row['pace_display']) and str(row['pace_display']).strip():
            pace = str(row['pace_display'])
            # Add unit suffix if not already present
            if use_metric and 'min/km' not in pace:
                pace += ' min/km'
            elif not use_metric and 'min/mi' not in pace:
                pace += ' min/mi'
        else:
            # Fallback to manual formatting
            if use_metric:
                pace = f"{row['pace']:.2f} min/km"
            else:
                pace_mph = convert_to_mph(row['pace'])
                pace = f"{pace_mph:.2f} min/mi"
        
        grade = f"{row['grade']:.1f}%"
        time = row['cumulative_time_hms']
        clock_time = row['clock_time']
        notes_text = row.get('Notes', '') if 'Notes' in row else ''
        
        # Build row data dynamically based on available columns (removed km_num)
        row_data = [distance, pace, grade, time, clock_time]
        
        # Add cutoff time if available
        if has_cutoff_time:
            cutoff_time = row.get('cutoff_time_formatted', '') if 'cutoff_time_formatted' in row else ''
            if cutoff_time == pd.NaT or pd.isna(cutoff_time):
                cutoff_time = ''
            row_data.append(cutoff_time)
        
        # Add cutoff buffer if available
        if has_cutoff_buffer:
            cutoff_buffer = row.get('cutoff_buffer_minutes', '') if 'cutoff_buffer_minutes' in row else ''
            if pd.notna(cutoff_buffer) and cutoff_buffer != '':
                cutoff_buffer = f"{cutoff_buffer}"
            else:
                cutoff_buffer = ''
            row_data.append(cutoff_buffer)
        
        # Add marker if available
        if has_markers:
            marker = row.get('Marker', '') if 'Marker' in row else ''
            row_data.append(marker)
        
        # Create a wrapped paragraph for notes if there's text
        if notes_text and str(notes_text).strip():
            # Create a paragraph style for notes with smaller font and wrapping
            notes_style = ParagraphStyle(
                'NotesStyle',
                parent=styles['Normal'],
                fontSize=7,
                leading=8,
                alignment=0,  # Left alignment
                wordWrap='LTR'
            )
            notes = Paragraph(str(notes_text).strip(), notes_style)
        else:
            notes = ''
        
        row_data.append(notes)
        splits_data.append(row_data)
    
    # Create splits table with simplified column widths (removed KM column)
    # Start with base column widths - now 5 columns instead of 6
    col_widths = [1.0*inch, 0.8*inch, 0.6*inch, 0.7*inch, 0.9*inch]  # Base 5 columns
    
    # Add optional columns with wider fixed widths
    if has_cutoff_time:
        col_widths.append(0.9*inch)  # Increased from 0.7
    if has_cutoff_buffer:
        col_widths.append(1.0*inch)  # Increased from 0.7 for "Cutoff Buffer (min)"
    if has_markers:
        col_widths.append(0.8*inch)
    
    # Always add Notes column last
    col_widths.append(1.3*inch)  # Slightly increased Notes width
    
    splits_table = Table(splits_data, colWidths=col_widths)
    
    # Calculate notes column index (always last)
    notes_col_index = len(col_widths) - 1
    
    splits_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Changed to TOP for better text wrapping
        ('LEFTPADDING', (0, 0), (-1, -1), 4),  # Add padding for better readability
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        # Special alignment for notes column - left align for better readability
        ('ALIGN', (notes_col_index, 1), (notes_col_index, -1), 'LEFT'),
    ]))
    
    story.append(splits_table)
    story.append(Spacer(1, 20))
    
    # Build PDF with custom footer on all pages
    doc.build(story, onFirstPage=add_page_footer, onLaterPages=add_page_footer)
    buffer.seek(0)
    return buffer

def merge_custom_markers(analyzer_final_df, custom_marker_data, use_km_markers=True):
    """
    Merge custom markers (like aid stations) with the analyzer's final DataFrame
    based on the nearest kilometer marker.
    
    Args:
        analyzer_final_df: DataFrame from GPXAnalyzer.final_df
        custom_marker_data: DataFrame with columns ['Distance', 'Nickname']
        use_km_markers: Boolean indicating if distances are in km (True) or miles (False)
    
    Returns:
        DataFrame: Updated final_df with custom marker information merged
    """
    
    # Create a copy to avoid modifying the original
    df = analyzer_final_df.copy()
    
    # Initialize custom marker columns if they don't exist
    if 'custom_marker' not in df.columns:
        df['custom_marker'] = ''
    if 'marker_nickname' not in df.columns:
        df['marker_nickname'] = ''
    
    # Return original df if no custom markers provided
    if custom_marker_data is None or len(custom_marker_data) == 0:
        return df
    
    # Clean and validate custom marker data
    custom_markers = custom_marker_data.copy()
    
    # Remove rows with missing or invalid data
    custom_markers = custom_markers.dropna(subset=['Distance', 'Nickname'])
    custom_markers['Distance'] = pd.to_numeric(custom_markers['Distance'], errors='coerce')
    custom_markers = custom_markers[custom_markers['Distance'] > 0]
    custom_markers = custom_markers[custom_markers['Nickname'].str.strip() != '']
    
    if len(custom_markers) == 0:
        return df
    
    #try to interpret cutoff times from custom markers
    if not custom_markers.empty and len(custom_markers) > 0:
        # Check if 'Cutoff Time' column exists and has valid entries
        if 'Cutoff Time' in custom_markers.columns:
            # Initialize cutoff_time_formatted column if it doesn't exist
            if 'cutoff_time_formatted' not in custom_markers.columns:
                custom_markers['cutoff_time_formatted'] = pd.NA
                
            for idx, row in custom_markers.iterrows():
                cutoff_time_str = row.get('Cutoff Time', None)
                if pd.notna(cutoff_time_str) and str(cutoff_time_str).strip() != '':
                    try:
                        cutoff_str = str(cutoff_time_str).strip()
                        # Try parsing with seconds first (HH:MM:SS)
                        try:
                            custom_markers.at[idx, 'cutoff_time_formatted'] = datetime.datetime.strptime(cutoff_str, "%H:%M:%S").time()
                        except ValueError:
                            # If that fails, try parsing without seconds (HH:MM)
                            custom_markers.at[idx, 'cutoff_time_formatted'] = datetime.datetime.strptime(cutoff_str, "%H:%M").time()
                    except ValueError:
                        # Fill with NA value instead of showing warning to avoid breaking computation
                        custom_markers.at[idx, 'cutoff_time_formatted'] = pd.NA


    # Convert distances to km if they're in miles
    if not use_km_markers:
        custom_markers['Distance'] = custom_markers['Distance'].apply(convert_to_km)
    
    # Get only kilometer marker rows for matching
    km_markers = df[df['is_km_marker'] == 1].copy()
    
    if len(km_markers) == 0:
        return df
    
    # Initialize cutoff_time_formatted column in main df if cutoff times exist in input
    if 'Cutoff Time' in custom_marker_data.columns:
        if 'cutoff_time_formatted' not in df.columns:
            df['cutoff_time_formatted'] = pd.NA

    # For each custom marker, find the nearest kilometer marker
    for _, marker in custom_markers.iterrows():
        target_distance = marker['Distance']
        nickname = marker['Nickname'].strip()
        cutoff_time = marker.get('cutoff_time_formatted', pd.NA) if 'cutoff_time_formatted' in marker else pd.NA
        
        # Find the closest km marker by total_distance
        distances = np.abs(km_markers['total_distance'] - target_distance)
        closest_idx = distances.idxmin()
        
        # Get the km_number of the closest marker
        closest_km = km_markers.loc[closest_idx, 'km_number']
        
        # Update all rows with this km_number to include the custom marker
        mask = (df['km_number'] == closest_km) & (df['is_km_marker'] == 1)
        
        if mask.any():
            # If there's already a custom marker, append with separator
            existing_marker = df.loc[mask, 'custom_marker'].iloc[0]
            existing_nickname = df.loc[mask, 'marker_nickname'].iloc[0]
            
            if existing_marker and existing_marker.strip():
                df.loc[mask, 'custom_marker'] = f"{existing_marker}, {nickname}"
                df.loc[mask, 'marker_nickname'] = f"{existing_nickname}, {nickname}"
            else:
                df.loc[mask, 'custom_marker'] = nickname
                df.loc[mask, 'marker_nickname'] = nickname
            
            # Add cutoff time if column is available (even if cutoff_time is NA)
            if 'cutoff_time_formatted' in df.columns:
                df.loc[mask, 'cutoff_time_formatted'] = cutoff_time
    
    return df

def get_custom_markers_summary(analyzer_final_df):
    """
    Extract a summary of custom markers from the final DataFrame.
    
    Args:
        analyzer_final_df: DataFrame with merged custom markers
    
    Returns:
        DataFrame: Summary of custom markers with their positions and details
    """
    
    # Filter for km markers that have custom markers
    custom_marker_rows = analyzer_final_df[
        (analyzer_final_df['is_km_marker'] == 1) & 
        (analyzer_final_df['custom_marker'].str.strip() != '')
    ].copy()
    
    if len(custom_marker_rows) == 0:
        return pd.DataFrame(columns=['KM', 'Distance', 'Marker', 'Pace', 'Time'])
    
    # Create summary DataFrame
    summary = custom_marker_rows[[
        'km_number', 'total_distance', 'custom_marker', 'pace', 'cumulative_time_hms'
    ]].copy()
    
    summary.columns = ['KM', 'Distance', 'Marker', 'Pace', 'Time']
    summary = summary.reset_index(drop=True)
    
    return summary

def plotly_elevation_plot(analyzer, total_elevation_gain, use_metric=True):
    "create elevation plot using plotly for output"

    elevation_df = analyzer.final_df[['total_distance', 'elevation']].copy()
    elevation_df = elevation_df.dropna(subset=['elevation'])

    #creating plotly chart if elevation data exists
    if total_elevation_gain > 0:
        # Convert units if imperial is selected
        if not use_metric:
            elevation_df['total_distance'] = elevation_df['total_distance'].apply(convert_to_miles)
            elevation_df['elevation'] = elevation_df['elevation'] * 3.28084  # Convert meters to feet
            distance_label = 'Distance (miles)'
            elevation_label = 'Elevation (ft)'
        else:
            distance_label = 'Distance (km)'
            elevation_label = 'Elevation (m)'
        
        elevation_plot = px.line(
            elevation_df,
            x='total_distance',
            y='elevation',
            labels={
                'total_distance': distance_label,
                'elevation': elevation_label
            },
            height=300
        )
        elevation_plot.update_traces(line=dict(color='#3498DB', width=2))
        elevation_plot.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False)
        )
    else:
        elevation_plot = None


    return elevation_plot


def plotly_pace_plot(data, use_metric=True):
    "create pace plot used in the streamlit output"
    
    # Handle both analyzer objects and DataFrames
    if hasattr(data, 'final_df'):
        # It's an analyzer object
        pace_df = data.final_df[['total_distance', 'pace']].copy()
    else:
        # It's a DataFrame - assume it has the correct column names
        pace_df = data[['total_distance', 'pace']].copy()
    
    pace_df = pace_df.dropna(subset=['pace'])

    #creating plotly chart if elevation data exists
    if len(pace_df) > 1:
        # Convert units if imperial is selected
        if not use_metric:
            pace_df['total_distance'] = pace_df['total_distance'].apply(convert_to_miles)
            pace_df['pace'] = pace_df['pace'].apply(convert_to_mph)
            distance_label = 'Distance (miles)'
            pace_label = 'Pace (min/mile)'
        else:
            distance_label = 'Distance (km)'
            pace_label = 'Pace (min/km)'
        
        pace_plot = px.line(
            pace_df,
            x='total_distance',
            y='pace',
            labels={
                'total_distance': distance_label,
                'pace': pace_label
            },
            height=300
        )
        pace_plot.update_traces(line=dict(color='#3498DB', width=2))
        pace_plot.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False)
        )
    else:
        pace_plot = None



    return pace_plot