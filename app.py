import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, session
from werkzeug.utils import secure_filename
import json
from bs4 import BeautifulSoup
import html
import math
import requests

UPLOAD_FOLDER = r'C:\Users\simon_w3\OneDrive - UGent\School\Ugent\2de ma ing.-arch\Masterproef\GMasterproef\Final\Flask_webserver\static'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'dd793de789f6df5210f233ce4a83f92d'

def allowed_file(filename,extension):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == extension
        
def process_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def reprocess_json(editeddata,data,file_path):
    for id,value in editeddata.items():
            for parameters in data:
                if parameters["id"] == id:
                    try:
                        parameters["value"] = int(value)
                    except:
                        try:
                            parameters["value"] = float(value)
                        except:
                            parameters["value"] = value  
    newdata = json.dumps(data, indent = 4, sort_keys=True)
    with open(file_path, 'w') as json_file:
        json_file.write(newdata)
        
def bpmnprocessor(bpmnfilepath, jsonfilepath):

    def convertformula(node):
        return str(html.unescape(node['name']))

    def round_up(n, decimals=0):
        multiplier = 10 ** decimals
        return math.ceil(n * multiplier) / multiplier

    with open(jsonfilepath, 'r') as database:
        database = json.load(database)

    bpmn = open(bpmnfilepath,'r').read()
    bsdata=BeautifulSoup(bpmn,'xml')
    data = bsdata.process
    graphics=bsdata.BPMNPlane
    start = data.startEvent

    positive_message = None
    negative_message = None

    local_dict = {}
    global_dict=locals()
    endparameters = [] #parameters noted with M that have to be filled in in the end
    usedparameters = []
    errorloop = True
    ms = None
    shapecolorid=[start['id']]
    linecolorid=[]
    wrongoutputlineid = []
    continuenext = True #otherwise a node is skipped after a gateway
    allcallactivities = data.findAll("callActivity") #list of all microservices

    next = start
    while next.name != "endEvent" and errorloop:
        for node in data:
            try:
                incoming = node.find_all('incoming')
                all_incoming = [x.string for x in incoming]
                if next.outgoing.string in all_incoming:                
                    if continuenext:
                        next = node
                        shapecolorid.append(next['id'])
                    continuenext = True

                    annotationassociation = data.find("association", attrs={"sourceRef" : next["id"]})
                    if annotationassociation:
                        annotationnode = data.find("textAnnotation", attrs = {"id" : annotationassociation["targetRef"]})
                        annotation  = annotationnode.text

                    if next.name == "receiveTask":
                        dataobject = data.find('dataObjectReference',attrs = {'id' : next.dataInputAssociation.sourceRef.string})
                        dataobjectid = dataobject["name"]
                        #colors
                        shapecolorid.append(dataobject["id"])
                        linecolorid.append(next.dataInputAssociation["id"])

                        for call in allcallactivities:
                            if call.find('targetRef',string=next.dataInputAssociation.sourceRef.string):
                                ms = call
                                msurl = ms["name"]
                                print(msurl)

                        if dataobjectid[-1:] == "M":
                            endparameters.append(dataobjectid)

                        elif ms:
                            parameterms = data.find(attrs= {'id' : ms.dataInputAssociation.sourceRef.string})
                            parameteridms = parameterms["name"]
                            parametermsvalues = eval(parameteridms,global_dict,local_dict)
                            try:             
                                response = requests.post(msurl,data=json.dumps(parametermsvalues))
                                if response.status_code == 200:
                                    msvalue = response.json()
                                    local_dict[dataobjectid] = msvalue
                                    database[int(dataobjectid[1:])-1]['value']= local_dict[dataobjectid]
                            
                            except:
                                negative_message = f'cannot connect to microservice: {msurl}'
                                errorloop = False
                                break
                            
                            usedparameters.append(dataobjectid)
                            #colors
                            shapecolorid.append(ms["id"])
                            shapecolorid.append(parameterms["id"])
                            linecolorid.append(ms.dataInputAssociation['id'])
                            linecolorid.append(ms.dataOutputAssociation['id'])
        
                            ms = None                     

                        else:
                            databasevalue = database[int(dataobjectid[1:])-1]['value']
                            if databasevalue is not None:
                                try:
                                    validation = database[int(dataobjectid[1:])-1]['validation']
                                    if eval(str(databasevalue) + validation):
                                        local_dict[dataobjectid] = databasevalue
                                        usedparameters.append(dataobjectid)
                                    else:
                                        negative_message = f'Parameter {dataobjectid}({databasevalue}) is not valid: {validation}'
                                        errorloop = False
                                        break
                                except:
                                        local_dict[dataobjectid] = databasevalue
                                        usedparameters.append(dataobjectid)
                            else:
                                negative_message =f'{dataobjectid} is absent from the database'
                                errorloop = False
                                break
                        
                    elif next.name == "sendTask":
                        dataobject = data.find('dataObjectReference',attrs = {'id' : next.dataOutputAssociation.targetRef.string})
                        database[int(dataobject['name'][1:])-1]['value'] = local_dict[dataobject['name']]
                        usedparameters.append(dataobject['name'])
                        #colors
                        shapecolorid.append(dataobject["id"])
                        linecolorid.append(next.dataOutputAssociation["id"])

                    elif next.name == "exclusiveGateway":
                        outgoing = next.find_all('outgoing')
                        all_outgoing = [x.string for x in outgoing]
                        options = [data.find("sequenceFlow", attrs = {"id" : x}) for x in all_outgoing]
                        for flow in options:
                            formula = convertformula(flow)
                            if eval(formula,global_dict,local_dict):
                                next = data.find(attrs={"id" : flow['targetRef']})
                                continuenext = False
                                #colors
                                shapecolorid.append(next['id'])
                            else:
                                wrongoutputlineid.append(flow["id"])
                
                    elif next.name == "scriptTask":
                        formula = convertformula(next)
                        exec(formula,global_dict,local_dict)

                    elif next.name == "serviceTask":
                        formula = convertformula(next)
                        if eval(formula,global_dict,local_dict) == False:
                            negative_message = annotation.format(**local_dict)
                            errorloop = False
                            break
            except:
                pass

    #kleuren van tasks die niet uitgevoerd worden
    for content in data.findAll('sequenceFlow'):
        try:
            if content['sourceRef'] in shapecolorid and content['targetRef'] in shapecolorid:
                    linecolorid.append(content['id'])
        except:
            pass
        
        linecolorid = [x for x in linecolorid if x not in wrongoutputlineid]

    for association in data.findAll("association"):
        if association['targetRef'].find('TextAnnotation') != -1 and association['sourceRef'] in shapecolorid:
            linecolorid.append(association['id'])
            shapecolorid.append(association['targetRef'])
        
    try:
        if next.name == "endEvent":
            shapecolorid.append(bsdata.find("participant", attrs = {'processRef' : data['id']})["id"])
            shapecolorid.extend(x['id'] for x in data.findAll("lane"))
    except:
        pass

    for shape in graphics:
        try:
            id = shape['bpmnElement']
            if shape.name == "BPMNShape" and id not in shapecolorid:
                shape['bioc:stroke']="#B7B7B7"
                shape["color:border-color"]="#B7B7B7"
            elif shape.name == "BPMNEdge"and id not in linecolorid:
                shape['bioc:stroke']="#B7B7B7"
                shape["color:border-color"]="#B7B7B7"
        except:
            pass

    #exporteren van aangepaste database & bpmn
    finished_database = json.dumps(database, indent = 4, sort_keys=True)
    with open(jsonfilepath[:-5]+"checked.json", 'w') as json_file:
        json_file.write(finished_database)

    with open(bpmnfilepath[:-5]+"checked.bpmn","w") as new:
        new.write(str(bsdata))
    
    if not negative_message:
        positive_message = "BPMN processed succesfully"
    return usedparameters, endparameters, positive_message, negative_message

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        
        if request.form.get('processbutton') == "true":
            session['done'] = True
            filepathjson = session.get('file_path_json')
            filepathbpmn = session.get('file_path_bpmn')
            filenamebpmn = session.get('filename_bpmn')
            session['file_path_bpmn_checked'] = filepathbpmn[:-5]+'checked.bpmn'
            session['file_path_json_checked']= filepathjson[:-5]+'checked.json'
            usedparameters, endparameters, positive_message, negative_message = bpmnprocessor(filepathbpmn,filepathjson)
            session['usedparameters'] = usedparameters
            if endparameters:
                session['endparameters'] = endparameters
            return render_template('index.html',filenamebpmn = filenamebpmn, positive_message=positive_message, negative_message=negative_message, done=session.get('done'))
        
        else:
            jsondatabase = request.files.get('json')
            bpmndiagram = request.files.get('bpmn')
            
            if allowed_file(jsondatabase.filename,"json") is False or allowed_file(bpmndiagram.filename,"bpmn") is False:
                session['filename_bpmn'] = None
                session['file_path_json'] = None
                return render_template('index.html', negative_message='File type not supported')
            
            if jsondatabase and bpmndiagram and allowed_file(jsondatabase.filename,"json") and allowed_file(bpmndiagram.filename,"bpmn"):
                filenamedatabase = secure_filename(jsondatabase.filename)
                file_path_json = os.path.join(app.config['UPLOAD_FOLDER'], filenamedatabase)
                jsondatabase.save(file_path_json)
                session['file_path_json'] = file_path_json
                session['filename_json'] = filenamedatabase
                filenamebpmn = secure_filename(bpmndiagram.filename)
                file_path_bpmn = os.path.join(app.config['UPLOAD_FOLDER'], filenamebpmn)
                bpmndiagram.save(file_path_bpmn)
                session['file_path_bpmn'] = file_path_bpmn
                session['filename_bpmn'] = filenamebpmn
                return render_template('index.html', positive_message='Files uploaded successfully',filenamebpmn=session.get('filename_bpmn'), done=session.get('done'))
    return render_template('index.html', done=session.get('done'),filenamebpmn=session.get('filename_bpmn'))


