testenv:
	pip install -r requirements.txt
	pip install -e .

test:
	coverage run --branch --source=clinto --omit=clinto/tests* `which nosetests`
	coverage report
