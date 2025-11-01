import { Link } from "react-router-dom";

function Header () {
    return (
        <nav className = "header">
            <div className = "navbar-links">
                <Link to="/">Logout</Link>
                <Link to="/preferences">Preferences</Link>
                <Link to="/schedule">Schedule</Link>
            </div>
        </nav>
    )
}

export default Header;