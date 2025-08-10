import pandas as pd
import sqlite3
import folium
import os
import argparse
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List, Tuple, Optional, Union
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
import geopandas as gpd
from shapely.geometry import Point
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging
import hashlib
import pickle
from pathlib import Path
import concurrent.futures
import threading
import time

DEFAULT_CSV_FILE = "geodata.csv"
DEFAULT_DB_FILE = "geolocations.db"
OUTPUT_MAP = "map.html"
OUTPUT_PLOT = "geolocation_plot.png"
OUTPUT_CLUSTER_MAP = "cluster_map.html"
OUTPUT_STATS_REPORT = "geodata_analysis_report.html"
OUTPUT_CLUSTER_PLOT = "clustering_analysis.png"
OUTPUT_HEATMAP = "geodata_heatmap.html"
OUTPUT_TIMELINE = "geodata_timeline.html"
OUTPUT_3D_MAP = "3d_geodata_map.html"
OUTPUT_NETWORK_GRAPH = "geodata_network.html"
OUTPUT_ANOMALY_REPORT = "anomaly_detection_report.html"

# Configuration
CONFIG = {
    'max_clusters': 10,
    'min_cluster_size': 3,
    'eps_threshold': 0.5,
    'anomaly_threshold': 2.0,
    'cache_ttl': 3600,  # 1 hour
    'max_concurrent_requests': 5,
    'geocoding_timeout': 10,
    'plot_style': 'seaborn-v0_8',
    'map_tile': 'OpenStreetMap'
}

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geodata_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

csv_content = """id,name,latitude,longitude,timestamp
1,Location1,55.424975,37.578936,2025-04-22 12:00:00
2,Location2,55.817062, 37.383687,2025-04-28 22:00:00
3,Location3,55.457021, 37.598932,2025-04-28 22:00:00
4,Vologda,59.223058, 39.889616,2004-01-26 06:15:00
5,St. Petersburg,59.947343, 30.304550,2025-04-28 22:00:00
6,N. Novgorod,56.330062, 43.998288,2025-04-28 22:00:00
7,Kazan,55.800484, 49.105920,2025-04-28 22:00:00
8,Location4,55.826270, 37.637526,2025-04-28 22:00:00
9,Location5,55.715765, 37.553634,2025-04-28 22:00:00
10,Location6,55.791170, 37.559590,2025-04-28 22:00:00
11,Kaliningrad,54.712899, 20.496575,2025-04-28 22:00:00
12,Location7,55.775551, 37.658467,2025-04-28 22:00:00
13,Location8,55.761132, 37.606334,2025-04-28 22:00:00
14,Location9,55.457021, 37.598932,2022-11-22 10:00:00
15,Location10,55.397756, 37.564221,2025-04-25 16:00:00
16,Location11,55.421855, 37.569188,2025-03-03 17:00:00
17,Location12,55.446694, 37.545452,2024-12-22 16:00:00
18,Location13,55.329042, 37.483137,2024-12-22 16:00:00
19,Location14,55.346994, 37.395084,2013-10-10 20:00:00
20,Russia,54.712899, 20.496575,2025-04-28 22:00:00
21,IqnixTech,55.423306, 37.579285,2022-03-24 15:00:00
22,Podolsk Cadets Square,55.423252,37.518292,2022-03-24 15:00:00
23,Yaroslavl',57.626559,39.893813,2025-04-28 22:00:00
24,Kostroma,57.767918,40.926894,2025-04-28 22:00:00
25,Tver',56.858745,35.917421,2025-04-28 22:00:00
26,Smolensk,54.778263,32.051054,2025-04-28 22:00:00
27,Bryansk,53.243397,34.360934,2025-04-28 22:00:00
28,Vladimir,56.130789,40.404232,2025-04-28 22:00:00
29,Arkhangel'sk,64.546907,40.497798,2025-04-28 22:00:00
30,Volgograd,48.706584,44.493640,2025-04-28 22:00:00
31,Sochi,43.593763,39.705235,2025-04-28 22:00:00
32,Pyatigorsk,44.042100,43.065374,2025-04-28 22:00:00
33,Taganrog,47.211333,38.931935,2025-04-28 22:00:00
34,Serpukhov,54.914743,37.412855,2025-06-26 09:00:00
35,Minsk,53.908358,27.552593,2025-06-26 09:00:00
36,Petrozavodsk,61.793016,34.333415,2025-06-26 09:00:00
37,Murmansk,68.977104,33.056507,2025-06-26 09:00:00
38,Rogachevo Airport,71.611780,52.466269,2025-06-26 09:00:00
39,White lip,71.536107,52.343941,2025-06-26 09:00:00
40,Vorkuta,67.503124,64.043542,2025-06-26 09:00:00
41,Kostomuksha,64.589504,30.579746,2025-06-26 09:00:00
42,Mount Elbrus,43.353264,42.435176,2025-06-26 09:00:00
43,Mogilev,53.898607,30.321062,2025-06-26 09:00:00
44,Brest,52.099228,23.683341,2025-06-26 09:00:00
45,Vitebsk,55.184919,30.199976,2025-06-26 09:00:00
46,Gomel',52.430170,31.003547,2025-06-26 09:00:00
47,Lida,53.892105,25.301492,2025-06-26 09:00:00
48,Grodno,53.678613,23.829195,2025-06-26 09:00:00
49,Nicosia,35.180810,33.309687,2017-06-18 09:00:00
50,Voronezh,51.673499,39.165851,2025-06-26 09:00:00
51,Perm',58.010005,56.205969,2025-06-26 09:00:00
52,Ekaterinburg,56.846331,60.565068,2025-06-26 09:00:00
53,Chelyabinsk,55.206957,61.335616,2025-06-26 09:00:00
54,Penza,53.207064,44.977984,2025-06-26 09:00:00
55,Ishim,56.109267,69.448386,2025-06-26 09:00:00
56,New Urengoi,66.097072,76.636497,2025-06-26 09:00:00
57,Salehard,66.530350,66.612494,2025-06-26 09:00:00
58,Lisbon,38.707890,-9.136594,2025-06-26 09:00:00
59,Madrid,40.425930,-3.731654,2025-06-26 09:00:00
60,Paris,48.881132,2.311644,2025-06-26 09:00:00
61,Zurich,47.407862,8.520059,2025-06-26 09:00:00
62,Rome,41.914719,12.482877,2025-06-26 09:00:00
63,Zagreb,45.822709,15.972358,2025-06-26 09:00:00
64,Belgrad,44.828813,20.441536,2025-06-26 09:00:00
65,Saraevo,43.865163,18.416096,2025-06-26 09:00:00
66,Podgorica,42.446889,19.252691,2025-06-26 09:00:00
67,Skopje,42.005096,21.410225,2025-06-26 09:00:00
68,Athens,37.976831,23.721869,2025-06-26 09:00:00
69,Valletta,35.909522,14.497309,2025-06-26 09:00:00
70,Sofia,42.707223,23.303571,2025-06-26 09:00:00
71,Ankara,39.936230,32.836350,2025-06-26 09:00:00
72,Kiyv,50.452781,30.491683,2025-06-26 09:00:00
73,Chisinau,47.047938,28.818493,2025-06-26 09:00:00
74,Tiraspol',46.840622,29.605553,2025-06-26 09:00:00
75,Vienna,48.216069,16.346624,2025-06-26 09:00:00
76,Berlin,52.541051,13.363503,2025-06-26 09:00:00
77,London,51.515809,-0.143102,2025-06-26 09:00:00
78,Dublin,53.345623,-6.263454,2025-06-26 09:00:00
79,Belfast,54.604409,-5.933219,2025-06-26 09:00:00
80,Edinburgh,55.961359,-3.203278,2025-06-26 09:00:00
81,Cardiff,51.488329,-3.181262,2025-06-26 09:00:00
82,Brussels,50.872572,4.337084,2025-06-26 09:00:00
83,Bern,46.957572,7.419276,2025-06-26 09:00:00
84,Prague,50.085905,14.420254,2025-06-26 09:00:00
85,Bratislava,48.149815,17.106164,2025-06-26 09:00:00
86,Ljubljana,46.056947,14.491805,2025-06-26 09:00:00
87,Yerevan,40.189968,44.504648,2025-06-26 09:00:00
88,Baku,40.375437,49.832436,2025-06-26 09:00:00
89,Tbilisi,41.708837,44.790851,2025-06-26 09:00:00
90,Budapest,47.504919,19.032534,2025-06-26 09:00:00
91,Bucharest,47.504919,19.032534,2025-06-26 09:00:00
92,Warsaw,52.244743,20.980920,2025-06-26 09:00:00
93,Copenhagen,55.679387,12.576443,2025-06-26 09:00:00
94,Stockholm,59.334317,18.063845,2025-06-26 09:00:00
95,Helsinki,60.170228,24.949242,2025-06-26 09:00:00
96,Oslo,59.916958,10.727128,2025-06-26 09:00:00
97,Tallin,59.446613,24.734589,2025-06-26 09:00:00
98,Riga,56.948737,24.096135,2025-06-26 09:00:00
99,Vilnius,54.693775,25.262965,2025-06-26 09:00:00
100,Tirana,41.328274,19.803082,2025-06-26 09:00:00
101,Las Palmas,28.146240,-15.477006,2025-06-26 09:00:00
102,Capetown,-33.850570,18.361057,2025-06-26 09:00:00
103,Cape Agulhas,-34.828719,20.002542,2025-06-26 09:00:00
104,Antananarivo,-18.903319,47.487769,2025-06-26 09:00:00
105,Luanda,-8.786183,13.165362,2025-06-26 09:00:00
106,Gaborone,-24.652652,25.906923,2025-06-26 09:00:00
107,Saint Helena,-15.987508,-5.746086,2025-06-26 09:00:00
108,Maseru,-29.316488,27.493672,2025-06-26 09:00:00
109,Moroni,-11.694591,43.255062,2025-06-26 09:00:00
110,Maputo,-25.969286,32.573175,2025-06-26 09:00:00
111,Windhoek,-22.567379,17.087409,2025-06-26 09:00:00
112,Volchansky municipal district,60.000000,60.000000,2025-06-26 09:00:00
113,Taldyapan rural district,50.000000,50.000000,2025-06-26 09:00:00
114,Novokalitvenskoye rural settlement,50.000000,40.000000,2025-06-26 09:00:00
115,Northeastern Province Kenya,0.000000,40.000000,2025-06-26 09:00:00
116,Kikorongo Uganda,0.000000,30.000000,2025-06-26 09:00:00
117,Atlantic Ocean,0.000000,0.000000,2025-06-26 09:00:00
118,Estuariy Gabon,0.000000,10.000000,2025-06-26 09:00:00
119,The English Channel,50.000000,0.000000,2025-06-26 09:00:00
120,North Sea,55.000000,0.000000,2025-06-26 09:00:00"""

