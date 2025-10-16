#Map package
import datetime
import gpxpy
from geopy.distance import geodesic

#Data wrangling
import pandas as pd
import numpy as np
import math

#visualization
import folium
import matplotlib.pyplot as plt

#Usage Order IMPORTANT
# analyzer = GPXAnalyzer('route.gpx')
# analyzer.load_gpx()
# analyzer.map_adjustment(loops=2)  
# analyzer.calculate_distances()     # Must be before find_kilometer_markers
# analyzer.find_kilometer_markers()  # Creates km_number column

# pace_calc = PaceCalculator(analyzer, 6.2)
# pace_calc.calculate_pace()  

# map = MapVisualizer(analyzer.final_df)
# map.create_base_map()
# map.add_kilometer_markers()
# map.save('my_map.html')

class GPXAnalyzer:
    def __init__(self, gpx_file_path):
        self.gpx_file_path = gpx_file_path
        self.gpx_parsed = None
        self.df = None
        self.final_df = None
        self.km_markers = {}
        
    def load_gpx(self):
        with open(self.gpx_file_path, 'r') as gpx_file:
            self.gpx_parsed = gpxpy.parse(gpx_file)

        # Extract track points (latitude, longitude, elevation)
        points = []
        for track in self.gpx_parsed.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append((point.latitude, point.longitude, point.elevation))

        # You can then convert these points into a Pandas DataFrame for easier manipulation
        self.df = pd.DataFrame(points, columns=['latitude', 'longitude', 'elevation'])

        #finding elevation data if none given 
        if self.df['elevation'].isnull().all():
            self.df['elevation'] = 0

    #right now only allows for looping
    def map_adjustment(self, loops: int = 0):

        #looping input gpx route by concatenating
        if loops > 0:
            loop_holder = []
            for _ in range(loops):
                copy_df = self.df.copy()  # Create a copy of the DataFrame
                copy_df['lap'] = _ + 1  # Add a column to indicate the loop number
                loop_holder.append(copy_df)
            self.final_df = pd.concat(loop_holder, axis=0).reset_index(drop=True)
        else:
            self.df['loop'] = 1  # Add a column to indicate the loop number
            self.final_df = self.df


    def calculate_distances(self):
        def calculate_segment_distances(df):
            # Get previous row coordinates using shift()
            prev_coords = list(zip(df['latitude'].shift(1), df['longitude'].shift(1)))
            curr_coords = list(zip(df['latitude'], df['longitude']))
            
            distances = []
            for i, (curr, prev) in enumerate(zip(curr_coords, prev_coords)):
                if i == 0 or pd.isna(prev[0]):  # First row has no previous
                    distances.append(0.0)
                else:
                    distances.append(geodesic(prev, curr).kilometers)
    
            return distances
        
        self.final_df['segment_distance'] = calculate_segment_distances(self.final_df)
        self.final_df['total_distance'] = self.final_df['segment_distance'].cumsum()
    
    def find_kilometer_markers(self):
        # Find the row index closest to each whole kilometer
        def find_kilometer_markers(df):
            """
            For each whole kilometer, find the row index that has the closest total_distance
            """
            max_distance = int(df['total_distance'].max()) + 1
            kilometer_markers = {}
            
            for km in range(max_distance):
                # Find the index of the row closest to this kilometer
                differences = np.abs(df['total_distance'] - km)
                closest_idx = differences.idxmin()
                kilometer_markers[km] = closest_idx
            
            return kilometer_markers

        # Get the kilometer markers
        km_markers = find_kilometer_markers(self.final_df)

        # Create a column that indicates if this row is a kilometer marker
        self.final_df['is_km_marker'] = 0
        self.final_df['km_number'] = np.nan

        # Mark the kilometer marker rows
        for km, row_idx in km_markers.items():
            self.final_df.loc[row_idx, 'is_km_marker'] = 1
            self.final_df.loc[row_idx, 'km_number'] = km

