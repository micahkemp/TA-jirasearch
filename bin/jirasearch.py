from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option

import sys
from datetime import datetime
from jira import JIRA
from mako.template import Template

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

        # if we can't access search_et, set it to the epoch time
        try:
            search_et_epoch = self.search_results_info.search_et
        except:
            search_et_epoch = 0.0

        # if we can't access search_lt, set it to now
        try:
            search_lt_epoch = self.search_results_info.search_lt
        except:
            search_lt_epoch = float(datetime.now().strftime("%s"))

        # format timestamps to be appropriate for JQL
        search_et_jira = datetime.fromtimestamp(search_et_epoch).strftime("%Y/%m/%d %H:%M")
        search_lt_jira = datetime.fromtimestamp(search_lt_epoch).strftime("%Y/%m/%d %H:%M")

        # perform substitution
        templated_query = Template(self.query).render(earliest=search_et_jira, latest=search_lt_jira)

        events = []
        for issue in self.jira.search_issues(templated_query, maxResults=self.limit):
            event = {
                '_time': datetime.strptime(issue.fields.created, "%Y-%m-%dT%H:%M:%S.000+0000").strftime("%s"),
                '_raw': "{}: {}".format(issue.key, issue.fields.summary),
                'id': issue.key,
            }
            for field in field_id_for_field:
                field_id = field_id_for_field[field]
                try:
                    field_value = getattr(issue.fields, field_id)
                    if isinstance(field_value, list):
                        event[field] = []
                        for value in field_value:
                            event[field].append("{}".format(value))
                    elif field_value:
                        event[field] = "{}".format(field_value)
                    else:
                        event[field] = []
                except:
                    event[field] = []

            events.append(event)

        sorted_events = sorted(events, None, lambda x: x['_time'], True)
        for event in sorted_events:
            yield event

dispatch(JIRAsearchCommand, sys.argv, sys.stdin, sys.stdout, __name__)
