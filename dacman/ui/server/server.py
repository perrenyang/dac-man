# server.py
from flask import Flask, render_template, json
from astropy.io import fits
from dacman import Executor, DataDiffer
from dacman.plugins.default import DefaultPlugin

app = Flask(__name__, static_folder='../fits/build/static', template_folder='../fits/build')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/api/fitstest')
def api_fits_test():
	hdul = fits.open('../spCFrame-b1-00161868.fits')
	output = hdul[5].header[3]
	print(output)
	return json.jsonify({
		'output' : output
	})

@app.route('/api/dacmantest')
def api_dacman_test():
	file1 = '../../../examples/data/simple/v0/file1'
	file2 = '../../../examples/data/simple/v1/file1'
	comparisons = [(file1, file2)]
	differ = DataDiffer(comparisons, executor=Executor.DEFAULT)
	differ.use_plugin(DefaultPlugin)
	results = differ.start()
	print(results)
	return json.jsonify(results)

@app.route('/api/fitsinfo')
def api_fits_info():
	hdul = fits.open('../spCFrame-b1-00161868.fits')
	output = hdul.info(output=False)
	return json.jsonify(output)

@app.route('/hello')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
