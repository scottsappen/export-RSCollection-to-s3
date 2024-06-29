import argparse

def create_or_overwrite_file(output_file, content):
    with open(output_file, 'w') as file:
        file.write(content + "\n")
    print(f"Content written to {output_file}")

def generate_RS_export_script(param_RS_region, param_RS_apikey, param_RS_wsdotcollectionname, param_RS_outputformat,
                              param_RS_integrationname, param_RS_AWSROLE_credentials, param_AWS_S3bucketuri, 
                              param_AWS_S3outputchunksize, param_RS_querysynchronous, param_RS_adv_filtercollection_byID, param_RS_AWSEXTID_credentials):
    # Prepare the hex characters for filtering
    hex_chars = '0123456789abcdef'
    
    # List to hold all queries
    queries = []
    
    # Determine the base query
    base_query = f"INSERT INTO '{param_AWS_S3bucketuri}/{param_RS_wsdotcollectionname}' "
    
    if param_RS_AWSROLE_credentials:
        base_query += (
            f"CREDENTIALS=(AWS_ROLE='{param_RS_AWSROLE_credentials}', "
            f"AWS_EXTERNAL_ID='{param_RS_AWSEXTID_credentials}') "
        )
    else:
        base_query += f"INTEGRATION = '{param_RS_integrationname}' "
    
    base_query += f"FORMAT = (TYPE='{param_RS_outputformat}', INCLUDE_QUERY_ID=true) SELECT * FROM {param_RS_wsdotcollectionname}"
    
    # Generate queries based on the filter collection parameter
    if param_RS_adv_filtercollection_byID == '1':
        for hexvalue in hex_chars:
            query = base_query + f" WHERE _id LIKE '{hexvalue}%'"
            if param_AWS_S3outputchunksize:
                query += f" HINT(s3_sync_op_output_chunk_size={param_AWS_S3outputchunksize})"
            queries.append(query)
    elif param_RS_adv_filtercollection_byID == '2':
        for hexvalue1 in hex_chars:
            for hexvalue2 in hex_chars:
                query = base_query + f" WHERE _id LIKE '{hexvalue1}{hexvalue2}%'"
                if param_AWS_S3outputchunksize:
                    query += f" HINT(s3_sync_op_output_chunk_size={param_AWS_S3outputchunksize})"
                queries.append(query)
    else:
        query = base_query
        if param_AWS_S3outputchunksize:
            query += f" HINT(s3_sync_op_output_chunk_size={param_AWS_S3outputchunksize})"
        queries.append(query)
    
    # Check if the query should be synchronous or asynchronous
    async_query = 'true' if param_RS_querysynchronous is None or param_RS_querysynchronous.upper() != 'TRUE' else 'false'
    
    # Generate the output content with multiple CURL requests if needed
    content = ""
    for query in queries:
        content += (
            f"curl --request POST \\\n"
            f"     --url https://api.{param_RS_region}.rockset.com/v1/orgs/self/queries \\\n"
            f"     --header 'Authorization: ApiKey {param_RS_apikey}' \\\n"
            f"     --header 'accept: application/json' \\\n"
            f"     --header 'content-type: application/json' \\\n"
            f"     --data @- <<EOF\n"
            f"{{\n"
            f"  \"sql\": {{\n"
            f"    \"query\": \"{query}\"\n"
            f"  }},\n"
            f"  \"async\": {async_query}\n"
            f"}}\n"
            f"EOF\n\n"
        )
    
    return content

def main():
    parser = argparse.ArgumentParser(description="Generate Rockset export script and write to a file.")
    parser.add_argument('--output_file', type=str, required=True, help="The name of the output file.")  # Required
    parser.add_argument('--param_RS_region', type=str, required=True, help="Rockset region.")  # Required
    parser.add_argument('--param_RS_apikey', type=str, required=True, help="Rockset API key.")  # Required
    parser.add_argument('--param_RS_wsdotcollectionname', type=str, required=True, help="Rockset collection name.")  # Required
    parser.add_argument('--param_RS_outputformat', type=str, choices=['JSON', 'PARQUET'], required=True, help="Output format (JSON or PARQUET).")  # Required
    parser.add_argument('--param_RS_integrationname', type=str, help="Rockset integration name.")  # Optional
    parser.add_argument('--param_RS_AWSROLE_credentials', type=str, help="Rockset AWS role credentials.")  # Optional
    parser.add_argument('--param_RS_AWSEXTID_credentials', type=str, help="Any external ID that is the AWS IAM Role")  # Optional
    parser.add_argument('--param_AWS_S3bucketuri', type=str, required=True, help="AWS S3 bucket URI.")  # Required
    parser.add_argument('--param_AWS_S3outputchunksize', type=str, help="AWS S3 output chunk size.", nargs='?', default=None)  # Optional
    parser.add_argument('--param_RS_querysynchronous', type=str, help="Run query synchronously if TRUE.", nargs='?', default=None)  # Optional
    parser.add_argument('--param_RS_adv_filtercollection_byID', type=str, choices=['1', '2'], help="Filter collection to split large tables.", nargs='?', default=None)  # Optional
    
    args = parser.parse_args()

    # Ensure one of param_RS_integrationname or param_RS_AWSROLE_credentials is provided
    if not (args.param_RS_integrationname or args.param_RS_AWSROLE_credentials):
        parser.error("Either param_RS_integrationname or param_RS_AWSROLE_credentials must be provided.")
    
    # Generate the content
    content = generate_RS_export_script(
        args.param_RS_region, args.param_RS_apikey, args.param_RS_wsdotcollectionname, args.param_RS_outputformat,
        args.param_RS_integrationname, args.param_RS_AWSROLE_credentials, args.param_AWS_S3bucketuri, args.param_AWS_S3outputchunksize, args.param_RS_querysynchronous, args.param_RS_adv_filtercollection_byID, args.param_RS_AWSEXTID_credentials
    )
    
    # Write the content to the file
    create_or_overwrite_file(args.output_file, content)

if __name__ == "__main__":
    main()
