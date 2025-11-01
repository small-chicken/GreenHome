import { Link } from "react-router-dom";
import "./Header.css";
import {useContext} from "react";
import { AuthContext } from "../../Contexts/AuthContext.jsx";

function Header () {
    const {user, setUser} = useContext(AuthContext);
    function handleLogout() {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        setUser(null);
    }
    
    return (
        <nav className = "header">
            <div className="username-display">
               <p>Welcome, <strong>{user.username}</strong></p> 
            </div>
            <div className = "navbar-links">
                <Link to="/preferences">Preferences</Link>
                <Link to="/schedule">Schedule</Link>
            </div>
            <div className = "authentication-links">
                <Link to="/login" onClick={handleLogout}>Logout</Link>
            </div>
        </nav>
    )
}

export default Header;