from jira import JIRA
from atlassian import Confluence
import psycopg2
import json

class JiraFetcher:
    def __init__(self, jira_server, jira_user, jira_token):
        self.jira = JIRA(server=jira_server, basic_auth=(jira_user, jira_token))
        
    def fetch_issues(self, project, issuetype, status):
        query = f'project={project} AND issuetype="{issuetype}" AND status="{status}"'
        return self.jira.search_issues(query, maxResults=1000)

class RCAResolver:
    def __init__(self, confluence_server, confluence_user, confluence_token):
        self.confluence = Confluence(url=confluence_server, username=confluence_user, password=confluence_token)
    
    def search_rca(self, jira_id):
        results = self.confluence.cql(f'title ~ "{jira_id}"')
        if results['size'] > 0:
            return results['results'][0]['_links']['base'] + results['results'][0]['_links']['webui']
        return None

class DatabaseDumper:
    def __init__(self, db_params):
        self.conn = psycopg2.connect(**db_params)
    
    def insert_data(self, table_name, record):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {table_name} (jira_id, error, context, resolution, tags, rca_doc)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (record['jira_id'], record['error'], record['context'], record['resolution'], json.dumps(record['tags']), record['rca_doc']))
            self.conn.commit()

def main():
    jira_fetcher = JiraFetcher(jira_server='https://your-jira-instance', jira_user='email', jira_token='token')
    rca_resolver = RCAResolver(confluence_server='https://your-confluence-instance', confluence_user='email', confluence_token='token')
    db_dumper = DatabaseDumper(db_params={'host':'localhost', 'dbname':'errorsdb', 'user':'user', 'password':'pass'})
    
    issues = jira_fetcher.fetch_issues('INVESTBANK', 'Bug', 'Closed')
    
    for issue in issues:
        rca_link = None
        attachments = issue.fields.attachment
        if attachments:
            for attach in attachments:
                if "rca" in attach.filename.lower():
                    rca_link = attach.content
        
        if not rca_link:
            rca_link = rca_resolver.search_rca(issue.key)
        
        data = {
            "jira_id": issue.key,
            "error": issue.fields.summary,
            "context": issue.fields.description,
            "resolution": issue.fields.resolution.description if issue.fields.resolution else "Not Available",
            "tags": issue.fields.labels,
            "rca_doc": rca_link
        }
        
        db_dumper.insert_data('jira_errors', data)

if __name__ == "__main__":
    main()
