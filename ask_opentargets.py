import argparse
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import openai
import requests

from utils import extract_values

parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)

parser.add_argument(
    "--store_output",
    action=argparse.BooleanOptionalAction,
    help='Flag to store the output to file "output.json"',
)
parser.set_defaults(feature=False)
args = parser.parse_args()

log_file = "main.log"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "[%(asctime)s] %(name)-12s: %(levelname)-8s : %(lineno)d %(message)s"
)
fh = logging.FileHandler(log_file)
ch = logging.StreamHandler()

ch.setLevel(logging.INFO)
ch.setFormatter((formatter))

fh.setLevel(logging.DEBUG)
fh.setFormatter((formatter))

logger.addHandler((fh))
logger.addHandler((ch))


# read Open AI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Open Targets graphQL schema example
# read from file
prompt_template = Path("graphql_schema_test_3.txt").read_text()

# Prime the target query for completion
# prime_prompt = "query top_n_associated_diseases {\n  search(queryString:"
prime_prompt = "query query {"

# Custom input by the user
# user_input = "Find the top 2 diseases associated with BRCA1"

# Working inputs
# user_input ="What are the targets of vorinostat"
# user_input = "What is the symbol of the gene ENSG00000169083"
user_input = "What are the top 3 diseases associated with BRCA1"
# user_input = "Find drugs that are used for treating ulcerative colitis"
# user_input = "What is the description of the disease cancer"
# user_input = "Which diseases are associated with the genes targetted by fasudil?"

# Not working inputs
# user_input = "Show all the diseases that have at least 5 pathways associated with Alzheimer"
# user_input = "What are the main consequences of diabetes?"

# user_input ="What are the targets of vorinostat"#"What is the symbol of the gene ENSG00000169083" #"What are the targets of vorinostat"#"What are the top 3 diseases associated with BRCA1"#input("How can I help you today?\n")

prompt_user = prompt_template + "### " + user_input + "\n" + prime_prompt

logger.debug(prompt_user)

response = openai.ChatCompletion.create(  # openai.Completion.create(
    model="gpt-3.5-turbo",
    # prompt=prompt_template + "### " + user_input + "\n" + prime_prompt,
    messages=[{"role": "user", "content": prompt_user}],
    temperature=0,
    max_tokens=250,
    # top_p=1,
    # frequency_penalty=0,
    # presence_penalty=0,
    stop=["###"],
)

# Accessing the output of chatgpt
response_text = response["choices"][0]["message"]["content"]

query_string = prime_prompt + response_text

# # filename with current date and time
query_file = "query_" + datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p") + ".txt"

# # write query to file with current date and time
s = f"# User input: {user_input}\n{query_string}\n"
Path(query_file).write_text(s)
logger.info(f"Custom graphQL query was written to file: {query_file}")
logger.debug(query_string)

# Set base URL of GraphQL API endpoint
base_url = "https://api.platform.opentargets.org/api/v4/graphql"

# Perform POST request and check status code of response
# This handles the cases where the Open Targets API is down or our query is invalid
try:
    response = requests.post(base_url, json={"query": query_string})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logger.error(err)

# Transform API response from JSON into Python dictionary and print in console
api_response = json.loads(response.text)

if args.store_output:
    Path("output.json").write_text(json.dumps(api_response))
    logger.info("Api response stored on file output.json")
else:
    logger.info(api_response)
# hits_list = api_response["data"]["search"]["hits"][0]

# print("\n\nQuerying Open Targets genetics database...\n\n")

# disease_list = extract_values(hits_list, "disease")
# for i, j in enumerate(disease_list):
#     print(f"{i+1}. {j['name']}")
