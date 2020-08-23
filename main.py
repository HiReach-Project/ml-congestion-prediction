import hashlib
import json
from datetime import datetime

import pandas as pd
from fbprophet import Prophet
from flask import Flask, request, Response, jsonify
from werkzeug.exceptions import abort

from database import engine, db_session
from models import Base, Company

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Initialized the db")


@app.before_request
def authorize_requests():
    hashed_key = hashlib.sha3_256(str(request.args.get('key')).encode('utf-8')).hexdigest()
    db_company = db_session.query(Company).filter_by(access_key=hashed_key).first()
    if db_company is None:
        abort(403)


@app.route('/api/predict', methods=['POST'])
def predict():
    ml_data = request.json
    df = pd.DataFrame.from_dict(ml_data)
    df['timestamp'] = pd.DatetimeIndex(df['timestamp']).tz_convert(None)
    df = df.rename(columns={'timestamp': 'ds', 'value': 'y'})

    date_to_predict = request.args.get('prediction_date')

    model = Prophet(uncertainty_samples=0)
    model.fit(df)

    future_date = pd.DataFrame({'ds': [date_to_predict]})
    future_date['ds'] = pd.DatetimeIndex(future_date['ds']).tz_convert(None)

    forecast = model.predict(future_date)

    json_response = json.dumps({
        "predicted_value": forecast['yhat'].values[0].astype(str),
        "predicted_date": request.args.get('prediction_date')
    })

    return Response(json_response, mimetype='application/json')


@app.errorhandler(403)
def forbidden_error(error):
    return jsonify(
        {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "status": error.code,
            "error": "Forbidden",
            "message": "",
            "path": request.path
        }
    ), error.code


@app.errorhandler(404)
def page_not_found_error(error):
    return jsonify(
        {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "status": error.code,
            "error": "Not Found",
            "message": "The requested URL was not found on the server.",
            "path": request.path
        }
    ), error.code


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify(
        {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "status": error.code,
            "error": "Internal Server Error",
            "message": "Oops! Something went wrong on our side.",
            "path": request.path
        }
    ), error.code


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0')
