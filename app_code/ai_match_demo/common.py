# system
from google.oauth2 import service_account
import os
import pathlib
import google.auth
from google.cloud import storage
import json
import logging
from groq import Groq

# parameters
from dotenv import load_dotenv
load_dotenv()
GCP_CLOUD_FOLDER = os.environ.get('GCP_CLOUD_FOLDER')
GCP_KEY_NAME = os.environ.get('GCP_KEYNAME')
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GROQ_API_KEY = os.environ.get('GROK_API_KEY')

CD = pathlib.Path(__file__).parent.resolve()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def transfer_file_from_gcs(remote_path, local_path, force=False):
    ''' this is logic that loads a pickle file from cloud
    to local server '''

    # first try local
    if force or not os.path.isfile(local_path) or os.path.getsize(local_path) < 50:

        # then remote
        credentials, project_id = google_credentials()
        storage_client = storage.Client(project=project_id, credentials=credentials)

        bucket = storage_client.bucket(GCP_CLOUD_FOLDER)
        blob = bucket.blob(remote_path)
        blob.download_to_filename(local_path)


    return True

def google_credentials():

    # test for interactive
    def is_interactive():
        import __main__ as main
        return not hasattr(main, '__file__')

    # test for secrets file
    #pdir = find_directory_in_parents(GCP_KEY_NAME)
    #json_file_path = '_not_real'
    #if pdir is not None:
    #    json_file_path = os.path.join(pdir, GCP_KEY_NAME)
    pdir = "d"
    json_file_path = find_file_recursively(GCP_KEY_NAME)

    # sanity
    credentialed = False
    if is_interactive() or not os.path.isfile(json_file_path):
        logger.info("No Google Cloud credentials available")

        # try loading from application default
        try:
            credentials, project_id = google.auth.default()
            if credentials:

                logger.info("got credentials from application default")
                credentialed = True
            else:
                logger.error("warning could not find application default credentials")

        except google.auth.exceptions.DefaultCredentialsError as e:
            logger.info("unable to credential from Google from service account or application default")
            raise e
    else:

        # Load the TOML file
        logger.info("Using Google Cloud service account credentials")
        with open(json_file_path, "rb") as fin:
            creds_data = json.loads(fin.read())

        # Create a credentials object from the extracted dictionary
        credentials = service_account.Credentials.from_service_account_info(creds_data)
        project_id = PROJECT_ID
        credentialed = True

    return credentials, project_id

def find_directory_in_parents(target_directory_name, start_path=__file__):
    """
    Search for a directory with the given name in the current directory and all parent directories.

    Parameters:
    - target_directory_name: The name of the directory to search for.
    - start_path: The directory path to start the search from. Defaults to the current directory.

    Returns:
    The full path to the found directory, or None if the directory is not found.
    """
    current_dir = pathlib.Path(start_path).resolve()

    while True:
        potential_match = current_dir / target_directory_name
        if potential_match.is_dir():
            return potential_match
        if current_dir.parent == current_dir:
            # This means we've reached the root directory and the directory was not found.
            return None
        current_dir = current_dir.parent

def find_file_recursively(filename, start_dir=None):
    if start_dir is None:
        start_dir = os.path.dirname(os.path.abspath(__file__))

    for root, dirs, files in os.walk(start_dir):
        if filename in files:
            return os.path.abspath(os.path.join(root, filename))
    
    return None

