import os
import pandas as pd
import geopandas as gpd
import coordtrans
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.strtree import STRtree
from pyproj import Proj, transform

MUSEUM_PATH = '/Users/HaoZheng/Desktop/prototype/museum.csv'
SHOPPING_PATH = '/Users/HaoZheng/Desktop/prototype/df_Weibo.csv'
TIME = 1
WALK_SPEED = 2000
DISTANCE = TIME * WALK_SPEED

start_pt_bd = [121.4444203,31.199584]

# Violent search the best route
def route(pt_gdf, score, distance, visited, best_score, lines):
    for i in range(len(pt_gdf)):
        #print('Index i :{}'.format(i))
        #print('score : {}, visited : {}, dist: {}'.format(score, visited, distance+visited[-1].distance(pt_gdf['geometry'][i])+visited[0].distance(pt_gdf['geometry'][i])))
        if pt_gdf['geometry'][i] not in visited and distance+visited[-1].distance(pt_gdf['geometry'][i])+visited[0].distance(pt_gdf['geometry'][i])<DISTANCE:
            #print('Input {}'.format(i))
            score += pt_gdf['score'][i]
            distance += visited[-1].distance(pt_gdf['geometry'][i])
            visited.append(pt_gdf['geometry'][i])
            best_score, lines = route(pt_gdf, score, distance, visited, best_score, lines)
            visited = visited[:-1]
            score -= pt_gdf['score'][i]
            #print('Output {}\n'.format(i))
        elif (score > best_score)and LineString([(p.x, p.y) for p in visited]).is_simple:
            best_score = score
            lines = visited
    return best_score, lines


# Build rtree for museum
museum_df = pd.read_csv(MUSEUM_PATH)
pt_list = []
id_list = []
for i in range(len(museum_df)):
    wgs84_pt = coordtrans.BD09toWGS84(museum_df['lng'][i], museum_df['lat'][i])
    mercator_pt = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), wgs84_pt[0], wgs84_pt[1])
    pt = Point(mercator_pt[0], mercator_pt[1])
    pt_list.append(pt)
    id_list.append(id(pt))
museum_gdf = gpd.GeoDataFrame({'id':id_list,'score':museum_df['rating'],'geometry':pt_list})
museum_rtree = STRtree(museum_gdf['geometry'])

# Build rtree for shopping
shopping_df = pd.read_csv(SHOPPING_PATH, delimiter='\t')
shopping_df = shopping_df[['name', 'latitude', 'longitude', 'scores']]
shopping_df.columns = ['name', 'lat', 'lng', 'score']
shopping_df["score"] = shopping_df["score"].str.split(',').str[0]
shopping_df["score"] = shopping_df["score"].replace(['-'], '20')
shopping_df["score"] = pd.to_numeric(shopping_df["score"])
pt_list = []
id_list = []
for i in range(len(shopping_df)):
    wgs84_pt = coordtrans.GCJ02toWGS84(shopping_df['lng'][i], shopping_df['lat'][i])
    mercator_pt = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), wgs84_pt[0], wgs84_pt[1])
    pt = Point(mercator_pt[0], mercator_pt[1])
    pt_list.append(pt)
    id_list.append(id(pt))
shopping_gdf = gpd.GeoDataFrame({'id':id_list,'score':shopping_df['score'],'geometry':pt_list})
shopping_rtree = STRtree(shopping_gdf['geometry'])

# Transform the coordinates of start point to web mercator
start_pt_wgs84 = coordtrans.BD09toWGS84(start_pt_bd[0], start_pt_bd[1])
start_pt_mercator = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), start_pt_wgs84[0], start_pt_wgs84[1])
start_pt = Point(start_pt_mercator[0], start_pt_mercator[1])

# Choose the poi in reachable boundary
museum_temp_pt = museum_rtree.query(start_pt.buffer(DISTANCE))
museum_temp_id = [id(pt) for pt in museum_temp_pt]
museum_gdf = museum_gdf[museum_gdf['id'].isin(museum_temp_id)].reset_index(drop=True)
shopping_temp_pt = shopping_rtree.query(start_pt.buffer(DISTANCE))
shopping_temp_id = [id(pt) for pt in shopping_temp_pt]
shopping_gdf = shopping_gdf[shopping_gdf['id'].isin(shopping_temp_id)].reset_index(drop=True)
print('RTree queried, {} museum and {} shopping poi found!'.format(len(museum_gdf), len(shopping_gdf)))

# Find the route for the museum, shopping, etc.
_, temp_lines = route(museum_gdf, 0, 0, [start_pt], 0, None)
temp_lines.append(start_pt)
temp_coords = [(p.x, p.y) for p in temp_lines]
museum_ring = LineString(temp_coords)
_, temp_lines = route(shopping_gdf, 0, 0, [start_pt], 0, None)
temp_lines.append(start_pt)
temp_coords = [(p.x, p.y) for p in temp_lines]
shopping_ring = LineString(temp_coords)

# Generate the route map
basemap = shopping_gdf.plot(column='score', cmap='Blues', markersize=5)
basemap = museum_gdf.plot(ax=basemap, column='score', cmap='Reds', markersize=8)
start_gpd = gpd.GeoDataFrame({'geometry':[Point(start_pt_mercator[0], start_pt_mercator[1])]})
start_gpd.plot(ax=basemap, color='green', )
museum_ring_gpd = gpd.GeoDataFrame({'geometry':[museum_ring]})
museum_ring_gpd.plot(ax=basemap, color='pink')
shopping_ring_gpd = gpd.GeoDataFrame({'geometry':[shopping_ring]})
shopping_ring_gpd.plot(ax=basemap, color='cyan')

plt.show()