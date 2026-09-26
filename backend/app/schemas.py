
from datetime import date, time
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)
    verification_channel: Literal["email", "phone"] = "email"

    @field_validator("phone")
    @classmethod
    def normalize_phone_input(cls, v):
        return v.strip() if v else v

    @field_validator("email")
    @classmethod
    def normalize_email_input(cls, v):
        return str(v).strip().lower() if v else v


class LoginIn(BaseModel):
    identifier: str = Field(min_length=3, max_length=255)
    password: str


class OTPRequestIn(BaseModel):
    channel: str
    destination: str
    purpose: str = "verification"

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v):
        if v not in {"email", "phone"}:
            raise ValueError("channel must be email or phone")
        return v

class OTPVerifyIn(OTPRequestIn):
    code: str = Field(pattern=r"^\d{6}$")



class CampusCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=160)
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(default="", max_length=120)
    pincode: str = Field(default="", max_length=12)
    email_domains: list[str] = Field(default_factory=list)
    description: str = Field(default="", max_length=4000)
    current_semester: str = Field(default="Current semester", max_length=80)


class CampusUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    slug: str | None = Field(default=None, min_length=2, max_length=160)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    pincode: str | None = Field(default=None, max_length=12)
    description: str | None = Field(default=None, max_length=4000)
    current_semester: str | None = Field(default=None, max_length=80)
    active: bool | None = None


class CampusDomainIn(BaseModel):
    domain: str = Field(min_length=3, max_length=120)


class CampusJoinIn(BaseModel):
    student_id: str = Field(default="", max_length=80)



class CampusVerificationReviewIn(BaseModel):
    note: str = Field(default="", max_length=2000)

class SellerApplyIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    bio: str = Field(default="", max_length=2000)

class AddressIn(BaseModel):
    label: str = Field(default="Personal", max_length=40)
    line1: str = Field(min_length=3, max_length=180)
    line2: str = Field(default="", max_length=180)
    locality: str = Field(default="", max_length=120)
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=120)
    pincode: str = Field(min_length=5, max_length=12)
    landmark: str = Field(default="", max_length=180)
    is_default: bool = False

class ListingImageIn(BaseModel):
    url: str
    alt: str = ""
    sort_order: int = 0

class ListingCreateIn(BaseModel):
    campus_slug: str
    title: str = Field(min_length=2, max_length=180)
    category: str = Field(min_length=2, max_length=80)
    subcategory: str = ""
    condition: str = "good"
    listing_type: str = "sell"
    price: Decimal = Field(ge=0)
    rental_price: Decimal | None = Field(default=None, ge=0)
    rental_period: str = ""
    deposit: Decimal | None = Field(default=None, ge=0)
    description: str = ""
    saleor_product_id: str | None = None
    pickup_location_id: int | None = None
    pickup_address_id: int | None = None
    pickup_area: str = ""
    pickup_landmark: str = ""
    pickup_instructions: str = Field(default="", max_length=500)
    distance_km: Decimal | None = Field(default=None, ge=0)
    images: list[ListingImageIn] = Field(default_factory=list, max_length=6)
    course_ids: list[int] = Field(default_factory=list, max_length=20)

class ListingUpdateIn(BaseModel):
    title: str | None = None
    category: str | None = None
    subcategory: str | None = None
    condition: str | None = None
    listing_type: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    rental_price: Decimal | None = Field(default=None, ge=0)
    rental_period: str | None = None
    deposit: Decimal | None = Field(default=None, ge=0)
    description: str | None = None
    pickup_location_id: int | None = None
    pickup_address_id: int | None = None
    pickup_area: str | None = None
    pickup_landmark: str | None = None
    pickup_instructions: str | None = Field(default=None, max_length=500)
    course_ids: list[int] | None = Field(default=None, max_length=20)

class OfferCreateIn(BaseModel):
    listing_id: int
    amount: Decimal = Field(gt=0)
    message: str = Field(default="", max_length=2000)
    expires_hours: int = Field(default=48, ge=1, le=168)

class MessageCreateIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)

class ConversationCreateIn(BaseModel):
    listing_id: int

class WantedCreateIn(BaseModel):
    campus_slug: str
    title: str = Field(min_length=2, max_length=180)
    category: str = Field(min_length=2, max_length=80)
    description: str = ""
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    needed_by: date | None = None

class SwapCreateIn(BaseModel):
    offered_listing_id: int
    requested_listing_id: int
    message: str = Field(default="", max_length=2000)

class PickupScheduleIn(BaseModel):
    pickup_location_id: int | None = None
    pickup_address_id: int | None = None
    pickup_date: date
    pickup_time: time

class HandoffIn(BaseModel):
    code: str = Field(pattern=r"^\d{4}$")

class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=2000)

class PaymentCreateIn(BaseModel):
    transaction_id: int
    method: str = "upi"

class PaymentVerifyIn(BaseModel):
    provider_order_id: str
    provider_payment_id: str
    signature: str

class CourseCreateIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=160)
    semester: str = ""

class ReportIn(BaseModel):
    target_type: str
    target_id: int
    reason: str
    notes: str = ""

class LostFoundCreateIn(BaseModel):
    campus_slug: str
    item_type: str
    title: str = Field(min_length=2, max_length=160)
    description: str = ""
    location_text: str = ""
    item_date: date | None = None

class LostFoundClaimIn(BaseModel):
    message: str = Field(default="", max_length=1000)

class AdminResolveIn(BaseModel):
    status: str

class AdminUserStatusIn(BaseModel):
    active: bool

class CourseTagIn(BaseModel):
    course_ids: list[int] = Field(default_factory=list, max_length=20)