class PaceCalculator:
    def __init__(self, gpx_analyzer, base_pace):
        self.gpx_analyzer = gpx_analyzer
        self.base_pace = base_pace
        
    def calculate_pace(self, decay=False, hill_mode=False):

        #creating local reference
        df = self.gpx_analyzer.final_df
        
        #calculating grade per km segment
        df['km_number'] = df['km_number'].ffill()

        grade_per_km = df.groupby('km_number')['elevation'].agg(['first', 'last'])
        grade_per_km['elevation_change'] = grade_per_km['last'] - grade_per_km['first']
        grade_per_km['grade'] = grade_per_km['elevation_change'] / 1.0  # since it's per km, divide by 1 km
        grade_per_km.reset_index(inplace=True)

        #Calculate the grade between each point
        df = df.merge(grade_per_km[['km_number', 'grade']], on='km_number', how='left', suffixes=('', '_per_km'))

        #segment gain 
        df['segment_gain'] = df['elevation'].diff()

        #creating function to calculate pace over each segment
        def speed_calculation(base_pace, current_distance, grade, total_race_distance, decay: bool = False, hill_mode: bool = False):
            """
            Estimate pace (minutes per km) based on segment distance and grade.
            Uses logarithmic decay for more realistic fatigue modeling.
            """
            # pace is min/km
            adjusted_pace = base_pace
            
            if decay:
                # Logarithmic decay - pace slows down more after halfway point
                halfway_point = total_race_distance / 2

                if current_distance <= halfway_point:
                    early_decay = 0.05 * math.log(1 + current_distance/halfway_point)
                else:
                    progress_beyond_halfway = (current_distance - halfway_point)
                    early_decay = 0.05 * math.log(2) + 0.2 * math.log(1 + progress_beyond_halfway)

                adjusted_pace += early_decay  # ADD to make pace slower

            if hill_mode and grade > 0 and grade < 20:
                # Hill adjustment - pace decreases based on positive grade
                grade_factor = 0.08  # pace decreases by 0.08 min/km for every 1% increase in grade
                adjusted_pace += grade_factor * grade
            elif hill_mode and grade >= 20:
                grade_factor = 0.12  # pace decreases by 0.12 min/km for every 1% increase in grade
                adjusted_pace += grade_factor * grade
                adjusted_pace = min(adjusted_pace, 12.5) #ensure pace doesn't exceed equivalent of 20 min/mile
            
            return adjusted_pace

        # Get total race distance for decay calculation
        total_race_distance = df['total_distance'].max()

        # Use the base_pace provided by the user (not hardcoded)
        df['pace'] = df.apply(
            lambda row: speed_calculation(
                self.base_pace,  # Use instance variable instead of hardcoded value
                row['total_distance'], 
                row['grade'], 
                total_race_distance,
                decay=decay,  # Use parameter passed to method
                hill_mode=hill_mode  # Use parameter passed to method
            ), 
            axis=1
        )
        
        # Assign the modified df back to the analyzer
        self.gpx_analyzer.final_df = df
    
    def calculate_times(self):
        # Calculate segment and cumulative times using df
        df = self.gpx_analyzer.final_df
        # Add your pace calculation logic here
        # Calculate segment times and cumulative time
        df['segment_time'] = df['segment_distance'] * df['pace']  # time in minutes
        df['cumulative_time'] = df['segment_time'].cumsum()

        # Convert cumulative time to hours:minutes:seconds format
        def minutes_to_hms(minutes):
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            secs = int((minutes % 1) * 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d}"

        df['cumulative_time_hms'] = df['cumulative_time'].apply(minutes_to_hms)

        self.gpx_analyzer.final_df = df

    def calculate_clock_times(self, race_start_time):
        # Calculate clock times based on race start time
        df = self.gpx_analyzer.final_df
        # Ensure race_start_time is a datetime.time object
        if not isinstance(race_start_time, datetime.time):
            raise ValueError("race_start_time must be a datetime.time object")
        
        df['clock_time'] = df['cumulative_time'].apply(
            lambda x: (datetime.datetime.combine(datetime.date.today(), race_start_time) + datetime.timedelta(minutes=x)).strftime('%H:%M:%S')
        )

        self.gpx_analyzer.final_df = df


