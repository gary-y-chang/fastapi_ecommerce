from fastapi import FastAPI, Form, Depends
from routers import user_controller, shop_controller, product_controller, browse_controller, shoppingcart_controller, notify_controller, wallet_controller, sponsor_controller
from pydantic import BaseModel

app = FastAPI(openapi_tags= [user_controller.tag_meta, shop_controller.tag_meta, product_controller.tag_meta, shoppingcart_controller.tag_meta, browse_controller.tag_meta, notify_controller.tag_meta,
    wallet_controller.tag_meta, sponsor_controller.tag_meta])
app.include_router(user_controller.router)
app.include_router(shop_controller.router)
app.include_router(product_controller.router)
app.include_router(browse_controller.router)
app.include_router(shoppingcart_controller.router)
app.include_router(notify_controller.router)
app.include_router(wallet_controller.router)
app.include_router(sponsor_controller.router)

class Login(BaseModel):
    username: str
    password: str = None

    @classmethod
    def as_form(cls, username: str = Form(...), password: str = Form(None)):
        return cls(username=username, password=password)


@app.post("/", tags=['Hello'])
async def root(login_data: Login = Depends(Login.as_form)):
    return {"username": login_data.username, "password": login_data.password}
    # return {"message": "Hello World"}


