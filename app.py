import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, session
from werkzeug.utils import secure_filename
import json
from bs4 import BeautifulSoup


UPLOAD_FOLDER = r'C:\Users\simon_w3\OneDrive - UGent\School\Ugent\2de ma ing.-arch\Masterproef\GMasterproef\Final\Flask_webserver\static'
ALLOWED_EXTENSIONS = {'bpmn','txt','json'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'dd793de789f6df5210f233ce4a83f92d'

done= False

def allowed_file(filename,extension):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == extension

"""
def process_file(file_path):
    # Perform your script action on the file
    # For example, let's assume you want to convert the file to uppercase
    with open(file_path, 'r') as f:
        content = f.read().upper()
    with open(file_path, 'w') as f:
        f.write(content)
"""
        
def process_json(file_path):
    # Load the JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)

    applicant_data = [item for item in data if item['id'][:1] == 'A']
    bim_data = [item for item in data if item['id'][:1] == 'B']
    gis_data = [item for item in data if item['id'][:1] == 'G']

    # Return the data and null IDs
    return data, applicant_data, bim_data, gis_data

def process_bpmn(file_path):
    bpmn = open(file_path,'r').read()
    bsdata=BeautifulSoup(bpmn,'xml')
    
    return bsdata

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        done = True
        jsondatabase = request.files.get('json')
        bpmndiagram = request.files.get('bpmn')
        if allowed_file(jsondatabase.filename,"json") is False or allowed_file(bpmndiagram.filename,"bpmn") is False:
            session['filename_bpmn'] = None
            session['file_path_json'] = None
            return render_template('index.html', message='File type not supported')
        if jsondatabase and bpmndiagram and allowed_file(jsondatabase.filename,"json") and allowed_file(bpmndiagram.filename,"bpmn"):
            filenamedatabase = secure_filename(jsondatabase.filename)
            file_path_json = os.path.join(app.config['UPLOAD_FOLDER'], filenamedatabase)
            jsondatabase.save(file_path_json)
            session['file_path_json'] = file_path_json

            filenamebpmn = secure_filename(bpmndiagram.filename)
            file_path_bpmn = os.path.join(app.config['UPLOAD_FOLDER'], filenamebpmn)
            bpmndiagram.save(file_path_bpmn)
            session['file_path_bpmn'] = file_path_bpmn
            session['filename_bpmn'] = filenamebpmn

            return render_template('index.html', message='File uploaded successfully', filename=filenamedatabase, filename2 = filenamebpmn, filepathjson=file_path_json,done=done)

    return render_template('index.html',done=False)




@app.route('/input', methods=['GET','POST'])
def input():
    file_path_json = session.get('file_path_json')  # Retrieve file_path from the session

    if not file_path_json:
        return render_template("input.html",done=done)

    # Process the file and get the data and null IDs
    data, applicant_data, bim_data, gis_data = process_json(file_path_json)

    if request.method == 'POST':
        editeddata = request.form
        return render_template('input.html', edit=editeddata,done=done,filepathjson=file_path_json, data=data, applicant_data=applicant_data, bim_data=bim_data, gis_data=gis_data)

    
    return render_template('input.html',filepathjson=file_path_json,done=done, data=data, applicant_data=applicant_data, bim_data=bim_data, gis_data=gis_data)


@app.route('/bpmn', methods=['GET','POST'])
def bpmn():
    file_path_bpmn = session.get('filename_bpmn')    
    return render_template('bpmn.html',file_path_bpmn=file_path_bpmn,done=done)

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

if __name__ == '__main__':
    app.run(debug=True)
