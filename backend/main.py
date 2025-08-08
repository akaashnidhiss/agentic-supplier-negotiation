from fastapi import FastAPI
from .routes import router



app = FastAPI()
app.include_router(router)  # No prefix

@app.get('/')
def read_root():
    return {'message': 'Supplier Communication & Document Exchange Agent API'}
