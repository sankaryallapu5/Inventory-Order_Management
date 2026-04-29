# from pydantic import BaseModel, Field
# from typing import Optional

# class OrderCreate(BaseModel):
#     product_id: int
#     quantity: int = Field(gt=0)

# class OrderUpdate(BaseModel):
#     status: Optional[str] = None

# class Product(BaseModel):
#     name: str
#     price: float = Field(gt=0)
#     stock: int = Field(ge=0)

# class UserCreate(BaseModel):
#     username: str
#     password: str

# class UserLogin(BaseModel):
#     username: str
#     password: str

from pydantic import BaseModel, Field
from typing import Optional

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)

class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class OrderUpdate(BaseModel):
    status: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str