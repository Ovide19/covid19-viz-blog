#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 19:27:56 2020

@author: sheldon
"""
import folium
import numpy as np
import datetime
import pandas as pd
import unidecode
import branca.colormap as cm
colormap =cm.linear.YlOrRd_09.scale(0, 1000)
import departements
from flask import Flask
import os
#import os

legend_html = '''
<div style="position: fixed;
     padding: .5em; top: 10px; left: 60px; width: 30em; height: 5em;
     border:2px solid grey; z-index:9999; font-size:14px; background: #eee;
     "> &nbsp; COVID-19 related deaths for Metropolitan France<br>
     &nbsp; Data recovered from https://github.com/opencovid19-fr/data  <br>
</div>
'''

def download_csv_from_github():
     download_start_time=datetime.datetime.now()
     data=pd.read_csv('https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv')
     download_end_time=datetime.datetime.now()  
     download_duration=download_end_time-download_start_time
     return data, download_duration



class CovidData(object):
   
    def __init__(self):
         self.Data, self.download_duration = download_csv_from_github()
         self.Departements = departements.coordinates         
         self.Coordinates=pd.DataFrame.from_dict(self.Departements, orient='index')
         self.Coordinates['maille_code']=self.Coordinates.index         
         self.map = folium.Map(location=[46,2],
              tiles = 'Stamen Terrain',
              zoom_start=6)         
         self.merged_data_last = None


    def merge_data_and_coordinates(self):
         self.merged_data=self.Data.merge(self.Coordinates, left_on='maille_code', right_on='maille_code')

    def drop_rows_with_missing_info(self):
         self.merged_data=self.merged_data.dropna(subset=['deces'])

    def select_last_date(self):
         self.merged_data_last=self.merged_data.sort_values('date').groupby('maille_code').tail(1)


    def plot_departments(self,data,custom_color):
         radius = data['deces'].values.astype('float')
         latitude = data[0].values.astype('float')
         longitude = data[1].values.astype('float')
         name = data['maille_nom'].values.astype('str')   
         latest_date = data['date'].values.astype('str')
         for la,lo,ra,na,ld in zip(latitude,longitude,radius,name,latest_date):
              label=unidecode.unidecode(na.replace("'","-"))+': '+str(ra)[:-2]+ ' victims by '+str(ld)+'.'
              folium.Circle(
                       location=[la,lo],
                       radius=5000*np.log(ra),
                       fill=True,
                       color='grey',
                       fill_color=colormap(ra),
                       fill_opacity=0.8
                   ).add_child(folium.Popup(label)).add_to(self.map)
               

def create_map():
     CODA=CovidData()
     CODA.merge_data_and_coordinates()
     CODA.drop_rows_with_missing_info()
     CODA.select_last_date()
     CODA.plot_departments(CODA.merged_data_last,'grey')
     CODA.map.get_root().html.add_child(folium.Element(legend_html))
     colormap.caption = 'COVID-19 death toll per department (Source: opencovid19-fr)'
     CODA.map.add_child(colormap)

     return CODA

#global Coda
#Coda = create_map()
#
#Coda.map.save("./COVID_map.html")



app = Flask(__name__)

@app.route("/")
def display_map():
     CODA = create_map()
     return CODA.map._repr_html_()

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=os.environ.get('PORT', 80))

