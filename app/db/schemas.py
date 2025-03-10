from pydantic import BaseModel, Field

class MessageRequestSignUP(BaseModel):
    phone_number: str = Field(default="+917389058485")
    agent_id: str = Field(default="")
    full_name: str = Field(default="agent_full_name")
    broker_name: str = Field(default="")
    type: str = Field(default="buyer")
    listing_realtor_msg: str = Field(default="")


class CreatebookingRequest(BaseModel):
    buyer_agent_phone_number: str = Field(default="+917389058485")
    address: str = Field(default="booking_address_test")
    mls_number: str = Field(default="mls_number_test")
    buyer_selected_date: str = Field(default="date_test")
    buyer_selected_time: str = Field(default="time_test")
    listing_agent_phone_number: str = Field(default="")
    listing_agent_session_id: str = Field(default="")
    status: str = Field(default="pending")

class BuyerRealtorSignUP(BaseModel):
    full_name: str = Field(default="")
    agent_id: str = Field(default="")
    broker_name: str = Field(default="")
    phone_number: str = Field(default="")

class ListingRealtorSignUP(BaseModel):
    booking_address: str = Field(default="")
    mls_number: str = Field(default="")
    date: str = Field(default="")
    time: str = Field(default="")
    buyer_agent_phone_number: str = Field(default="")

class BuyerRealtorConfirmation(BaseModel):
    phone_number: str = Field(default="")
    mls_number: str = Field(default="")
    booking_id: str = Field(default="")
    date: str = Field(default="")
    time: str = Field(default="")
    confirmation: str = Field(default="")

class ListingRealtorConfirmation(BaseModel):
    confirmation: str = Field(default="")
    date: str = Field(default="")
    time: str = Field(default="")
    session_id: str = Field(default="")

class GetBooking(BaseModel):
    phone_number: str = Field(default="")
    booking_id: str = Field(default="")
    mls_number: str = Field(default="")