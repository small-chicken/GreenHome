import { useState } from "react";
import { useNavigate } from "react-router-dom";
import './RegistrationForm.css';

function RegistrationForm() {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");

    const onSubmit = (e) => {
        e.preventDefault();
        if (username && password && email) {
        navigate("/schedule");
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