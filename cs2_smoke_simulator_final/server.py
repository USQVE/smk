from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from physics_engine import EnhancedPhysicsEngine
from smoke_finder import SmokeFinder, SearchStrategy
from physics_config import ThrowType
import numpy as np

app = Flask(__name__, static_folder='web')
CORS(app)

physics_engine = None
smoke_finder = None

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'initialized': physics_engine is not None})

@app.route('/find_smokes', methods=['POST'])
def find_smokes():
    global physics_engine, smoke_finder
    if physics_engine is None:
        physics_engine = EnhancedPhysicsEngine(gui=False)
        smoke_finder = SmokeFinder(physics_engine)
    try:
        data = request.json
        target_pos = np.array(data['target_pos'])
        throw_type = ThrowType[data.get('throw_type', 'LEFT_CLICK')]
        strategy = SearchStrategy[data.get('strategy', 'GRID_SEARCH')]
        solutions = smoke_finder.find_smokes(target_pos, throw_type, strategy, 10)
        return jsonify({'success': True, 'smokes': [s.to_dict() for s in solutions]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Server: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
