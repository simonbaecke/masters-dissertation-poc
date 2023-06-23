# Proof of Concept Application
This tool is a proof of concept application of the master's dissertation "Data-based compliance checking against building requirements". It presents a methodology for Automatic Compliance Checking and Decision-Making with the use of the Business Process Model and Notation (BPMN). An example diagram and database are attached to illustrate the capabilities of the tool, but it is possible to upload other BPMN XML diagrams and their associated JSON databases to check compliance.

## Installation
To run the tool, simply download the zip folder and extract the content or clone the repository in a terminal.
```
 git clone https://github.com/simonbaecke/masters-dissertation-poc.git
```
When this is done the app.py file has to be executed, which can also be done in the terminal. Note that all dependencies have to be installed for correct functioning of the tool, these are listed in the dependencies.txt file.
```
python app.py
```

 To make use of the microservices in the example of the rainwater regulation, visit https://github.com/simonbaecke/masters-dissertation/blob/main/microservices.
## Use
You can upload a BPMN diagram and a corresponding JSON database or you can select the example files at the Example Rainwater Regulation page.

![alt text](https://github.com/simonbaecke/GMasterproef/blob/main/home.png)
![alt text](https://github.com/simonbaecke/GMasterproef/blob/main/example.png)

The parameters of the database can be viewed at the parameter page. They can be edited or filled in manually or with another JSON file that has an array structure with "id" : value as content. After the checking procedure, the checked diagram and its parameters can be seen at the results page. In the case that something goes wrong, a message will appear giving more information to the user. For instance when parameters are not valid or missing, the process is stopped and the user will be asked to fill in the correct information.

## Contact
Feel free to reach out to me at simon.baecke@gmail.com if you have any questions or for a more detailed introduction to the tool.
