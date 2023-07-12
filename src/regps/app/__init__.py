from app.service import falcon_app, swagger_ui

print("Starting RegPS...")
app = falcon_app()
api_doc=swagger_ui(app)