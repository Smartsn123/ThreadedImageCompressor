from flask import Flask, render_template,request, Response,jsonify,send_from_directory,make_response
from werkzeug import secure_filename
app = Flask(__name__)
import urllib
import urllib2
import os,re,ast
import json,os,boto
from multiprocessing.pool import ThreadPool
from utilities import ImageProcessor, upload_to_s3
import random, string,pandas
from cStringIO import StringIO

UPLOAD_FOLDER = os.getcwd()+'/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def IsImageUrl(inp ):

	if  ( inp.split('.')[-1] in ['jpg','png','PNG','JPEG','JPG'] ) and ( inp.split(':')[0] in['http:','https']) :
		return True
	return False


def getUrlsFromFile(filename):
	fl = open(filename,'r')
	urls =[]
	lines = fl.read()
	#print lines
	lines = lines.split('\n')
	print lines
	for ln in lines:
		print ln
		for wd in ln.split(','):
			if IsImageUrl(wd ):
				urls.append(wd)
	print urls
	return urls	


@app.route('/')
def hello_world():
     return render_template("form.html")


@app.route('/upload',methods=['GET','POST'])
def upload_file():
	File = request.files['datafile']
	QL,SZ = request.form['info'].split(',')
	QL = int(QL)
	SZ = float(SZ)/100.0
	print QL,SZ
	print File
	if File:
		filename = secure_filename(File.filename)
		dest_file =os.path.join(app.config['UPLOAD_FOLDER'],filename)
        try:
            	File.save(dest_file)
            	if dest_file.split('.')[-1] in ['csv' ,'xls']:
            		urls = getUrlsFromFile(dest_file)#real all urls from csv file
            		os.remove(dest_file)#delete the uploaded csv file
            		output = {'type':'input_url','data':urls}
            		return json.dumps(output)

            	elif dest_file.split('.')[-1] in ['jpg' ,'png','JPEG','PNG','jpeg']:
            		print "Uploaded image ///////////////"
            		image = ImageProcessor()
            		image.set_from_file(dest_file)
            		image.compress(QL,SZ)
            		data = {}
            		data['name']=randomword(12)+'.'+image._type
            		data['bucket_name'] = "mishacollins"
            		data['type'] = 'image/'+image._type
            		data['content'] = image._compressed
            		base_url = upload_to_s3(data)
            		output=[]
            		print base_url,data['name']
            		output = ( '{}/{}'.format(str(base_url), str(data['name'] )  ) )
            		os.remove(dest_file)#delete the uploaded image
            		return json.dumps({'type':'link' ,'data':base_url})

        except:
            	    return Response("Error Uploading!", status=449, mimetype='application/json')

@app.route("/getCSV", methods=['POST'])
def getCSV():
	print request.form
	data = list(request.form)[0]
	data = ast.literal_eval(data)
	print data
	if len(data.keys())==0:
		return None
	csv_file=""
	for i in range(len(data.keys())):
		for wd in data[str(i)]:
			csv_file+= wd+','
		csv_file+='\n'
	response = make_response(csv_file)
	response.headers["Content-Disposition"] = "attachment; filename=result.csv"
	response.headers["Content-Description"]= "File Transfer"
	response.headers["Cache-Control"]= "public"
	response.headers["Content-Type"]= "application/octet-stream"
	response.headers["Content-Transfer-Encoding"]="binary"
	return response

            

@app.route('/convert', methods=['POST'])
def submit():

	print request.form
	data = list(request.form)[0]
	data = data.strip('[').strip(']')
	print data
	data = ast.literal_eval(data)
	print data
	urls = data['urls']
	QL = int(data['qual'])
	SZ = float(data['size'])/100.0
	resp ={}
	for url in urls:
		image = ImageProcessor(url)
		conv_status = image.compress(QL, SZ)['status']
		if conv_status == 1:
			data = {}
			data['name']= randomword(12)+'.'+image._type
			data['bucket_name'] = "mishacollins"
			data['type'] = 'image/'+image._type
			data['content'] = image._compressed
			data['status'] =0
			res = upload_to_s3(data)
			if data['status'] == 1:
				resp[url]=res
			else:
				resp[url]='Failed While uploading to S3'
		else:
			resp[url]='Invalid Image File/ Failed While Compressing'
	return Response(json.dumps(resp) ,status=200, mimetype='application/json')

@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)
	

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1',port=8080,threaded=True)

    