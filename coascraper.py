#!/usr/bin/env python
"""
A simple script to scrape data from Scopus and Google search results to fill out the NSF coascraper spreadsheet

Uses pybliometrics to pull data from Scopus (https://pybliometrics.readthedocs.io/en/stable/index.html)

You will need to obtain an Elsevier API key from here: https://dev.elsevier.com/apikey/manage. This is a 32 character
string.

And you will need to find out your Scopus Author ID. This is an 11 digit number, and is often listed on the left side of
your Orcid profile. You can also get it from the URL of your author page on Scopus.
"""

import datetime
import pandas as pd
import requests
import re
from googlesearch import search
from pybliometrics.scopus import AuthorRetrieval, ContentAffiliationRetrieval, config
from pybliometrics.scopus.exception import Scopus429Error

# replace the 'x' with your values
API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
Author_id = 'xxxxxxxxxxx'

# get my publications
try:
    Documents = AuthorRetrieval(Author_id).get_documents()
except Scopus429Error:
    # first time pybliometrics is run, it sets the API_KEY
    config["Authentication"]["APIKey"] = API_KEY
    Documents = AuthorRetrieval(Author_id).get_documents()

# How many googled pages to scrape looking for email addresses
num_url_search_email = 5

# today's date
today = datetime.datetime.now()

# prepare a dataframe to hold the results
data = pd.DataFrame(columns=['Name', 'Organizational Affiliation', 'Optional  (email, Department)', 'Last Active'])

# Loop over documents
for doc in Documents:

    # check whether the publication date is within the last 48 months
    coverDate = datetime.datetime.strptime(doc.coverDate, '%Y-%m-%d')
    if (today - coverDate).days <= 30 * 48:

        # get the ids of all the co-authors, and loop over them
        for id in doc.author_ids.split(';'):

            # check whether to add this author to the dataset
            if (id != Author_id) and ((id not in data.index) or (data['Last Active'].loc[id] < coverDate)):

                # get their info from scopus
                CoAuthor = AuthorRetrieval(id)
                name = '{}, {}'.format(CoAuthor.surname, CoAuthor.given_name)
                print('')
                print(f'name:        {name}')

                # get an affiliation with an OrgID (starts with a 6)
                affil_id = CoAuthor.affiliation_current
                if affil_id[0] != '6' and CoAuthor.affiliation_history is not None:
                    affil_id_list = [a for a in CoAuthor.affiliation_history if a[0] == '6']
                    if len(affil_id_list) > 0:
                        affil_id = affil_id_list[0]
                affiliation = ContentAffiliationRetrieval(affil_id)
                affil_name = affiliation.affiliation_name
                print(f'affiliation: {affil_name}')

                # google them
                google_results = search(' '.join(['email', CoAuthor.given_name, CoAuthor.surname, affiliation.org_domain]),
                                        num=num_url_search_email, only_standard=True, pause=5.)
                # scrape the results, looking for their email address
                email_list = []
                for url in google_results:
                    if not url[-3:]=='pdf':
                        print(f'  scraping {url}')
                        try:
                            html = requests.get(url).text
                            # this uses regex to find something like an email address
                            scraped_email = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}", html)
                            email_list += scraped_email
                            # keep only unique entries that contain the first three letters of the author's lastname
                            email_list = list(set([e for e in email_list if CoAuthor.surname[:3].lower() in e.split('@')[0].lower()]))
                            # if that is removing too many valid results, comment that line out and uncomment this one
                            # email = list(set([e for e in email_list]))
                            # stop if you have at least 2 unique emails
                            if len(email_list)>1:
                                break
                        except:
                            pass
                email = ', '.join(email_list)
                print(f'email:       {email}')

                # add the results to the dataframe
                data = data.append(pd.DataFrame.from_dict({id: {
                    'Name': name,
                    'Organizational Affiliation': '{}, {}'.format(affiliation.org_domain, affil_name),
                    'Optional  (email, Department)': email,
                    'Last Active': coverDate
                }}, orient='index'))

# output the results as an excel file
data.to_excel('coascraper.xlsx')
