import React, { useState, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import {AuthContext} from "../../Contexts/AuthContext.jsx"
import './LoginForm.css';

const LoginForm=()=> {
    const navigate = useNavigate();

    const { setUser } = useContext(AuthContext);

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const onSubmit = async(e) => {
        e.preventDefault();
        setError("");

        try {
      const response = await fetch("http://127.0.0.1:8000/scheduler/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username:username.trim(), password }),
      });

      if (!response.ok) {
      // DRF sends errors like { non_field_errors: ["Invalid credentials"] }
      const backendError =
        data.non_field_errors?.[0] ||
        data.detail ||
        data.error ||
        "Login failed";
      throw new Error(backendError);
    }

      const data = await response.json();
      console.log("✅ Logged in:", data);

      // Store tokens locally
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);

      // Save user in context
      setUser({
        username: data.user.username,
        email: data.user.email,
        access: data.access,
      });

      // Redirect to schedule
      navigate("/schedule");
    } catch (err) {
      console.error("Error:", err);
      setError(err.message || "Something went wrong");
    }
  };

    return (
        <div className='wrapper'>
           <form onSubmit={onSubmit}>
                <h1>Login</h1>
                <div className="input-box">
                    <input 
                        type="text" 
                        placeholder="Username" 
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
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
                <button type="submit">Login</button>

                <div className="register-link">
                    <p>Don't have an account?</p>
                    <button onClick={() => navigate('/Registration')}>Register</button>
                </div>
           </form>
        </div>        
    );
};

export default LoginForm;