import React from 'react';
import './LoginForm.css';

const LoginForm=()=> {
    return (
        <div className='wrapper'>
           <form action="">
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
                        required
                    />
                </div>
                <button type="submit">Login</button>
                <div className="register-link">
                    <p>Don't have an account?</p>
                    <button>Register</button>
                </div>
           </form>
        </div>        
    );
};

export default LoginForm;