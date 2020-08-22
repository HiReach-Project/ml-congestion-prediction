from flask import Flask, request, Response
import pandas as pd
import json
from fbprophet import Prophet

app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict():
    ml_data = request.json
    df = pd.DataFrame.from_dict(ml_data)
    df['dateRounded'] = pd.DatetimeIndex(df['dateRounded']).tz_convert(None)
    df = df.rename(columns={'dateRounded': 'ds', 'devices': 'y'})

    date_to_predict = request.args.get('prediction_date')

    model = Prophet(uncertainty_samples=0)
    model.fit(df)

    future_date = pd.DataFrame({'ds': [date_to_predict]})
    future_date['ds'] = pd.DatetimeIndex(future_date['ds']).tz_convert(None)

    forecast = model.predict(future_date)

    print(forecast[['ds', 'yhat']].tail())

    json_response = json.dumps({
        "predicted_value": forecast['yhat'].values[0].astype(str),
        "predicted_date": request.args.get('prediction_date')
    })
    print(json_response)

    return Response(json_response, mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
