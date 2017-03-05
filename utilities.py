import sys
from boto.s3.connection import S3Connection
import boto
from boto.s3.key import Key
from cStringIO import StringIO
from PIL import Image 
import urllib2, cStringIO
from random import choice
from string import ascii_uppercase
import threading

AWS_KEY=''
AWS_SECRET=''
conn = None





def get_bucket_url(bucket_name,conn):
    bucket = conn.get_bucket(bucket_name)
    bucket_location = bucket.get_location()
    return 'http://s3-'+bucket_location+'.amazonaws.com/'+bucket_name


def upload_to_s3(myfile):
    conn = S3Connection(aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET)
    try:
     bucket = conn.get_bucket(myfile['bucket_name'])
     k = Key(bucket)
     k.key = myfile['name']
     headers={}
     headers['Content-Type'] = myfile['type']
     base_url = get_bucket_url(myfile['bucket_name'],conn)
     k.set_contents_from_string(myfile['content'], headers=headers, policy='public-read')
     myfile['status'] =1
     return  '{}/{}'.format( str(base_url), str(k.key) )
    except:
     myfile['status'] =0
     return "Failed to Convert!"
    
    

    
##############################################################################
class ImageProcessor:
    
    def __init__(self,url=None):
        site = None
        if url != None:
            self._url = url
            try:
                site = urllib2.urlopen(url)
            except:
                site=None
                pass
        if site!= None and site.code != 200:
                print "Invalid URL!"
        else:
          try:
            self._image = cStringIO.StringIO(site.read())
            self._type = url.split('.')[-1]
            print "***************"+self._type

            if  (self._type in ['png','jpeg','jpg','JPEG','PNG']):
                if self._type == 'png':
                    self._type = 'PNG'
                else:
                    self._type = 'JPEG'
            else:
                self._image = None
                self._type =None
                print "Error Loading image from url"
          except:
                pass

           
                
    def set_from_file(self, filename):
        self._image = cStringIO.StringIO( open(filename,'r').read())
        self._type =  filename.split('.')[-1]
        if  ( self._type in ['png','jpeg','jpg','JPEG','PNG']):
                if self._type == 'png':
                    self._type = 'PNG'
                else:
                    self._type = 'JPEG'
        else:
            print "Image not in valid format"

    def set_image_from_url(self , url):
        return self.__init__(url)


    def show(self):
        if '_image' in self.__dict__:
            img = Image.open(self._image)
            img.show()
        else :
            print "empty object, please set image first !"

    def showCompressed(self):
        if '_compressed' in self.__dict__:
            img = Image.open(self._compressed)
            img.show()
        else :
            print "Image uncompressed, please used object.compress_image() first !"


    def compress(self,ql = 50 , red=0.5 ,fixed_size=None):
        if '_image' in self.__dict__ and self._image!=None:
            tmp = StringIO()
            img = Image.open(self._image)
            print img.size
            nw =  int ( float(img.size[0]) * (red) )
            nh =  int ( float(img.size[1]) * (red) )
            if fixed_size != None:
                nw = fixed_size[0]
                nh = fixed_size[1]
            try:
                img = img.resize( (nw,nh ),Image.ANTIALIAS)
                img.save(tmp, self._type, quality=ql,optimize=True)
                tmp.seek(0)
                self._compressed = tmp.getvalue()
                return {'status':1 , 'message':'success'}
            except:
                return { 'status':0, 'message':"Unable Resie image , try different scale/size"}
        else:
            return { 'status':0, 'message':"Image not Set"}

                

    def size(self):
        print  Image.open(self._image).size,
        if '_compressed' in self.__dict__:
            print 'compressed size: '+str(len(self._compressed))
        print ''
        

    

if __name__ == '__main__':
    ip = ImageProcessor('https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png')
    ip.compress()
    ip.show()
    ip.size()
    ip.save_to_s3()




