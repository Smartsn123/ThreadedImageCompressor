from flask import Flask, render_template,request, Response,jsonify,send_from_directory,make_response
app = Flask(__name__)
from werkzeug import secure_filename
import urllib
import urllib2
import os,re,ast
import json,os,boto
from multiprocessing.pool import ThreadPool
from utilities import ImageProcessor, upload_to_s3,save_to_local
import random, string
import socket
from cStringIO import StringIO
import time


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
	#print lines
	for ln in lines:
		print ln
		for wd in ln.split(','):
			if IsImageUrl(wd ):
				urls.append(wd)
	#print urls
	return urls	

def save_file(myfile,dest='local'):
	if dest != 'local':
		return upload_to_s3(myfile)
	else:
		url = save_to_local(myfile)
		host_port =request.url.split('/')[2]
		url = 'http://'+( host_port)+'/'+url
		return url


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
		filename=str(time.time()).split('.')[0]+'_'+filename
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
            		base_url = save_file(data)
            		output=[]
            		print base_url
            		host_port =request.url.split('/')[2]
            		src_url = 'http://'+( host_port)+'/uploads/'+filename
            		src_size = str(image.getSize()[0])+','+str(image.getSize()[1])
            		compressed_size = str(image.getCompressedSize()[0])+','+str(image.getCompressedSize()[1])
            		return json.dumps({'type':'link' ,'data':base_url, 'source_data':src_url , 'src_size': src_size ,'resp_size':compressed_size})

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
	#print request.form
	data = list(request.form)[0]
	data = data.strip('[').strip(']')
	#print data
	data = ast.literal_eval(data)
	#print data
	urls = data['urls']
	QL = int(data['qual'])
	SZ = float(data['size'])/100.0
	print QL , SZ
	print data
	resp =[]
	print urls
	print len(urls)
	for url in urls:
		print url,'###############################'
		image = ImageProcessor(url)
		print "here----1"
		conv_status = image.compress(QL, SZ)['status']
		print "here----2"
		if conv_status == 1:
			print "here----"
			data = {}
			data['name']= randomword(12)+'.'+image._type
			data['bucket_name'] = "mishacollins"
			data['type'] = 'image/'+image._type
			data['content'] = image._compressed
			data['status'] =0
			res = save_file(data)
			if data['status'] == 1:
				src_size = str(image.getSize()[0])+','+str(image.getSize()[1])
				compressed_size = str(image.getCompressedSize()[0])+','+str(image.getCompressedSize()[1])
				resp.append( ({'type':'link' ,'data':res, 'source_data':url , 'src_size': src_size ,'resp_size':compressed_size}))
			else:
                           resp.append( ({'type':'link' ,'data':'Failed while saving', 'source_data':url ,'src_size': '0,0', 'resp_size':'0,0'}) )
                else:
                   resp.append({'type':'link' ,'data':'Failed while saving', 'source_data':url , 'src_size': '0,0' ,'resp_size':'0,0'})
	return Response(json.dumps(resp) ,status=200, mimetype='application/json')

@app.route('/static/<path:path>')
def send_js(path):
	print '#####################'
	print path
	return send_from_directory('static', path)

@app.route('/uploads/<path:path>')
def send_files(path):
	return send_from_directory('uploads', path)
	

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=8090,threaded=True)

    
