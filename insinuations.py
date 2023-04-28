from lxml import html 
import database
import datetime
import requests
import os

def get_sics(db: database.PayGapDatabase, url = "https://resources.companieshouse.gov.uk/sic/"):
    req = requests.get(url)
    tree = html.fromstring(req.content.decode())
    bigtable = tree.xpath("/html/body/main/table/tbody")[0]
    for tr_elem in bigtable.getchildren():
        td_code, td_description = tr_elem

        if td_code.getchildren() != []:
            # if contains a <strong> element which indicates a section
            current_section_code = td_code.getchildren()[0].text.replace("Section ", "").strip()
            current_section_description = td_description.getchildren()[0].text.strip()

            db.append_sic_sections(current_section_code, current_section_description)

        else:
            sic_code = int(td_code.text)
            sic_desc = td_description.text.rstrip()
            db.append_sic(sic_code, sic_desc, current_section_code)

def get_companyinfo_url(company_number, url = "https://find-and-update.company-information.service.gov.uk/company/%s"):
    if company_number.isdigit():
        company_number = "%08d" % int(company_number)

    return url % company_number

def lookup_company(company_number):
    company = {}
    req = requests.get(
        get_companyinfo_url(company_number),
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/534.50.2 (KHTML, like Gecko) Version/5.0.6 Safari/533.22.3'}
    )

    if req.status_code not in [200, 404]:
        raise ConnectionError("Couldn't connect- it %d'd. Was looking for company %s" % (req.status_code, company_number))

    tree = html.fromstring(req.content.decode())

    status_elem = tree.xpath('//*[@id="company-status"]')
    if len(status_elem) == 1:
        company["status"] = status_elem[0].text.strip()
    else:
        company["status"] = None

    incorp_elem = tree.xpath('//*[@id="company-creation-date"]')
    if len(incorp_elem) == 1:
        company["incorporated"] = datetime.datetime.strptime(incorp_elem[0].text.strip(), "%d %B %Y")
    else:
        company["incorporated"] = None

    type_elem = tree.xpath('//*[@id="company-type"]')
    if len(type_elem) == 1:
        company["type_"] = type_elem[0].text.strip()
    else:
        company["type_"] = None

    company["sics"] = set()
    for i in range(9):
        sic_elem = tree.xpath('//*[@id="sic%d"]' % i)
        if len(sic_elem) == 1:
            company["sics"].add(int(sic_elem[0].text.strip().split(" - ")[0]))
        else:
            break

    return company

if __name__ == "__main__":
    # if not os.path.exists(".docker"):
    #     import dotenv
    #     dotenv.load_dotenv(dotenv_path = "db.env")
    #     host = "srv.home"
    # else:
    #     host = "db"

    # with database.PayGapDatabase(host = host) as db:
    #     get_sics(db)
    print(lookup_company("02838054"))