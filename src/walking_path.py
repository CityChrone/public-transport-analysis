import pandas as pd
from osmnx.distance import euclidean_dist_vec
from osmnx.distance import great_circle as great_circle_vec
import time


def compute_df_for_nearest_node(G):
    if not G or (G.number_of_nodes() == 0):
        raise ValueError(
            'G argument must be not be empty or should contain at least one node')

    # dump graph node coordinates into a pandas dataframe indexed by node id
    # with x and y columns
    coords = [[node, data['x'], data['y']]
              for node, data in G.nodes(data=True)]
    df = pd.DataFrame(coords, columns=['node', 'x', 'y']).set_index('node')

    # add columns to the dataframe representing the (constant) coordinates of
    # the reference point
    return df


def get_nearest_node(df, point, method='haversine', return_dist=False):
    start_time = time.time()
    df['reference_y'] = point[0]
    df['reference_x'] = point[1]

    # calculate the distance between each node and the reference point
    if method == 'haversine':
        # calculate distance vector using haversine (ie, for
        # spherical lat-long geometries)
        distances = great_circle_vec(df['reference_y'],
                                     df['reference_x'],
                                     df['y'],
                                     df['x'])

    elif method == 'euclidean':
        # calculate distance vector using euclidean distances (ie, for projected
        # planar geometries)
        distances = euclidean_dist_vec(df['reference_y'],
                                       df['reference_x'],
                                       df['y'],
                                       df['x'])

    else:
        raise ValueError(
            'method argument must be either "haversine" or "euclidean"')

    # nearest node's ID is the index label of the minimum distance
    nearest_node = distances.idxmin()
    # log('Found nearest node ({}) to point {} in {:,.2f} seconds'.format(nearest_node, point, time.time()-start_time))

    # if caller requested return_dist, return distance between the point and the
    # nearest node as well
    if return_dist:
        return nearest_node, distances.loc[nearest_node]
    else:
        return nearest_node
