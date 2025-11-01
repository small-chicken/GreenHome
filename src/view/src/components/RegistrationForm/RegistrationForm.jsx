import { useState } from "react";
import { useNavigate } from "react-router-dom";
import './RegistrationForm.css';

function RegistrationForm() {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");

    const onSubmit = async (e) => {
        e.preventDefault();
        setError("");

        try {
            const response = await fetch("http://127.0.0.1:8000/scheduler/register/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password }),
            });

            if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || "Registration failed");
            }

            const data = await response.json();
            console.log("✅ Registered:", data);

            // Save tokens for later authenticated requests
            localStorage.setItem("access", data.access);
            localStorage.setItem("refresh", data.refresh);

            // Redirect after success
            navigate("/schedule");
        } catch (err) {
            console.error("Error:", err);
            setError(err.message || "Something went wrong");
        }
        };

    return (
        <div className='wrapper'>
           <form onSubmit={onSubmit}>
                <h1>Register</h1>
                <div className="input-box">
                    <input 
                        type="text" 
                        placeholder="Username" 
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div className="email-box">
                    <input 
                        type="email" 
                        placeholder="Email" 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div className="password-box">
                    <input 
                        type="password" 
                        placeholder="Password" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit">Register</button>

                <div className="login-link">
                    <p>Don't have an account?</p>
                    <button onClick={() => navigate('/Login')}>Login</button>
                </div>
           </form>
        </div>        
    );
};
  
export default RegistrationForm;