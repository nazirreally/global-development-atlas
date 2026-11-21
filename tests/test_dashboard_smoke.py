"""Offline code-path smoke test with tiny isolated test fixtures (not dashboard data)."""
from __future__ import annotations
import runpy, sys, types
from pathlib import Path
from unittest.mock import patch
import pandas as pd

class FakeSt(types.ModuleType):
    def __init__(self):
        super().__init__('streamlit')
        self.sidebar = self
        self.figures=[]
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def cache_data(self,**_):return lambda fn:fn
    def set_page_config(self,**_):pass
    def markdown(self,*args,**kw):pass
    def columns(self,items):return [self]*(items if isinstance(items,int) else len(items))
    def tabs(self,items):return [self]*len(items)
    def selectbox(self,label,options,index=0,**_):return list(options)[index]
    def select_slider(self,label,options,value=None,**_):return value if value is not None else list(options)[0]
    def multiselect(self,label,options,default=None,**_):return default if default is not None else []
    def slider(self,label,min_value,max_value,value=None,**_):return max_value if value is None else value
    def checkbox(self,label,value=False,**_):return value
    def radio(self,label,options,**_):return list(options)[0]
    def plotly_chart(self,fig,**_):self.figures.append(fig)
    def metric(self,*args,**_):pass
    def dataframe(self,*args,**_):pass
    def download_button(self,*args,**_):pass
    def info(self,*args,**_):pass
    def warning(self,*args,**_):pass
    def error(self,*args,**_):raise AssertionError(str(args))
    def stop(self):raise AssertionError('st.stop invoked')

def test_all_four_workspace_code_paths():
    from atlas import data
    meta=pd.DataFrame([{'iso3':k,'country':v,'region':'South Asia','income':'Lower middle income'} for k,v in [('PAK','Pakistan'),('IND','India'),('DEU','Germany')]])
    def indicator_data(code):
        return pd.DataFrame([{'iso3':iso,'year':year,'value':20.0+i*12+j*2+(len(code)%4)} for i,iso in enumerate(['PAK','IND','DEU']) for j,year in enumerate([2020,2021,2022])])
    carbon=pd.DataFrame([{'iso3':iso,'year':year,'value':i+j/10+.25} for i,iso in enumerate(['PAK','IND','DEU']) for j,year in enumerate([2020,2021,2022])])
    fake=FakeSt()
    with patch.dict(sys.modules,{'streamlit':fake}),patch.object(data,'countries',return_value=meta),patch.object(data,'indicator',side_effect=indicator_data),patch.object(data,'co2_per_capita',return_value=carbon):
        runpy.run_path(str(Path(__file__).resolve().parents[1]/'app.py'),run_name='__main__')
    assert len(fake.figures)>=5
    assert all(len(fig.data)>=1 for fig in fake.figures)
