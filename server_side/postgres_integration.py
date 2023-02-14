import configparser
import json
import logging
import hashlib

import sqlalchemy
from sqlalchemy import create_engine, MetaData, exc, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

try:
    from server_side.objects_mapped import UsersMapped
    from server_side import objects_mapped

except ModuleNotFoundError:
    from objects_mapped import UsersMapped
    import objects_mapped

# Will be moved to config.ini
users_list_file_path = "./users.json"

# Will be moved to constants file
USERS_TABLE_NAME = 'users'
ACTIVE_USER_STATUS = 1
BLOCKED_USER_STATUS = 0


class PostgresIntegration:
    # Special users
    CHAT_GPT_USER = "ChatGPT"
    ADMIN_USER = "Admin"

    users_list = None
    credentials = None

    # # Will be taken from SQL DB
    # users_list = ["Lisa", "Avi", "Tsahi", "Era", "Bravo", "Dariya", CHAT_GPT_USER, ADMIN_USER]
    #
    # # Move this to SQL DB
    # credentials = {"Lisa": hash("TestMe"),
    #                "Avi": hash("MoreMoreMore"),
    #                "Era": hash("Come on"),
    #                "Tsahi": hash("Virtual Environment"),
    #                "Admin": hash("AdminPassword")}

    def __init__(self, config_file_path):

        # Reading DB name, host and credentials from config
        config = configparser.ConfigParser()
        config.read(config_file_path)
        hst = config.get("SQL_DB", "host")
        usr = config.get("SQL_DB", "user")
        pwd = config.get("SQL_DB", "password")
        db_name = config.get("SQL_DB", "db_name")

        try:
            self.cursor, self.engine = self.connect_me(hst, usr, pwd, db_name)
            # Initiating a session
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            self.metadata = db.MetaData(bind=self.engine)

            self.create_validate_tables()
            self.fetch_credentials()

        except TypeError:
            logging.critical("SQL DB - Failed to connect, please verify SQL DB container is running")

    # Connect to DB
    def connect_me(self, hst, usr, pwd, db_name):
        """
        This method is used to establish a connection to MySQL DB.
        Credentials , host and DB name are taken from "config.ini" file.
        :param hst: host
        :param usr: user
        :param pwd: password
        :param db_name: DB name
        :return: SqlAlchemy connection (cursor)
        """

        try:

            url = f'postgresql+psycopg2://{usr}:{pwd}@{hst}:5432/{db_name}'

            # Create an engine object.
            engine = create_engine(url, echo=True, isolation_level="READ UNCOMMITTED")

            # Create database if it does not exist.
            if not database_exists(engine.url):
                create_database(engine.url)
                cursor = engine.connect()
                return cursor, engine
            else:
                # Connect the database if exists.
                cursor = engine.connect()
                return cursor, engine

        # Wrong Credentials error
        except sqlalchemy.exc.OperationalError as e:
            logging.critical("SQL DB -  Can't connect, verify credentials and host, verify the server is available")
            logging.critical(e)

        # General error
        except Exception as e:
            logging.critical("SQL DB - Failed to connect, reason is unclear")
            logging.critical(e)

    def hash_string(self, input_: str):
        hash_object = hashlib.sha256(input_.encode())
        return hash_object.hexdigest()

    def create_fill_users_table(self):
        self.users_table = UsersMapped()
        #objects_mapped.Base.metadata.create_all(self.engine)

        logging.info(f"Filling the {USERS_TABLE_NAME} with the default data from the users.json file.")
        objects_mapped.Base.metadata.create_all(self.engine)

        # Inserting the default test users
        self.session.add_all(self.read_user_creds_from_file(users_list_file_path))
        self.session.commit()

        return True

    def create_validate_tables(self):
        """
        This method can be used to validate, that all needed table are exist.
        If they aren't the method will create them
        :param engine: Sql Alchemy engine
        """
        tables = self.engine.table_names()

        # Creating the 'users' table if not exists - column for each "User" object property.
        if USERS_TABLE_NAME not in tables:
            logging.warning(f"{USERS_TABLE_NAME} table is missing! Creating the {USERS_TABLE_NAME} table")

            if not self.create_fill_users_table():
                logging.error(f"Error! Failed to create the {USERS_TABLE_NAME} table!")
                raise ValueError(f"Error! Failed to create the {USERS_TABLE_NAME} table!")

        # Compare the content of the table to the file content. If it doesn't identical - drop the table
        # and create it from scratch, insert all info from the file
        else:
            if not self.compare_credentials_sql_against_file(users_list_file_path):
                logging.warning(f"The content of the '{USERS_TABLE_NAME} differs from the file content."
                                f" Renewing the table.")

                # Base = declarative_base(bind=self.engine)
                #
                #
                # # drop the table
                # Base.metadata.drop_all(self.engine)

                # table = db.Table(USERS_TABLE_NAME, self.metadata, autoload=True)
                # objects_mapped.Base.metadata.drop_all()
                # objects_mapped.Base.metadata.create_all(self.engine)



                # table = db.Table(USERS_TABLE_NAME, self.metadata, autoload=True)
                # table.drop()
                # self.metadata.execute(checkfirst=True)
                #metadata = db.MetaData()


                # # SQL Alchemy table instance is passed to the "fill_table" method
                # table = db.Table(USERS_TABLE_NAME, self.metadata, autoload=True)
                # table.drop()
                # self.metadata.execute(checkfirst=True)
                #
                print("Checkpoint!!")


                # if not self.create_fill_users_table():
                #     logging.error(f"Error! Failed to create the {USERS_TABLE_NAME} table!")
                #     raise ValueError(f"Error! Failed to create the {USERS_TABLE_NAME} table!")

    def get_table_content(self, table):
        """
        Get table content from DB
        :param table: table name, String
        :return: tuple
        """

        metadata = db.MetaData()
        table_ = db.Table(table, metadata, autoload=True, autoload_with=self.engine)

        query = db.select([table_])
        ResultProxy = self.cursor.execute(query)
        result = ResultProxy.fetchall()

        return result

    def get_all_available_users_list(self):
        """
        Extracts all existing users from Postgres DB and returns as a list
        :return: list
        """

        return list(self.credentials.keys())

    def get_users_hashed_password(self, username):
        return self.credentials[username]

    def compare_credentials_sql_against_file(self, users_list_file_path):
        """
           This function compares the credentials of users stored in a PostgreSQL database with those stored in a JSON file.

           :param users_list_file_path: The path to the JSON file containing the users' credentials to be compared.
           :type users_list_file_path: str
           :return: True if the users' credentials in the database and the file match, False otherwise.
           :rtype: bool
        """
        users_creds_table = self.get_table_content(USERS_TABLE_NAME)

        with open(users_list_file_path, "r") as f:
            file_content = f.read()

        file_content = json.loads(file_content)
        users_creds_file = file_content['users']

        if len(users_creds_table) != len(users_creds_file):
            return False

        users_creds_table.sort(key=lambda x: x[0])
        users_creds_file.sort(key=lambda x: x['id'])

        for j in range(0, len(users_creds_table)):
            table_record = users_creds_table[j]
            file_item = users_creds_file[j]

            if file_item['id'] != table_record[0]:
                return False
            if file_item['username'] != table_record[1]:
                return False
            if self.hash_string(file_item['password']) != table_record[2]:
                return False

        return True

    def read_user_creds_from_file(self, file_path):

        user_mapped_objects = []

        with open(file_path, "r") as f:
            file_content = f.read()

        file_content = json.loads(file_content)
        users_vs_creds = file_content['users']

        for item in users_vs_creds:
            print(f"User {item['username']} , "
                  f"plain password: {item['password']} - {type(item['username'])},"
                  f" hashed password: {self.hash_string(item['password'])}")

            user_mapped_objects.append(UsersMapped(id=item['id'],
                                                   user_name=item['username'],
                                                   user_password=self.hash_string(item['password']),
                                                   user_status=ACTIVE_USER_STATUS))

        return user_mapped_objects

    def fetch_credentials(self):
        try:
            result = {}
            data_from_sql = self.get_table_content(USERS_TABLE_NAME)

            for record in data_from_sql:
                result[record[1]] = record[2]

            self.credentials = result
            return True

        except Exception as e:
            logging.error(f"Failed to fetch credentials from SQL - {e}")
            return False




if __name__ == "__main__":
    config_file_path = "./config.ini"

    postgres_integration = PostgresIntegration(config_file_path)
    users_creds_table = postgres_integration.get_table_content(USERS_TABLE_NAME)

    # with open(users_list_file_path, "r") as f:
    #     file_content = f.read()
    #
    # file_content = json.loads(file_content)
    # users_creds_file = file_content['users']
    #
    # if len(users_creds_table) != len(users_creds_file):
    #     print(False)
    #
    # users_creds_table.sort(key=lambda x: x[0])
    # users_creds_file.sort(key=lambda x: x['id'])
    #
    print("Checkpoint 2")
    print(users_creds_table)
    # print(users_creds_file)
    #
    # for i in range(0, len(users_creds_table)):
    #     table_record = users_creds_table[i]
    #     file_item = users_creds_file[i]
    #
    #     if file_item['id'] != table_record[0]:
    #         print(False)
    #     if file_item['username'] != table_record[1]:
    #         print(False)
    #     if postgres_integration.hash_string(file_item['password']) != table_record[2]:
    #         print(False)
    #
    # print(True)
