import configparser
import json
import logging
import hashlib

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import sqlalchemy as db
from sqlalchemy import exc
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
            self.users_table = UsersMapped()
            objects_mapped.Base.metadata.create_all(self.engine)

            logging.info(f"Filling the {USERS_TABLE_NAME} with the default data from the users.json file.")
            objects_mapped.Base.metadata.create_all(self.engine)

            # Inserting the default test users

            self.session.add_all(self.read_user_creds_from_file(users_list_file_path))
            self.session.commit()

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


    def read_user_creds_from_file(self, file_path):

        user_mapped_objects = []

        with open(file_path, "r") as f:
            file_content = f.read()

        file_content = json.loads(file_content)
        users_vs_creds = file_content['users']

        for item in users_vs_creds:
            print(f"User {item['username']} , "
                  f"plain password: {item['password']} - {type(item['username'])}, hashed password: {self.hash_string(item['password'])}")

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

    def hash_string(self, input_: str):
        hash_object = hashlib.sha256(input_.encode())
        return hash_object.hexdigest()




if __name__ == "__main__":
    config_file_path = "./config.ini"
    postgres_integration = PostgresIntegration(config_file_path)

    users_creds = postgres_integration.get_table_content(USERS_TABLE_NAME)
    print(users_creds)