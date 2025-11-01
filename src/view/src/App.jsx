import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Registration from "./pages/Registration.jsx";
import Events from "./pages/Events.jsx";
import Schedule from "./pages/Schedule.jsx";

function App() {

  return (
    <main className="main-content">
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registration" element={<Registration />} />
        <Route path="/events" element={<Events />} />
        <Route path="/schedule" element={<Schedule />} />
      </Routes>
    </main>
  )
}

export default App
