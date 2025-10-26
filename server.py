import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from agent.ai_agent import main as ai_main

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _parse_json_result(result_data, query):
    """Parse JSON result from AI agent."""
    if 'result' in result_data and result_data.get('success', True):
        return jsonify({
            'status': 'success',
            'result': result_data.get('answer', result_data['result']),
            'query': result_data.get('query', query)
        })
    elif not result_data.get('success', True):
        return jsonify({
            'status': 'error',
            'message': result_data.get('result', 'Unknown error')
        }), 500
    return None


def _parse_fallback_result(result, query):
    """Fallback parser for string results."""
    if isinstance(result, str) and 'FINAL_ANSWER:' in result:
        final_answer = result.split('FINAL_ANSWER:')[-1].strip('[] \'"')
        if 'Query:' in final_answer:
            final_answer = final_answer.split('Result:')[-1].strip()
        return jsonify({
            'status': 'success',
            'result': final_answer,
            'query': query
        })
    return None


def _process_agent_result(result, query):
    """Process and format agent result."""
    import json
    
    if result is None:
        logger.error("Agent returned None - possible timeout or error")
        return jsonify({
            'status': 'error',
            'message': 'Agent failed to process query. Check logs for details.'
        }), 500
    
    try:
        if isinstance(result, str):
            result_data = json.loads(result)
            logger.debug(f"Parsed result data: {result_data}")
            response = _parse_json_result(result_data, query)
            if response:
                return response
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI agent response as JSON: {e}")
        logger.error(f"Raw result: {result}")
        fallback = _parse_fallback_result(result, query)
        if fallback:
            return fallback
    
    logger.error(f"Unexpected result format: {result}")
    return jsonify({
        'status': 'error',
        'message': 'Unexpected response format from agent',
        'raw_result': str(result) if result else 'None'
    }), 500


@app.route('/api/query', methods=['POST'])
async def handle_query():
    try:
        data = request.get_json()
        query = data.get('query')
        preferences = data.get('preferences', {})
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        logger.info(f"Received query: {query}")
        logger.info(f"User preferences: {preferences}")
        
        result = await ai_main(query, preferences=preferences)
        return _process_agent_result(result, query)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Make sure the server is accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)
