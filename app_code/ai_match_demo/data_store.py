# system
import pandas as pd
import pathlib
import os
import aiohttp
import asyncio
import websockets
import ssl
import random
import time as time
from dotenv import load_dotenv
from groq import Groq

# panel
import param
import panel as pn
from panel.viewable import Viewer

# app
import common

# parameters
CD = pathlib.Path(__file__).parent.resolve()

load_dotenv()
GCP_CLOUD_FOLDER = os.getenv('GCP_CLOUD_FOLDER')

EXAMPLE_PATIENTS = os.path.join(CD, 'data/demo_patients.csv')
EXAMPLE_PATIENTS_CLOUD = f'demo_patients.csv'

#EXAMPLE_TRIALS = os.path.join(CD, 'data/nci_trials.csv')
EXAMPLE_TRIALS = os.path.join(CD, 'data/trial_nct.june10.csv')
EXAMPLE_TRIALS_CLOUD = f'nci_trials.csv'

#EXAMPLE_SIM = os.path.join(CD, 'data/trial_similarity.csv')
EXAMPLE_SIM = os.path.join(CD, 'data/trialpatient_sim_nct.june10.csv')
EXAMPLE_SIM_CLOUD = f'trial_similarity.csv'

AUTH_TOKEN = os.getenv('TOKEN')
CERT_PEM = os.getenv('CERT_KEYNAME')
CERT = ssl.create_default_context(cafile=CERT_PEM)
AI_SIMILAR_URL = os.getenv('AI_SIMILAR')

