from app import create_app,database
app = create_app()
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8121,
        debug=False,
    )