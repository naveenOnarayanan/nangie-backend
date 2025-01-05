import json
from flask import Flask, request, jsonify
from backend_lambda import lambda_handler

# Initialize Flask app
app = Flask(__name__)

def create_mock_event(path_parameters=None, query_parameters=None, body=None):
    """Create a mock API Gateway event"""
    return {
        'pathParameters': path_parameters or {},
        'queryStringParameters': query_parameters or {},
        'body': json.dumps(body) if body else None,
    }

@app.route('/test/direct', methods=['GET'])
def test_direct():
    """Test the lambda function directly with a mock event"""
    code = request.args.get('code', 'NANGIE123')
    
    # Create a mock event
    test_event = create_mock_event(
        path_parameters={'code': code}
    )
    
    # Call lambda handler directly
    response = lambda_handler(test_event, None)
    
    return jsonify(response)

@app.route('/api/user/<code>', methods=['GET'])
def api_endpoint(code):
    """Simulate the actual API Gateway endpoint"""
    # Create a mock event that matches API Gateway's format
    test_event = create_mock_event(
        path_parameters={'code': code}
    )
    
    # Call lambda handler
    response = lambda_handler(test_event, None)
    
    # Extract the response body and status code
    return (
        response['body'],
        response['statusCode'],
        response['headers']
    )

def run_single_test():
    """Run a single test case directly"""
    test_event = create_mock_event(
        path_parameters={'code': 'NANGIE123'}
    )
    
    print("Testing with event:", json.dumps(test_event, indent=2))
    response = lambda_handler(test_event, None)
    print("\nResponse:", json.dumps(response, indent=2))

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("No!")
        # Run single test case
        run_single_test()
    else:
        print("Hello!")
        # Run Flask development server
        app.run(debug=True, port=5000)
