from dataclasses import dataclass
import operator
import datetime
import pymysql
import os

@dataclass
class PayGapDatabase:
    
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



if __name__ == "__main__":
    if not os.path.exists(".docker"):
        import dotenv
        dotenv.load_dotenv(dotenv_path = "db.env")
        host = "srv.home"
    else:
        host = "db"

    with PayGapDatabase(host = host) as db:
        print(db.get_years())
        print(db.get_pay_by_sic_section("bonuses", None))

