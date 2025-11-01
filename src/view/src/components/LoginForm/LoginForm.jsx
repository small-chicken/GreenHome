import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import './LoginForm.css';

const LoginForm=()=> {

    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const onSubmit = (e) => {
        e.preventDefault();
        if (username && password) {
        navigate("/schedule");
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