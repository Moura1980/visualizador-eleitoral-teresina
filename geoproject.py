import geopandas as gpd
import matplotlib.pyplot as plt

data = gpd.read_file("dados.xlsx")

# print(data.head(10))

data.plot()
plt.show()