class MapVisualizer:
    def __init__(self, df):
        self.df = df
        self.map = None
    
    def _add_legend(self):
        """Add a legend showing lap colors to the map"""
        # Get unique lap numbers from the data
        if 'lap' in self.df.columns:
            unique_laps = sorted(self.df['lap'].dropna().unique())
        else:
            unique_laps = [1]  # Default to single lap
        
        # Color mapping (same as used in marker functions)
        colors = ['blue', 'green', 'red', 'purple', 'orange']
        
        # Build legend HTML
        legend_items = []
        for lap in unique_laps:
            color_index = (int(lap) - 1) % len(colors)
            color = colors[color_index]
            legend_items.append(f'&nbsp; Lap {int(lap)} &nbsp; <i class="fa fa-circle" style="color:{color}"></i><br>')
        
        legend_html = f'''
        <div style="position: fixed; 
             bottom: 50px; left: 50px; width: 150px; height: {60 + len(unique_laps) * 20}px; 
             border:2px solid grey; z-index:9999; font-size:14px;
             background-color:white; opacity: 0.9; border-radius: 5px; padding: 10px;">
             <b>Lap Legend</b> <br>
             {''.join(legend_items)}
        </div>
        '''
        
        # Add the legend to the map
        self.map.get_root().html.add_child(folium.Element(legend_html))
        
    def create_base_map(self):
        # Create basic map with track
        df = self.df
        m2 = folium.Map(location=[df['latitude'][0], df['longitude'][0]], zoom_start=12)

        # Add the main track
        folium.PolyLine(df[['latitude', 'longitude']].values, color='red', weight=2.5, opacity=1).add_to(m2)

        # Add markers for start and end points (optional)
        folium.Marker([df['latitude'].iloc[0], df['longitude'].iloc[0]], popup='Start/End').add_to(m2)

        self.map = m2
    
    def add_kilometer_markers_directional(self):
        # Add directional arrows at kilometer points
        if self.map is None:
            raise ValueError("Map not created yet. Call create_base_map() first.")

        def calculate_bearing(lat1, lon1, lat2, lon2):
            """
            Calculate the bearing (direction) from point 1 to point 2
            Returns bearing in degrees (0-360)
            """
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            dlon = lon2 - lon1
            
            y = math.sin(dlon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            
            bearing = math.atan2(y, x)
            bearing = math.degrees(bearing)
            bearing = (bearing + 360) % 360  # Convert to 0-360 range
            
            return bearing

        def create_arrow_icon(color, rotation):
            """
            Create a custom HTML/CSS arrow icon for better directional visualization
            """
            return folium.DivIcon(
                html=f'''
                <div style="
                    width: 0; 
                    height: 0; 
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-bottom: 20px solid {color};
                    transform: rotate({rotation}deg);
                    transform-origin: 8px 12px;
                "></div>
                ''',
                icon_size=(16, 16),
                icon_anchor=(8, 12)
            )
        
        #creating local references
        combined = self.df
        m2 = self.map
        
        # Add kilometer markers with directional arrows
        if 'is_km_marker' not in combined.columns:
            raise ValueError("is_km_marker does not exist make sure to run analyzer.find_kilometer_markers() first")
        
        km_marker_rows = combined[combined['is_km_marker'] == 1].copy()

        for i, (index, row) in enumerate(km_marker_rows.iterrows()):
            # Calculate bearing to next point (look ahead for smoother direction)
            #take minimum of 5 or remaining markers for bearing calculation
            look_ahead = min([5, len(km_marker_rows) - i - 1])
            if look_ahead > 0 and index + look_ahead < len(combined):
                next_point_idx = index + look_ahead
                bearing = calculate_bearing(
                    row['latitude'], row['longitude'],
                    combined.iloc[next_point_idx]['latitude'], combined.iloc[next_point_idx]['longitude']
                )
                
                # Dynamic color coding based on lap number
                colors = ['blue', 'green', 'red', 'purple', 'orange']
                lap_number = row.get('lap', 1)  # Default to 1 if lap column doesn't exist
                color_index = (lap_number - 1) % len(colors)  # Cycle through colors
                color = colors[color_index]
                
                # Create custom arrow marker
                arrow_icon = create_arrow_icon(color, bearing)
                
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    icon=arrow_icon,
                    popup=f"KM {int(row['km_number'])}<br>Distance: {row['total_distance']:.3f} km<br>Elevation: {row['elevation']:.1f} m<br>Bearing: {bearing:.1f}°"
                ).add_to(m2)
            else:
                # For the last point, use a circle marker since there's no next point
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=8,
                    popup=f"KM {int(row['km_number'])}<br>Distance: {row['total_distance']:.3f} km<br>Elevation: {row['elevation']:.1f} m<br>FINISH",
                    color='red',
                    fillColor='red',
                    fillOpacity=0.8
                ).add_to(m2)
        
        # Add legend to show lap colors
        self._add_legend()
    
    def add_kilometer_markers(self):
        # Add simple circle markers at kilometer points (non-directional)
        if self.map is None:
            raise ValueError("Map not created yet. Call create_base_map() first.")
        
        #creating local references
        combined = self.df
        m2 = self.map
        
        # Add kilometer markers with simple circles
        if 'is_km_marker' not in combined.columns:
            raise ValueError("is_km_marker does not exist make sure to run analyzer.find_kilometer_markers() first")
        
        km_marker_rows = combined[combined['is_km_marker'] == 1].copy()

        for i, (index, row) in enumerate(km_marker_rows.iterrows()):
            # Dynamic color coding based on lap number
            colors = ['blue', 'green', 'red', 'purple', 'orange']
            lap_number = row.get('lap', 1)  # Default to 1 if lap column doesn't exist
            color_index = (lap_number - 1) % len(colors)  # Cycle through colors
            color = colors[color_index]
            
            # Create simple circle marker
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=4,
                popup=f"KM {int(row['km_number'])}<br>Distance: {row['total_distance']:.3f} km<br>Elevation: {row['elevation']:.1f} m",
                color=color,
                fillColor=color,
                fillOpacity=1.0,
                weight=2
            ).add_to(m2)
        
        # Add legend to show lap colors
        self._add_legend()
            
    def save_map(self, filename):
        # Save map to HTML file
        self.map.save(filename)

