import csv
from flask import Flask
from flask import render_template
app = Flask(__name__)

csv_path = './static/combined_addresses.csv'
csv_obj = csv.DictReader(open(csv_path, 'r'))
csv_list = list(csv_obj)
# http://stackoverflow.com/questions/1747817/python-create-a-dictionary-with-list-comprehension
csv_dict = dict([[o['id'], o] for o in csv_list])

@app.route("/")
def index():
    return render_template('index.html', 
           object_list=csv_list,
)


#@app.route('/<number>/')
#def detail(number):
#    return render_template('detail.html',
#        object=csv_dict[number],
#    )

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5000,
        use_reloader=True,
        debug=True,
    )
