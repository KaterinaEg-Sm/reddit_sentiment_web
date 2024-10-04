from flask import Flask, render_template
app = Flask(__name__)
print("Flask app is starting")



@app.route("/")
def index():
    print("Load Page 1")
    return render_template('index.html')


if __name__ == '_main_':
    app.run(debug=True, host='0.0.0.0', port=5001)