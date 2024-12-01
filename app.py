from flask import Flask, render_template, request
import api2
app = Flask(__name__)
print("Flask app is starting")



@app.route("/")
def index():
    print("Load Page 1")
    return render_template('index.html')


@app.route('/getdata', methods=['POST'])
def getdata():
    data = request.json
    subreddit = data.get('subreddit')
    word = data.get('word')
    result = api2.datacheck(subreddit, word)    
    return result  




if __name__ == '_main_':
    app.run(debug=True, host='0.0.0.0', port=5001)