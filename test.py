from app.db.mysql_db_crud import fetch_listings_by_mls_number
from app.utils.log_utils import setup_logger
import re

logger = setup_logger("test")

if __name__ == "__main__":
    mls_number = "R2357773"
    data = fetch_listings_by_mls_number(mls_number)
    logger.debug(data)