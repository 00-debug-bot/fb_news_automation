"""
Web Server Module
Provides Flask API for n8n webhook integration and manual triggering
"""

import logging
import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.main import NewsAutomationSystem, setup_logging

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)

# Initialize automation system
automation_system = None


def get_automation_system():
    """Get or create automation system instance"""
    global automation_system
    if automation_system is None:
        # Load config
        config = {}
        config_path = os.getenv('CONFIG_PATH', './config/config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        automation_system = NewsAutomationSystem(config)
    
    return automation_system


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'fb-news-automation'
    })


@app.route('/run', methods=['GET', 'POST'])
def run_automation():
    """
    Trigger automation cycle via API
    
    Accepts optional JSON body with:
    - topic: Process a single specific topic
    - trends: Process a list of trends
    """
    try:
        system = get_automation_system()
        
        # Check for custom input
        data = request.get_json(silent=True) or {}
        
        if 'topic' in data:
            # Process single topic
            result = system.process_single_topic(data['topic'])
            return jsonify({
                'success': result is not None,
                'result': result
            })
        
        elif 'trends' in data:
            # Process batch of trends
            results = []
            for trend in data['trends']:
                result = system._process_trend(trend)
                if result:
                    results.append(result)
            
            return jsonify({
                'success': len(results) > 0,
                'results': results,
                'processed': len(results),
                'total': len(data['trends'])
            })
        
        else:
            # Run full automation cycle
            result = system.run_cycle()
            return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in /run endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get current system status and statistics"""
    try:
        system = get_automation_system()
        
        # Get storage stats
        stats = system.storage.get_post_stats(days=7)
        
        # Get recent topics
        recent_topics = system.storage.get_recent_topics(count=10)
        
        return jsonify({
            'status': 'running',
            'statistics': stats,
            'recent_topics': recent_topics,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in /status endpoint: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/topics', methods=['GET'])
def get_topics():
    """Get list of recently posted topics"""
    try:
        system = get_automation_system()
        
        limit = request.args.get('limit', 20, type=int)
        topics = system.storage.get_all_topics(limit=limit)
        
        return jsonify({
            'topics': topics,
            'count': len(topics)
        })
    
    except Exception as e:
        logger.error(f"Error in /topics endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/trends', methods=['GET'])
def get_trends():
    """Fetch current trending topics without processing"""
    try:
        system = get_automation_system()
        
        # Fetch trends
        trends = system._fetch_trends()
        
        return jsonify({
            'trends': trends,
            'count': len(trends)
        })
    
    except Exception as e:
        logger.error(f"Error in /trends endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/preview', methods=['POST'])
def preview_news_card():
    """
    Preview a news card without posting
    
    Accepts JSON body with:
    - topic: The topic to process
    """
    try:
        data = request.get_json(silent=True) or {}
        
        if 'topic' not in data:
            return jsonify({
                'error': 'Topic is required'
            }), 400
        
        system = get_automation_system()
        
        # Set skip_facebook flag
        original_skip = system.skip_facebook
        system.skip_facebook = True
        
        try:
            result = system.process_single_topic(data['topic'])
            
            if result:
                return jsonify({
                    'success': True,
                    'preview': result,
                    'note': 'Image created but not posted to Facebook'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to process topic'
                }), 400
        
        finally:
            system.skip_facebook = original_skip
    
    except Exception as e:
        logger.error(f"Error in /preview endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/cleanup', methods=['POST'])
def cleanup_storage():
    """
    Clean up old records from storage
    
    Accepts optional JSON body with:
    - days: Number of days threshold (default: 30)
    """
    try:
        data = request.get_json(silent=True) or {}
        days = data.get('days', 30)
        
        system = get_automation_system()
        system.storage.cleanup_old_records(days=days)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up records older than {days} days'
        })
    
    except Exception as e:
        logger.error(f"Error in /cleanup endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /health',
            'GET /status',
            'GET /topics',
            'GET /trends',
            'POST /run',
            'POST /preview',
            'POST /cleanup'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error'
    }), 500


def main():
    """Run the web server"""
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting web server on port {port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )


if __name__ == '__main__':
    main()