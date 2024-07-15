# system
from datetime import datetime
import asyncio
import numpy as np
import pandas as pd

# panel
import param
from panel.viewable import Viewer
import panel as pn
pn.extension('tabulator')

# app
from data_store import DataStore
import common

class View(Viewer):
    data_store = param.ClassSelector(class_=DataStore)

class SidebarView(View):

    def __init__(self, **params):
        super().__init__(**params)

        # create slider for setting minimum similarity of trial matches
        self.minsim_slider = pn.widgets.FloatSlider(name='Similarity', \
            start=0.01, end=1.0, step=0.01, \
            value=self.data_store.minimum_similarity)

        # create switch for trial checker
        self.local_llm_switch = pn.widgets.Switch(name='Local LLM', \
            value=self.data_store.local_llm)

        # link to datastore
        self.minsim_slider.link(self.data_store, value='minimum_similarity')


    def __panel__(self):

        option2 = pn.pane.Markdown("""\
### Local LLM
Use DFCI hosted LLM (default), or use GROQ.
""", sizing_mode='stretch_width')

        return pn.Column(
            pn.pane.Markdown("""\
## Key Parameters

### Minimum patient to trial similarity
Matches between patients and trials which fall below this threshold are excluded by default.
""", sizing_mode='stretch_width'),
            self.minsim_slider,
            #self.local_llm_switch
        )

class PatientSummaryView(View):

    # track when edit button is clicked.
    edits = param.Integer(default=0)

    # constants
    _template_part1 = """# Patient Summary
***
"""

    @param.depends('edits', watch=True)
    async def update_toggle_label(self):

        # set state
        self.data_store.updated = True

        # persist results
        self.data_store.patient_summary = self.text_editor.value


    def view(self):
        ''' display editor or text depending on edit mode '''
        return self.text_editor


    def __init__(self, **params):
        super().__init__(**params)
        
        # patient basic stats
        self.template_part1_display = pn.pane.Markdown(\
            self._template_part1, sizing_mode='stretch_width')

        # display for AI summary
        self.text_display = pn.pane.Markdown(self.data_store.patient_summary, sizing_mode='stretch_width')

        # AI summary editor: default hidden
        self.text_editor = pn.widgets.TextAreaInput(value=self.data_store.patient_summary, rows=10, \
            resizable='height', height=300,
            auto_grow=True,
            sizing_mode='stretch_width')

        # toggle button for edit/search
        def _search_sim_button(event):

            # note we've been pressed
            setattr(self, 'edits', self.edits + 1)

            # set state
            setattr(self, 'data_store.updated', True)
        self.edit_button = pn.widgets.Button(name='Search trials', button_type='primary')
        self.edit_button.on_click(lambda event: setattr(self, 'edits', self.edits + 1))
        #self.edit_button.on_click(_search_sim_button)


    def __panel__(self):

        self._layout = pn.Column(self.template_part1_display, self.view(), self.edit_button)            
        return self._layout




class ContentView(View):
    def __init__(self, **params):
        super().__init__(**params)

        self.gspec = pn.GridSpec(sizing_mode='stretch_both')
        #gspec[:, 0:2] = pn.Spacer(styles={"border": "1px solid red"})
        #self.gspec[:, 0:8] = pn.Spacer(styles={"border": "1px solid black"})
        #self.gspec[:, 9:10] = pn.Spacer(styles={"border": "1px solid white"})

class HomeView(ContentView):
    ''' home page stuff '''

    custom_css = """\
.bigger-font {
    font-size: 1.3em;
}
.centered-vertical {
    display: flex;
    align-items: center;
    height: 100%;
}
.centered-horizontal {
    justify-content: center;
    width: 100%;
}
"""
    def __init__(self, **params):
        super().__init__(**params)

        # setup tss
        pn.config.raw_css.append(self.custom_css)

    async def toggle_view(self, event):

        # update summary
        self.data_store.patient_summary = self.text_area.value
        print(f"Setting patient summary: {self.data_store.patient_summary}")

        # swap the view
        self.data_store.patient_view = not self.data_store.patient_view


    def __panel__(self):
        
        # simplify the content
        self.text_area = pn.widgets.TextAreaInput(
            #name='Patient summary', 
            placeholder=self.data_store.patient_summary,
            value=self.data_store.patient_summary,
            #align="center",
            max_length=10000,
            height=150,
            auto_grow=True,
            sizing_mode='stretch_width'
        )
        title = pn.widgets.StaticText(name='', value='If you have questions please send an email to matchminer@dfci.harvard.edu', styles=
        {
            "display": "flex",
            "justify-content": "center",
            "width": "100%",
            "font-size": "1.2em",
            "font-weight": "bold"
        })
        

        # create elements for summarizing trial
        trial_stats = pn.Row(pn.indicators.Number(name='Clinical trials', \
            value=self.data_store.trials_df.shape[0], format='{value}'), css_classes=['centered-horizontal'])

        button = pn.widgets.Button(name='Match this patient', button_type='primary')
        #button.on_click(self.toggle_view)
        button.on_click(lambda event: asyncio.ensure_future(self.toggle_view(event)))

        instr = pn.pane.Markdown(f'''\
Please enter information describing a theoretical patient. Please include information including the primary cancer type, subtype of the cancer, the stage of the patients disease and any clinically relavent biomarkers. 
''', \
    sizing_mode='stretch_width', css_classes=['bigger-font'])
        content = pn.Column(
            pn.Row(
                pn.pane.Image(f'{common.CD}/assets/matchminer_man.png', width=150),
                pn.pane.Markdown(f'''\
Technology demonstration of clinical trial matching via Llama3 and fine-tuned embedding models. The prototype currently matches agains {self.data_store.trials_df.shape[0]} clinical trials at DFCI.

**Do not put any identifying information into this website and do not use it for actual\
 screening of patients**. 
''', sizing_mode='stretch_width', css_classes=['centered-vertical', 'bigger-font'])
            ),
            #pn.layout.VSpacer(),   # Add vertical space before the content
            #title,
            #pn.Spacer(height=5),
            self.text_area,
            button,
            instr,
            #pn.layout.VSpacer(),   # Add vertical space after the content,
            styles={"border": "0px solid black"}
        )

        # update content
        self.gspec[:, 0:1] = pn.Spacer()
        self.gspec[:, 1:7] = content
        self.gspec[:, 7:8] = pn.Spacer()
        return self.gspec

