from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas import Product, OrderCreate, OrderUpdate, UserCreate, UserLogin
import uuid
import logging
from jose import jwt

app = FastAPI()

# ---------------------------
# LOGGING
# ---------------------------
logging.basicConfig(level=logging.INFO)

def send_alert(message: str):
    logging.warning(f"🚨 ALERT: {message}")

# ---------------------------
# AUTH CONFIG
# ---------------------------
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
security = HTTPBearer()

# ---------------------------
# IN-MEMORY DATABASE
# ---------------------------
users = {}
products = {}
orders = {}
product_counter = 1

ALLOWED_STATUS = ["CREATED", "SHIPPED", "DELIVERED"]

# ---------------------------
# TOKEN FUNCTIONS
# ---------------------------
def create_token(username: str):
    return jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------------------
# HOME
# ---------------------------
@app.get("/")
def home():
    return {"message": "Inventory API is running"}

# ---------------------------
# AUTH APIs
# ---------------------------
@app.post("/signup")
def signup(user: UserCreate):
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")

    users[user.username] = user.password
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin):
    if user.username not in users or users[user.username] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ---------------------------
# PRODUCT APIs (PROTECTED)
# ---------------------------

@app.post("/products")
def create_product(product: Product, username: str = Depends(verify_token)):
    global product_counter

    product_id = product_counter
    products[product_id] = product.dict()
    product_counter += 1

    if product.stock <= 5:
        send_alert(f"Low stock for product '{product.name}' (ID: {product_id})")

    return {"product_id": product_id, "message": "Product created"}

@app.get("/products")
def get_products(username: str = Depends(verify_token)):
    return products

@app.get("/products/{product_id}")
def get_product(product_id: int, username: str = Depends(verify_token)):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    return products[product_id]

@app.put("/products/{product_id}")
def update_product(product_id: int, product: Product, username: str = Depends(verify_token)):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    products[product_id] = product.dict()

    if product.stock == 0:
        send_alert(f"Product {product_id} OUT OF STOCK")
    elif product.stock <= 5:
        send_alert(f"Low stock for product {product_id}")

    return {"message": "Product updated"}

# ---------------------------
# ORDER APIs (PROTECTED)
# ---------------------------

@app.post("/orders")
def create_order(order: OrderCreate, username: str = Depends(verify_token)):

    if order.product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    product = products[order.product_id]

    if product["stock"] < order.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    product["stock"] -= order.quantity

    order_id = str(uuid.uuid4())

    orders[order_id] = {
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "CREATED",
        "user": username
    }

    send_alert(f"Order created {order_id} by {username}")

    if product["stock"] == 0:
        send_alert(f"Product {order.product_id} OUT OF STOCK")
    elif product["stock"] <= 5:
        send_alert(f"Low stock for product {order.product_id}")

    return {"order_id": order_id}

@app.get("/orders")
def get_orders(username: str = Depends(verify_token)):
    return orders

@app.get("/orders/{order_id}")
def get_order(order_id: str, username: str = Depends(verify_token)):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[order_id]

@app.patch("/orders/{order_id}")
def update_order(order_id: str, update: OrderUpdate, username: str = Depends(verify_token)):

    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    if update.status:
        status = update.status.upper()

        if status not in ALLOWED_STATUS:
            raise HTTPException(status_code=400, detail="Invalid status")

        orders[order_id]["status"] = status

        if status == "SHIPPED":
            send_alert(f"Order {order_id} shipped")
        elif status == "DELIVERED":
            send_alert(f"Order {order_id} delivered")

    return {"message": "Order updated"}