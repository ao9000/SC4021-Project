import os
import shutil

import requests
import subprocess

import json
import xml.etree.ElementTree as ET

# Delete later
import pandas as pd
from collections import defaultdict

class SolrManager:
    def __init__(self, solr_dir, csv_path):
        self.solr_dir = solr_dir
        self.csv_path = csv_path
        self.solrconfig_xml_filepath = os.path.join(solr_dir, "server\solr\search_reddit\conf\solrconfig.xml")

        # Check if Solr is already running and the core exists
        if not self.check_solr_status() or not self.core_exists():
            self.start_solr()
            self.delete_existing_core()
            self.create_core()
            self.add_custom_schema()
            self.add_spellcheck()
            self.refresh_core()
            self.ingest_data()

    def core_exists(self):
        response = requests.get("http://localhost:8983/solr/admin/cores", params={"action": "STATUS"})
        return "search_reddit" in response.json()["status"]

    def check_solr_status(self):
        result = subprocess.run([os.path.join(self.solr_dir, "bin\\solr.cmd"), "status"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout == 'No running Solr nodes found.\n':
            return False
        else:
            return True
    
    def start_solr(self):
        try:
            # Run the command to start Solr
            subprocess.run([os.path.join(self.solr_dir, "bin\\solr.cmd"), "start"], check=True)
            print("Solr started successfully.")
        except subprocess.CalledProcessError as e:
            # Handle any errors that occur during the process
            print(f"Start Solr error code: {e}")

    def delete_existing_core(self):
        # Delete any existing core
        response = requests.get("http://localhost:8983/solr/admin/cores?action=UNLOAD&core=search_reddit&deleteInstanceDir=True&deleteDataDir=True")

        # Check the response
        if response.status_code == 200:
            print("Existing core found, deleted existing core.")
        else:
            print("No existing core found.")

    def create_core(self):

        # Define source and destination directories
        source_dir = os.path.join(self.solr_dir, "server\\solr\\configsets\\_default")
        destination_dir = os.path.join(self.solr_dir, "server\\solr\\search_reddit")

        # Remove the existing destination directory if it exists
        if os.path.exists(destination_dir):
            shutil.rmtree(destination_dir)

        # Copy the source directory to the destination
        shutil.copytree(source_dir, destination_dir)

        # Create core
        response = requests.get("http://localhost:8983/solr/admin/cores?action=CREATE&name=search_reddit&instanceDir=search_reddit")

        if response.status_code == 200:
            print("Core created successfully.")
        else:
            print("Error in creating core.")

    def add_custom_schema(self):
        schema_list = []
        
        schema_list.append({"add-field-type":
                                {"name":"text_reddit",
                                "class":"solr.TextField",
                                "positionIncrementGap":"100",
                                "multiValued":True,
                                "indexAnalyzer":{"tokenizer":
                                                    {"class":"solr.WhitespaceTokenizerFactory"},
                                                    "filters":[{"class":"solr.StopFilterFactory",
                                                                "ignoreCase":True,"words":"stopwords.txt"},
                                                                {"class":"solr.LowerCaseFilterFactory"},
                                                                {"class":"solr.SnowballPorterFilterFactory","language":"English"},
                                                                {"class":"solr.NGramFilterFactory","minGramSize":2,"maxGramSize":20}]},
                                                                "queryAnalyzer":{"tokenizer":{"class":"solr.WhitespaceTokenizerFactory"},
                                                                                "filters":[{"class":"solr.StopFilterFactory", "ignoreCase":True,"words":"stopwords.txt"},
                                                                                            {"class":"solr.SynonymGraphFilterFactory","ignoreCase":True,"synonyms":"synonyms.txt","expand":True},
                                                                                            {"class":"solr.LowerCaseFilterFactory"},
                                                                                            {"class":"solr.SnowballPorterFilterFactory","language":"English"}]}}}
        )
        schema_list.append({"add-field":{"name":"author","type":"string","stored":True,"indexed":True, "multiValued":False, "omitNorms":True,"docValues":True}})
        schema_list.append({"add-field":{"name":"text","type":"text_reddit","stored":True,"indexed":True,"required":True}})
        schema_list.append({"add-field":{"name":"created_utc","type":"pdates","stored":True,"indexed":True, "multiValued":False, "omitNorms":True,"docValues":True}})
        schema_list.append({"add-field":{"name":"edited","type":"pdates","stored":True,"indexed":True}})
        schema_list.append({"add-field":{"name":"id","type":"string","stored":True,"indexed":True,"multiValued":False,"required":True}})
        schema_list.append({"add-field":{"name":"num_comments","type":"pdoubles","stored":True,"indexed":True, "multiValued":False, "omitNorms":True,"docValues":True}})
        schema_list.append({"add-field":{"name":"permalink","type":"string","stored":True,"multiValued":False}})
        # schema_list.append({"add-field":{"name":"score","type":"plong","stored":True,"indexed":True, "multiValued":False, "omitNorms":True,"docValues":True}})
        schema_list.append({"add-field":{"name":"upvote","type":"plong","stored":True,"indexed":True, "multiValued":False, "omitNorms":True,"docValues":True}})
        schema_list.append({"add-field":{"name":"subreddit_name","type":"string","stored":True,"multiValued":True}})
        schema_list.append({"add-field":{"name":"upvote_ratio","type":"pdoubles","stored":True,"indexed":True, "multiValued":False, "omitNorms":True,"docValues":True}})
        schema_list.append({"add-field":{"name":"url","type":"string","stored":True,"multiValued":False}})
        schema_list.append({"add-field":{"name":"type","type":"string","stored":True,"multiValued":True}})
        schema_list.append({"add-field":{"name":"post_id","type":"string","stored":True,"multiValued":True}})


        for schema_dict in schema_list:
            response = requests.get("http://localhost:8983/api/cores/search_reddit/schema", params=schema_dict)
            
            # Check the response
            if response.status_code == 200:
                print(f"Added schema with name: {schema_dict[list(schema_dict.keys())[0]]['name']}")
            else:
                print(f"Could not add schema with name: {schema_dict[list(schema_dict.keys())[0]]['name']}")

    def add_spellcheck(self):
        # Parse the XML file
        tree = ET.parse(self.solrconfig_xml_filepath)
        root = tree.getroot()

        # Find the element with name "spellcheck" and change its value
        for elem in root.iter('str'):
            if elem.attrib.get('name') == 'spellcheck':
                elem.text = 'true'
        
        # Find the element with name "queryAnalyzerFieldType" and change its value
        for elem in root.iter('str'):
            if elem.attrib.get('name') == 'queryAnalyzerFieldType':
                elem.text = 'text_reddit'

        # Find the element with name "field" under "spellchecker" and change its value
        for elem in root.iter('lst'):
            if elem.attrib.get('name') == 'spellchecker':
                for child_elem in elem.iter('str'):
                    if child_elem.attrib.get('name') == 'field':
                        child_elem.text = 'text'

        # Write back the modified XML to the file
        tree.write(self.solrconfig_xml_filepath)

    def ingest_data(self):
        # Open and read the CSV file
        with open(self.csv_path, "rb") as file:
            # Make the POST request with the CSV file as the request body
            response = requests.post("http://localhost:8983/solr/search_reddit/update?commit=true", data=file, headers={"Content-type":"application/csv"})
        
        # Check the response status
        if response.status_code == 200:
            print("CSV data successfully sent to Solr.")
        else:
            print("CSV data was not sent, error code: ", response.status_code)  

    def get_text_query_result(self, text, type, date_range=None, num_rows=10, phrase_search=False):

        if len(text.split(" ")) > 1:
            # If searching for the whole phrase
            if phrase_search:
                query = f'text:"{text}"'
            else:
                query = f'text:({text.replace(" ", " AND ")})'
        else:
            query = f"text:({text})"

        query = query + f" AND type:{type}"

        if date_range:
            query = query + f" AND created_utc:[{str(date_range[0])}T00:00:00Z TO {str(date_range[1])}T23:59:59Z]"

        print("get_text_query_result's query:")
        print(query)

        params = {
            "q" : query,
            "rows" : num_rows,
            "sort": "upvote desc"
        }

        response = requests.get("http://localhost:8983/solr/search_reddit/query", params=params)
        print(response)

        # Check the response
        if response.status_code == 200:
            return response.json()
        else:
            return None
 
    def get_comment_from_post_id_and_text(self, post_id, text, num_rows=10):

        result = []

        # Reddit uses id with "t3_" prefix to indicate post_id globally
        post_id = f"t3_{post_id}"

        query = f"post_id:{post_id} AND type:comment"

        params = {
            "q" : query,
            "rows" : num_rows,
            "sort": "upvote desc"
        }
        response = requests.get("http://localhost:8983/solr/search_reddit/query", params=params).json()

        if not response["response"]["numFound"] == 0:
            return response["response"]["docs"]
        else:
            return None

    def refresh_core(self):

        params = {
            "action": "RELOAD",
            "core": "search_reddit",
            "wt": "json"
        }

        response = requests.post("http://localhost:8983/solr/admin/cores", params=params)

        if response.status_code == 200:
            print("Core reloaded successfully.")
        else:
            print("Core was not reloaded, error code: ", response.status_code)

    def spellcheck(self, text):
        params = {
            "indent": "true",
            "spellcheck.q": text,
            "spellcheck": "true",
            "spellcheck.collate": "true"
        }

        response = requests.get("http://localhost:8983/solr/search_reddit/spell", params=params)

        # Check the response
        if response.status_code == 200:
            return response.json()
        else:
            return None

# Only for testing purposes, not meant for using in the application
if __name__ == "__main__":

    print(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "solr-9.5.0-slim"))

    solr_manager = SolrManager(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "solr-9.5.0-slim"),
                            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "data/(copy)cleaned_combined_data.csv"))

    # result = solr_manager.get_text_query_result("ford", type="comment", num_rows=10, phrase_search=False)
    # result = solr_manager.get_comment_from_post_id_and_text("ngqmpr", "ford")
    result = solr_manager.spellcheck("graet")
    print(type(result))
    print(json.dumps(result, indent=4))
