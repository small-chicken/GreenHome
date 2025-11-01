import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Registration from "./pages/Registration.jsx";
import Preferences from "./pages/Preferences.jsx";
import Options from "./pages/Options.jsx";
import Schedule from "./pages/Schedule.jsx";
import Calendar from "./components/Calendar/Calendar.jsx";

function App() {

  return (
    <main className="main-content">
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/registration" element={<Registration />} />
        <Route path="/preferences" element={<Preferences />} />
        <Route path="/options" element={<Options />} />
        <Route path="/schedule" element={<Schedule />} />
      </Routes>
    </main>
  )
}

export default App
