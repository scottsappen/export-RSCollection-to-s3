# export-RSCollection-to-s3
You can use our `INSERT INTO s3` feature to export collection data from Rockset and write it directly to Amazon S3. 

### Example

Say you have a collection `analytics` in workspace `commons` . An example query using `INSERT INTO s3` to export all data from `commons.analytics` to the s3 path `s3://analyticsdata/query1` would look like the following:

```sql
INSERT INTO 's3://analyticsdata/query1'
  INTEGRATION = 's3export'
SELECT * FROM commons.analytics
```

See our [`INSERT INTO s3` documentation](https://docs.rockset.com/documentation/reference/insert-into-s3#insert-into-s3-examples) for more information, requirements, and examples.

# **Export Collection Data Using Script-Generated cURL Request**

Follow the below steps to export your data from Rockset. These steps involve using a script to create a custom cURL request that utilizes our [`INSERT INTO s3`](https://docs.rockset.com/documentation/reference/insert-into-s3#insert-into-s3-examples) feature to export data from Rockset and write directly to Amazon s3.

## Requirements

- Python 3.x
- Rockset API Key
- Write access to an S3 bucket and appropriate IAM Policy/Roles configured
- S3 Bucket must be created in the same region as the Rockset collection

## Recommendations

- Before exporting data from Rockset, stop all ingestion and processes (e.g. Query Lambdas)
- For most, it may be easiest to create a single S3 bucket for all exported collections
    - Different workspaces and collections can be exported to different paths in that bucket
- Use [async queries](https://docs.rockset.com/documentation/docs/async-queries) for large amounts of data
- The query must execute within 30 minutes - you can batch your export into multiple smaller exports if you exceed this time limit
- Export to Parquet will generally be faster for larger datasets as a tradeoff to JSON being easier to read

## Step 1: Download the Script

First you’ll want to download the script we have already created to assist in exporting collection data, titled `export_RSCollection_to_AWSS3.py` , which is available in GitHub [here](https://github.com/scottsappen/export-RSCollection-to-s3/blob/main/export_RSCollection_to_AWSS3.py).

## Step 2: Execute the Script

The following examples will create an output file named `export_mycollection_script.sh` .

### Option 1: Use a Rockset integration

<aside>
💡 This is our recommended option.

</aside>

This example uses a read/write Rockset S3 Integration. You can use an existing valid integration or create a new one in the [Integrations tab of the Rockset console](https://console.rockset.com/integrations). You will then use this integration name when executing the script. 

```python
python3 export_RSCollection_to_AWSS3.py \
    --output_file export_mycollection_script.sh \
    --param_RS_region usw2a1 \
    --param_RS_apikey myRSAPIKey \
    --param_RS_wsdotcollectionname prod.mycollection \
    --param_RS_outputformat JSON \
    --param_AWS_S3bucketuri s3://myS3bucket \
    --param_RS_integrationname myRS_S3_IntegrationName
```

### Option 2: Use an AWS IAM Role and AWS External ID

This example uses an AWS IAM Role and AWS External ID instead of a Rockset Integration. You will input these values directly in the script.

<aside>
💡 This example assumes you already have an IAM Role and Policy with read/write access set up.

</aside>

```python
python3 export_RSCollection_to_AWSS3.py \
    --output_file export_mycollection_script.sh \
    --param_RS_region usw2a1 \
    --param_RS_apikey myRSAPIKey \
    --param_RS_wsdotcollectionname prod.mycollection \
    --param_RS_outputformat JSON \
    --param_AWS_S3bucketuri s3://myS3bucket \
    --param_RS_AWSROLE_credentials myIAMroleARN \
    --param_RS_AWSEXTID_credentials myExternalID
```

- **Command Line Arguments**
    - `-output_file` (required): Name of the output file that will contain the generated text
    - `-param_RS_region` (required): The Rockset region your collection exists.
    - `-param_RS_apikey` (required): Your Rockset API key.
    - `-param_RS_wsdotcollectionname` (required): The name of your Rockset workspace.dot.collection. E.g. myproductionenv.mycollection
    - `—param_RS_outputformat` (required): JSON or PARQUET
    - `—param_AWS_S3bucketuri` (required): Your S3 bucket uri
    - `—param_RS_AWSROLE_credentials (optional)`: Either param_RS_integrationname or param_RS_AWSROLE_credentials must be provided.
    - `param_RS_AWSEXTID_credentials (optional)`: Used in conjunction with param_RS_AWSROLE_credentials, Any external ID that is the AWS IAM Role
    - `—param_RS_integrationname (optional)`: Either param_RS_integrationname or param_RS_AWSROLE_credentials must be provided.
    - `—param_AWS_S3outputchunksize` (optional): 1000 is the default if not specified
    - `—param_RS_querysynchronous` (optional): FALSE is the default if you provide nothing; that is to say that an asynchronous query is the default and your script will return you a query_id immediately while the query is still running at Rockset in the background; but if you provide TRUE your query will run synchronously and block until success or failure
    - `—param_RS_adv_filtercollection_byID` (optional): This is advanced feature and only accepts an integer of 1 or 2. If you have a really large dataset, you might need to filter the collection to export it by _id using one of the 16 hex values starting the GUID. If you select 1, then the output file will contain 16 queries that will run sequentially. If you select 2, then the output file will contain 256 queries (16^2) that will run sequentially. Keep this in mind if you are running against large datasets.

### Output

Executing either of the above example options will create a file named with the generated cURL POST command and SQL statement. When you run the script, the collection data will be exported from Rockset and written directly to S3.

The default query mode for this execution is asynchronous. We recommend running this async to ensure that you do not hit any query timeouts. When running async, you will see a response like this:

```JSON
{"query_id":"a63d329a-964e-45d3-a314-30ca0f43ed6a:kBotPiX:0","status":"QUEUED","stats":{"elapsed_time_ms":9,"throttled_time_micros":9000}}
```

Once the request has completed, the results in S3 will look like the following:

```
Amazon S3 → Buckets → myS3bucket → prod.mycollection → a63d329a-964e-45d3-a314-30ca0f43ed6a_kBotPiX_0 → Documents
```

Note that the `a63d329a-964e-45d3-a314-30ca0f43ed6a_kBotPiX_0` value here is a randomly generated query ID from Rockset that identifies your query with the exported results in S3.
