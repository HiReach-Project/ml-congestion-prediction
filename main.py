import hashlib
import json
import pickle
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from fbprophet import Prophet
from flask import Flask, request, Response, jsonify
from werkzeug.exceptions import abort

from database import engine, db_session
from models import Base, Company

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

SAVED_MODELS_PATH = 'saved_models'


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Initialized the db")


@app.before_request
def authorize_requests():
    hashed_key = hashlib.sha3_256(str(request.args.get('key')).encode('utf-8')).hexdigest()
    db_company = db_session.query(Company).filter_by(access_key=hashed_key).first()
    if db_company is None:
        abort(403)


def validate_url_params(args):
    if not args.get('lat') or not args.get('lon') or not args.get('radius') or not args.get('prediction_date'):
        abort(400)


def create_path(args):
    lat = args.get('lat')
    lon = args.get('lon')
    radius = args.get('radius')
    return SAVED_MODELS_PATH + '/' + lat + '_' + lon + '_' + radius + '.pkl'


@app.route('/api/prediction', methods=['POST'])
def predict():
    start = time.time()
    validate_url_params(request.args)
    date_to_predict = request.args.get('prediction_date')

    model_path = create_path(request.args)
    if Path(model_path).exists():
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    elif not request.data:
        print('isNone')
        return 'Not cached'
    else:
        ml_data = request.json
        df = pd.DataFrame.from_dict(ml_data)
        df['timestamp'] = pd.DatetimeIndex(df['timestamp']).tz_convert(None)
        df = df.rename(columns={'timestamp': 'ds', 'value': 'y'})

        model = Prophet(uncertainty_samples=0)
        # prevent negative values
        df['y'] = df['y'] + 1
        df['y'] = np.log(df['y'])
        model.fit(df)
        save_model(model, model_path)

    print(time.time() - start)
    future_date = pd.DataFrame({'ds': [date_to_predict]})
    future_date['ds'] = pd.DatetimeIndex(future_date['ds']).tz_convert(None)

    forecast = model.predict(future_date)
    # convert log back
    forecast[forecast.columns[1:]] = np.exp(forecast[forecast.columns[1:]]) - 1

    print(time.time() - start)
    json_response = json.dumps({
        "predicted_value": forecast['yhat'].values[0].astype(str),
        "predicted_date": request.args.get('prediction_date')
    })

    return Response(json_response, mimetype='application/json')


def save_model(model, model_path):
    Path(SAVED_MODELS_PATH).mkdir(exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    print("*** Data Saved ***")


@app.errorhandler(400)
def forbidden_error(error):
    return jsonify(
        {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "status": error.code,
            "error": "Bad Request",
            "message": "The client sent a request that this server could not understand.",
            "path": request.path
        }
    ), error.code


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
