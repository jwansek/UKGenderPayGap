from dataclasses import dataclass
import operator
import datetime
import pymysql
import pandas
import app
import os

@dataclass
class PayGapDatabase:
    
    postcode_lookup_obj = None
    host: str = "db"
    user: str = "root"
    passwd: str = None
    db: str = "paygap"
    port: int = 3306

    def __enter__(self):
        if self.passwd is None:
            self.passwd = os.environ["MYSQL_ROOT_PASSWORD"]
            
        try:
            self.__connection = self.__get_connection()
        except Exception as e:
            print(e)
            if e.args[0] == 1049:
                self.__connection = self.__build_db()
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def __get_connection(self):
        return pymysql.connect(
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.passwd,
            charset = "utf8mb4",
            database = self.db
        )

    def __build_db(self):
        print("Building database...")
        self.__connection = pymysql.connect(
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.passwd,
            charset = "utf8mb4",
        )
        with self.__connection.cursor() as cursor:
            # unsafe:
            cursor.execute("CREATE DATABASE %s" % self.db)
            cursor.execute("USE %s" % self.db)

            cursor.execute("""
            CREATE TABLE sic_sections(
                sic_section_id CHAR(1) NOT NULL PRIMARY KEY,
                sic_section_name VARCHAR(128) NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE sic(
                sic_code INT UNSIGNED NOT NULL PRIMARY KEY,
                sic_description VARCHAR(512) NOT NULL,
                sic_section CHAR(1) NOT NULL,
                FOREIGN KEY (sic_section) REFERENCES sic_sections(sic_section_id)
            );
            """)

            cursor.execute("""
            CREATE TABLE employer(
                company_number CHAR(8) NOT NULL PRIMARY KEY,
                name VARCHAR(512) NOT NULL,
                address TEXT NOT NULL,
                postcode VARCHAR(8) NOT NULL,
                policy_link VARCHAR(256) NULL,
                responsible_person VARCHAR(128) NOT NULL,
                size VARCHAR(20) NOT NULL,
                current_name VARCHAR(512) NULL,
                status VARCHAR(32) NULL,
                type_ VARCHAR(128) NULL,
                incorporated DATETIME NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE employer_sic(
                company_number CHAR(8) NOT NULL,
                sic_code INT UNSIGNED NOT NULL,
                PRIMARY KEY (company_number, sic_code),
                FOREIGN KEY (company_number) REFERENCES employer(company_number),
                FOREIGN KEY (sic_code) REFERENCES sic(sic_code)
            );
            """)

            cursor.execute("""
            CREATE TABLE pay(
                pay_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                company_number CHAR(8) NOT NULL,
                source VARCHAR(64) NOT NULL,
                date_submitted DATETIME NOT NULL,
                DiffMeanHourlyPercent DECIMAL(8,3) NOT NULL,
                DiffMedianHourlyPercent DECIMAL(8,3) NOT NULL,
                DiffMeanBonusPercent DECIMAL(8,3) NOT NULL,
                DiffMedianBonusPercent DECIMAL(8,3) NOT NULL,
                MaleBonusPercent DECIMAL(8,3) NOT NULL,
                FemaleBonusPercent DECIMAL(8,3) NOT NULL,
                MaleLowerQuartile DECIMAL(8,3) NOT NULL,
                FemaleLowerQuartile DECIMAL(8,3) NOT NULL,
                MaleLowerMiddleQuartile DECIMAL(8,3) NOT NULL,
                FemaleLowerMiddleQuartile DECIMAL(8,3) NOT NULL,
                MaleUpperMiddleQuartile DECIMAL(8,3) NOT NULL,
                FemaleUpperMiddleQuartile DECIMAL(8,3) NOT NULL,
                MaleTopQuartile DECIMAL(8,3) NOT NULL,
                FemaleTopQuartile DECIMAL(8,3) NOT NULL,
                FOREIGN KEY (company_number) REFERENCES employer(company_number)
            );
            """)

            self.__connection.commit()
            return self.__connection

    def _wrap_percent(self, word):
        return "%%%s%%" % (word)

    def append_sic_sections(self, section_id, description):
        # print("Section ID: '%s', Description: '%s'" % (section_id, description))
        with self.__connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sic_sections VALUES (%s, %s) ON DUPLICATE KEY UPDATE sic_section_name = %s;
            """, (section_id, description, description))
        self.__connection.commit()

    def append_sic(self, code, description, section_id):
        print("Appended code %d (%s) under section %s" % (code, description, section_id))
        with self.__connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sic VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE sic_description = %s, sic_section = %s;
            """, (code, description, section_id, description, section_id))
        self.__connection.commit()

    def append_employer(self, company_number, name, address, postcode, policy_link, responsible_person, size, current_name, \
        status, type_, incorporated, sics):

        # print("incorporated: %s" % str(incorporated))
        # print("sics", sics)
        # print("name: %s" % name)
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO employer (company_number, name, address, postcode, policy_link, responsible_person, size, current_name, status, type_, incorporated) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            name = %s, address = %s, postcode = %s, policy_link = %s, responsible_person = %s, size = %s, 
            current_name = %s, status = %s, type_ = %s, incorporated = %s;
            """, (
                company_number, name, address, postcode, policy_link, responsible_person, size, current_name, status, type_, incorporated,
                name, address, postcode, policy_link, responsible_person, size, current_name, status, type_, incorporated
            ))
            # sql = """INSERT INTO employer (company_number, name, address, postcode, policy_link, responsible_person, size, current_name, status, type_, incorporated) 
            # VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');""" % (
            #     company_number, name, address, postcode, policy_link, responsible_person, size, current_name, status, type_, incorporated
            # )
            # print(sql)

        self.append_employer_sics(company_number, sics)
        self.__connection.commit()

    def append_pay_info(self, company_number, source, date_submitted, diff_mean_hourly_percent, diff_median_hourly_percent, \
        diff_mean_bonus_percent, diff_median_bonus_percent, male_bonus_percent, female_bonus_percent, male_lower_quartile, \
        female_lower_quartile, male_lower_middle_quartile, female_lower_middle_quartile, male_upper_middle_quartile, \
        female_upper_middle_quartile, male_top_quartile, female_top_quartile):

        try:
            float(diff_mean_hourly_percent)
        except ValueError:
            diff_mean_hourly_percent = None


        with self.__connection.cursor() as cursor:
            cursor.execute("DELETE FROM pay WHERE company_number = %s AND source = %s;", (company_number, source))

            try:
                cursor.execute("""
                INSERT INTO pay (company_number, source, date_submitted, DiffMeanHourlyPercent, DiffMedianHourlyPercent,
                DiffMeanBonusPercent, DiffMedianBonusPercent, MaleBonusPercent, FemaleBonusPercent, MaleLowerQuartile,
                FemaleLowerQuartile, MaleLowerMiddleQuartile, FemaleLowerMiddleQuartile, MaleUpperMiddleQuartile,
                FemaleUpperMiddleQuartile, MaleTopQuartile, FemaleTopQuartile) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
                """, (
                    company_number, source, date_submitted, diff_mean_hourly_percent, diff_median_hourly_percent,
                    diff_mean_bonus_percent, diff_median_bonus_percent, male_bonus_percent, female_bonus_percent, male_lower_quartile,
                    female_lower_quartile, male_lower_middle_quartile, female_lower_middle_quartile, male_upper_middle_quartile,
                    female_upper_middle_quartile, male_top_quartile, female_top_quartile
                ))
            except pymysql.err.DataError:
                return

        self.__connection.commit()


    def append_employer_sics(self, company_number, sics):
        with self.__connection.cursor() as cursor:
            cursor.execute("DELETE FROM employer_sic WHERE company_number = %s", (company_number, ))

            for sic in sics:
                cursor.execute("SELECT * FROM sic WHERE sic_code = %s", (sic, ))
                if cursor.fetchone() != None:
                    cursor.execute("INSERT INTO employer_sic VALUES (%s, %s);", (company_number, sic))

    def search_company(self, company_prefix):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT name, company_number FROM employer 
            WHERE name LIKE '%s' OR current_name LIKE '%s';
            """ % (
                self._wrap_percent(company_prefix),
                self._wrap_percent(company_prefix)
            ))

            return [(i[0].title(), i[1]) for i in cursor.fetchall()]

    def get_company_types(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT type_ FROM employer WHERE type_ IS NOT NULL;")
            return [i[0] for i in cursor.fetchall()]

    def get_company_sizes(self):
        return [
            "Not Provided",
            "Less than 250",
            "250 to 499",
            "500 to 999",
            "1000 to 4999",
            "5000 to 19,999",
            "20,000 or more"
        ]

    def get_sic_sections(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT sic_section_name FROM sic_sections")
            return [i[0] for i in cursor.fetchall()]

    def _source_name_to_year(self, source):
        return os.path.splitext(source)[0].split("-")[-1].strip().replace("to", "-")

    def get_pay_by_year(self, pay_type, sic_section_name = None, employer_type = None, employer_size = None):
        sql = "SELECT source, -AVG("
        if pay_type.lower() == "hourly":
            sql += "DiffMedianHourlyPercent"
        elif pay_type.lower() == "bonuses":
            sql += "DiffMedianBonusPercent"
        sql += ") FROM pay"

        subqueries = []
        args = []
        if sic_section_name is not None:
            subqueries.append("""
            company_number IN (
                SELECT DISTINCT company_number FROM employer_sic WHERE sic_code IN (
                    SELECT DISTINCT sic_code FROM sic WHERE sic_section = (
                        SELECT sic_section_id FROM sic_sections WHERE sic_section_name = %s
                    )
                )
            )""")
            args.append(sic_section_name)
        if employer_type is not None:
            subqueries.append("""
            company_number IN (
                SELECT company_number FROM employer WHERE type_ = %s
            )
            """)
            args.append(employer_type)
        if employer_size is not None:
            subqueries.append("""
            company_number IN (
                SELECT company_number FROM employer WHERE size = %s
            )
            """)
            args.append(employer_size)

        with self.__connection.cursor() as cursor:
            if sic_section_name is not None or employer_type is not None or employer_size is not None:
                sql += " WHERE {}".format(" OR ".join(subqueries))

                sql += " GROUP BY source ORDER BY source;"
                cursor.execute(sql, tuple(args))

            else:
                sql += " GROUP BY source ORDER BY source;"
                cursor.execute(sql)

            # print(sql)
            # print(tuple(args))
            return [(self._source_name_to_year(i[0]), float(i[1])) for i in cursor.fetchall()]

    def get_years(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT source FROM pay;")
            return [self._source_name_to_year(i[0]) for i in cursor.fetchall()]

    def get_pay_for_employer(self, pay_type, company_id,):
        for section_name in self.get_sic_sections():
            sql = "SELECT source, -AVG("
            if pay_type.lower() == "hourly":
                sql += "DiffMedianHourlyPercent"
            elif pay_type.lower() == "bonuses":
                sql += "DiffMedianBonusPercent"
            sql += """
            ) FROM pay WHERE company_number = %s GROUP BY source ORDER BY source;
            """
            with self.__connection.cursor() as cursor:
                cursor.execute(sql, (company_id, ))
                return [[i[0], float(i[1])] for i in cursor.fetchall()]
    
    def get_pay_by_sic_section(self, pay_type, year = None):
        pay = []
        for section_name in self.get_sic_sections():
            sql = "SELECT -AVG("
            if pay_type.lower() == "hourly":
                sql += "DiffMedianHourlyPercent"
            elif pay_type.lower() == "bonuses":
                sql += "DiffMedianBonusPercent"
            sql += """
            ) FROM pay WHERE company_number IN (
                SELECT DISTINCT company_number FROM employer_sic WHERE sic_code IN (
                    SELECT DISTINCT sic_code FROM sic WHERE sic_section = (
                        SELECT sic_section_id FROM sic_sections WHERE sic_section_name = %s
                    )
                )
            )
            """

            if year is not None:
                sql += " AND source LIKE %s"

            sql += ";"

            with self.__connection.cursor() as cursor:
                # print(sql, (section_name, "%" + year.replace("to", "-") + "%"))
                if year is None:
                    cursor.execute(sql, (section_name, ))
                else:
                    cursor.execute(sql, (section_name, "%" + year.replace("-", "to") + "%"))

                f = cursor.fetchone()[0]
                if f is not None:
                    pay.append((section_name, float(f)))
        
        return sorted(pay, key = operator.itemgetter(1), reverse = True)

    def get_heatmap_data(self, pay_type, year = None):
        sql = "SELECT insinuated_loc, COUNT(insinuated_loc), -AVG("
        if pay_type.lower() == "hourly":
            sql += "DiffMedianHourlyPercent"
        elif pay_type.lower() == "bonuses":
            sql += "DiffMedianBonusPercent"
        sql += """
        ) FROM employer INNER JOIN pay ON pay.company_number = employer.company_number
        WHERE insinuated_loc_type IS NOT NULL
        """
        if year is not None:
            sql += " AND source LIKE %s"

        sql += " GROUP BY insinuated_loc;"

        with self.__connection.cursor() as cursor:
            if year is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, ("%" + year.replace("-", "to") + "%", ))

            return [[i[0], i[1], float(i[2])] for i in cursor.fetchall()]

    def _get_postcode_lookup_obj(self, path_):
        return pandas.read_csv(path_)

    def _get_counties(self):
        return {feature["properties"]["name"] for feature in app.UK_GEOJSON["features"]}

    def append_counties(self, path_):
        if self.postcode_lookup_obj is None:
            self.postcode_lookup_obj = self._get_postcode_lookup_obj(path_)

        counties = self._get_counties()
        postcodes = self._get_postcodes()

        with self.__connection.cursor() as cursor:

            cursor.execute("ALTER TABLE employer ADD COLUMN IF NOT EXISTS insinuated_loc VARCHAR(69) DEFAULT NULL;")
            cursor.execute("ALTER TABLE employer ADD COLUMN IF NOT EXISTS insinuated_loc_type VARCHAR(25) DEFAULT NULL;")
        
            for i, j in enumerate(postcodes, 1):
                id_, postcode = j
                found_locations = self.postcode_lookup_obj[
                    (self.postcode_lookup_obj["Postcode 1"] == postcode) | 
                    (self.postcode_lookup_obj["Postcode 2"] == postcode) | 
                    (self.postcode_lookup_obj["Postcode 3"] == postcode)
                ]
                if len(found_locations) == 1:
                    county, la = found_locations[["County Name", "Local Authority Name"]].values[0]
                    if la in counties:
                        cursor.execute("UPDATE employer SET insinuated_loc = %s, insinuated_loc_type = 'Local Authority' WHERE company_number = %s", (la, id_))

                        print("[%d/%d] Using local authority '%s' for postcode '%s'" % (i, len(postcodes), la, postcode))
                    elif county in counties:
                        cursor.execute("UPDATE employer SET insinuated_loc = %s, insinuated_loc_type = 'County' WHERE company_number = %s", (county, id_))

                        print("[%d/%d] Using county '%s' for postcode '%s'" % (i, len(postcodes), county, postcode))
                    elif "Northamptonshire" in la:
                        print("Manually fixing Northamptonshire...")
                        cursor.execute("UPDATE employer SET insinuated_loc = %s, insinuated_loc_type = 'County' WHERE company_number = %s", ("Northamptonshire", id_))
                    elif "Bournemouth" in la:
                        print("Manually fixing Bournemouth...")
                        cursor.execute("UPDATE employer SET insinuated_loc = %s, insinuated_loc_type = 'County' WHERE company_number = %s", ("Bournemouth", id_))
                    else:
                        print("[%d/%d] Didn't recoginse the local authority '%s' or the county '%s'" % (i, len(postcodes), la, county))
                else:
                    print("[%d/%d] Couldn't find a county for postcode '%s' (company id '%s')" % (i, len(postcodes), postcode, id_))

                # break
        self.__connection.commit()

    def _get_postcodes(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT company_number, TRIM(SUBSTRING_INDEX(address, ',', -1)) FROM employer;")
            return cursor.fetchall()

    def get_pay_by_employer_size(self, pay_type, year = None):
        sql = "SELECT size, COUNT(size), -AVG("
        if pay_type.lower() == "hourly":
            sql += "DiffMedianHourlyPercent"
        elif pay_type.lower() == "bonuses":
            sql += "DiffMedianBonusPercent"
        sql += ") FROM employer INNER JOIN pay ON pay.company_number = employer.company_number"
        if year is not None:
            sql += " AND source LIKE %s"
        sql += " GROUP BY size ORDER BY size;"

        with self.__connection.cursor() as cursor:
            if year is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, ("%" + year.replace("-", "to") + "%", ))

            return sorted([(i[0], i[1], float(i[2])) for i in cursor.fetchall()], key = lambda e: self.get_company_sizes().index(e[0]))

    def get_pay_by_employer_type(self, pay_type, year = None):
        sql = "SELECT type_, -AVG("
        if pay_type.lower() == "hourly":
            sql += "DiffMedianHourlyPercent"
        elif pay_type.lower() == "bonuses":
            sql += "DiffMedianBonusPercent"
        sql += ") FROM employer INNER JOIN pay ON pay.company_number = employer.company_number WHERE type_ IS NOT NULL"
        if year is not None:
            sql += " AND source LIKE %s"
        sql += " GROUP BY type_;"

        with self.__connection.cursor() as cursor:
            if year is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, ("%" + year.replace("-", "to") + "%", ))

            return sorted([(i[0], float(i[1])) for i in cursor.fetchall()], key = operator.itemgetter(1), reverse = True)

    def get_employer_details(self, employer_id):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT name, address, postcode, policy_link, responsible_person, size, status, type_, incorporated FROM employer WHERE company_number = %s;", (employer_id, ))
            o = cursor.fetchone()

        return {
            "Employer Name": o[0].title(),
            "Address": o[1],
            "Postcode": o[2],
            "Policy Link": o[3],
            "Named responsible person": o[4],
            "Number of Employees": o[5],
            "Status": o[6],
            "Employer Type": o[7],
            "Incorporated Date": o[8],
            "Companies House Link": "https://find-and-update.company-information.service.gov.uk/company/" + employer_id
        }



if __name__ == "__main__":
    if not os.path.exists(".docker"):
        import dotenv
        dotenv.load_dotenv(dotenv_path = "db.env")
        host = "srv.home"
    else:
        host = "db"

    with PayGapDatabase(host = host) as db:
        # print(db.get_years())
        # print(db.get_pay_by_sic_section("bonuses", None))
        # print(db.get_pay_for_employer("bonuses", "RC000651"))
        print(db.get_employer_details("RC000651"))
        # print(db.append_counties())

