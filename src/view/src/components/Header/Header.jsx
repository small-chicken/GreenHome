import { Link } from "react-router-dom";
import "./Header.css";

function Header ({ isAuthenticated = false, onLogout }) {
    return (
        <nav className = "header">
            <div className = "navbar-links">
                <Link to="/preferences">Preferences</Link>
                <Link to="/schedule">Schedule</Link>
            </div>
            <div className = "authentication-links">
                {isAuthenticated ? (
                    <Link to="/" onClick={onLogout}>Logout</Link>
                ) : (
                     <>
                        <Link to="/login">Log in</Link>
                        <Link to="/registration">Register</Link>
                    </>
                )}
            </div>
        </nav>
    )
}

export default Header;