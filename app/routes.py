from flask import Blueprint, request, jsonify
from app.services import calculate_total_compensation # Import the calculation function

# Create a Blueprint
# Using a blueprint helps organize routes, especially as the application grows.
# We name it 'main_routes' here, but you could name it based on functionality (e.g., 'compensation_api')
main_routes = Blueprint('main_routes', __name__)

# Example placeholder route
@main_routes.route('/')
def index():
    # This might eventually serve the React app or just be an API status check
    return jsonify({"status": "API is running"})

# We will add the /api/calculate_compensation route here in Step 2
@main_routes.route('/api/calculate_compensation', methods=['POST'])
def handle_calculate_compensation():
    """API endpoint to calculate compensation based on JSON input."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # --- Input Validation --- 
    required_fields = ["role_level", "team_revenue", "last_years_salary", "performance_multiplier"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Basic type checking (more robust validation could be added)
    try:
        role_level = str(data["role_level"])
        team_revenue = float(data["team_revenue"])
        last_years_salary = float(data["last_years_salary"])
        performance_multiplier = float(data["performance_multiplier"])

        # Add constraints if needed (e.g., positive numbers)
        if team_revenue < 0 or last_years_salary < 0 or performance_multiplier < 0:
             raise ValueError("Numeric inputs must be non-negative.")
             
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input type or value: {e}"}), 400
    # --- End Input Validation ---

    # Call the service function to perform the calculation
    result = calculate_total_compensation(
        role_level=role_level,
        team_revenue=team_revenue,
        last_years_salary=last_years_salary,
        performance_multiplier=performance_multiplier
    )

    # Check if the calculation service returned an error
    if "error" in result:
        # Determine appropriate status code based on error type if needed
        status_code = 400 if "Invalid role level" in result["error"] else 500
        return jsonify(result), status_code

    # Return the successful calculation results
    response_data = {
        "inputs_received": data, # Echo back inputs
        **result # Unpack the calculation results dictionary
    }
    return jsonify(response_data), 200