class TrialSimilarityView(ContentView):

    # columns to display
    to_display = ['short_title', 'study_status', 'trial_start_dt', 'long_title', 'trial_summary', \
        'study_url']
    
    @staticmethod
    def trial_fn(row):
        css = """\
<style>
.wrap-content {
    white-space: normal !important;
    word-wrap: break-word !important;
}
</style>
"""

        md = pn.pane.Markdown(f"""\
**{row['long_title']}**

## Trial summary
{row['trial_summary']}

## Study Url
{row['study_url']}""", sizing_mode='scale_width', css_classes=['wrap-content'])
        col = pn.Column(md)
        return col

    @param.depends('data_store.minimum_similarity', watch=True)
    def relayout(self):

        # patient summary
        self.ps_view = PatientSummaryView(data_store=self.data_store)

        # create simplified view
        self.tdf = self.data_store.trialsim_df[self.to_display + [self.data_store.active_id]].copy()
        self.tdf = self.tdf.rename(columns={self.data_store.active_id: 'Similarity'})

        # apply filters
        self.tdf = self.tdf[self.tdf.Similarity >= self.data_store.minimum_similarity]

        # sort it and limit
        self.tdf = self.tdf.sort_values("Similarity", ascending=False)
        self.tdf = self.tdf.iloc[0:10]

        # add boolean indicator.
        self.tdf['checked'] = pd.Series([None] * len(self.tdf), dtype=pd.BooleanDtype())

        # sanity check.
        if self.tdf.shape[0] == 0:
            
            # no matches
            self.trial_table = pn.pane.Alert("No trials matched this description.", alert_type="warning")

        else:

            # setup tabulator
            tabulator_formatters = {
                'Similarity': {'type': 'progress', 'max': 1.0, },
                'short_title': {'type': 'plaintext', 'title': 'Title'},
                'checked': {'type': 'tickCross', 'title': 'Checked', 'allowEmpty': True}
            }
            titles = {
                'Similarity': 'Score',
                'short_title': 'Trial',
                'checked': 'Checked'
            }
            twidths = {
                'index': '10%',
                'short_title': '60%',
                'Similarity': '15%',
                'checked': '15%'
            }
            self.trial_table = pn.widgets.Tabulator(self.tdf, \
                formatters=tabulator_formatters, hidden_columns=['nct_id', 'study_status', 'trial_start_dt', 'purpose', \
                    'eligibility_criteria', 'study_url', 'long_title', 'trial_summary'],\
                    row_content=TrialSimilarityView.trial_fn, widths=twidths, sizing_mode='stretch_width',\
                    titles=titles, page_size=10, pagination='remote', theme="materialize"
                )

    @param.depends('data_store.updated', 'data_store.minimum_similarity', watch=True)
    def updated_watcher(self):
        print("Update watcher called")
        if self.data_store.updated == False:
            print("no relayout")
            return

        print("yes relayout")

        # recompute everything
        self.relayout()

        # populate view
        self.patient[0] = self.ps_view
        self.stack[2] = self.trial_table
        self.data_store.updated = False

        # note that we can begin checking these trials
        print("NEED TO CHECK THESE")
        self.data_store.checking_trials = True

    @param.depends('data_store.checking_trials', watch=True)
    def check_trials(self):

        print("check trials")
        if not self.data_store.checking_trials:
            print("debounce")
            return

        # bring up the indicator
        self.stack[1] = pn.indicators.Progress(\
            name='Indeterminate Progress', active=True, sizing_mode='stretch_width',
            max = self.trial_table.value.shape[0] - 1, value=0
        )

        idx = 0
        for nct_id, row in self.trial_table.value.iterrows():

            # assess quality
            print("checking", nct_id)
            trial_summary = row['trial_summary']
            keep_match = self.data_store.ask_groq_about_trial_loosely(\
                self.data_store.patient_summary, trial_summary)
            #keep_match = self.data_store.fake_something()

            # assign it
            self.trial_table.value.at[nct_id, 'checked'] = keep_match
            self.trial_table.param.trigger('value')

            # track progress
            self.stack[1].value = idx
            self.stack[1].param.trigger('value')
            idx += 1

        # reset this
        self.data_store.checking_trials = False

    def __panel__(self):

        # header content
        header = pn.pane.Markdown(\
f'''# Trial Recommendations
Below is a list of clinical trial recommendations for the described patient. These are \
based off similarity of the patient to clinical trial criteria available from public \
sources.
        ''')

        self.patient = pn.Column(pn.Spacer())
        self.trial_table = pn.pane.Markdown("waiting...")

        # update content
        self.stack = pn.Column(header, pn.Spacer(), self.trial_table)
        self.gspec[:, 0:2] = self.patient
        self.gspec[:, 2:8] = self.stack
        return self.gspec