import mysql.connector
import re, os
from app.utils.log_utils import setup_logger
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger("mysql_db_crud")

db_config = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "pool_name": "mypool",
    "pool_size": 5,
}

pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def fetch_data(query, params=()):
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results

    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def fetch_listings_by_mls_number(mls_number):
    query = "SELECT * FROM mlsr_listings WHERE listingid = %s LIMIT 1;"
    params = (mls_number,)
    data = fetch_data(query, params)
    if not data:
        return None
    row = data[0]
    final_data = {"listingid": row[2], "status": row[3], "streetaddress": row[8], "listprice_2": str(row[20]), "remarks": row[26], "agent_email": row[208],
            "agent_name": row[209], "agent_phone": re.sub(r"\D", "", row[210]), "agent_id": row[212]}
    return final_data