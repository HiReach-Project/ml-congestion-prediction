# Prediction API  
This is a REST API built on top of [fbprophet](https://facebook.github.io/prophet/) for forecasting time-series data.
It is used by the [Congestion Tracing API](https://github.com/HiReach-Project/congestion-tracing-standalone) to predict future congestion.

## Installation
### Postgres database
Tested with: PostgreSQL 12.2

Create a database:
```shell script
sudo -u postgres psql
create database "database_name" owner "database_owner";
```
### Run the API in a docker container
Build docker container:
```shell script
docker build -t prediction_api .
```
Run the container:
```shell script
docker run --network=host prediction_api
```
# API specification
## Authorization
All API requests require the use of an API key.
To authenticate an API request, you should append your API key as a URL parameter.
```http
POST /api/predict/?key=1234567890
```
**Note**: for security reasons there is NO default api key added in the database. For testing the API, a hashed key must be manually added,
 after running the container, as a SHA3_256 encoded string into the `company` table.  
 The hash can be obtained easily from [here](https://md5calc.com/hash/sha3-256/1234567890).  
 Example adding the SHA3_256 encoded hash of `1234567890` key in the database:
```sql
insert into company values(1, 'your_company_name', '01da8843e976913aa5c15a62d45f1c9267391dcbd0a76ad411919043f374a163');
``` 
## Endpoints
### Make a prediction
To make a prediction a POST request is needed containing the time-series data as JSON in the request body and the prediction
date as a url parameter.
```http
POST /api/predict/?key=1234567890&prediction_date=2020-08-02T20:07:31Z
```
*  **URL Params**

   **Required:**   
   `key=[string]` - Authorization key.  
   `prediction_date=[timestamp]` - A future timestamp for which you want the prediction to be made. The timestamp must use the ISO 8601 standard.

*  **Request body**
    ```json
    [
        {
            "timestamp": "2020-08-02T20:07:00Z",
            "value": 1
        },
        {
            "timestamp": "2020-08-02T20:07:30Z",
            "value": 4
        }
    ]
    ```

*  **Sample call:**
    ```shell script
    curl --request POST 'http://localhost:5000/api/predict?key=1234567890&prediction_date=2020-08-19T17:07:33.478200Z' \
    --header 'Content-Type: application/json' \
    --data-raw '[
        {
            "timestamp": "2020-08-02T20:07:00Z",
            "value": 1
        },
        {
            "timestamp": "2020-08-02T20:07:30Z",
            "value": 4
        }
    ]'
    ```
   **Success Response:**
        
    **Code:** 200 OK  
    **Content:**
    ```json
       {
           "predicted_value": "4.041208956969186",
           "predicted_date": "2020-08-19T17:07:33.478200Z"
       }
    ```  
    `predicted_value` - is the value predicted by the machine learning algorithm trained on data from the request body.  
    `predicted_date` - represents the future date for which the prediction has been made.


## Error Responses  
**Code:** 403 FORBIDDEN  
**Content:**   
```json
{
    "timestamp": "2020-08-22T13:21:05.045562Z",
    "status": 403,
    "error": "Forbidden",
    "message": "",
    "path": "/api/predict"
}
```
**Code:** 404 NOT FOUND  
**Content:**   
```json
{
    "timestamp": "2020-08-23T16:32:22.854640Z",
    "status": 404,
    "error": "Not Found",
    "message": "The requested URL was not found on the server.",
    "path": "/api/a-wrong-path"
}
```
**Code:** 500 INTERNAL SERVER ERROR  
**Content:**   
```json
{
    "timestamp": "2020-08-22T13:21:05.045562Z",
    "status": 500,
    "error": "Internal Server Error",
    "message": "Oops! Something went wrong on our side.",
    "path": "/api/predict"
}
```