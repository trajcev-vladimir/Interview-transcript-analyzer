import json
import yaml
from datetime import datetime
import logging

logger = logging.getLogger("Report_Output")

class Export:
    def __init__(self, report, candidate_id, json_temp_path="./config/template.json", config_path="./config/config.yaml"):
    # Open configuration file and fetch values
        with open(json_temp_path) as t:
            self.temp_json = json.load(t)
        with open(config_path) as c:
            config = yaml.safe_load(c)
            self.criteria = config["pipeline"]["criteria_list"]
        self.report = report
        self.candidate_id = candidate_id
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


    def json_report(self):
        for crit in self.criteria:
            # Fetch the question and description for a category from the json template file
            self.temp_json[crit]["initial_assessment"] = self.report[crit]["assessment"]

        json_report_path=f"./reports/JSON report for {self.candidate_id}_req_ID_{self.timestamp}.json"

        with open(json_report_path, "w") as e:
            json.dump(self.temp_json, e, indent=4)

        return json_report_path

    def full_report(self):
        full_report_path = f"./full_reports/Full_Report for {self.candidate_id}_req_ID_{self.timestamp}.json"
        with open(full_report_path, "w") as e:
            json.dump(self.report, e, indent=4)
        return full_report_path



