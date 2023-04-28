import insinuations
import database
import datetime
import time
import json
import csv
import sys
import os

def parse_csv(db, csv_path):
    insinuations.get_sics(db)

    with open(csv_path, "r") as f:
        num_lines = len(f.readlines())
    i = 0

    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        headers = next(reader)

        for name, id_, address, postcode, company_id, sic_codes, diff_mean_hourly_percent, diff_median_hourly_percent, \
            diff_mean_bonus_percent, diff_median_bonus_percent, male_bonus_percent, female_bonus_percent, male_lower_quartile, \
            female_lower_quartile, male_lower_middle_quartile, female_lower_middle_quartile, male_upper_middle_quartile, \
            female_upper_middle_quartile, male_top_quartile, female_top_quartile, policy_link, responsible_person, size, \
            current_name, submitted_after_deadline, duedate, submitted_date in reader:
            
            if company_id.strip() != "":
                try:
                    sic_codes = {int(i.strip()) for i in sic_codes.split(",")}
                except ValueError:
                    sic_codes = set()

                while True:
                    try:
                        company = insinuations.lookup_company(company_id)
                    except ConnectionError as e:
                        print("Couldn't connect... Error: '%s'... Waiting 20 seconds..." % str(e))
                        time.sleep(20)
                    else:
                        break

                company["sics"] = company["sics"].union(sic_codes)
                company["company_number"] = company_id
                company["name"] = name
                company["address"] = address
                company["postcode"] = postcode
                company["policy_link"] = policy_link
                company["responsible_person"] = responsible_person
                company["size"] = size
                company["current_name"] = current_name

                print("%.2f%%" % ((i / num_lines) * 100), company)
                print(
                    company_id, os.path.basename(csv_path), datetime.datetime.strptime(submitted_date, "%Y/%m/%d %H:%M:%S"), 
                    diff_mean_hourly_percent, diff_median_hourly_percent, diff_mean_bonus_percent, diff_median_bonus_percent, 
                    male_bonus_percent, female_bonus_percent, male_lower_quartile, female_lower_quartile, 
                    male_lower_middle_quartile, female_lower_middle_quartile, male_upper_middle_quartile, 
                    female_upper_middle_quartile, male_top_quartile, female_top_quartile
                )
                db.append_employer(**company)
                db.append_pay_info(
                    company_id, os.path.basename(csv_path), datetime.datetime.strptime(submitted_date, "%Y/%m/%d %H:%M:%S"), 
                    diff_mean_hourly_percent, diff_median_hourly_percent, diff_mean_bonus_percent, diff_median_bonus_percent, 
                    male_bonus_percent, female_bonus_percent, male_lower_quartile, female_lower_quartile, 
                    male_lower_middle_quartile, female_lower_middle_quartile, male_upper_middle_quartile, 
                    female_upper_middle_quartile, male_top_quartile, female_top_quartile
                )
                i += 1

                # break

if __name__ == "__main__":
    if not os.path.exists(".docker"):
        import dotenv
        dotenv.load_dotenv(dotenv_path = "db.env")
        host = "srv.home"
    else:
        host = "db"

    with database.PayGapDatabase(host = host) as db:
        parse_csv(db, sys.argv[1])