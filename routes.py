from becca-runs.app import app
from flask import jsonify 

@app.route("/hello", method='GET')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)