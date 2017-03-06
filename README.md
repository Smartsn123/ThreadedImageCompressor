# ThreadedImageCompressor
Application take input list of image urls , CSV with image URLS  or Image Itself and allows compression as per your choice of quality and  Size

NOTE : this application only compresses JPEG and PNG image files


![Alt text](sample.png?raw=true "")


# Introduction 

This app is based on a Flask backend and does not store any data and converts the image and resturns images dynamically uploading them  to AWS.

This app Uses Flaskto Expose function to convert the image and Uses Materialize HTML+CSS for frontend.

Javascript  and Jquery tougether ensure that user can keep on using the application foe converting images from multiple sources withour needing to reload the page after any Operation.

Flask server is run Threaded and lage inputs are chunked into samller chunks and  each chunk is Run in a different thread with ajax request.

Variable Ajax_sent is used to keep track of the ajax requests sent and sets limits to maximum no  simultaneous of ajax requests to 5


#Running

To run do folllwing commands .

chmod +x requirements.sh

sudo ./requirements.sh

python server.py

and goto : http://127.0.0.1:8080/