@app.route('/input', methods=['GET','POST'])
def input():
    file_path_json = session.get('file_path_json')

    if not file_path_json:
        return render_template("input.html",done=session.get('done'))

    data = process_json(file_path_json)
    applicant_data = [item for item in data if item['id'][:1] == 'A']
    bim_data = [item for item in data if item['id'][:1] == 'B']
    gis_data = [item for item in data if item['id'][:1] == 'G']

    names = ["BIM", "GIS", "Applicant"]
    zipt = zip([bim_data,gis_data,applicant_data],names)

    if request.method == 'POST':
        editeddata = request.form
        reprocess_json(editeddata,data, file_path_json)

    return render_template('input.html',filepathjson=file_path_json,done=session.get('done'), data=data, zipt=zipt)


@app.route('/bpmn', methods=['GET','POST'])
def bpmn():
    endparameters = session.get('endparameters')
    usedparameters = session.get('usedparameters')
    filename_bpmn_checked = session.get('filename_bpmn')[:-5]+'checked.bpmn'
    filename_json_checked = session.get('filename_json')[:-5]+'checked.json'

    file_path_json = session.get('file_path_json_checked')
    data = process_json(file_path_json)
    if endparameters:
        endparameter_data = [item for item in data if item['id'] in endparameters]
        applicant_data = [item for item in data if item['id'][:1] == 'A' and ( item['id'] in usedparameters or item['id'] in endparameters)]
    else:
        endparameter_data = None
        session['enteredadd'] = True
        applicant_data = [item for item in data if item['id'][:1] == 'A' and item['id'] in usedparameters]
    bim_data = [item for item in data if item['id'][:1] == 'B' and item['id'] in usedparameters]
    gis_data = [item for item in data if item['id'][:1] == 'G' and item['id'] in usedparameters]
    regulation_data = [item for item in data if item['id'][:1] == 'R' and (item['value'] or item['value'] == 0)]
    names = ["Regulation","BIM", "GIS", "Applicant"]
    zipt = zip([regulation_data, bim_data,gis_data,applicant_data],names)

    if request.method == 'POST':
        editeddata = request.form
        reprocess_json(editeddata,data, file_path_json)
        session['enteredadd'] = True

    return render_template('bpmn.html',filename_bpmn_checked = filename_bpmn_checked, filename_json_checked = filename_json_checked,done=session.get('done'), zipt=zipt, endparameters=endparameter_data, enteredadd = session.get('enteredadd'))

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

@app.route('/reloadbpmn', methods=['POST'])
def reloadbpmn():
    return redirect(url_for('bpmn'))

if __name__ == '__main__':
    app.run(debug=True)