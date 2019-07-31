import pandas as pd
unpickled_df = pd.read_pickle("D:\Project\ODEA7\PTrun\\20190729-cdown\\dummy.pkl")

unpickled_df.to_pickle("D:\Project\ODEA7\PTrun\\20190729-cdown\\dummy111.pkl",compression ='bz2')

unpickled_df = pd.read_pickle("D:\Project\ODEA7\PTrun\\20190729-cdown\\dummy111.pkl")
pass