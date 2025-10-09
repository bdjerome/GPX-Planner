
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import datetime

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

def generate_gpx_analysis_pdf(analyzer, km_data, total_distance, avg_pace, finish_time, 
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
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
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
        pace_str = f"{avg_pace:.2f} min/km"
        elevation_str = f"{total_elevation_gain:.0f} m"
    else:
        miles_distance = convert_to_miles(total_distance)
        mph_pace = convert_to_mph(avg_pace)
        elevation_ft = total_elevation_gain * 3.28084
        distance_str = f"{miles_distance:.2f} miles"
        pace_str = f"{mph_pace:.2f} min/mile"
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
    story.append(Spacer(1, 30))
    
    # Kilometer Splits Table
    story.append(Paragraph("Kilometer Splits", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Prepare splits data
    splits_data = [['KM', 'Distance', 'Pace', 'Grade (%)', 'Cumulative Time', 'Notes']]
    
    for _, row in km_data.iterrows():
        km_num = f"{row['km_number']:.0f}"
        
        if use_metric:
            distance = f"{row['total_distance']:.2f} km"
            pace = f"{row['pace']:.2f} min/km"
        else:
            distance_miles = convert_to_miles(row['total_distance'])
            pace_mph = convert_to_mph(row['pace'])
            distance = f"{distance_miles:.2f} mi"
            pace = f"{pace_mph:.2f} min/mi"
        
        grade = f"{row['grade']:.1f}%"
        time = row['cumulative_time_hms']
        notes = row.get('Notes', '') if 'Notes' in row else ''
        
        splits_data.append([km_num, distance, pace, grade, time, notes])
    
    # Create splits table with dynamic column widths
    col_widths = [0.6*inch, 1*inch, 1*inch, 0.8*inch, 1.2*inch, 2*inch]
    splits_table = Table(splits_data, colWidths=col_widths)
    splits_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(splits_table)
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,  # Center alignment
        textColor=colors.grey
    )
    story.append(Paragraph("Generated by GPX Pace Planner", footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer