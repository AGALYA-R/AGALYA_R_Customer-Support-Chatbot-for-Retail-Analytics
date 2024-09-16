import re
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from transformers import AutoModelForCausalLM, AutoTokenizer

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Load the LLM model and tokenizer
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Serve frontend files
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Handle chat requests
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message').lower()

        if not user_message:
            return jsonify({"response": "No message received."})

        # Handle greetings
        if any(greeting in user_message for greeting in ['hello', 'hi', 'hey', 'hiii']):
            return jsonify({"response": "Hello! How can I assist you today?"})

        # Handle jokes
        if any(keyword in user_message for keyword in ['joke', 'funny']):
            return jsonify({"response": "Why don’t scientists trust atoms? Because they make up everything!"})

        # Handle motivational quotes
        if 'motivate' in user_message or 'inspire' in user_message:
            return jsonify({"response": "Believe in yourself! Every journey begins with a single step."})

        # Handle weather questions (Example - you can link to an actual weather API)
        if 'weather' in user_message:
            return jsonify({"response": "I'm not connected to a weather service yet, but it looks sunny outside!"})

        # Handle database-related queries
        if 'sales' in user_message or 'product' in user_message:
            response = handle_sql_queries(user_message)
        else:
            # Generate LLM response for general queries
            response = generate_llm_response(user_message)

        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"response": "An error occurred while processing the request."}), 500

def extract_product_name(message):
    # Improved regex to handle various cases
    match = re.search(r'\bsales\s+for\s+(?:a\s+|the\s+)?([a-zA-Z\s]+)', message, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None



def handle_sql_queries(message):
    try:
        conn = sqlite3.connect('e:/retail/backend/retail_data.db')
        cursor = conn.cursor()

        # Total sales for last week
        if 'sales' in message and 'last week' in message:
            query = """
                SELECT SUM(quantity_sold) 
                FROM sales 
                WHERE sale_date BETWEEN date('now', 'start of week', '-1 week') AND date('now', 'start of week', '-1 day')
            """
            cursor.execute(query)
            result = cursor.fetchone()
            total_sales = result[0] if result else 0
            return f"Total sales last week: {total_sales}"

        # Total sales for last month
        elif 'sales' in message and 'last month' in message:
            query = """
                SELECT SUM(quantity_sold) 
                FROM sales 
                WHERE sale_date BETWEEN date('now', 'start of month', '-1 month') AND date('now', 'start of month', '-1 day')
            """
            cursor.execute(query)
            result = cursor.fetchone()
            total_sales = result[0] if result else 0
            return f"Total sales last month: {total_sales}"
        # Sales trends for the past year
        elif 'sales trends' in message and 'past year' in message:
            query = """
                SELECT strftime('%Y-%m', sale_date) as month, SUM(quantity_sold) as total_sales 
                FROM sales 
                WHERE sale_date BETWEEN '2023-01-01' AND '2023-12-31' 
                GROUP BY month 
                ORDER BY month
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if results:
                trends = "\n".join([f"{row[0]}: {row[1]}" for row in results])
                return f"Sales trends for the past year:\n{trends}"
            else:
                return "No sales data available for the past year."

        # Sales for a specific product
        elif 'sales' in message and ('product' in message or 'for' in message):
            product_name = extract_product_name(message)
            if product_name:
                sanitized_product_name = product_name.lower()

                # Debugging: Print the sanitized product name
                print(f"Sanitized product name: {sanitized_product_name}")

                query = """
                    SELECT SUM(quantity_sold) 
                    FROM sales 
                    WHERE LOWER(product_name) = ?
                """
                cursor.execute(query, (sanitized_product_name,))
                result = cursor.fetchone()

                # Debugging: Print the query result
                print(f"Query result: {result}")

                total_sales = result[0] if result else 0
                return f"Total sales for {product_name}: {total_sales}"
            else:
                return "Product name not found in the message."

        # Best-selling product
        elif 'best-selling' in message:
            query = """
                SELECT product_name, SUM(quantity_sold) as total_sales 
                FROM sales 
                GROUP BY product_name 
                ORDER BY total_sales DESC 
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            best_selling = result[0] if result else "Unknown"
            return f"The best-selling product is {best_selling}"

        else:
            return "Sorry, I couldn't understand your query."

    except sqlite3.Error as e:
        return f"Database error: {str(e)}"
    finally:
        conn.close()

def generate_llm_response(message):
    try:
        # Encode the message and send to GPT model
        inputs = tokenizer.encode(message + tokenizer.eos_token, return_tensors='pt')
        outputs = model.generate(inputs, max_length=100, num_return_sequences=1, 
                                 pad_token_id=tokenizer.eos_token_id, 
                                 temperature=0.9, top_k=50, top_p=0.95)
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Filter out overly generic or irrelevant GPT responses
        if len(response.strip()) == 0:
            return "Sorry, I couldn't come up with a response."
        
        return response.strip()
    
    except Exception as e:
        return "Sorry, I couldn't process your request."


if __name__ == '__main__':
    app.run(debug=True, port=5000)