class DataValidator:
    """Advanced data validation and cleaning for geodata"""
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """Validate if coordinates are within valid ranges"""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def validate_timestamp(timestamp_str: str) -> bool:
        """Validate timestamp format"""
        try:
            pd.to_datetime(timestamp_str)
            return True
        except:
            return False
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the dataframe"""
        logger.info("Starting data validation and cleaning...")
        
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates()
        logger.info(f"Removed {initial_count - len(df)} duplicate rows")
        
        # Clean timestamp column - remove leading/trailing whitespace
        if 'timestamp' in df.columns:
            df['timestamp'] = df['timestamp'].astype(str).str.strip()
        
        # Validate coordinates
        valid_coords = df.apply(
            lambda row: DataValidator.validate_coordinates(row['latitude'], row['longitude']), 
            axis=1
        )
        df = df[valid_coords]
        logger.info(f"Removed {len(valid_coords) - valid_coords.sum()} rows with invalid coordinates")
        
        # Validate timestamps
        valid_timestamps = df['timestamp'].apply(DataValidator.validate_timestamp)
        df = df[valid_timestamps]
        logger.info(f"Removed {len(valid_timestamps) - valid_timestamps.sum()} rows with invalid timestamps")
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Add derived columns
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['month'] = df['timestamp'].dt.month
        df['year'] = df['timestamp'].dt.year
        
        # Calculate time-based features
        df['time_since_midnight'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60
        
        logger.info(f"Data cleaning completed. Final dataset: {len(df)} rows")
        return df

class DataEnhancer:
    """Enhance geodata with additional information"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="geodata_analyzer")
        self.cache = {}
        self.cache_timestamps = {}
    
    def get_location_info(self, lat: float, lon: float) -> Dict:
        """Get additional location information using reverse geocoding"""
        cache_key = f"{lat:.6f}_{lon:.6f}"
        
        # Check cache
        if cache_key in self.cache:
            if time.time() - self.cache_timestamps[cache_key] < CONFIG['cache_ttl']:
                return self.cache[cache_key]
        
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}", timeout=CONFIG['geocoding_timeout'])
            if location:
                info = {
                    'country': location.raw.get('address', {}).get('country', 'Unknown'),
                    'state': location.raw.get('address', {}).get('state', 'Unknown'),
                    'city': location.raw.get('address', {}).get('city', 'Unknown'),
                    'postcode': location.raw.get('address', {}).get('postcode', 'Unknown'),
                    'address': location.address
                }
            else:
                info = {'country': 'Unknown', 'state': 'Unknown', 'city': 'Unknown', 
                       'postcode': 'Unknown', 'address': 'Unknown'}
            
            # Cache the result
            self.cache[cache_key] = info
            self.cache_timestamps[cache_key] = time.time()
            
            return info
        except Exception as e:
            logger.warning(f"Failed to get location info for {lat}, {lon}: {e}")
            return {'country': 'Unknown', 'state': 'Unknown', 'city': 'Unknown', 
                   'postcode': 'Unknown', 'address': 'Unknown'}
    
    def enhance_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhance dataframe with additional location information"""
        logger.info("Enhancing data with location information...")
        
        # Add location info for a sample of points to avoid rate limiting
        sample_size = min(50, len(df))
        sample_indices = np.random.choice(df.index, sample_size, replace=False)
        
        enhanced_df = df.copy()
        enhanced_df['country'] = 'Unknown'
        enhanced_df['state'] = 'Unknown'
        enhanced_df['city'] = 'Unknown'
        enhanced_df['postcode'] = 'Unknown'
        enhanced_df['full_address'] = 'Unknown'
        
        for idx in sample_indices:
            row = df.loc[idx]
            info = self.get_location_info(row['latitude'], row['longitude'])
            enhanced_df.loc[idx, 'country'] = info['country']
            enhanced_df.loc[idx, 'state'] = info['state']
            enhanced_df.loc[idx, 'city'] = info['city']
            enhanced_df.loc[idx, 'postcode'] = info['postcode']
            enhanced_df.loc[idx, 'full_address'] = info['address']
        
        logger.info("Data enhancement completed")
        return enhanced_df

def ensure_csv_exists(csv_path):
    """Ensure CSV file exists, create if missing"""
    if not os.path.exists(csv_path):
        with open(csv_path, "w", encoding='utf-8') as f:
            f.write(csv_content)
        logger.info(f"{csv_path} создан автоматически.")

def load_data(csv_path):
    """Load and preprocess data"""
    logger.info(f"Loading data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Clean and validate data
    df = DataValidator.clean_dataframe(df)
    
    # Enhance with additional information
    enhancer = DataEnhancer()
    df = enhancer.enhance_dataframe(df)
    
    return df

class AdvancedAnalyzer:
    """Advanced geodata analysis including clustering and anomaly detection"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.cluster_models = {}
        self.analysis_results = {}
    
    def perform_clustering(self, df: pd.DataFrame, method: str = 'kmeans', n_clusters: int = None) -> Dict:
        """Perform clustering analysis on geodata"""
        logger.info(f"Performing {method} clustering...")
        
        if len(df) < CONFIG['min_cluster_size']:
            logger.warning("Insufficient data for clustering")
            return {}
        
        # Prepare coordinates for clustering
        coords = df[['latitude', 'longitude']].values
        coords_scaled = self.scaler.fit_transform(coords)
        
        if method == 'kmeans':
            if n_clusters is None:
                # Find optimal number of clusters
                n_clusters = self._find_optimal_clusters(coords_scaled)
            
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = model.fit_predict(coords_scaled)
            
        elif method == 'dbscan':
            model = DBSCAN(eps=CONFIG['eps_threshold'], min_samples=CONFIG['min_cluster_size'])
            labels = model.fit_predict(coords_scaled)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        # Add cluster labels to dataframe
        df_clustered = df.copy()
        df_clustered['cluster'] = labels
        
        # Calculate cluster statistics
        cluster_stats = self._calculate_cluster_statistics(df_clustered)
        
        # Store results
        self.cluster_models[method] = model
        self.analysis_results[f'{method}_clustering'] = {
            'model': model,
            'labels': labels,
            'n_clusters': n_clusters,
            'cluster_stats': cluster_stats,
            'dataframe': df_clustered
        }
        
        logger.info(f"Clustering completed: {n_clusters} clusters found")
        return self.analysis_results[f'{method}_clustering']
    
    def _find_optimal_clusters(self, coords_scaled: np.ndarray) -> int:
        """Find optimal number of clusters using silhouette analysis"""
        max_clusters = min(CONFIG['max_clusters'], len(coords_scaled) // 2)
        if max_clusters < 2:
            return 2
        
        silhouette_scores = []
        for n in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            labels = kmeans.fit_predict(coords_scaled)
            if len(set(labels)) > 1:
                score = silhouette_score(coords_scaled, labels)
                silhouette_scores.append(score)
            else:
                silhouette_scores.append(0)
        
        optimal_clusters = np.argmax(silhouette_scores) + 2
        logger.info(f"Optimal number of clusters: {optimal_clusters}")
        return optimal_clusters
    
    def _calculate_cluster_statistics(self, df_clustered: pd.DataFrame) -> Dict:
        """Calculate comprehensive statistics for each cluster"""
        cluster_stats = {}
        
        for cluster_id in df_clustered['cluster'].unique():
            if cluster_id == -1:  # Noise points in DBSCAN
                continue
                
            cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
            
            stats = {
                'size': len(cluster_data),
                'center_lat': cluster_data['latitude'].mean(),
                'center_lon': cluster_data['longitude'].mean(),
                'radius_km': self._calculate_cluster_radius(cluster_data),
                'density': len(cluster_data) / self._calculate_cluster_area(cluster_data),
                'time_span': (cluster_data['timestamp'].max() - cluster_data['timestamp'].min()).total_seconds() / 3600,
                'countries': cluster_data['country'].value_counts().to_dict(),
                'cities': cluster_data['city'].value_counts().to_dict()
            }
            
            cluster_stats[cluster_id] = stats
        
        return cluster_stats
    
    def _calculate_cluster_radius(self, cluster_data: pd.DataFrame) -> float:
        """Calculate the radius of a cluster in kilometers"""
        center_lat = cluster_data['latitude'].mean()
        center_lon = cluster_data['longitude'].mean()
        
        max_distance = 0
        for _, row in cluster_data.iterrows():
            distance = geodesic((center_lat, center_lon), (row['latitude'], row['longitude'])).kilometers
            max_distance = max(max_distance, distance)
        
        return max_distance
    
    def _calculate_cluster_area(self, cluster_data: pd.DataFrame) -> float:
        """Calculate approximate area of a cluster in square kilometers"""
        if len(cluster_data) < 3:
            return 0.1  # Minimum area
        
        # Use convex hull approximation
        coords = cluster_data[['latitude', 'longitude']].values
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(coords)
            # Approximate area calculation
            area = 0.1  # Simplified calculation
        except:
            area = 0.1
        
        return area
    
    def detect_anomalies(self, df: pd.DataFrame) -> Dict:
        """Detect spatial and temporal anomalies in geodata"""
        logger.info("Detecting anomalies...")
        
        anomalies = {
            'spatial_outliers': [],
            'temporal_outliers': [],
            'coordinate_errors': [],
            'unusual_patterns': []
        }
        
        # Spatial outliers using distance-based approach
        coords = df[['latitude', 'longitude']].values
        distances = []
        
        for i, coord1 in enumerate(coords):
            min_distance = float('inf')
            for j, coord2 in enumerate(coords):
                if i != j:
                    distance = geodesic(coord1, coord2).kilometers
                    min_distance = min(min_distance, distance)
            distances.append(min_distance)
        
        # Detect spatial outliers
        distances_array = np.array(distances)
        mean_distance = np.mean(distances_array)
        std_distance = np.std(distances_array)
        
        spatial_outliers = distances_array > (mean_distance + CONFIG['anomaly_threshold'] * std_distance)
        anomaly_indices = np.where(spatial_outliers)[0]
        
        for idx in anomaly_indices:
            anomalies['spatial_outliers'].append({
                'index': idx,
                'coordinates': coords[idx],
                'name': df.iloc[idx]['name'],
                'distance_to_nearest': distances[idx],
                'anomaly_score': (distances[idx] - mean_distance) / std_distance
            })
        
        # Temporal anomalies
        timestamps = pd.to_datetime(df['timestamp'])
        time_diffs = timestamps.diff().dt.total_seconds() / 3600  # hours
        
        if len(time_diffs) > 1:
            mean_time_diff = time_diffs.mean()
            std_time_diff = time_diffs.std()
            
            temporal_outliers = np.abs(time_diffs - mean_time_diff) > (CONFIG['anomaly_threshold'] * std_time_diff)
            temporal_anomaly_indices = np.where(temporal_outliers)[0]
            
            for idx in temporal_anomaly_indices:
                anomalies['temporal_outliers'].append({
                    'index': idx,
                    'timestamp': timestamps.iloc[idx],
                    'name': df.iloc[idx]['name'],
                    'time_diff': time_diffs.iloc[idx],
                    'anomaly_score': abs(time_diffs.iloc[idx] - mean_time_diff) / std_time_diff
                })
        
        logger.info(f"Anomaly detection completed: {len(anomalies['spatial_outliers'])} spatial, {len(anomalies['temporal_outliers'])} temporal")
        return anomalies
    
    def generate_statistical_summary(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive statistical summary of geodata"""
        logger.info("Generating statistical summary...")
        
        summary = {
            'basic_stats': {
                'total_points': len(df),
                'unique_locations': df['name'].nunique(),
                'date_range': {
                    'start': df['timestamp'].min().isoformat(),
                    'end': df['timestamp'].max().isoformat(),
                    'duration_days': (df['timestamp'].max() - df['timestamp'].min()).days
                },
                'coordinate_bounds': {
                    'lat_min': df['latitude'].min(),
                    'lat_max': df['latitude'].max(),
                    'lon_min': df['longitude'].min(),
                    'lon_max': df['longitude'].max()
                }
            },
            'temporal_analysis': {
                'hourly_distribution': df['hour'].value_counts().to_dict(),
                'daily_distribution': df['day_of_week'].value_counts().to_dict(),
                'monthly_distribution': df['month'].value_counts().to_dict(),
                'yearly_distribution': df['year'].value_counts().to_dict()
            },
            'spatial_analysis': {
                'countries': df['country'].value_counts().to_dict(),
                'cities': df['city'].value_counts().to_dict(),
                'density_analysis': self._analyze_spatial_density(df)
            },
            'quality_metrics': {
                'completeness': self._calculate_data_completeness(df),
                'consistency': self._calculate_data_consistency(df)
            }
        }
        
        return summary
    
    def _analyze_spatial_density(self, df: pd.DataFrame) -> Dict:
        """Analyze spatial density patterns"""
        # Calculate point density in different regions
        density_analysis = {}
        
        # Grid-based density analysis
        lat_bins = pd.cut(df['latitude'], bins=10)
        lon_bins = pd.cut(df['longitude'], bins=10)
        
        density_grid = df.groupby([lat_bins, lon_bins]).size()
        density_analysis['grid_density'] = density_grid.to_dict()
        
        # Country-based density
        country_density = df.groupby('country').size().to_dict()
        density_analysis['country_density'] = country_density
        
        return density_analysis
    
    def _calculate_data_completeness(self, df: pd.DataFrame) -> Dict:
        """Calculate data completeness metrics"""
        total_cells = len(df) * len(df.columns)
        non_null_cells = df.count().sum()
        
        return {
            'overall_completeness': non_null_cells / total_cells,
            'column_completeness': (df.count() / len(df)).to_dict(),
            'row_completeness': (df.count(axis=1) / len(df.columns)).describe().to_dict()
        }
    
    def _calculate_data_consistency(self, df: pd.DataFrame) -> Dict:
        """Calculate data consistency metrics"""
        consistency_metrics = {}
        
        # Coordinate consistency
        lat_range = df['latitude'].max() - df['latitude'].min()
        lon_range = df['longitude'].max() - df['longitude'].min()
        
        consistency_metrics['coordinate_ranges'] = {
            'latitude_range': lat_range,
            'longitude_range': lon_range,
            'aspect_ratio': lat_range / lon_range if lon_range != 0 else 0
        }
        
        # Temporal consistency
        time_diffs = pd.to_datetime(df['timestamp']).diff().dt.total_seconds()
        consistency_metrics['temporal_consistency'] = {
            'mean_time_diff_hours': time_diffs.mean() / 3600,
            'std_time_diff_hours': time_diffs.std() / 3600,
            'min_time_diff_hours': time_diffs.min() / 3600,
            'max_time_diff_hours': time_diffs.max() / 3600
        }
        
        return consistency_metrics

def save_to_db(df, db_path):
    """Save dataframe to SQLite database with enhanced schema"""
    conn = sqlite3.connect(db_path)
    
    # Create enhanced schema
    df.to_sql('geolocations', conn, if_exists='replace', index=False)
    
    # Create additional tables for analysis
    if 'cluster' in df.columns:
        cluster_df = df[['id', 'cluster']].copy()
        cluster_df.to_sql('clusters', conn, if_exists='replace', index=False)
    
    # Create indexes for better performance
    conn.execute('CREATE INDEX IF NOT EXISTS idx_lat_lon ON geolocations(latitude, longitude)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON geolocations(timestamp)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_country ON geolocations(country)')
    
    conn.close()
    logger.info(f"Data saved to database: {db_path}")

def query_db(db_path, query):
    """Execute SQL query on database with error handling"""
    try:
        conn = sqlite3.connect(db_path)
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return pd.DataFrame()

class AdvancedVisualizer:
    """Advanced visualization capabilities for geodata"""
    
    def __init__(self):
        self.plotly_config = {'displayModeBar': True, 'scrollZoom': True}
        self.color_palette = px.colors.qualitative.Set3
    
    def create_enhanced_map(self, df: pd.DataFrame, output_html: str = OUTPUT_MAP, 
                           show_clusters: bool = False, show_heatmap: bool = False) -> None:
        """Create an enhanced interactive map with multiple visualization options"""
        if df.empty:
            logger.warning("Нет данных для отображения карты.")
            return
        
        logger.info("Creating enhanced map...")
        
        avg_lat = df['latitude'].mean()
        avg_lon = df['longitude'].mean()
        
        # Create base map
        geo_map = folium.Map(
            location=[avg_lat, avg_lon], 
            zoom_start=6,
            tiles=CONFIG['map_tile']
        )
        
        # Add different visualization layers
        if show_clusters and 'cluster' in df.columns:
            self._add_cluster_layer(geo_map, df)
        elif show_heatmap:
            self._add_heatmap_layer(geo_map, df)
        else:
            self._add_marker_layer(geo_map, df)
        
        # Add additional controls
        folium.LayerControl().add_to(geo_map)
        
        # Save map
        geo_map.save(output_html)
        logger.info(f"Enhanced map saved to {output_html}")
    
    def _add_marker_layer(self, geo_map: folium.Map, df: pd.DataFrame) -> None:
        """Add interactive markers to the map"""
        for _, row in df.iterrows():
            # Create popup content
            popup_content = f"""
            <div style="width: 200px;">
                <h4>{row.get('name', 'Location')}</h4>
                <p><strong>Coordinates:</strong> {row['latitude']:.6f}, {row['longitude']:.6f}</p>
                <p><strong>Timestamp:</strong> {row['timestamp']}</p>
                <p><strong>Country:</strong> {row.get('country', 'Unknown')}</p>
                <p><strong>City:</strong> {row.get('city', 'Unknown')}</p>
            </div>
            """
            
            # Choose marker color based on country or other criteria
            color = self._get_marker_color(row)
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row.get('name', 'Location'),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(geo_map)
    
    def _add_cluster_layer(self, geo_map: folium.Map, df: pd.DataFrame) -> None:
        """Add cluster visualization to the map"""
        from folium.plugins import MarkerCluster
        
        marker_cluster = MarkerCluster().add_to(geo_map)
        
        for _, row in df.iterrows():
            cluster_id = row.get('cluster', 0)
            color = self._get_cluster_color(cluster_id)
            
            popup_content = f"""
            <div style="width: 200px;">
                <h4>{row.get('name', 'Location')}</h4>
                <p><strong>Cluster:</strong> {cluster_id}</p>
                <p><strong>Coordinates:</strong> {row['latitude']:.6f}, {row['longitude']:.6f}</p>
                <p><strong>Country:</strong> {row.get('country', 'Unknown')}</p>
            </div>
            """
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(marker_cluster)
    
    def _add_heatmap_layer(self, geo_map: folium.Map, df: pd.DataFrame) -> None:
        """Add heatmap visualization to the map"""
        from folium.plugins import HeatMap
        
        # Prepare heatmap data
        heat_data = df[['latitude', 'longitude']].values.tolist()
        
        HeatMap(
            heat_data,
            radius=15,
            blur=10,
            max_zoom=13
        ).add_to(geo_map)
    
    def _get_marker_color(self, row: pd.Series) -> str:
        """Get marker color based on data attributes"""
        if 'country' in row and row['country'] != 'Unknown':
            # Use hash of country name for consistent colors
            country_hash = hash(row['country']) % len(self.color_palette)
            return self.color_palette[country_hash]
        return 'blue'
    
    def _get_cluster_color(self, cluster_id: int) -> str:
        """Get color for cluster markers"""
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 
                 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 
                 'lightgreen', 'gray', 'black', 'lightgray']
        return colors[cluster_id % len(colors)]
    
    def create_cluster_analysis_plot(self, df: pd.DataFrame, output_image: str = OUTPUT_CLUSTER_PLOT) -> None:
        """Create comprehensive clustering analysis visualization"""
        if df.empty or 'cluster' not in df.columns:
            logger.warning("No clustering data available for visualization")
            return
        
        logger.info("Creating cluster analysis plot...")
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Clustering Analysis Results', fontsize=16)
        
        # Plot 1: Scatter plot with clusters
        scatter = axes[0, 0].scatter(df['longitude'], df['latitude'], 
                                    c=df['cluster'], cmap='tab10', alpha=0.7)
        axes[0, 0].set_xlabel('Longitude')
        axes[0, 0].set_ylabel('Latitude')
        axes[0, 0].set_title('Geographic Distribution of Clusters')
        axes[0, 0].grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=axes[0, 0], label='Cluster ID')
        
        # Plot 2: Cluster sizes
        cluster_sizes = df['cluster'].value_counts().sort_index()
        axes[0, 1].bar(range(len(cluster_sizes)), cluster_sizes.values, 
                       color=plt.cm.tab10(range(len(cluster_sizes))))
        axes[0, 1].set_xlabel('Cluster ID')
        axes[0, 1].set_ylabel('Number of Points')
        axes[0, 1].set_title('Cluster Sizes')
        axes[0, 1].set_xticks(range(len(cluster_sizes)))
        axes[0, 1].set_xticklabels(cluster_sizes.index)
        
        # Plot 3: Temporal distribution by cluster
        if 'timestamp' in df.columns:
            df_temp = df.copy()
            df_temp['hour'] = pd.to_datetime(df_temp['timestamp']).dt.hour
            cluster_hour_dist = df_temp.groupby(['cluster', 'hour']).size().unstack(fill_value=0)
            cluster_hour_dist.plot(kind='bar', ax=axes[1, 0], stacked=True, alpha=0.8)
            axes[1, 0].set_xlabel('Cluster ID')
            axes[1, 0].set_ylabel('Number of Points')
            axes[1, 0].set_title('Temporal Distribution by Cluster')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Country distribution by cluster
        if 'country' in df.columns:
            cluster_country_dist = df.groupby(['cluster', 'country']).size().unstack(fill_value=0)
            cluster_country_dist.plot(kind='bar', ax=axes[1, 1], stacked=True, alpha=0.8)
            axes[1, 1].set_xlabel('Cluster ID')
            axes[1, 1].set_ylabel('Number of Points')
            axes[1, 1].set_title('Geographic Distribution by Cluster')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_image, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Cluster analysis plot saved to {output_image}")
    
    def create_interactive_heatmap(self, df: pd.DataFrame, output_html: str = OUTPUT_HEATMAP) -> None:
        """Create interactive heatmap using Plotly"""
        if df.empty:
            logger.warning("No data available for heatmap")
            return
        
        logger.info("Creating interactive heatmap...")
        
        # Create 2D histogram
        fig = go.Figure()
        
        fig.add_trace(go.Histogram2d(
            x=df['longitude'],
            y=df['latitude'],
            nbinsx=50,
            nbinsy=50,
            colorscale='Viridis',
            showscale=True
        ))
        
        fig.update_layout(
            title='Geodata Density Heatmap',
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            width=1000,
            height=700
        )
        
        fig.write_html(output_html, config=self.plotly_config)
        logger.info(f"Interactive heatmap saved to {output_html}")
    
    def create_timeline_visualization(self, df: pd.DataFrame, output_html: str = OUTPUT_TIMELINE) -> None:
        """Create interactive timeline visualization"""
        if df.empty or 'timestamp' not in df.columns:
            logger.warning("No timestamp data available for timeline")
            return
        
        logger.info("Creating timeline visualization...")
        
        # Prepare timeline data
        df_timeline = df.copy()
        df_timeline['timestamp'] = pd.to_datetime(df_timeline['timestamp'])
        df_timeline = df_timeline.sort_values('timestamp')
        
        # Create timeline plot
        fig = go.Figure()
        
        # Add scatter plot for timeline
        fig.add_trace(go.Scatter(
            x=df_timeline['timestamp'],
            y=df_timeline['latitude'],
            mode='markers',
            marker=dict(
                size=8,
                color=df_timeline['longitude'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Longitude')
            ),
            text=df_timeline['name'],
            hovertemplate='<b>%{text}</b><br>' +
                         'Time: %{x}<br>' +
                         'Latitude: %{y:.4f}<br>' +
                         'Longitude: %{marker.color:.4f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Geodata Timeline',
            xaxis_title='Timestamp',
            yaxis_title='Latitude',
            width=1200,
            height=600,
            hovermode='closest'
        )
        
        fig.write_html(output_html, config=self.plotly_config)
        logger.info(f"Timeline visualization saved to {output_html}")
    
    def create_3d_map(self, df: pd.DataFrame, output_html: str = OUTPUT_3D_MAP) -> None:
        """Create 3D visualization of geodata"""
        if df.empty:
            logger.warning("No data available for 3D map")
            return
        
        logger.info("Creating 3D map...")
        
        # Create 3D scatter plot
        fig = go.Figure()
        
        # Add 3D scatter
        fig.add_trace(go.Scatter3d(
            x=df['longitude'],
            y=df['latitude'],
            z=df['timestamp'].apply(lambda x: pd.to_datetime(x).timestamp()),
            mode='markers',
            marker=dict(
                size=5,
                color=df['timestamp'].apply(lambda x: pd.to_datetime(x).timestamp()),
                colorscale='Viridis',
                opacity=0.8
            ),
            text=df['name'],
            hovertemplate='<b>%{text}</b><br>' +
                         'Longitude: %{x:.4f}<br>' +
                         'Latitude: %{y:.4f}<br>' +
                         'Timestamp: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title='3D Geodata Visualization',
            scene=dict(
                xaxis_title='Longitude',
                yaxis_title='Latitude',
                zaxis_title='Timestamp (Unix)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=1000,
            height=700
        )
        
        fig.write_html(output_html, config=self.plotly_config)
        logger.info(f"3D map saved to {output_html}")
    
    def create_network_graph(self, df: pd.DataFrame, output_html: str = OUTPUT_NETWORK_GRAPH) -> None:
        """Create network graph showing connections between nearby points"""
        if df.empty:
            logger.warning("No data available for network graph")
            return
        
        logger.info("Creating network graph...")
        
        # Calculate distances between points and create edges
        edges = []
        nodes = []
        
        for i, row1 in df.iterrows():
            nodes.append({
                'id': i,
                'name': row1['name'],
                'lat': row1['latitude'],
                'lon': row1['longitude']
            })
            
            for j, row2 in df.iterrows():
                if i != j:
                    distance = geodesic(
                        (row1['latitude'], row1['longitude']),
                        (row2['latitude'], row2['longitude'])
                    ).kilometers
                    
                    # Only connect points within reasonable distance
                    if distance < 100:  # 100 km threshold
                        edges.append({
                            'source': i,
                            'target': j,
                            'distance': distance
                        })
        
        # Create network visualization
        fig = go.Figure()
        
        # Add edges
        for edge in edges[:100]:  # Limit edges for performance
            fig.add_trace(go.Scatter(
                x=[df.iloc[edge['source']]['longitude'], df.iloc[edge['target']]['longitude']],
                y=[df.iloc[edge['source']]['latitude'], df.iloc[edge['target']]['latitude']],
                mode='lines',
                line=dict(width=0.5, color='gray', opacity=0.3),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=[node['lon'] for node in nodes],
            y=[node['lat'] for node in nodes],
            mode='markers',
            marker=dict(
                size=8,
                color='red',
                opacity=0.8
            ),
            text=[node['name'] for node in nodes],
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        
        fig.update_layout(
            title='Geodata Network Graph',
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            width=1000,
            height=700,
            showlegend=False
        )
        
        fig.write_html(output_html, config=self.plotly_config)
        logger.info(f"Network graph saved to {output_html}")

def create_map(df, output_html=OUTPUT_MAP):
    """Legacy map creation function - now uses AdvancedVisualizer"""
    visualizer = AdvancedVisualizer()
    visualizer.create_enhanced_map(df, output_html)

def create_time_distribution_plot(df, output_image=OUTPUT_PLOT):
    """Enhanced time distribution plot with multiple visualizations"""
    if df.empty:
        logger.warning("Нет данных для построения графика.")
        return

    # Set style
    plt.style.use(CONFIG['plot_style'])
    
    # Create comprehensive time analysis
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Comprehensive Temporal Analysis', fontsize=16)
    
    # Plot 1: Daily distribution
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_counts = df['date'].value_counts().sort_index()
    
    axes[0, 0].plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, markersize=6)
    axes[0, 0].set_xlabel('Дата')
    axes[0, 0].set_ylabel('Количество точек')
    axes[0, 0].set_title('Распределение точек по датам')
    axes[0, 0].tick_params(axis='x', rotation=45)
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Hourly distribution
    hourly_counts = df['hour'].value_counts().sort_index()
    axes[0, 1].bar(hourly_counts.index, hourly_counts.values, alpha=0.7, color='skyblue')
    axes[0, 1].set_xlabel('Час дня')
    axes[0, 1].set_ylabel('Количество точек')
    axes[0, 1].set_title('Распределение по часам')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Weekly distribution
    weekly_counts = df['day_of_week'].value_counts()
    weekly_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_counts = weekly_counts.reindex(weekly_order, fill_value=0)
    
    axes[1, 0].bar(range(len(weekly_counts)), weekly_counts.values, alpha=0.7, color='lightcoral')
    axes[1, 0].set_xlabel('День недели')
    axes[1, 0].set_ylabel('Количество точек')
    axes[1, 0].set_title('Распределение по дням недели')
    axes[1, 0].set_xticks(range(len(weekly_counts)))
    axes[1, 0].set_xticklabels(weekly_counts.index, rotation=45)
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Monthly distribution
    monthly_counts = df['month'].value_counts().sort_index()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_counts = monthly_counts.reindex(range(1, 13), fill_value=0)
    
    axes[1, 1].bar(monthly_counts.index, monthly_counts.values, alpha=0.7, color='lightgreen')
    axes[1, 1].set_xlabel('Месяц')
    axes[1, 1].set_ylabel('Количество точек')
    axes[1, 1].set_title('Распределение по месяцам')
    axes[1, 1].set_xticks(range(1, 13))
    axes[1, 1].set_xticklabels(month_names)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Enhanced time distribution plot saved to {output_image}")

def create_coordinate_scatter(df, output_image=OUTPUT_PLOT):
    """Enhanced coordinate scatter plot with multiple analysis views"""
    if df.empty:
        logger.warning("Нет данных для построения графика.")
        return
    
    # Set style
    plt.style.use(CONFIG['plot_style'])
    
    # Create comprehensive coordinate analysis
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Comprehensive Spatial Analysis', fontsize=16)
    
    # Plot 1: Basic scatter plot
    scatter = axes[0, 0].scatter(df['longitude'], df['latitude'], c='blue', alpha=0.6, s=50)
    axes[0, 0].set_xlabel('Долгота')
    axes[0, 0].set_ylabel('Широта')
    axes[0, 0].set_title('Распределение точек по координатам')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Density plot
    if len(df) > 100:  # Only for larger datasets
        try:
            from scipy.stats import gaussian_kde
            coords = df[['longitude', 'latitude']].values.T
            kde = gaussian_kde(coords)
            
            x_range = np.linspace(df['longitude'].min(), df['longitude'].max(), 100)
            y_range = np.linspace(df['latitude'].min(), df['latitude'].max(), 100)
            X, Y = np.meshgrid(x_range, y_range)
            positions = np.vstack([X.ravel(), Y.ravel()])
            Z = np.reshape(kde(positions).T, X.shape)
            
            im = axes[0, 1].contourf(X, Y, Z, levels=20, cmap='viridis')
            axes[0, 1].set_xlabel('Долгота')
            axes[0, 1].set_ylabel('Широта')
            axes[0, 1].set_title('Плотность точек (KDE)')
            plt.colorbar(im, ax=axes[0, 1])
        except:
            # Fallback to simple histogram
            axes[0, 1].hist2d(df['longitude'], df['latitude'], bins=30, cmap='viridis')
            axes[0, 1].set_xlabel('Долгота')
            axes[0, 1].set_ylabel('Широта')
            axes[0, 1].set_title('Гистограмма плотности')
    
    # Plot 3: Coordinate distributions
    axes[1, 0].hist(df['latitude'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    axes[1, 0].set_xlabel('Широта')
    axes[1, 0].set_ylabel('Частота')
    axes[1, 0].set_title('Распределение широт')
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].hist(df['longitude'], bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
    axes[1, 1].set_xlabel('Долгота')
    axes[1, 1].set_ylabel('Частота')
    axes[1, 1].set_title('Распределение долгот')
    axes[1, 0].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Enhanced coordinate scatter plot saved to {output_image}")

def create_advanced_visualizations(df: pd.DataFrame) -> None:
    """Create all advanced visualizations for the dataset"""
    logger.info("Creating advanced visualizations...")
    
    visualizer = AdvancedVisualizer()
    
    # Create all visualization types
    try:
        visualizer.create_interactive_heatmap(df)
        visualizer.create_timeline_visualization(df)
        visualizer.create_3d_map(df)
        visualizer.create_network_graph(df)
        logger.info("All advanced visualizations created successfully")
    except Exception as e:
        logger.error(f"Error creating advanced visualizations: {e}")

def generate_analysis_report(df: pd.DataFrame, analyzer: AdvancedAnalyzer, 
                           output_html: str = OUTPUT_STATS_REPORT) -> None:
    """Generate comprehensive HTML analysis report"""
    logger.info("Generating analysis report...")
    
    # Perform analysis
    summary = analyzer.generate_statistical_summary(df)
    anomalies = analyzer.detect_anomalies(df)
    
    # Create HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Geodata Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; border-radius: 3px; }}
            .anomaly {{ color: red; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Geodata Analysis Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="section">
            <h2>Basic Statistics</h2>
            <div class="metric">Total Points: {summary['basic_stats']['total_points']}</div>
            <div class="metric">Unique Locations: {summary['basic_stats']['unique_locations']}</div>
            <div class="metric">Date Range: {summary['basic_stats']['date_range']['start']} to {summary['basic_stats']['date_range']['end']}</div>
            <div class="metric">Duration: {summary['basic_stats']['date_range']['duration_days']} days</div>
        </div>
        
        <div class="section">
            <h2>Coordinate Bounds</h2>
            <div class="metric">Latitude: {summary['basic_stats']['coordinate_bounds']['lat_min']:.4f} to {summary['basic_stats']['coordinate_bounds']['lat_max']:.4f}</div>
            <div class="metric">Longitude: {summary['basic_stats']['coordinate_bounds']['lon_min']:.4f} to {summary['basic_stats']['coordinate_bounds']['lon_max']:.4f}</div>
        </div>
        
        <div class="section">
            <h2>Data Quality Metrics</h2>
            <div class="metric">Overall Completeness: {summary['quality_metrics']['completeness']['overall_completeness']:.2%}</div>
        </div>
        
        <div class="section">
            <h2>Anomaly Detection</h2>
            <div class="metric">Spatial Outliers: {len(anomalies['spatial_outliers'])}</div>
            <div class="metric">Spatial Outliers: {len(anomalies['temporal_outliers'])}</div>
        </div>
        
        <div class="section">
            <h2>Top Countries</h2>
            <table>
                <tr><th>Country</th><th>Count</th></tr>
                {''.join([f"<tr><td>{country}</td><td>{count}</td></tr>" for country, count in list(summary['spatial_analysis']['countries'].items())[:10]])}
            </table>
        </div>
        
        <div class="section">
            <h2>Top Cities</h2>
            <table>
                <tr><th>City</th><th>Count</th></tr>
                {''.join([f"<tr><td>{city}</td><td>{count}</td></tr>" for country, count in list(summary['spatial_analysis']['cities'].items())[:10]])}
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Analysis report saved to {output_html}")

def create_anomaly_report(df: pd.DataFrame, analyzer: AdvancedAnalyzer, 
                         output_html: str = OUTPUT_ANOMALY_REPORT) -> None:
    """Generate detailed anomaly detection report"""
    logger.info("Generating anomaly report...")
    
    anomalies = analyzer.detect_anomalies(df)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Anomaly Detection Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .anomaly {{ color: red; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </div>
    </head>
    <body>
        <h1>Anomaly Detection Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="section">
            <h2>Spatial Outliers ({len(anomalies['spatial_outliers'])})</h2>
            <table>
                <tr><th>Location</th><th>Coordinates</th><th>Distance to Nearest (km)</th><th>Anomaly Score</th></tr>
                {''.join([f"<tr><td>{anomaly['name']}</td><td>{anomaly['coordinates'][0]:.4f}, {anomaly['coordinates'][1]:.4f}</td><td>{anomaly['distance_to_nearest']:.2f}</td><td class='anomaly'>{anomaly['anomaly_score']:.2f}</td></tr>" for anomaly in anomalies['spatial_outliers'][:20]])}
            </table>
        </div>
        
        <div class="section">
            <h2>Temporal Outliers ({len(anomalies['temporal_outliers'])})</h2>
            <table>
                <tr><th>Location</th><th>Timestamp</th><th>Time Difference (hours)</th><th>Anomaly Score</th></tr>
                {''.join([f"<tr><td>{anomaly['name']}</td><td>{anomaly['timestamp']}</td><td>{anomaly['time_diff']:.2f}</td><td class='anomaly'>{anomaly['anomaly_score']:.2f}</td></tr>" for anomaly in anomalies['temporal_outliers'][:20]])}
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Anomaly report saved to {output_html}")

def main():
    """Enhanced main function with advanced geodata analysis capabilities"""
    parser = argparse.ArgumentParser(description="Advanced Geodata Analysis Tool")
    
    # Basic arguments
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV_FILE,
                        help="Path to CSV file")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_FILE,
                        help="Path to SQLite database")
    parser.add_argument("--filter", type=str,
                        help="SQL condition for data filtering (e.g., 'latitude > 30')")
    
    # Visualization options
    parser.add_argument("--map", action='store_true',
                        help="Create map visualization")
    parser.add_argument("--map-type", choices=['markers', 'clusters', 'heatmap'], default='markers',
                        help="Type of map visualization")
    parser.add_argument("--plot", choices=['time', 'coordinates'], default=None,
                        help="Create plots: 'time' for temporal analysis, 'coordinates' for spatial analysis")
    
    # Advanced analysis options
    parser.add_argument("--analyze", action='store_true',
                        help="Perform comprehensive data analysis")
    parser.add_argument("--cluster", choices=['kmeans', 'dbscan'], default=None,
                        help="Perform clustering analysis")
    parser.add_argument("--clusters", type=int, default=None,
                        help="Number of clusters for K-means")
    parser.add_argument("--detect-anomalies", action='store_true',
                        help="Detect spatial and temporal anomalies")
    parser.add_argument("--generate-reports", action='store_true',
                        help="Generate HTML analysis reports")
    parser.add_argument("--advanced-viz", action='store_true',
                        help="Create advanced interactive visualizations")
    
    # Output options
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Output directory for generated files")
    parser.add_argument("--verbose", action='store_true',
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting advanced geodata analysis...")
    
    # Ensure CSV exists and load data
    ensure_csv_exists(args.csv)
    data = load_data(args.csv)
    
    if data.empty:
        logger.error("No data loaded. Exiting.")
        return
    
    logger.info(f"Loaded {len(data)} data points")
    
    # Save to database
    save_to_db(data.copy(), args.db)
    
    # Initialize analyzer
    analyzer = AdvancedAnalyzer()
    
    # Apply filtering if specified
    if args.filter:
        query_str = f"SELECT * FROM geolocations WHERE {args.filter}"
        logger.info(f"Applying filter: {query_str}")
        filtered_df = query_db(args.db, query_str)
        
        if filtered_df.empty:
            logger.warning("Filter returned no results")
            return
        
        data = filtered_df
        logger.info(f"Filtered data: {len(data)} points")
    
    # Perform clustering if requested
    if args.cluster:
        logger.info(f"Performing {args.cluster} clustering...")
        clustering_result = analyzer.perform_clustering(data, args.cluster, args.clusters)
        
        if clustering_result:
            # Create cluster visualization
            visualizer = AdvancedVisualizer()
            visualizer.create_cluster_analysis_plot(data)
            
            # Update data with cluster labels
            data = clustering_result['dataframe']
    
    # Create map visualizations
    if args.map:
        logger.info("Creating map visualization...")
        visualizer = AdvancedVisualizer()
        
        if args.map_type == 'clusters' and 'cluster' in data.columns:
            visualizer.create_enhanced_map(data, OUTPUT_CLUSTER_MAP, show_clusters=True)
            logger.info(f"Cluster map saved to {OUTPUT_CLUSTER_MAP}")
        elif args.map_type == 'heatmap':
            visualizer.create_enhanced_map(data, OUTPUT_MAP, show_heatmap=True)
            logger.info(f"Heatmap saved to {OUTPUT_MAP}")
        else:
            visualizer.create_enhanced_map(data, OUTPUT_MAP)
            logger.info(f"Standard map saved to {OUTPUT_MAP}")
    
    # Create plots
    if args.plot == 'time':
        logger.info("Creating time distribution plot...")
        create_time_distribution_plot(data)
    elif args.plot == 'coordinates':
        logger.info("Creating coordinate scatter plot...")
        create_coordinate_scatter(data)
    
    # Perform comprehensive analysis
    if args.analyze:
        logger.info("Performing comprehensive analysis...")
        
        # Generate statistical summary
        summary = analyzer.generate_statistical_summary(data)
        logger.info(f"Analysis completed. Dataset contains {summary['basic_stats']['total_points']} points")
        
        # Generate reports if requested
        if args.generate_reports:
            generate_analysis_report(data, analyzer)
            create_anomaly_report(data, analyzer)
            logger.info("Analysis reports generated")
    
    # Detect anomalies
    if args.detect_anomalies:
        logger.info("Detecting anomalies...")
        anomalies = analyzer.detect_anomalies(data)
        logger.info(f"Anomaly detection completed: {len(anomalies['spatial_outliers'])} spatial, {len(anomalies['temporal_outliers'])} temporal")
    
    # Create advanced visualizations
    if args.advanced_viz:
        logger.info("Creating advanced visualizations...")
        create_advanced_visualizations(data)
    
    # Display summary
    logger.info("Analysis completed successfully!")
    logger.info(f"Total data points processed: {len(data)}")
    
    if 'cluster' in data.columns:
        n_clusters = data['cluster'].nunique()
        logger.info(f"Clustering: {n_clusters} clusters identified")
    
    if args.generate_reports:
        logger.info("Generated files:")
        logger.info(f"  - Analysis report: {OUTPUT_STATS_REPORT}")
        logger.info(f"  - Anomaly report: {OUTPUT_ANOMALY_REPORT}")
        logger.info(f"  - Interactive visualizations: {OUTPUT_HEATMAP}, {OUTPUT_TIMELINE}, {OUTPUT_3D_MAP}, {OUTPUT_NETWORK_GRAPH}")

if __name__ == "__main__":
    main()