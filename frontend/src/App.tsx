import { useState } from 'react';
import './App.css';

// --- Interfaces for Data Structures ---
type RoleLevel = "Junior" | "Mid-level" | "Senior" | "Executive";

interface CompInputForm {
  role_level: RoleLevel;
  team_revenue: string; // Use string for input fields, convert later
  last_years_salary: string;
  performance_multiplier: string;
}

interface LtiBreakdown {
  deferred_cash: number;
  equity_award_value: number;
  fund_investment_amount: number;
}

interface CompResult {
  inputs_received?: CompInputForm; // Optional: Echoed inputs
  calculated_base_salary?: number;
  target_bonus_amount?: number;
  performance_bonus?: number;
  lti_breakdown?: LtiBreakdown;
  immediate_cash_bonus?: number;
  error?: string; // To display calculation or API errors
}

// --- Role Level Options --- 
const roleLevels: RoleLevel[] = ["Junior", "Mid-level", "Senior", "Executive"];

function App() {
  // --- State Variables ---
  const [formData, setFormData] = useState<CompInputForm>({
    role_level: "Mid-level", // Default value
    team_revenue: '',
    last_years_salary: '',
    performance_multiplier: '1.0', // Default value
  });

  const [result, setResult] = useState<CompResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // --- Batch Upload State ---
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchError, setBatchError] = useState<string | null>(null);
  const [batchLoading, setBatchLoading] = useState<boolean>(false);

  // --- Event Handlers ---
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value,
    }));
    setError(null); // Clear previous errors on input change
    setResult(null); // Clear previous results
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    // Basic Frontend Validation (can be expanded)
    if (!formData.team_revenue || !formData.last_years_salary || !formData.performance_multiplier) {
      setError("Please fill in all numeric fields.");
      setIsLoading(false);
      return;
    }

    // --- Prepare data for API --- 
    // Convert string inputs to numbers where appropriate
    const payload = {
      ...formData,
      team_revenue: parseFloat(formData.team_revenue),
      last_years_salary: parseFloat(formData.last_years_salary),
      performance_multiplier: parseFloat(formData.performance_multiplier),
    };

    // Validate numeric conversion
    if (isNaN(payload.team_revenue) || isNaN(payload.last_years_salary) || isNaN(payload.performance_multiplier)) {
        setError("Please enter valid numbers for revenue, salary, and multiplier.");
        setIsLoading(false);
        return;
    }
    if (payload.team_revenue < 0 || payload.last_years_salary < 0 || payload.performance_multiplier < 0) {
        setError("Numeric inputs cannot be negative.");
        setIsLoading(false);
        return;
    }

    // --- API Call (will be implemented in Step 4) ---
    try {
      // The request goes to /api/calculate_compensation, which Vite will proxy
      // to http://localhost:5000/api/calculate_compensation
      const response = await fetch('/api/calculate_compensation', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add Auth headers here if needed (implemented in Step 5)
          // 'Authorization': 'Basic ' + btoa('username:password'), 
        },
        body: JSON.stringify(payload),
      });

      const data: CompResult = await response.json();

      if (!response.ok) {
          // Use the error message from the backend if available
        throw new Error(data.error || `HTTP error! Status: ${response.status}`);
      }

      // Check if backend itself returned a logical error (e.g., invalid role)
      if (data.error) {
          throw new Error(data.error);
      }

      setResult(data); // Set the successful result data

    } catch (err: any) {
      console.error("API Call failed:", err); // Log the error for debugging
      // Display a user-friendly error message
      setError(err.message || "Failed to fetch compensation data. Check console for details.");
      setResult(null); // Ensure no previous results are shown
    }

    setIsLoading(false);
  };

  // --- Batch Upload Handler ---
  const handleBatchFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setBatchFile(e.target.files[0]);
      setBatchError(null);
    }
  };

  const handleBatchSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBatchError(null);
    setBatchLoading(true);

    if (!batchFile) {
      setBatchError('Please select a CSV or Excel file to upload.');
      setBatchLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append('file', batchFile);

    try {
      const response = await fetch('/api/batch_calculate_compensation', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Batch calculation failed.');
      }
      // Download the CSV file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'compensation_results.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setBatchError(err.message);
    } finally {
      setBatchLoading(false);
    }
  };

  // --- Helper to format currency ---
  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `£${value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // --- Render Logic ---
  return (
    <div className="container mx-auto p-4 max-w-2xl bg-white shadow-md rounded-lg">
      <h1 className="text-2xl font-bold mb-6 text-center text-gray-700">Compensation Calculator</h1>

      {/* --- Input Form --- */}
      <form onSubmit={handleSubmit} className="space-y-4 mb-8">
        {/* Role Level */}
        <div>
          <label htmlFor="role_level" className="block text-sm font-medium text-gray-700 mb-1">Role Level:</label>
          <select
            id="role_level"
            name="role_level"
            value={formData.role_level}
            onChange={handleInputChange}
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          >
            {roleLevels.map(level => (
              <option key={level} value={level}>{level}</option>
            ))}
          </select>
        </div>

        {/* Team Revenue */}
        <div>
          <label htmlFor="team_revenue" className="block text-sm font-medium text-gray-700 mb-1">Trailing 12m Team Revenue (£):</label>
          <input
            type="number"
            id="team_revenue"
            name="team_revenue"
            value={formData.team_revenue}
            onChange={handleInputChange}
            required
            step="any" // Allow decimals
            min="0"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="e.g., 20000000"
          />
        </div>

        {/* Last Year's Salary */}
        <div>
          <label htmlFor="last_years_salary" className="block text-sm font-medium text-gray-700 mb-1">Last Year's Base Salary (£):</label>
          <input
            type="number"
            id="last_years_salary"
            name="last_years_salary"
            value={formData.last_years_salary}
            onChange={handleInputChange}
            required
            step="any"
            min="0"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="e.g., 250000"
          />
        </div>

        {/* Performance Multiplier */}
        <div>
          <label htmlFor="performance_multiplier" className="block text-sm font-medium text-gray-700 mb-1">Performance Multiplier:</label>
          <input
            type="number"
            id="performance_multiplier"
            name="performance_multiplier"
            value={formData.performance_multiplier}
            onChange={handleInputChange}
            required
            step="0.01" // Allow fine adjustments
            min="0" // Technically could be 0, though likely higher
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="e.g., 1.2"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${isLoading ? 'bg-indigo-300' : 'bg-indigo-600 hover:bg-indigo-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50`}
        >
          {isLoading ? 'Calculating...' : 'Calculate Compensation'}
        </button>
      </form>

      {/* --- Error Display --- */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      {/* --- Results Display --- */}
      {result && !error && (
        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Calculation Results:</h2>
          <div className="space-y-3">
            <ResultItem label="Calculated Base Salary" value={formatCurrency(result.calculated_base_salary)} />
            <ResultItem label="Target Bonus Amount" value={formatCurrency(result.target_bonus_amount)} />
            <ResultItem label="Performance Bonus (Total)" value={formatCurrency(result.performance_bonus)} isBold={true}/>
            
            <h3 className="text-lg font-medium pt-3 text-gray-700 border-t border-gray-200 mt-3">Bonus & LTI Breakdown:</h3>
            <ResultItem label="Immediate Cash Bonus" value={formatCurrency(result.immediate_cash_bonus)} />
            {result.lti_breakdown && (
              <>
                <ResultItem label="Deferred Cash" value={formatCurrency(result.lti_breakdown.deferred_cash)} />
                <ResultItem label="Fund Investment Amount" value={formatCurrency(result.lti_breakdown.fund_investment_amount)} />
                <ResultItem label="Equity Award Value" value={formatCurrency(result.lti_breakdown.equity_award_value)} />
              </>
            )}
          </div>
        </div>
      )}
      {/* --- Batch Upload Section --- */}
      <div className="mt-10 p-6 bg-white rounded-lg shadow border border-gray-200">
        <h2 className="text-lg font-semibold mb-4 text-gray-800">Batch Compensation Calculator (CSV/Excel Upload)</h2>
        <form onSubmit={handleBatchSubmit} className="space-y-4">
          <input
            type="file"
            accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            onChange={handleBatchFileChange}
            className="block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          <button
            type="submit"
            disabled={batchLoading}
            className={`w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${batchLoading ? 'bg-indigo-300' : 'bg-indigo-600 hover:bg-indigo-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50`}
          >
            {batchLoading ? 'Processing...' : 'Upload & Download Results'}
          </button>
        </form>
        {batchError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mt-4" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{batchError}</span>
          </div>
        )}
        <div className="text-xs text-gray-500 mt-3">
          File must contain columns: <code>role_level</code>, <code>team_revenue</code>, <code>last_years_salary</code>, <code>performance_multiplier</code>. Results will be downloaded as a CSV.
        </div>
      </div>
    </div>
  );
}

// --- Helper Component for Result Items --- 
interface ResultItemProps {
    label: string;
    value: string | number;
    isBold?: boolean;
}

const ResultItem: React.FC<ResultItemProps> = ({ label, value, isBold = false }) => (
    <div className="flex justify-between items-center text-sm">
        <span className="text-gray-600">{label}:</span>
        <span className={`text-gray-900 ${isBold ? 'font-semibold' : ''}`}>{value}</span>
    </div>
);


export default App;
