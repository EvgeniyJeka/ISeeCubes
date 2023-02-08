import configparser
import logging

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import sqlalchemy as db
from sqlalchemy import exc

try:
    from server_side.objects_mapped import UsersMapped
    from server_side import objects_mapped

except ModuleNotFoundError:
    from objects_mapped import UsersMapped
    import objects_mapped

class PostgresIntegration:

    # Special users
    CHAT_GPT_USER = "ChatGPT"
    ADMIN_USER = "Admin"

    # Will be taken from SQL DB
    users_list = ["Lisa", "Avi", "Tsahi", "Era", "Bravo", "Dariya", CHAT_GPT_USER, ADMIN_USER]

    # Move this to SQL DB
    credentials = {"Lisa": hash("TestMe"),
                   "Avi": hash("MoreMoreMore"),
                   "Era": hash("Come on"),
                   "Tsahi": hash("Virtual Environment"),
                   "Admin": hash("AdminPassword")}

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
            self.create_validate_tables()

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
            # engine = create_engine('postgresql+psycopg2://scott:tiger@localhost/mydatabase')

            # Create an engine object.
            engine = create_engine(url, echo=True)

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

        # Creating the 'offers' table if not exists - column for each "Offer" object property.
        if 'users' not in tables:
            logging.warning("Logs: 'offers' table is missing! Creating the 'offers' table")
            self.users_table = UsersMapped()
            objects_mapped.Base.metadata.create_all(self.engine)

    def get_all_available_users_list(self):
        """
        Extracts all existing users from Postgres DB and returns as a list
        :return: list
        """

        return self.users_list


    def get_users_hashed_password(self, username):
        return self.credentials[username]