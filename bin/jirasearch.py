from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option

import sys
from jira import JIRA

@Configuration()
class JIRAsearchCommand(GeneratingCommand):
    query = Option(require=True)
    limit = Option(default=10000)

    # need to get this from config instead
    #jira_url = 
    #jira_username = 
    #jira_password = 

    jira = JIRA(jira_url, basic_auth=(jira_username, jira_password))

    def generate(self):
        field_id_for_field = {}
        for field in self.jira.fields():
            field_id_for_field[field['name']] = field['id']

        events = []
        for issue in self.jira.search_issues(self.query, maxResults=self.limit):
            event = {
                '_time': issue.fields.created,
                '_raw': "{}: {}".format(issue.key, issue.fields.summary),
                'id': issue.key,
            }
            for field in field_id_for_field:
                field_id = field_id_for_field[field]
                try:
                    field_value = getattr(issue.fields, field_id)
                    event[field] = field_value
                except:
                    event[field] = []

            events.append(event)

        sorted_events = sorted(events, None, lambda x: x['_time'], True)
        for event in sorted_events:
            yield event

dispatch(JIRAsearchCommand, sys.argv, sys.stdin, sys.stdout, __name__)
