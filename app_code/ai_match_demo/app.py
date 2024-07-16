# system
import pathlib

# panel
import param
import panel as pn
import pandas as pd
from panel.viewable import Viewer
from bokeh.themes import Theme

# app
from data_store import DataStore
from views import HomeView, TrialSimilarityView, SidebarView
import common

# simplify.
CD = pathlib.Path(__file__).parent.resolve()

# global styling
pn.extension('tabulator')
##00629B
#pn.extension(design='material', global_css=[':root { --design-primary-color: white; --font-size: 122px}'])
custom_css = """
p {
    font-size: 2em;
}

"""

class App(Viewer):

    data_store = param.ClassSelector(class_=DataStore)

    def __init__(self, **params):
        super().__init__(**params)

        # holder of main content.
        self.content = pn.Column(pn.Spacer())

        # content
        self.home_view = HomeView(data_store=self.data_store)
        #self.trial_view = TrialSimilarityView(data_store=self.data_store)

        # sidebar
        self.side_view = SidebarView(data_store=self.data_store)

        # main template
        self._template = pn.template.MaterialTemplate(
            title='MatchMiner Llama Demo',
            collapsed_sidebar=True,
            sidebar=[self.side_view],
            #header_color='black',
            header_background='#00629B',
            #logo=f'{common.CD}/assets/matchminer_man.png'
            logo=f'{CD}/assets/noun-molecules-orange.png',
        )

        # add our custom css
        self._template.config.raw_css.append(custom_css)

        # add home page
        self._template.main.append(self.content)
        self.update_display()

    @param.depends('data_store.patient_view', watch=True)
    def update_display(self):
        ''' choose which view to display '''

        if self.data_store.patient_view:
            # patient view
            self.trial_view = TrialSimilarityView(data_store=self.data_store)
            self.content[0] = self.trial_view
        else:
            # default view
            self.content[0] = self.home_view

    #@param.depends('data_store.updated', watch=True)
    #def thinking(self):
    #    self._template()
    #    self._template.open_modal()

    def __panel__(self):
        return self._template

    def servable(self):
        if pn.state.served:
            return self._template.servable()
        return self


App(
    data_store=DataStore()
).servable()