class DataStore(Viewer):

    data = param.DataFrame()
    patient_summary = param.String(default="No summary available", doc="A clinical summary of patient")

    # core data
    patients_df = param.DataFrame()
    trials_df = param.DataFrame()
    similar_df = param.DataFrame()
    trialsim_df = param.DataFrame()
    active_id = '99196a2'

    # matching parameters
    minimum_similarity = param.Number(default=0.4)

    # state variables
    patient_view = param.Boolean(default=False)
    updated = param.Boolean(default=False)
    checking_trials = param.Boolean(default=False)
    local_llm = param.Boolean(default=True)

    def __init__(self, **params):
        super().__init__(**params)

        # initialize data
        self._prep_data_folder()

        # load patients
        self.patients_df = pd.read_csv(EXAMPLE_PATIENTS).set_index('patient_id')

        # set active
        self.active_id = self.patients_df.index[random.randint(0, self.patients_df.shape[0]-1)]

        # check URL for encoded summary
        url_val = pn.state.session_args.get('summary')
        
        # check URL for force to results
        force_go_to_results = pn.state.session_args.get('force_go_to_results')

        # use this as default if present, if not pull from examples
        if url_val is not None and url_val[0]:
            self.patient_summary = url_val[0].decode('utf-8')

            if force_go_to_results and force_go_to_results[0]:
                self.patient_view = True

        else:
            self.patient_summary = self.patients_df.loc[self.active_id, 'patient_summary']

        # load trials
        self.trials_df = self._load_trials()

        # load similarity
        self.similar_df = pd.read_csv(EXAMPLE_SIM).set_index('nct_id')
        self.similar_df = self.similar_df.loc[self.trials_df.index]

        # create merged monstrosity
        self.trialsim_df = pd.DataFrame()
        self.trialsim_df = pd.merge(self.trials_df, self.similar_df, left_index=True, right_index=True, how='left')
        #for x in self.trials_df.index:
        #    self.trialsim_df[x] = 0

    def _prep_data_folder(self):
        ''' ensures the data folder has necessary data '''
        common.transfer_file_from_gcs(EXAMPLE_PATIENTS_CLOUD, EXAMPLE_PATIENTS)
        common.transfer_file_from_gcs(EXAMPLE_TRIALS_CLOUD, EXAMPLE_TRIALS)
        common.transfer_file_from_gcs(EXAMPLE_SIM_CLOUD, EXAMPLE_SIM)

    def _load_trials(self):

        #trials_df = pd.read_csv(EXAMPLE_TRIALS).set_index('nct_id').drop(columns='Unnamed: 0')
        trials_df = pd.read_csv(EXAMPLE_TRIALS).set_index('nct_id')

        #for x in ['start_date',
        #    'primary_completion_date',
        #    'completion_date',
        #    'first_posted',
        #    'results_first_posted',
        #    'last_update_posted',
        #    'trial_start_dt']:
        for x in ['statusModule.startDateStruct.date']:
            try:
                trials_df[x] = pd.to_datetime(trials_df[x])
            except ValueError:
                trials_df[x] = None

        # take this susbet
        new_cols = ['identificationModule.briefTitle', 'statusModule.overallStatus', 'statusModule.startDateStruct.date', 
            'identificationModule.officialTitle', 'descriptionModule.detailedDescription', 'trial_summary']
        trials_df = trials_df[new_cols].copy()

        # rename the columns
        xx = dict()
        for x, y in zip(['short_title', 'study_status', 'trial_start_dt', 'long_title', \
            'eligibility_criteria'], new_cols):
            xx[y] = x
        trials_df = trials_df.rename(columns=xx)
        trials_df['study_url'] = trials_df.index.map(lambda x: f'https://clinicaltrials.gov/study/{x}')

        return trials_df

    #@pn.cache(to_disk=True, cache_path="./sim_cache")
    @param.depends('patient_view', 'patient_summary', watch=True)
    async def _update_trial_similarity(self):
        # Define the headers
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        # craft payload
        data = {"summary": self.patient_summary}

        print("entering async")
        async with aiohttp.ClientSession() as session:
            async with session.post(AI_SIMILAR_URL, json=data, ssl=CERT) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"Request failed with status {response.status}")
                if 'application/json' in response.headers.get('Content-Type', ''):
                    data = await response.json()
                else:
                    text = await response.text()
                    raise aiohttp.ClientError(f"Unexpected content type: {response.headers.get('Content-Type')}\n{text}")
                print("recieved similarities")
                

                # update the summaries
                sr = pd.Series(data)
                self.trialsim_df.loc[sr.index, self.active_id] = sr.values
                self.updated = True

    @pn.cache(to_disk=True, cache_path="./groq_cache")
    def ask_groq_about_trial_loosely(self, patient_summary, trial_summary):
        # create client
        client = Groq(
            api_key=common.GROQ_API_KEY,
        )

        chat_completion = client.chat.completions.create(
            #
            # Required parameters
            #
            messages=[
                # Set an optional system message. This sets the behavior of the
                # assistant and can be used to provide specific instructions for
                # how it should behave throughout the conversation.
                {
                    'role':'system', 
                    'content': """\
You are a brilliant oncologist with encyclopedic knowledge about cancer and its treatment. 
Your job is to evaluate whether a given clinical trial is a reasonable consideration for a 
patient, given a clinical trial summary and a patient summary."""},
                # Set a user message for the assistant to respond to.
                {
                    'role':'user', 
                    'content': f"Here is a summary of the clinical trial:\n {trial_summary}.\nHere is a summary of the patient:\n" + patient_summary + """
        Base your judgment on whether the patient generally fits the cancer type(s), prior treatment(s), and biomarker criteria specified for the trial.
        You do not have to determine if the patient is actually eligible; instead please just evaluate whether it is reasonable for the trial to be considered further by the patient's oncologist.
        Some trials have biomarker requirements that are not assessed until formal eligibility screening begins; please ignore these requirements.
        Reason step by step, then answer the question "Is this trial a reasonable consideration for this patient?" with a one-word Yes! or No! answer."""
                }
            ],

            # The language model which will generate the completion.
            model="llama3-70b-8192",

            #
            # Optional parameters
            #

            # Controls randomness: lowering results in less random completions.
            # As the temperature approaches zero, the model will become deterministic
            # and repetitive.
            temperature=0.01,

            # The maximum number of tokens to generate. Requests can use up to
            # 32,768 tokens shared between prompt and completion.
            max_tokens=1024,

            # Controls diversity via nucleus sampling: 0.5 means half of all
            # likelihood-weighted options are considered.
            top_p=1,

            # A stop sequence is a predefined or user-specified text string that
            # signals an AI to stop generating content, ensuring its responses
            # remain focused and concise. Examples include punctuation marks and
            # markers like "[end]".
            stop=None,

            # If set, partial message deltas will be sent.
            stream=False,
        )

        # API wait
        time.sleep(.3)

        # Print the completion returned by the LLM.
        #print(chat_completion.choices[0].message.content)
        msg = chat_completion.choices[0].message.content
        if msg.count("Yes!") > 0:
            return True
        return False

    def fake_something(self):

        import random
        result = random.choice([True, False])
        time.sleep(.2)


        return result