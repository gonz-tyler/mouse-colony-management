import mysql.connector
import environ

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()  # Load environment variables from a .env file

host = env("DB_HOST", default="localhost")
user = env("DB_USER", default="root")
passwd = env("DB_PASSWORD", default="")

dataBase = mysql.connector.connect(

    host=host,
    user=user,
    passwd=passwd,

)

cursorObject = dataBase.cursor()

try:
    cursorObject.execute("CREATE DATABASE mouse_colony_db")
    print("Database set successfully")
except:
    print("Error creating database")
