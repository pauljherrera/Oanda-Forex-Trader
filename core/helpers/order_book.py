import pandas as pd


def get_dataframe(ord1_data, ord2_data , columns):
    """
    return a dataframe with the important data of each order

    """
    values_1 = [ord1_data['created_at'],ord1_data['id'],ord1_data['price'],
                ord1_data['size'],ord1_data['Stop Loss'],
                ord1_data['Target Price'], ord1_data['status']]

    values_2 = [ord2_data['created_at'], ord2_data['id'], ord2_data['price'],
                ord2_data['size'], ord2_data['Stop Loss'],
                ord2_data['Target Price'], ord2_data['status']]

    df = pd.DataFrame([values_1,values_2],columns=columns)

    return df
