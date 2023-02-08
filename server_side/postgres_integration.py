


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

    def get_all_available_users_list(self):
        """
        Extracts all existing users from Postgres DB and returns as a list
        :return: list
        """

        return self.users_list


    def get_users_hashed_password(self, username):
        return self.credentials[username]