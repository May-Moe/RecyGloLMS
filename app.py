# from recyglolms import create_app  # Import the app factory function

# # Create the app using the factory function
# app = create_app()

# # Run the app if directly running this script
# if __name__ == '__main__':
#     app.run(debug=True)  # Run the Flask app
#     # app.run(host="0.0.0.0", port=8080)  # Ensure it listens on the correct host/port

from recyglolms import create_app

app = create_app()  # ✅ Create the app instance

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)

