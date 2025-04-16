from flask import Blueprint, request, jsonify, send_file
from app.services import calculate_total_compensation # Import the calculation function
import pandas as pd
import io

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

@main_routes.route('/api/batch_calculate_compensation', methods=['POST'])
def batch_calculate_compensation():
    """Batch API endpoint to process uploaded CSV or Excel files and return results as downloadable file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    # Determine file type and read into DataFrame
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({"error": "Unsupported file type. Please upload CSV or Excel files."}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {e}"}), 400

    # Required columns
    required_fields = ["role_level", "team_revenue", "last_years_salary", "performance_multiplier"]
    missing_fields = [col for col in required_fields if col not in df.columns]
    if missing_fields:
        return jsonify({"error": f"Missing required columns: {', '.join(missing_fields)}"}), 400

    # Prepare results list
    results = []
    for idx, row in df.iterrows():
        try:
            result = calculate_total_compensation(
                role_level=str(row["role_level"]),
                team_revenue=float(row["team_revenue"]),
                last_years_salary=float(row["last_years_salary"]),
                performance_multiplier=float(row["performance_multiplier"])
            )
        except Exception as e:
            result = {"error": str(e)}
        # Combine input and output for each row
        row_result = {**row.to_dict(), **result}
        results.append(row_result)

    # Create result DataFrame
    result_df = pd.DataFrame(results)
    # Output as CSV
    output = io.StringIO()
    result_df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='compensation_results.csv'
    )
