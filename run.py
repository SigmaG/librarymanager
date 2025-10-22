from src.librarymanager import create_app

app = create_app()

if __name__ == '__main__':
    # bind to 0.0.0.0 so the dev server is reachable from the host / container
    app.run(host='0.0.0.0', debug=True)
