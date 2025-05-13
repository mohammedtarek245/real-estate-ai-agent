import os
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import pandas as pd
from Ai_agnet_realestate import ArabicRealEstateAgent

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# Initialize global variables
properties_df = None
ai_agent = None

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///realestate_chat.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the database
db.init_app(app)

# Load property data function
def load_data():
    global properties_df, ai_agent
    try:
        properties_df = pd.read_csv("fake_real_estate_data_with_currency.csv")
        # Initialize the AI agent
        ai_agent = ArabicRealEstateAgent(properties_df, dialect="egyptian")
        logger.debug("Property data loaded successfully")
    except Exception as e:
        logger.error(f"Error loading property data: {str(e)}")
        properties_df = pd.DataFrame()
        ai_agent = None

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import Chat, Message
    db.create_all()
    # Load data during app initialization
    load_data()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    chat_id = data.get('chat_id')
    
    if not chat_id:
        # Create a new chat if not provided
        new_chat = Chat(title="Real Estate Chat")
        db.session.add(new_chat)
        db.session.commit()
        chat_id = new_chat.id
    
    # Save user message to database
    user_msg = Message(
        chat_id=chat_id,
        content=user_message,
        is_user=True
    )
    db.session.add(user_msg)
    db.session.commit()
    
    try:
        # Process the message through the AI agent
        ai_response = ai_agent.process_input(user_message)
        
        # Save AI response to database
        ai_msg = Message(
            chat_id=chat_id,
            content=ai_response,
            is_user=False
        )
        db.session.add(ai_msg)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': ai_response,
            'chat_id': chat_id
        })
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.',
            'chat_id': chat_id
        })

@app.route('/api/chats', methods=['GET'])
def get_chats():
    chats = Chat.query.all()
    return jsonify({
        'chats': [{'id': chat.id, 'title': chat.title} for chat in chats]
    })

@app.route('/api/messages/<int:chat_id>', methods=['GET'])
def get_messages(chat_id):
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    return jsonify({
        'messages': [
            {
                'id': msg.id,
                'content': msg.content,
                'is_user': msg.is_user,
                'timestamp': msg.created_at.isoformat()
            } for msg in messages
        ]
    })

@app.route('/api/dialect', methods=['POST'])
def change_dialect():
    data = request.json
    dialect = data.get('dialect', 'egyptian')
    
    if ai_agent:
        confirmation = ai_agent.set_dialect(dialect)
        return jsonify({
            'status': 'success',
            'message': confirmation
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'AI agent not initialized'
        })

@app.route('/api/initial-message', methods=['GET'])
def get_initial_message():
    if ai_agent:
        greeting = ai_agent.get_greeting()
        return jsonify({
            'status': 'success',
            'message': greeting
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'AI agent not initialized'
        })

@app.route('/api/dialects', methods=['GET'])
def get_available_dialects():
    if ai_agent:
        dialects = ai_agent.get_available_dialects()
        return jsonify({
            'status': 'success',
            'dialects': dialects
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'AI agent not initialized'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
