# Congestion API - a REST API built to track congestion spots and
# crowded areas using real-time location data from mobile devices.
#
# Copyright (C) 2020, University Politehnica of Bucharest, member
# of the HiReach Project consortium <https://hireach-project.eu/>
# <andrei[dot]gheorghiu[at]upb[dot]ro. This project has received
# funding from the European Union’s Horizon 2020 research and
# innovation programme under grant agreement no. 769819.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
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

    if float(args.get('lat')) < -90 or float(args.get('lat')) > 90:
        abort(400)

    if float(args.get('lon')) < -180 or float(args.get('lon')) > 180:
        abort(400)

    if float(args.get('radius')) > 6378000:
        abort(400)


def create_path(args):
    lat = args.get('lat')
    lon = args.get('lon')
    radius = args.get('radius')
    return SAVED_MODELS_PATH + '/' + lat + '_' + lon + '_' + radius + '.pkl'


@app.route('/api/prediction', methods=['POST'])
def predict():
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

    future_date = pd.DataFrame({'ds': [date_to_predict]})
    future_date['ds'] = pd.DatetimeIndex(future_date['ds']).tz_convert(None)

    forecast = model.predict(future_date)
    # convert log back
    forecast[forecast.columns[1:]] = np.exp(forecast[forecast.columns[1:]]) - 1

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
