import React from "react";
import { Link } from "react-router-dom";
import './EventSetter.css';

function EventSetter() {
    const appliances = [{name: "Washing Machine", id: 0},
                    {name: "Dishwasher", id: 1},
                    {name: "Dryer", id: 2},
                    {name: "Electric Vehicle", id: 3},
                    {name: "Heating System", id: 4},
                    {name: "Kitchen Appliances", id: 5},
    ]

   const [open, setOpen] = React.useState(false);
   const [label, setLabel] = React.useState("Choose an appliance");
   const ref = React.useRef(null);

   React.useEffect(() => {
    const onDocClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
    }, []);

    return (
    <div className="event-setter">

      <div
        className={`pref-dropdown ${open ? "is-open" : ""}`}
        ref={ref}
      >
        <button
          type="button"
          className="pref-dropdown__trigger"
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          {label} ▾
        </button>

        <div className="pref-dropdown__menu" role="menu">
          {appliances.map((a) => (
            <Link
              key={a.id}
              to={`/appliances/${a.id}`}
              role="menuitem"
              className="pref-dropdown__item"
              onClick={() => {
                setLabel(a.name);
                setOpen(false);
              }}
            >
              {a.name}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default EventSetter