from typing import Literal

from pydantic import BaseModel, Field, field_validator

MIN_DELIVERY_PARTNERS = 2   # a vendor must have at least this many delivery partners to apply


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=10, max_length=128)
    role: str = "student"
class LoginIn(BaseModel): email: str; password: str
class AdminSetPasswordIn(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)
class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)
class StudentCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    phone: str = Field(min_length=7, max_length=32)
    password: str = Field(min_length=10, max_length=128)
class StudentProfileIn(BaseModel):
    phone: str = Field(min_length=7, max_length=32)
class ApplicationIn(BaseModel):
    business_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=7, max_length=32)
    description: str = Field(max_length=3000)
    business_address: str = Field(min_length=4, max_length=1000)
    contact_person: str = Field(min_length=2, max_length=120)
    agreement_reference: str = Field(default="", max_length=160)
    delivery_partners: int = Field(le=500)

    @field_validator("delivery_partners")
    @classmethod
    def at_least_two_delivery_partners(cls, value):
        if value < MIN_DELIVERY_PARTNERS: raise ValueError(f"At least {MIN_DELIVERY_PARTNERS} delivery partners are required to apply")
        return value
class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=3000)
    category_id: int
    price: float = Field(ge=0)
    stock: int = Field(ge=0)
    available: bool = True
    image_url: str = Field(default="", max_length=500)
    dietary: Literal["vegetarian","non_vegetarian","vegan","unspecified"] = "vegetarian"
    spice_level: Literal["mild","medium","hot"] | None = None
    allergens: str = Field(default="", max_length=500)
    portion: str = Field(default="", max_length=100)
    prep_time_minutes: int | None = Field(default=None, ge=0, le=240)
    menu_section: str = Field(default="", max_length=100)
class AdminProductIn(ProductIn):
    vendor_id: int
class BulkAvailabilityIn(BaseModel):
    available: bool

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=3000)
    category_id: int | None = None
    price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    available: bool | None = None
    image_url: str | None = Field(default=None, max_length=500)
    dietary: Literal["vegetarian","non_vegetarian","vegan","unspecified"] | None = None
    spice_level: Literal["mild","medium","hot"] | None = None
    allergens: str | None = Field(default=None, max_length=500)
    portion: str | None = Field(default=None, max_length=100)
    prep_time_minutes: int | None = Field(default=None, ge=0, le=240)
    menu_section: str | None = Field(default=None, max_length=100)
class CartLineIn(BaseModel): product_id: int; quantity: int = Field(ge=1, le=99); variant_id: int | None = None; addon_ids: list[int] = Field(default_factory=list, max_length=20)
class QuantityIn(BaseModel): quantity: int = Field(ge=1, le=99)
class CheckoutIn(BaseModel): delivery_location: str = Field(default="", max_length=160)
class DeliveryPointsIn(BaseModel): points: list[str] = Field(default_factory=list, max_length=30)
class ArrivalIn(BaseModel): stage: Literal["main_gate", "hostel_gate"]
class DecisionIn(BaseModel): decision: str; remarks: str = Field(default="", max_length=2000); agreement_valid: bool | None = None
class DeliveryIn(BaseModel): delivers_to_bmu: bool
class StatusIn(BaseModel): status: str
class VendorTermsIn(BaseModel):
    minimum_order_amount: float | None = Field(default=None, ge=0)
    delivery_terms_note: str = Field(default="", max_length=2000)
    terms_confirmed: bool = False
class VariantEntryIn(BaseModel):
    id: int | None = None
    name: str = Field(min_length=1, max_length=160)
    price: float = Field(ge=0)
    dietary: Literal["vegetarian","non_vegetarian","vegan","unspecified"] = "unspecified"
    preparation: str = Field(default="", max_length=80)
    portion: str = Field(default="", max_length=100)
    available: bool = False
class VariantListIn(BaseModel): variants: list[VariantEntryIn] = Field(max_length=100)
class AddonEntryIn(BaseModel):
    id: int | None = None
    name: str = Field(min_length=1, max_length=120)
    price: float | None = Field(default=None, ge=0)
    available: bool = False
class AddonListIn(BaseModel): addons: list[AddonEntryIn] = Field(max_length=100)
class AdminListingUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=3000)
    category_id: int | None = None
    price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    dietary: Literal["vegetarian","non_vegetarian","vegan","unspecified"] | None = None
    spice_level: Literal["mild","medium","hot"] | None = None
    allergens: str | None = Field(default=None, max_length=500)
    portion: str | None = Field(default=None, max_length=100)
    prep_time_minutes: int | None = Field(default=None, ge=0, le=240)
    menu_section: str | None = Field(default=None, max_length=100)
    available: bool | None = None
    menu_status: Literal["review","published","paused","draft","removed"] | None = None
    review_note: str = Field(default="", max_length=1000)
