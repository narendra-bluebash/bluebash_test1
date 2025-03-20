from app.utils.log_utils import setup_logger

logger = setup_logger("properties_service")

def get_property_by_address_or_mls_number(mls_number, address):
    if mls_number in ["123", "456", "789", "123456"]:
        response = {
            "streetaddress": "123 Main St, San Francisco, CA 94105",
            "mls_number": mls_number,
            "price": "$1,000,000",
            "bedrooms": "3",
            "bathrooms": "2",
            "sqft": "1,500",
            "lot_size": "0.25",
            "year_built": "2000",
            "description": "This is a beautiful 3 bedroom, 2 bathroom home with 1,500 sqft of living space on a 0.25 acre lot. The home was built in 2000 and is listed for $1,000,000.",
            "agent_name": "Bob",
            "agent_phone": "+917347256305"
        }
    elif mls_number == "654321":
        response = {
            "streetaddress": "456 Elm St, San Francisco, CA 94105",
            "mls_number": mls_number,
            "price": "$1,500,000",
            "bedrooms": "4",
            "bathrooms": "3",
            "sqft": "2,000",
            "lot_size": "0.5",
            "year_built": "2010",
            "description": "This is a beautiful 4 bedroom, 3 bathroom home with 2,000 sqft of living space on a 0.5 acre lot. The home was built in 2010 and is listed for $1,500,000.",
            "agent_name": "Bob1",
            "agent_phone": "+917347256302"
        }
    elif address == "321 Oak St, San Francisco, CA 94105":
        response = {
            "streetaddress": address,
            "mls_number": "789012",
            "price": "$2,000,000",
            "bedrooms": "5",
            "bathrooms": "4",
            "sqft": "2,500",
            "lot_size": "0.75",
            "year_built": "2020",
            "description": "This is a beautiful 5 bedroom, 4 bathroom home with 2,500 sqft of living space on a 0.75 acre lot. The home was built in 2020 and is listed for $2,000,000.",
            "agent_name": "Bob2",
            "agent_phone": "+917347256303"
        }
    else:
        logger.error(f"Property not found for address: {address}, mls_number: {mls_number}")
        response = None
    return response